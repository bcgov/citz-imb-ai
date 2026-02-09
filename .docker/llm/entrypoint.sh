#!/bin/bash
#
# llama.cpp multi-model entrypoint
# Starts llama-server instances using GGUF files already present in /models.
#
set -euo pipefail

MODEL_SOURCE_DIR="${MODEL_SOURCE_DIR:-/models}"
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-false}"
DOWNLOAD_ONLY="${DOWNLOAD_ONLY:-false}"
REQUIRE_AVX512="${REQUIRE_AVX512:-true}"
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

is_true() {
    local v
    v=$(echo "${1:-false}" | tr '[:upper:]' '[:lower:]')
    [[ "$v" == "1" || "$v" == "true" || "$v" == "yes" || "$v" == "on" ]]
}

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

    # Hard fail only when explicitly required by runtime config.
    if is_true "$REQUIRE_AVX512" && ! $has_avx512; then
        echo -e ""
        echo -e "${RED}FATAL: This binary requires AVX-512 (compiled with -march=sapphirerapids).${NC}"
        echo -e "${RED}This CPU does not support AVX-512. Rebuild with a compatible TARGET_ARCH.${NC}"
        exit 1
    elif ! $has_avx512; then
        echo -e ""
        echo -e "${YELLOW}WARNING:${NC} AVX-512 not present; continuing because REQUIRE_AVX512=${REQUIRE_AVX512}."
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
echo -e "Model source:    ${YELLOW}${MODEL_SOURCE_DIR}${NC}"
echo -e "Context size:    ${YELLOW}${CONTEXT_SIZE:-4096}${NC}"
echo -e "Threads/model:   ${YELLOW}${THREADS:-auto}${NC}"
echo -e "Download mode:   ${YELLOW}${DOWNLOAD_MODELS}${NC}"
echo -e "Download only:   ${YELLOW}${DOWNLOAD_ONLY}${NC}"
echo -e "Require AVX-512: ${YELLOW}${REQUIRE_AVX512}${NC}"
echo ""

# ─── Validate and start each model ───────────────────────────────────────────────
require_file() {
    local filename="$1"
    local path="${MODEL_SOURCE_DIR}/${filename}"
    if [[ ! -f "$path" ]]; then
        echo -e "  ${RED}Missing${NC} ${filename} in ${MODEL_SOURCE_DIR}"
        return 1
    fi
    echo -e "  ${GREEN}Found${NC} ${filename}"
}

download_file() {
    local source="$1"
    local filename="$2"
    local explicit_url="${3:-}"
    local out="${MODEL_SOURCE_DIR}/${filename}"
    local tmp="${out}.part"
    local url=""

    if [[ -n "$explicit_url" ]]; then
        url="$explicit_url"
    elif [[ "$source" =~ ^https?:// ]]; then
        url="$source"
    else
        url="https://huggingface.co/${source}/resolve/main/${filename}?download=true"
    fi

    mkdir -p "$MODEL_SOURCE_DIR"
    echo -e "  ${YELLOW}Downloading${NC} ${filename} from ${url}"
    rm -f "$tmp"

    # Prefer wget (matches successful host behavior), fallback to curl.
    if [[ -n "${HF_TOKEN:-}" ]]; then
        if ! wget --tries=5 --waitretry=2 --header="Authorization: Bearer ${HF_TOKEN}" -O "$tmp" "$url"; then
            curl -fL --retry 5 --retry-delay 2 \
                -H "Authorization: Bearer ${HF_TOKEN}" \
                -o "$tmp" "$url"
        fi
    else
        if ! wget --tries=5 --waitretry=2 -O "$tmp" "$url"; then
            curl -fL --retry 5 --retry-delay 2 \
                -o "$tmp" "$url"
        fi
    fi

    # Guard against tiny HTML/error responses.
    local size
    size=$(stat -c%s "$tmp" 2>/dev/null || echo 0)
    if [[ "$size" -lt 1048576 ]]; then
        echo -e "  ${RED}Download failed${NC}: ${filename} is only ${size} bytes (expected model file)."
        rm -f "$tmp"
        return 1
    fi

    mv "$tmp" "$out"
    echo -e "  ${GREEN}Downloaded${NC} ${filename}"
}

for model_id in "${SELECTED_MODELS[@]}"; do
    # Read config for this model
    config_line=$(grep "^${model_id}|" "$CONFIG_FILE" || true)
    if [[ -z "$config_line" ]]; then
        echo -e "${RED}Unknown model ID: ${model_id}${NC} (skipping)"
        continue
    fi

    IFS='|' read -r id port model_source filename extra_args <<< "$config_line"

    echo -e "${YELLOW}[Model ${id}]${NC} Port :${port} - ${filename}"

    # Main model file should exist in MODEL_SOURCE_DIR (or be downloaded if enabled)
    if ! require_file "$filename"; then
        if is_true "$DOWNLOAD_MODELS"; then
            download_file "$model_source" "$filename"
        fi
    fi
    if ! require_file "$filename"; then
        echo -e "  ${YELLOW}Skipping model ${id} due to missing file after download attempt.${NC}"
        echo ""
        continue
    fi
    # Download mmproj file if specified in extra_args
    if [[ "$extra_args" == *"--mmproj"* ]]; then
        mmproj_file=$(echo "$extra_args" | sed -n 's/.*--mmproj \([^ ]*\).*/\1/p')
        mmproj_url=$(echo "$extra_args" | sed -n 's/.*--mmproj-url \([^ ]*\).*/\1/p')
        if [[ -n "$mmproj_file" ]]; then
            if ! require_file "$mmproj_file"; then
                if is_true "$DOWNLOAD_MODELS"; then
                    download_file "$model_source" "$mmproj_file" "$mmproj_url"
                fi
            fi
            if ! require_file "$mmproj_file"; then
                echo -e "  ${YELLOW}Skipping model ${id}; missing mmproj file after download attempt.${NC}"
                echo ""
                continue 2
            fi
        fi
    fi

    if is_true "$DOWNLOAD_ONLY"; then
        echo -e "  ${GREEN}Ready${NC} files for model ${id}; download-only mode so not starting server."
        echo ""
        continue
    fi

    # Build server command
    cmd=(
        llama-server
        -m "${MODEL_SOURCE_DIR}/${filename}"
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
        local_extra=$(echo "$extra_args" | sed "s|--mmproj |--mmproj ${MODEL_SOURCE_DIR}/|g" | sed "s|--mmproj-url [^ ]*||g")
        # shellcheck disable=SC2206
        cmd+=($local_extra)
    fi

    echo -e "  ${CYAN}Starting${NC} llama-server on :${port}..."
    "${cmd[@]}" > "/tmp/llm_model_${id}.log" 2>&1 &
    PIDS+=($!)
    echo -e "  PID: $!"
    echo ""
done

if is_true "$DOWNLOAD_ONLY"; then
    echo -e "${GREEN}Download-only mode complete.${NC}"
    exit 0
fi

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
    IFS='|' read -r id port model_source filename extra_args <<< "$config_line"
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
