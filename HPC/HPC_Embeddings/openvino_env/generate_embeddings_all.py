#!/usr/bin/env python3
import json
import numpy as np
import glob
import openvino as ov
from tqdm import tqdm
import os
import argparse
import re
from openvino.runtime import properties

# Add Modin with fallback to pandas if not available
try:
    import modin.pandas as pd
    from modin.config import Engine
    # Set Ray as the execution engine for Modin
    Engine.put("ray")
    print("Using Modin with Ray backend for enhanced DataFrame performance")
except ImportError:
    import pandas as pd
    print("Modin not found. Using regular pandas instead. Consider installing Modin for better performance.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process JSONL files across multiple folders and generate embeddings.')
    parser.add_argument('--base_dir', type=str, required=True,
                        help='Base directory containing the consol_XX folders')
    parser.add_argument('--output_base_dir', type=str, required=True,
                        help='Base directory for output files (e.g., Embeddings/acts/)')
    parser.add_argument('--model_path', type=str, default='openvino_model.xml',
                        help='Path to the OpenVINO model XML file')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size for inference')
    parser.add_argument('--num_streams', type=int, default=8,
                        help='Number of inference streams')
    parser.add_argument('--folder_pattern', type=str, default='consol_*',
                        help='Pattern to match folder names (e.g., consol_*)')
    parser.add_argument('--folder_range', type=str, default=None,
                        help='Range of folder numbers to process (e.g., 40-43)')
    parser.add_argument('--process_rank_0', action='store_true',
                        help='Process rank_0 files')
    parser.add_argument('--process_rank_1', action='store_true',
                        help='Process rank_1 files')
    parser.add_argument('--use_modin', action='store_true',
                        help='Use Modin for DataFrame operations (if available)')
    parser.add_argument('--ray_cpus', type=int, default=None,
                        help='Number of CPUs to use for Ray (Modin backend)')
    
    args = parser.parse_args()
    
    # If neither rank is specified, process both by default
    if not args.process_rank_0 and not args.process_rank_1:
        args.process_rank_0 = True
        args.process_rank_1 = True
        
    return args

def setup_openvino():
    # Configure OpenVINO Core
    core = ov.Core()

    # Set optimal CPU config for throughput
    core.set_property("CPU", {
        properties.hint.performance_mode(): properties.hint.PerformanceMode.THROUGHPUT,
        properties.num_streams(): "AUTO",
        properties.inference_num_threads(): 0,
        properties.hint.enable_cpu_pinning(): True,
        properties.hint.enable_hyper_threading(): True
    })
    
    return core

def read_jsonl_to_df(file_path):
    """Read JSONL file and return a DataFrame with metadata."""
    try:
        # Read lines as JSON
        with open(file_path, 'r') as f:
            data_list = [json.loads(line) for line in f]
        
        if not data_list:
            print(f"⚠️ No data found in {file_path}")
            return None, None
        
        # Extract tokens and metadata
        tokens_list = [item['tokens'] for item in data_list]
        metadata = [{k: v for k, v in item.items() if k != 'tokens'} for item in data_list]
        
        # Create DataFrame from metadata
        df = pd.DataFrame(metadata)
        
        # Add source file information
        df["source_file"] = os.path.basename(file_path)
        
        return df, tokens_list
    
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return None, None

def process_file(file_path, compiled_model, batch_size=16, num_streams=8):
    """Process a single JSONL file and return a DataFrame with embeddings."""
    print(f"\nProcessing: {file_path}")

    # Read data
    df, tokens_list = read_jsonl_to_df(file_path)
    if df is None or tokens_list is None or len(tokens_list) == 0:
        return None

    seq_len = len(tokens_list[0])
    print(f"Found {len(tokens_list)} examples with sequence length: {seq_len}")

    # Generate embeddings
    pooled_embeddings = generate_embeddings(tokens_list, compiled_model, batch_size, num_streams, seq_len)
    
    if not pooled_embeddings:
        print("⚠️ No embeddings generated")
        return None
    
    # Convert to numpy array
    final_embeddings = np.vstack(pooled_embeddings)
    print(f"Generated {final_embeddings.shape[0]} embeddings (dim: {final_embeddings.shape[1]})")
    
    # Add embeddings to DataFrame
    # Using a list comprehension for better performance with large arrays
    df["embedding"] = [list(map(float, vec)) for vec in final_embeddings]
    
    return df

def generate_embeddings(tokens_list, compiled_model, batch_size, num_streams, seq_len):
    """Generate embeddings using the compiled model."""
    pooled_embeddings = []
    infer_requests = [compiled_model.create_infer_request() for _ in range(num_streams)]

    for i in tqdm(range(0, len(tokens_list), batch_size * num_streams)):
        active_requests = []

        for j in range(num_streams):
            idx = i + j * batch_size
            if idx >= len(tokens_list):
                break

            batch_tokens = tokens_list[idx:idx+batch_size]
            batch_size_actual = len(batch_tokens)

            input_ids = np.array(batch_tokens).astype(np.int64)
            attention_mask = np.ones((batch_size_actual, seq_len), dtype=np.int64)
            token_type_ids = np.zeros((batch_size_actual, seq_len), dtype=np.int64)

            try:
                infer_requests[j].start_async({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids
                })
                active_requests.append((j, batch_size_actual))

            except Exception as e:
                print(f"Start_async error on stream {j}, falling back to sync: {e}")
                results = compiled_model({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids
                })
                output_key = list(results.keys())[0]
                mean_embeds = np.mean(results[output_key], axis=1)  # mean pooling
                pooled_embeddings.append(mean_embeds)

        for j, actual_batch_size in active_requests:
            infer_requests[j].wait()
            output_tensor = infer_requests[j].get_output_tensor()
            raw_output = output_tensor.data[:actual_batch_size]  # shape: (batch, seq, dim)
            mean_embeds = np.mean(raw_output, axis=1)  # mean pool across sequence
            pooled_embeddings.append(mean_embeds)
            
    return pooled_embeddings

def initialize_modin(ray_cpus=None):
    """Initialize Modin with Ray backend if available."""
    try:
        import ray
        # Only initialize Ray if it hasn't been initialized yet
        if not ray.is_initialized():
            if ray_cpus:
                ray.init(num_cpus=ray_cpus)
            else:
                ray.init()
            print(f"Initialized Ray with {ray.available_resources().get('CPU', 'unknown')} CPUs")
        return True
    except ImportError:
        print("Ray not available. Modin will use its default backend.")
        return False

def get_folders_to_process(base_dir, folder_pattern, folder_range=None):
    """Get list of folders to process based on pattern and range."""
    all_folders = glob.glob(os.path.join(base_dir, folder_pattern))
    
    # If no range is specified, return all matching folders
    if not folder_range:
        return sorted(all_folders)
    
    # Parse folder range (e.g., "40-43")
    try:
        range_start, range_end = map(int, folder_range.split('-'))
        
        # Filter folders based on range
        filtered_folders = []
        for folder in all_folders:
            folder_name = os.path.basename(folder)
            # Extract number from folder name using regex
            match = re.search(r'consol_(\d+)', folder_name)
            if match:
                folder_num = int(match.group(1))
                if range_start <= folder_num <= range_end:
                    filtered_folders.append(folder)
        
        return sorted(filtered_folders)
    
    except ValueError:
        print(f"⚠️ Invalid folder range format: {folder_range}. Using all matching folders.")
        return sorted(all_folders)

def process_folder(input_folder, output_folder, compiled_model, batch_size, num_streams, process_rank_0, process_rank_1):
    """Process all matching files in a folder and save results."""
    print(f"\n{'='*80}")
    print(f"Processing folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"{'='*80}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get list of files to process
    files_to_process = []
    
    if process_rank_0:
        rank_0_files = glob.glob(os.path.join(input_folder, "rank_0_*.jsonl"))
        files_to_process.extend(rank_0_files)
        
    if process_rank_1:
        rank_1_files = glob.glob(os.path.join(input_folder, "rank_1_*.jsonl"))
        files_to_process.extend(rank_1_files)
    
    if not files_to_process:
        print(f"⚠️ No files found in {input_folder} matching the specified rank patterns")
        return False
    
    print(f"Found {len(files_to_process)} files to process")
    
    # Process each file and save individually
    for file_path in files_to_process:
        df = process_file(file_path, compiled_model, batch_size, num_streams)
        if df is not None:
            base_name = os.path.basename(file_path)
            output_name = os.path.splitext(base_name)[0] + "_embeddings.csv"
            output_path = os.path.join(output_folder, output_name)
            
            print(f"Saving results ({len(df)} rows) to {output_path}...")
            df.to_csv(output_path, index=False)
            print(f"✅ Results saved to {output_path}")
    
    return True

def main():
    args = parse_arguments()
    
    # Initialize Modin if requested
    if 'modin' in pd.__name__ and args.use_modin:
        initialize_modin(args.ray_cpus)
    
    # Get list of folders to process
    folders = get_folders_to_process(args.base_dir, args.folder_pattern, args.folder_range)
    
    if not folders:
        print(f"⚠️ No folders found matching pattern: {os.path.join(args.base_dir, args.folder_pattern)}")
        return
    
    print(f"Found {len(folders)} folders to process:")
    for folder in folders:
        print(f"  - {folder}")
    
    # Setup OpenVINO
    core = setup_openvino()
    
    # Load and compile model
    print(f"Loading model from {args.model_path}")
    model = core.read_model(args.model_path)
    compiled_model = core.compile_model(model, "CPU")
    
    # Process each folder
    successful_folders = 0
    for input_folder in folders:
        folder_name = os.path.basename(input_folder)
        output_folder = os.path.join(args.output_base_dir, folder_name)
        
        success = process_folder(
            input_folder, 
            output_folder, 
            compiled_model, 
            args.batch_size, 
            args.num_streams,
            args.process_rank_0,
            args.process_rank_1
        )
        
        if success:
            successful_folders += 1
    
    print(f"\n{'='*80}")
    print(f"Processing complete. Successfully processed {successful_folders}/{len(folders)} folders.")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
