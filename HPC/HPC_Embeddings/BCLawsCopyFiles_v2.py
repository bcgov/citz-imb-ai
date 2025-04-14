#!/usr/bin/env python3
import os
import shutil
import argparse
import re
import multiprocessing
import time
from functools import partial
import glob

def find_xml_files(source_dir, is_regulation=False):
    """
    Find XML files in the directory structure.
    
    Parameters:
      source_dir: Source directory containing BC Laws structure
      is_regulation: Flag to indicate if processing regulations instead of acts
      
    Returns:
      List of (file_path, document_name) tuples
    """
    xml_files = []
    
    try:
        # Walk through the alphabetical grouping directories
        for letter_dir in os.listdir(source_dir):
            letter_path = os.path.join(source_dir, letter_dir)
            
            if not os.path.isdir(letter_path) or not (letter_dir.startswith('--') and letter_dir.endswith('--')):
                continue
                
            # Process each document within the letter group
            for doc_dir in os.listdir(letter_path):
                doc_path = os.path.join(letter_path, doc_dir)
                
                if not os.path.isdir(doc_path):
                    continue
                
                # Look for XML files directly in this folder
                for file_name in os.listdir(doc_path):
                    file_path = os.path.join(doc_path, file_name)
                    file_name_lower = file_name.lower()
                    
                    # Skip if not XML
                    if not file_path.lower().endswith('.xml'):
                        continue
                    
                    # Skip files to exclude based on patterns
                    if (
                        # Skip Part files
                        file_name_lower.startswith('part') or
                        # Skip Division files 
                        file_name_lower.startswith('division') or
                        # Skip Historical tables
                        'historical' in file_name_lower or
                        # Skip legislative changes
                        #'legislative' in file_name_lower or
                        # Skip table of contents
                        'table_of_contents' in file_name_lower or
                        # Skip "An Act to..." files which are typically special case Acts
                        file_name_lower.startswith('an act to')
                    ):
                        continue
                        
                    # Keep the file
                    xml_files.append((file_path, doc_dir))
                
                # Also check for XML files in potential "Act" subdirectory (some structures have this)
                act_subdir = os.path.join(doc_path, "Act")
                if os.path.isdir(act_subdir):
                    for file_name in os.listdir(act_subdir):
                        file_path = os.path.join(act_subdir, file_name)
                        file_name_lower = file_name.lower()
                        
                        # Skip if not XML
                        if not file_path.lower().endswith('.xml'):
                            continue
                        
                        # Skip files to exclude based on patterns
                        if (
                            # Skip Part files
                            file_name_lower.startswith('part') or
                            # Skip Division files 
                            file_name_lower.startswith('division') or
                            # Skip Historical tables
                            'historical' in file_name_lower or
                            # Skip legislative changes
                            'legislative' in file_name_lower or
                            # Skip table of contents
                            'table_of_contents' in file_name_lower or
                            # Skip "An Act to..." files which are typically special case Acts
                            file_name_lower.startswith('an act to')
                        ):
                            continue
                            
                        # Keep the file
                        xml_files.append((file_path, doc_dir))
    
    except Exception as e:
        print(f"Error finding XML files: {e}")
        
    return xml_files

def process_consolidation(consolidation_path, output_base_dir):
    """
    Process a single consolidation directory by finding XML files and copying them.
    
    Parameters:
      consolidation_path: Path to the consolidation directory
      output_base_dir: Base directory for output
    
    Returns:
      Dictionary with statistics about processed documents
    """
    consolidation_name = os.path.basename(consolidation_path)
    
    # Clean up consolidation name for folder name
    clean_name = consolidation_name.replace(' ', '_').replace('-', '_').replace(',', '').replace('(', '').replace(')', '')
    
    # Determine if this is a regulations or acts consolidation based on directory name
    is_regulation = "Regulations" in os.path.dirname(consolidation_path)
    
    # Create appropriate output directory
    if is_regulation:
        output_dir = os.path.join(output_base_dir, "reg_flat", clean_name)
    else:
        output_dir = os.path.join(output_base_dir, "act_flat", clean_name)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find XML files
    xml_files = find_xml_files(consolidation_path, is_regulation)
    
    # Copy files to destination
    copied_count = 0
    for file_path, doc_name in xml_files:
        # Create a nice filename
        file_name = os.path.basename(file_path)
        
        # Copy the file
        dest_path = os.path.join(output_dir, file_name)
        try:
            shutil.copy2(file_path, dest_path)
            copied_count += 1
        except Exception as e:
            print(f"Error copying {file_path}: {e}")
    
    return {
        "name": consolidation_name,
        "count": copied_count,
        "is_regulation": is_regulation
    }

def worker_init():
    """
    Initialize worker process - this helps with better logging in multiprocessing
    """
    # Setting a nicer process name for monitoring
    try:
        import setproctitle
        setproctitle.setproctitle(f"bclaws-worker")
    except ImportError:
        pass  # Optional dependency

def process_job(job, output_base_dir):
    """
    Worker function for parallel processing
    """
    start_time = time.time()
    consolidation_path, is_act = job
    consolidation_name = os.path.basename(consolidation_path)
    
    print(f"Started processing: {consolidation_name} ({'Act' if is_act else 'Regulation'})")
    
    result = process_consolidation(consolidation_path, output_base_dir)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Completed: {consolidation_name} - {result['count']} files copied in {duration:.2f} seconds")
    
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Copy BC Laws XML files to a flattened structure, organized by consolidation."
    )
    parser.add_argument(
        "--source", "-s", required=True,
        help="Path to the base directory containing Acts and Regulations folders"
    )
    parser.add_argument(
        "--destination", "-d", required=True,
        help="Path to the destination directory for the organized structure"
    )
    parser.add_argument(
        "--consolidation", "-c",
        help="Specific consolidation to process (e.g., 'Consol 14 - February 13, 2006'). If not specified, processes all."
    )
    parser.add_argument(
        "--acts-only", action="store_true",
        help="Process only Acts (skip Regulations)"
    )
    parser.add_argument(
        "--regs-only", action="store_true",
        help="Process only Regulations (skip Acts)"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=None,
        help="Number of worker processes to use (default: number of CPU cores)"
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(args.source)
    dest_dir = os.path.abspath(args.destination)

    # Normalize paths to handle spaces and special characters
    base_dir = os.path.normpath(base_dir)
    dest_dir = os.path.normpath(dest_dir)

    # Ensure base directory exists
    if not os.path.isdir(base_dir):
        print(f"Error: Source directory '{base_dir}' does not exist or is not a directory.")
        exit(1)
        
    # Create output directories
    act_flat_dir = os.path.join(dest_dir, "act_flat")
    reg_flat_dir = os.path.join(dest_dir, "reg_flat")
    
    os.makedirs(act_flat_dir, exist_ok=True)
    os.makedirs(reg_flat_dir, exist_ok=True)
        
    # Determine number of workers
    num_workers = args.workers if args.workers else multiprocessing.cpu_count()
    print(f"Using {num_workers} worker processes")
    
    # Initialize job list
    jobs = []
    
    # Build job list for acts if not skipped
    if not args.regs_only:
        acts_dir = os.path.join(base_dir, "Acts")
        if os.path.isdir(acts_dir):
            print(f"Scanning Acts in {acts_dir}")
            
            # Add specific consolidation or all consolidations to job list
            if args.consolidation:
                consolidation_path = os.path.join(acts_dir, args.consolidation)
                if os.path.isdir(consolidation_path):
                    jobs.append((consolidation_path, True))
                else:
                    print(f"Error: Consolidation '{args.consolidation}' not found in Acts directory.")
            else:
                # Add all consolidations
                for consolidation in sorted(os.listdir(acts_dir)):
                    consolidation_path = os.path.join(acts_dir, consolidation)
                    if os.path.isdir(consolidation_path):
                        jobs.append((consolidation_path, True))
                        
            print(f"Found {len(jobs)} Act consolidations to process")
        else:
            print(f"Warning: Acts directory '{acts_dir}' not found.")
    
    # Build job list for regulations if not skipped
    reg_jobs = []
    if not args.acts_only:
        regs_dir = os.path.join(base_dir, "Regulations")
        if os.path.isdir(regs_dir):
            print(f"Scanning Regulations in {regs_dir}")
            
            # Add specific consolidation or all consolidations to job list
            if args.consolidation:
                consolidation_path = os.path.join(regs_dir, args.consolidation)
                if os.path.isdir(consolidation_path):
                    reg_jobs.append((consolidation_path, False))
                else:
                    print(f"Error: Consolidation '{args.consolidation}' not found in Regulations directory.")
            else:
                # Add all consolidations
                for consolidation in sorted(os.listdir(regs_dir)):
                    consolidation_path = os.path.join(regs_dir, consolidation)
                    if os.path.isdir(consolidation_path):
                        reg_jobs.append((consolidation_path, False))
                        
            print(f"Found {len(reg_jobs)} Regulation consolidations to process")
        else:
            print(f"Warning: Regulations directory '{regs_dir}' not found.")
            
    # Combine jobs
    jobs.extend(reg_jobs)
    
    # Exit if no jobs
    if not jobs:
        print("No consolidations found to process. Exiting.")
        return
        
    # Initialize results and timing
    start_time = time.time()
    stats = {"acts": [], "regulations": []}
    
    try:
        # Create the process pool
        with multiprocessing.Pool(processes=num_workers, initializer=worker_init) as pool:
            # Create a partial function with fixed arguments
            worker_func = partial(process_job, output_base_dir=dest_dir)
            
            # Process jobs in parallel
            results = pool.map(worker_func, jobs)
            
            # Organize results
            for result in results:
                if result["is_regulation"]:
                    stats["regulations"].append(result)
                else:
                    stats["acts"].append(result)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        return
    
    # Calculate totals
    end_time = time.time()
    duration = end_time - start_time
    
    # Print statistics
    print("\n=== Processing Summary ===")
    print(f"Total Acts consolidations processed: {len(stats['acts'])}")
    total_acts_files = sum(item['count'] for item in stats['acts'])
    print(f"Total Act XML files copied: {total_acts_files}")
    
    print(f"Total Regulations consolidations processed: {len(stats['regulations'])}")
    total_regs_files = sum(item['count'] for item in stats['regulations'])
    print(f"Total Regulation XML files copied: {total_regs_files}")
    
    print(f"\nTotal XML files copied: {total_acts_files + total_regs_files}")
    print(f"Processing time: {duration:.2f} seconds")
    print(f"Output directory: {dest_dir}")
    print(f"  Acts: {act_flat_dir}")
    print(f"  Regulations: {reg_flat_dir}")

if __name__ == "__main__":
    # Fix for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()
