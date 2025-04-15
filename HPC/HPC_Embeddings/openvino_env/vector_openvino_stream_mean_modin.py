import json
import numpy as np
import glob
import openvino as ov
from tqdm import tqdm
import os
import argparse
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
    parser = argparse.ArgumentParser(description='Process JSONL files and generate embeddings.')
    parser.add_argument('--input_dir', type=str, default='../build/consol_42/',
                        help='Directory containing the JSONL files')
    parser.add_argument('--output_dir', type=str, default='./',
                        help='Directory to save the output files')
    parser.add_argument('--model_path', type=str, default='openvino_model.xml',
                        help='Path to the OpenVINO model XML file')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size for inference')
    parser.add_argument('--num_streams', type=int, default=8,
                        help='Number of inference streams')
    parser.add_argument('--single_output', action='store_true',
                        help='Save all results to a single CSV file')
    parser.add_argument('--output_filename', type=str, default='law_embeddings.csv',
                        help='Output filename when using single output')
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

def main():
    args = parse_arguments()
    
    # Initialize Modin if requested
    if 'modin' in pd.__name__ and args.ray_cpus:
        initialize_modin(args.ray_cpus)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup OpenVINO
    core = setup_openvino()
    
    # Load and compile model
    print(f"Loading model from {args.model_path}")
    model = core.read_model(args.model_path)
    compiled_model = core.compile_model(model, "CPU")
    
    # Get list of files to process
    files_to_process = []
    
    if args.process_rank_0:
        rank_0_files = glob.glob(os.path.join(args.input_dir, "rank_0_*.jsonl"))
        files_to_process.extend(rank_0_files)
        
    if args.process_rank_1:
        rank_1_files = glob.glob(os.path.join(args.input_dir, "rank_1_*.jsonl"))
        files_to_process.extend(rank_1_files)
    
    if not files_to_process:
        print(f"⚠️ No files found in {args.input_dir} matching the specified rank patterns")
        return
    
    print(f"Found {len(files_to_process)} files to process")
    
    if args.single_output:
        # Process all files and combine results
        all_dfs = []
        
        for file_path in files_to_process:
            df = process_file(file_path, compiled_model, args.batch_size, args.num_streams)
            if df is not None:
                all_dfs.append(df)
        
        if all_dfs:
            print(f"Combining {len(all_dfs)} DataFrames...")
            # Using Modin's concat for better performance
            combined_df = pd.concat(all_dfs, ignore_index=True)
            output_path = os.path.join(args.output_dir, args.output_filename)
            
            print(f"Saving combined results ({len(combined_df)} rows) to {output_path}...")
            # Save to CSV - this can be time-consuming with large DataFrames
            combined_df.to_csv(output_path, index=False)
            print(f"✅ All results saved to {output_path}")
        else:
            print("⚠️ No results to save")
    else:
        # Process each file and save individually
        for file_path in files_to_process:
            df = process_file(file_path, compiled_model, args.batch_size, args.num_streams)
            if df is not None:
                base_name = os.path.basename(file_path)
                output_name = os.path.splitext(base_name)[0] + "_embeddings.csv"
                output_path = os.path.join(args.output_dir, output_name)
                
                print(f"Saving results ({len(df)} rows) to {output_path}...")
                df.to_csv(output_path, index=False)
                print(f"✅ Results saved to {output_path}")

if __name__ == "__main__":
    main()
