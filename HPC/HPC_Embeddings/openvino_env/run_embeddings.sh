#!/bin/bash
# Script to run embeddings generation for acts or regulations
# Usage: ./run_embeddings.sh acts|regs [options]

# Display help function
show_help() {
    echo "Usage: $0 acts|regs [options]"
    echo ""
    echo "Required arguments:"
    echo "  acts|regs                      - Collection type to process"
    echo ""
    echo "Optional arguments:"
    echo "  --help                         - Show this help message and exit"
    echo "  --folder-range RANGE           - Folder range to process (e.g., '40-43' or 'all') [default: all]"
    echo "  --batch-size SIZE              - Batch size for processing [default: 16]"
    echo "  --num-streams NUM              - Number of streams [default: 8]"
    echo "  --download-model yes|no        - Download OpenVINO model from HuggingFace [default: no]"
    echo "  --base-dir DIR                 - Custom base directory for input files"
    echo "  --output-dir DIR               - Custom output directory for embeddings"
    echo ""
    echo "Default directories (if not specified):"
    echo "  For acts:"
    echo "    Base dir: /opt/app-root/src/Ashivaku/citz-imb-ai/HPC/HPC_Embeddings/build/Processed/acts"
    echo "    Output dir: Embeddings/acts"
    echo "  For regs:"
    echo "    Base dir: /opt/app-root/src/Ashivaku/citz-imb-ai/HPC/HPC_Embeddings/BCLaws_Output/reg_flat"
    echo "    Output dir: Embeddings/regs"
    echo ""
    echo "Examples:"
    echo "  $0 acts                        - Process all acts with default settings"
    echo "  $0 regs --folder-range 40-43   - Process regulations in folders 40-43"
    echo "  $0 acts --download-model yes   - Process acts and download the model"
    echo "  $0 acts --base-dir /path/to/acts --output-dir /path/to/output --batch-size 32"
    echo "                                 - Process acts using custom directories and batch size"
    exit 0
}

# Check if help is requested
if [ "$#" -eq 0 ] || [ "$1" == "--help" ] || [ "$2" == "--help" ]; then
    show_help
fi

# Validate first argument
if [ "$#" -lt 1 ]; then
    echo "Error: Missing collection type"
    echo "Run '$0 --help' for usage information"
    exit 1
fi

COLLECTION_TYPE=$1
shift  # Remove the first argument

# Default values
FOLDER_RANGE="all"
BATCH_SIZE=16
NUM_STREAMS=8
DOWNLOAD_MODEL="no"
CUSTOM_BASE_DIR=""
CUSTOM_OUTPUT_DIR=""

# Parse named arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --folder-range)
            FOLDER_RANGE="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --num-streams)
            NUM_STREAMS="$2"
            shift 2
            ;;
        --download-model)
            DOWNLOAD_MODEL="$2"
            shift 2
            ;;
        --base-dir)
            CUSTOM_BASE_DIR="$2"
            shift 2
            ;;
        --output-dir)
            CUSTOM_OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option '$1'"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Set default paths based on collection type
if [ "$COLLECTION_TYPE" == "acts" ]; then
    DEFAULT_BASE_DIR="/opt/app-root/src/Ashivaku/citz-imb-ai/HPC/HPC_Embeddings/build/Processed/acts"
    DEFAULT_OUTPUT_DIR="Embeddings/acts"
    FOLDER_PATTERN="consol_*"
elif [ "$COLLECTION_TYPE" == "regs" ]; then
    DEFAULT_BASE_DIR="/opt/app-root/src/Ashivaku/citz-imb-ai/HPC/HPC_Embeddings/BCLaws_Output/reg_flat"
    DEFAULT_OUTPUT_DIR="Embeddings/regs"
    FOLDER_PATTERN="Consol_*"
else
    echo "Error: First argument must be either 'acts' or 'regs'"
    echo "Run '$0 --help' for usage information"
    exit 1
fi

# Use custom directories if provided, otherwise use defaults
BASE_DIR=${CUSTOM_BASE_DIR:-$DEFAULT_BASE_DIR}
OUTPUT_BASE_DIR=${CUSTOM_OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_BASE_DIR"

# Set model paths
MODEL_DIR="openvino_model"
MODEL_XML="$MODEL_DIR/openvino_model.xml"
MODEL_BIN="$MODEL_DIR/openvino_model.bin"

# Download OpenVINO model if requested
if [ "$DOWNLOAD_MODEL" == "yes" ]; then
    echo "========================================================"
    echo "Downloading OpenVINO model from HuggingFace..."
    
    # Create model directory if it doesn't exist
    mkdir -p "$MODEL_DIR"
    
    # Download model files
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$MODEL_XML" "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/openvino/openvino_model.xml"
        wget -q --show-progress -O "$MODEL_BIN" "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/openvino/openvino_model.bin"
    elif command -v curl &> /dev/null; then
        curl -L "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/openvino/openvino_model.xml" -o "$MODEL_XML" --progress-bar
        curl -L "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/openvino/openvino_model.bin" -o "$MODEL_BIN" --progress-bar
    else
        echo "Error: Neither wget nor curl is installed. Cannot download model."
        exit 1
    fi
    
    # Check if download was successful
    if [ ! -f "$MODEL_XML" ] || [ ! -f "$MODEL_BIN" ]; then
        echo "Error: Failed to download model files."
        exit 1
    fi
    
    echo "OpenVINO model downloaded successfully to $MODEL_DIR/"
else
    # Check if model files exist
    if [ ! -f "$MODEL_XML" ] || [ ! -f "$MODEL_BIN" ]; then
        echo "Warning: OpenVINO model files not found at $MODEL_DIR/"
        echo "You can download them by rerunning the script with the download_model option set to 'yes'"
        echo "Continuing with the assumption that the model files are available elsewhere..."
    fi
fi

# Prepare range parameter
if [ "$FOLDER_RANGE" == "all" ]; then
    RANGE_PARAM=""
else
    RANGE_PARAM="--folder_range $FOLDER_RANGE"
fi

# Check if input directory exists
if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Input directory does not exist: $BASE_DIR"
    echo "Please check the path or create the directory before running this script."
    exit 1
fi

# Print execution plan
echo "========================================================"
echo "Running embeddings generation with the following settings:"
echo "  Collection type: $COLLECTION_TYPE"
echo "  Base directory: $BASE_DIR"
echo "  Output directory: $OUTPUT_BASE_DIR"
echo "  Folder pattern: $FOLDER_PATTERN"
echo "  Folder range: ${FOLDER_RANGE}"
echo "  Batch size: $BATCH_SIZE"
echo "  Number of streams: $NUM_STREAMS"
echo "  Model path: $MODEL_XML"
echo "  Downloaded model: $DOWNLOAD_MODEL"
echo "========================================================"

# Execute the Python script
python3 generate_embeddings_all.py \
    --base_dir "$BASE_DIR" \
    --output_base_dir "$OUTPUT_BASE_DIR" \
    --model_path "$MODEL_XML" \
    --batch_size "$BATCH_SIZE" \
    --num_streams "$NUM_STREAMS" \
    --folder_pattern "$FOLDER_PATTERN" \
    $RANGE_PARAM \
    --process_rank_0 \
    --process_rank_1 \
    --use_modin

# Check exit status
if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Embeddings generation completed successfully!"
    echo "Results saved to: $OUTPUT_BASE_DIR"
    echo "========================================================"
else
    echo "========================================================"
    echo "Error: Embeddings generation failed!"
    echo "========================================================"
    exit 1
fi
