# LLM folder overview

This folder is the wiring for our local/self-hosted LLM stack.

The short version:

- `llama-server` does the actual inference for each GGUF model.
- `LiteLLM` sits in front of those model servers and gives clients one OpenAI-compatible endpoint.
- This folder holds the config that ties those two layers together.

## What each file does

### `models.conf`

This is the source of truth for the backend model processes.

Each line defines:

- a model ID
- the port its `llama-server` process should listen on
- where to get the GGUF from
- the GGUF filename expected in `/models`
- any extra args, like `--mmproj` for vision models

If you add or change a backend model, this file is usually the first place to touch.

### `entrypoint.sh`

This is the startup script for the `llm_server` container.

It reads `models.conf`, checks which model IDs were requested through `MODELS`, optionally downloads missing GGUF files into `/models`, and then starts one `llama-server` process per selected model.

Important details:

- each model runs on its own port (`8090`, `8091`, etc.)
- the actual model files are not stored in this repo; they live in the Docker volume mounted at `/models`
- every `llama-server` process is started with `--api-key "$LLM_API_KEY"`
- vision models may also need an `mmproj` file

### `litellm_config.yaml`

This is the front-door routing table for LiteLLM.

It maps the public model names clients use, like `qwen25-3b`, to the correct backend `llama-server` port.

Example idea:

- client asks LiteLLM for model `qwen3-8b`
- LiteLLM looks up `qwen3-8b` in this file
- LiteLLM forwards the request to that model's backend `api_base`

This is why new models usually need changes in **two places**:

1. `models.conf` so the backend server exists
2. `litellm_config.yaml` so clients can route to it by name

## Why LiteLLM exists here

Without LiteLLM, every caller would need to know:

- which model lives on which port
- which models are currently enabled
- how to talk directly to each `llama-server`

LiteLLM removes that burden. In this setup it does three useful jobs:

1. It gives callers a single OpenAI-style API surface.
2. It routes requests by `model` name to the correct backend port.
3. It separates client-facing auth from backend auth.

That separation matters:

- clients authenticate to LiteLLM with `LITELLM_MASTER_KEY`
- LiteLLM authenticates to each `llama-server` with `LLM_API_KEY`

So LiteLLM is basically the stable front door, and `llama-server` instances are the workers behind it.

## How the request flow works

1. `docker compose` starts `llm_server`.
2. `entrypoint.sh` launches one or more `llama-server` processes from `models.conf`.
3. Each backend model listens on its own port and requires `LLM_API_KEY`.
4. `docker compose` starts `llm_proxy` after the backend is healthy.
5. Clients call LiteLLM on port `8080` (or through the deployed route).
6. LiteLLM reads the request's `model` field and forwards the call to the matching backend model.

In practice, the flow is:

`client -> LiteLLM -> llama-server for the selected model`

## When to use LiteLLM vs direct llama-server

Use LiteLLM for normal app traffic.

Use direct `llama-server` ports only when debugging a specific backend model, checking health, or isolating whether a problem is in the proxy layer or the model layer.

## Useful mental model for new devs

- `models.conf` = what can run
- `entrypoint.sh` = how it starts
- `litellm_config.yaml` = how callers reach it

If a model is "installed" but not selectable by clients, the usual cause is that one of those two config files was updated and the other was not.

## Common gotchas

- `litellm_config.yaml` uses backend hostnames directly. If deployment/network naming changes, update the `api_base` entries.
- The backend model names in LiteLLM are the names clients must send in the request body.
- Vision models often need both the main GGUF and an `mmproj` file.
- `drop_params: true` in LiteLLM helps ignore unsupported OpenAI-style params instead of breaking requests.

## Typical commands

Start the backend model server:

```bash
docker compose -f .docker/compose.controller.yaml up llm_server
```

Start the proxy in front of it:

```bash
docker compose -f .docker/compose.controller.yaml up llm_proxy
```

Run selected models only:

```bash
LLM_MODELS=1,7 docker compose -f .docker/compose.controller.yaml up llm_server
```

List models through the proxy:

```bash
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>"
```

Send a chat request through the proxy:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-8b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```
