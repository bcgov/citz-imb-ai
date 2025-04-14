import json
import numpy as np
import glob
import openvino as ov
from tqdm import tqdm
import pandas as pd
import os
from openvino.runtime import properties


# Configure OpenVINO
core = ov.Core()
#core.set_property("CPU", {
#    "NUM_STREAMS": "AUTO",
#    "PERFORMANCE_HINT": "THROUGHPUT"
#})

# Configure OpenVINO with optimized settings for throughput
#core = ov.Core()

# Get number of physical cores
cpu_count = os.cpu_count()

# Optimal configuration based on documentation
core.set_property("CPU", {
    # Set explicit throughput performance hint
    properties.hint.performance_mode(): properties.hint.PerformanceMode.THROUGHPUT,
    
    # Auto-configure optimal number of streams based on model's memory needs
    properties.num_streams(): "AUTO",
    
    # Use all available cores
    properties.inference_num_threads(): 0,
    
    # Enable CPU pinning on Linux (will be ignored if not supported)
    properties.hint.enable_cpu_pinning(): True,
    
    # Use both P-cores and E-cores if available
#    properties.hint.scheduling_core_type(): properties.hint.SchedulingCoreType.ALL,
    
    # Enable hyper-threading if available
    properties.hint.enable_hyper_threading(): True
})


# Load the model
model = core.read_model("openvino_model.xml")
compiled_model = core.compile_model(model, "CPU")

# Process a single file with adjusted input format
def process_file(file_path, batch_size=32):
    print(f"Processing: {file_path}")
    
    # Read data
    with open(file_path, 'r') as f:
        data_list = [json.loads(line) for line in f]
    
    # Extract tokens and metadata
    tokens_list = [item['tokens'] for item in data_list]
    metadata = [{k: v for k, v in item.items() if k != 'tokens'} for item in data_list]
    
    seq_len = len(tokens_list[0])  # Should be 255
    print(f"Found {len(tokens_list)} examples with sequence length: {seq_len}")
    
    # Process in batches
    all_embeddings = []
    
    for i in tqdm(range(0, len(tokens_list), batch_size)):
        batch_tokens = tokens_list[i:i+batch_size]
        batch_size_actual = len(batch_tokens)
        
        # Create proper inputs matching the example format
        # Reshape to (batch_size, seq_len)
        input_ids = np.array(batch_tokens).astype(np.int64)
        attention_mask = np.ones((batch_size_actual, seq_len), dtype=np.int64)
        token_type_ids = np.zeros((batch_size_actual, seq_len), dtype=np.int64)
        
        print(f"Batch input shape: {input_ids.shape}")
        
        try:
            # Try with all three inputs (similar to your working example)
            results = compiled_model({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids
            })
            
            # Get embeddings from output
            output_key = list(results.keys())[0]
            embeddings = results[output_key]
            all_embeddings.append(embeddings)
            print(f"Embedding shape for batch: {embeddings.shape}")
        
        except Exception as e:
            print(f"Error with all inputs: {e}")
            
            # Try with just input_ids and attention_mask
            try:
                results = compiled_model({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask
                })
                output_key = list(results.keys())[0]
                embeddings = results[output_key]
                all_embeddings.append(embeddings)
                print(f"Embedding shape for batch: {embeddings.shape}")
            
            except Exception as e2:
                print(f"Error with input_ids and attention_mask: {e2}")
                
                # Try with just input_ids
                try:
                    results = compiled_model({"input_ids": input_ids})
                    output_key = list(results.keys())[0]
                    embeddings = results[output_key]
                    all_embeddings.append(embeddings)
                    print(f"Embedding shape for batch: {embeddings.shape}")
                
                except Exception as e3:
                    print(f"Error with just input_ids: {e3}")
                    print("All attempts failed for this batch")
                    if i == 0:  # If even first batch fails, return None
                        return None, None
    
    # Combine all embeddings
    if all_embeddings:
        final_embeddings = np.vstack(all_embeddings)
        
        # Create DataFrame from metadata
        df = pd.DataFrame(metadata)
        
        print(f"Generated {final_embeddings.shape[0]} embeddings with dimension: {final_embeddings.shape[1]}")
        return df, final_embeddings
    else:
        return None, None

# Process one file
file_path = glob.glob("../build/consol_42/rank_0_thread_0.jsonl")[0]
df, embeddings = process_file(file_path)

if df is not None and embeddings is not None:
    # Add embeddings as a native list column (no string conversion)
    df['textEmbedding'] = embeddings.tolist()
    
    # Save to parquet format
    df.to_parquet("law_embeddings.parquet", compression="snappy")
    print("Results saved successfully in Parquet format!")
else:
    print("Processing failed")