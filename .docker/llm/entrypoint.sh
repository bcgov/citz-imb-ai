#!/bin/bash
#
# llama.cpp multi-model entrypoint
# Downloads GGUF models from HuggingFace if not present, then starts llama-server
# instances with OpenAI-compatible API on configured ports.
#
set -euo pipefail

MODELS_DIR="/models"
CONFIG_FILE="/etc/llm/models.conf"
PIDS=()

# ─── Colors ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Graceful shutdown ──────────────────────────────────────────────────────────
cleanup() {
    echo -e "\n${YELLOW}Shutting down LLM servers...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    wait
    echo -e "${GREEN}All servers stopped.${NC}"
    exit 0
}
trap cleanup SIGTERM SIGINT

# ─── CPU feature detection ────────────────────────────────────────────────────────
check_cpu() {
    local flags
    flags=$(grep -m1 '^flags' /proc/cpuinfo 2>/dev/null || echo "")
    local model
    model=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs)

    echo -e "${CYAN}CPU:${NC} ${model:-unknown}"

    local has_avx512=false has_amx=false has_avx2=false
    [[ "$flags" == *" avx2 "* ]]     && has_avx2=true
    [[ "$flags" == *" avx512f "* ]]   && has_avx512=true
    [[ "$flags" == *" amx_int8 "* ]]  && has_amx=true

    if $has_avx512; then
        echo -e "  AVX-512: ${GREEN}YES${NC}"
    else
        echo -e "  AVX-512: ${RED}NO${NC} - binary was compiled with AVX-512, expect SIGILL crash"
    fi

    if $has_amx; then
        echo -e "  AMX:     ${GREEN}YES${NC}"
    else
        echo -e "  AMX:     ${YELLOW}NO${NC} - AMX kernels will not be used"
    fi

    if $has_avx2; then
        echo -e "  AVX2:    ${GREEN}YES${NC}"
    else
        echo -e "  AVX2:    ${RED}NO${NC}"
    fi

    # Hard fail if AVX-512 is missing (binary will SIGILL)
    if ! $has_avx512; then
        echo -e ""
        echo -e "${RED}FATAL: This binary requires AVX-512 (compiled with -march=sapphirerapids).${NC}"
        echo -e "${RED}This CPU does not support AVX-512. Rebuild with a compatible TARGET_ARCH.${NC}"
        exit 1
    fi

    echo ""
}

# ─── Parse selected models ──────────────────────────────────────────────────────
IFS=',' read -ra SELECTED_MODELS <<< "${MODELS:-1,6}"

echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  llama.cpp LLM Server - Intel oneAPI MKL${NC}"
echo -e "${CYAN}  OpenAI-compatible API (/v1/chat/completions)${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""

check_cpu

echo -e "Selected models: ${YELLOW}${SELECTED_MODELS[*]}${NC}"
echo -e "Context size:    ${YELLOW}${CONTEXT_SIZE:-4096}${NC}"
echo -e "Threads/model:   ${YELLOW}${THREADS:-auto}${NC}"
echo ""

# ─── HuggingFace auth ───────────────────────────────────────────────────────────
if [[ -n "${HF_TOKEN:-}" ]]; then
    echo -e "${CYAN}Authenticating with HuggingFace...${NC}"
    huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential 2>/dev/null || true
fi

# ─── Download and start each model ──────────────────────────────────────────────
download_file() {
    local repo="$1"
    local filename="$2"
    local dest="${MODELS_DIR}/${filename}"

    if [[ -f "$dest" ]]; then
        echo -e "  ${GREEN}Found${NC} ${filename}"
        return 0
    fi

    echo -e "  ${YELLOW}Downloading${NC} ${filename} from ${repo}..."
    huggingface-cli download "$repo" "$filename" \
        --local-dir "$MODELS_DIR" \
        --local-dir-use-symlinks False \
        --quiet
    echo -e "  ${GREEN}Downloaded${NC} ${filename}"
}

for model_id in "${SELECTED_MODELS[@]}"; do
    # Read config for this model
    config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
    if [[ -z "$config_line" ]]; then
        echo -e "${RED}Unknown model ID: ${model_id}${NC} (skipping)"
        continue
    fi

    IFS='|' read -r id port hf_repo filename extra_args <<< "$config_line"

    echo -e "${YELLOW}[Model ${id}]${NC} Port :${port} - ${filename}"

    # Download main model file
    download_file "$hf_repo" "$filename"

    # Download mmproj file if specified in extra_args
    if [[ "$extra_args" == *"--mmproj"* ]]; then
        mmproj_file=$(echo "$extra_args" | grep -oP '(?<=--mmproj )\S+')
        if [[ -n "$mmproj_file" ]]; then
            download_file "$hf_repo" "$mmproj_file"
        fi
    fi

    # Build server command
    cmd=(
        llama-server
        -m "${MODELS_DIR}/${filename}"
        --host 0.0.0.0
        --port "$port"
        -c "${CONTEXT_SIZE:-4096}"
        --metrics
    )

    # Add threads if specified
    if [[ -n "${THREADS:-}" ]]; then
        cmd+=(-t "$THREADS")
    fi

    # Add extra args (e.g., --mmproj)
    if [[ -n "${extra_args:-}" ]]; then
        # Prepend models dir to mmproj path
        local_extra=$(echo "$extra_args" | sed "s|--mmproj |--mmproj ${MODELS_DIR}/|g")
        # shellcheck disable=SC2206
        cmd+=($local_extra)
    fi

    echo -e "  ${CYAN}Starting${NC} llama-server on :${port}..."
    "${cmd[@]}" > "/tmp/llm_model_${id}.log" 2>&1 &
    PIDS+=($!)
    echo -e "  PID: $!"
    echo ""
done

# ─── Wait for servers to become healthy ──────────────────────────────────────────
echo -n "Waiting for models to load"
for i in $(seq 1 60); do
    sleep 2
    echo -n "."
    # Check if all servers are up
    all_ready=true
    for model_id in "${SELECTED_MODELS[@]}"; do
        config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
        [[ -z "$config_line" ]] && continue
        port=$(echo "$config_line" | cut -d'|' -f2)
        if ! curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
            all_ready=false
            break
        fi
    done
    if $all_ready; then
        break
    fi
done
echo ""
echo ""

# ─── Status report ───────────────────────────────────────────────────────────────
echo -e "${GREEN}Server Status:${NC}"
for model_id in "${SELECTED_MODELS[@]}"; do
    config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
    [[ -z "$config_line" ]] && continue
    IFS='|' read -r id port hf_repo filename extra_args <<< "$config_line"
    if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "  :${port} ${GREEN}Online${NC} - ${filename}"
    else
        echo -e "  :${port} ${RED}Not ready${NC} - ${filename} (check /tmp/llm_model_${id}.log)"
    fi
done

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "OpenAI-compatible API endpoints:"
for model_id in "${SELECTED_MODELS[@]}"; do
    config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
    [[ -z "$config_line" ]] && continue
    port=$(echo "$config_line" | cut -d'|' -f2)
    echo "  http://llm_server:${port}/v1/chat/completions"
done
echo ""
echo "Health checks:"
for model_id in "${SELECTED_MODELS[@]}"; do
    config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
    [[ -z "$config_line" ]] && continue
    port=$(echo "$config_line" | cut -d'|' -f2)
    echo "  http://llm_server:${port}/health"
done
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"

# ─── Keep running, wait for any child to exit ────────────────────────────────────
wait -n "${PIDS[@]}" 2>/dev/null || true
echo -e "${RED}A server process exited unexpectedly. Check logs in /tmp/llm_model_*.log${NC}"
cleanup
