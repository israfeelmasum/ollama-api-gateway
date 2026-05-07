# Ollama API Gateway

> A production-ready FastAPI gateway for [Ollama](https://ollama.com) — adds API key authentication, OpenAI-compatible endpoints, intelligent model type detection, batch embeddings, streaming, and a Streamlit testing dashboard. Deploy locally with one command or behind Traefik with automatic HTTPS.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com)

---

## Why this exists

Vanilla Ollama exposes an unauthenticated HTTP server on port 11434 — fine on `localhost`, dangerous on the open internet. This project wraps Ollama with the production essentials you need to safely share LLM access with apps, teammates, or paying clients:

- **API key authentication** (header or bearer token) — no more accidental public access
- **OpenAI-compatible chat endpoints** — drop-in replacement for many client libraries
- **Automatic model classification** (text / vision / embedding / code) so clients can discover what's available
- **Batch embeddings** — embed dozens of texts in a single request
- **Server-Sent Event streaming** for token-by-token responses
- **Streamlit dashboard** for testing without writing code
- **Docker Compose stack** with optional Traefik + Let's Encrypt SSL
- **NVIDIA GPU support** out of the box
- **Stateless** — no database, no logs of prompts, no data retention

---

## Quick start (local)

```bash
git clone https://github.com/<your-org>/ollama-api-gateway.git
cd ollama-api-gateway

# Create your env file with at least one API key
cp .env.example .env
# Edit .env — replace the placeholder API_KEYS

# Bring up everything (Ollama + gateway + Streamlit UI)
docker compose up -d --build

# Pull at least one model into Ollama
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama pull nomic-embed-text
```

Then open:

| URL | Description |
|---|---|
| `http://localhost:8002/docs` | Swagger UI (interactive API docs) |
| `http://localhost:8502` | Streamlit testing dashboard |
| `http://localhost:8002/api/v1/health` | Health check |

To call the API:

```bash
curl http://localhost:8002/api/v1/models \
  -H "X-API-Key: <one-of-your-keys-from-.env>"
```

> **Don't have a GPU?** Open `docker-compose.yml` and remove the `deploy.resources` block from the `ollama` service. CPU works fine for smaller models.

---

## Production deployment (Traefik + HTTPS)

The bundled `docker-compose.yml` is wired for [Traefik](https://traefik.io) with automatic Let's Encrypt certificates.

1. Point three DNS records at your server: `api.example.com`, `ui.example.com`, `ollama.example.com` (replace `example.com` with your domain).
2. Make sure a Traefik instance is running on the external Docker network named `traefik-public` (or rename it in the compose file). Traefik must have the `letsencrypt` cert resolver configured.
3. Add `DOMAIN=example.com` to your `.env`.
4. Generate strong API keys:
   ```bash
   echo "API_KEYS=$(openssl rand -hex 32),$(openssl rand -hex 32)" >> .env
   ```
5. Deploy:
   ```bash
   docker compose up -d --build
   ```

That's it — Traefik will issue certs and route `https://api.example.com` to the gateway.

---

## Configuration

All configuration is in `.env`. Copy `.env.example` to get started.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where to reach Ollama (use `http://ollama:11434` inside docker-compose) |
| `OLLAMA_TIMEOUT` | `120` | Per-request timeout in seconds |
| `API_KEYS` | *(empty)* | Comma-separated list of valid API keys |
| `REQUIRE_API_KEY` | `true` | Set to `false` to disable auth (not recommended) |
| `AUTO_DETECT_MODEL_TYPE` | `true` | Classify models by name (text / vision / embedding / code) |
| `ENHANCE_RESPONSES` | `false` | Add gateway metadata to responses |
| `ALLOW_RAW_PASSTHROUGH` | `true` | Expose `/api/v1/raw/*` for direct Ollama API access |
| `CORS_ORIGINS` | `*` | Comma-separated CORS origins |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | Server bind address |
| `DEBUG` | `false` | Verbose logging |

### Adding new API keys

Edit `.env`, append to `API_KEYS` (comma-separated), then restart:

```bash
docker compose restart llmapi
```

> Public endpoints (no key required): `/`, `/docs`, `/redoc`, `/openapi.json`, `/api/v1/health`.

---

## API reference

Base URL: `http://localhost:8002` (local) or `https://api.example.com` (production).

### Authentication

Send your key in either header:

```http
X-API-Key: your-api-key
# or
Authorization: Bearer your-api-key
```

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/health` | No | Liveness check |
| GET | `/api/v1/health/status` | Yes | Detailed status (model count, etc.) |
| GET | `/api/v1/models` | Yes | List models. `?type=text\|vision\|embedding\|code` to filter |
| GET | `/api/v1/models/catalog` | Yes | Models grouped by type |
| GET | `/api/v1/models/{name}/info` | Yes | Detail for one model |
| POST | `/api/v1/models/classify` | Yes | Classify a model name |
| POST | `/api/v1/chat/completions` | Yes | Chat (non-streaming) |
| POST | `/api/v1/chat/stream` | Yes | Chat (SSE streaming) |
| POST | `/api/v1/embeddings` | Yes | Single-text embeddings |
| POST | `/api/v1/embeddings/batch` | Yes | Multi-text embeddings |
| POST | `/api/v1/vision/chat` | Yes | Vision + text |
| POST | `/api/v1/vision/stream` | Yes | Vision streaming |

Full interactive reference at `/docs` once running.

### Chat completion

```bash
curl -X POST http://localhost:8002/api/v1/chat/completions \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is machine learning?"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

| Field | Type | Required | Description |
|---|---|---|---|
| `model` | string | yes | e.g. `llama3.2` |
| `messages` | array | yes | `{role: "system\|user\|assistant", content: "..."}` |
| `temperature` | float | no | 0.0–2.0 |
| `max_tokens` | int | no | Cap on response tokens |
| `top_p` / `top_k` | float / int | no | Sampling params |
| `stream` | bool | no | Use `/chat/stream` instead for true SSE |

### Embeddings

```bash
curl -X POST http://localhost:8002/api/v1/embeddings \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "input": "Hello world"}'
```

Response:
```json
{ "model": "nomic-embed-text", "embeddings": [[0.123, -0.456, ...]] }
```

Batch (single round trip for many texts):

```bash
curl -X POST http://localhost:8002/api/v1/embeddings/batch \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "inputs": ["doc 1", "doc 2", "doc 3"]}'
```

> Both new (`input`) and legacy (`prompt`) Ollama embedding payloads are accepted.

### Vision

```bash
IMAGE=$(base64 -w 0 photo.jpg)

curl -X POST http://localhost:8002/api/v1/vision/chat \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llava\",
    \"prompt\": \"What is in this image?\",
    \"images\": [\"$IMAGE\"]
  }"
```

---

## Client examples

### Python

```python
import requests

API_URL = "http://localhost:8002"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Chat
r = requests.post(f"{API_URL}/api/v1/chat/completions", headers=headers, json={
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Hello!"}],
})
print(r.json()["message"]["content"])

# Embeddings
r = requests.post(f"{API_URL}/api/v1/embeddings", headers=headers, json={
    "model": "nomic-embed-text",
    "input": "Text to embed",
})
print(f"Dimensions: {len(r.json()['embeddings'][0])}")

# Streaming
r = requests.post(f"{API_URL}/api/v1/chat/stream", headers=headers, json={
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Tell me a story"}],
}, stream=True)
for chunk in r.iter_content(chunk_size=None):
    print(chunk.decode(), end="", flush=True)
```

### JavaScript / Node.js

```javascript
const API_URL = "http://localhost:8002";
const API_KEY = "your-api-key";
const headers = { "X-API-Key": API_KEY, "Content-Type": "application/json" };

const r = await fetch(`${API_URL}/api/v1/chat/completions`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    model: "llama3.2",
    messages: [{ role: "user", content: "Hello!" }],
  }),
});
const { message } = await r.json();
console.log(message.content);
```

---

## Recommended models

```bash
# General-purpose chat
docker exec ollama ollama pull llama3.2          # 3B, fast
docker exec ollama ollama pull llama3.1          # 8B, more capable
docker exec ollama ollama pull mistral           # 7B
docker exec ollama ollama pull qwen3.5           # latest Qwen

# Embeddings
docker exec ollama ollama pull nomic-embed-text  # 137M, 768 dims
docker exec ollama ollama pull qwen3-embedding   # newer, multilingual

# Vision
docker exec ollama ollama pull llava
docker exec ollama ollama pull qwen3-vl

# Code
docker exec ollama ollama pull codellama
docker exec ollama ollama pull deepseek-coder
```

Browse the full catalog at [ollama.com/library](https://ollama.com/library).

---

## Architecture

```
┌──────────┐      ┌──────────────────┐      ┌──────────┐
│  client  │ ───> │  FastAPI gateway │ ───> │  Ollama  │
└──────────┘      │  • auth          │      └──────────┘
                  │  • validation    │
                  │  • model classify│
                  │  • streaming     │
                  └──────────────────┘
```

Three Docker services:

| Service | Container | Purpose |
|---|---|---|
| `llmapi` | `ollama-gateway-api` | FastAPI gateway (port 8000 → host 8002) |
| `ollamaui` | `ollama-gateway-ui` | Streamlit dashboard (port 8501 → host 8502) |
| `ollama` | `ollama` | Ollama LLM engine (internal only by default) |

The gateway is **stateless** — restart it freely. Models live in the `ollama-data` volume.

---

## Streamlit testing dashboard

Visit `http://localhost:8502` (or `https://ui.example.com` in production) for a no-code UI with six tabs:

- **Chat** — multi-turn conversations with parameter sliders
- **Vision** — drag-and-drop image analysis
- **Embeddings** — single & batch with vector previews
- **Models** — browse catalog and inspect details
- **Health** — status checks
- **Raw Request** — send arbitrary JSON to any endpoint

---

## Project structure

```
ollama-api-gateway/
├── app/
│   ├── api/v1/
│   │   ├── routes/         # FastAPI route handlers
│   │   └── schemas/        # Pydantic request/response models
│   ├── core/               # Config, logging
│   ├── middleware/         # Auth middleware
│   ├── services/           # Ollama HTTP proxy
│   ├── main.py             # FastAPI app entrypoint
│   └── UI.py               # Streamlit dashboard
├── tests/
├── Dockerfile              # API gateway image
├── UIDockerfile            # Streamlit image
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── TESTING_GUIDE.md
└── README.md
```

---

## Testing

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

A complete 15-test suite for end-to-end verification lives in [`TESTING_GUIDE.md`](TESTING_GUIDE.md).

---

## Troubleshooting

<details>
<summary><b>401 "Missing API Key"</b></summary>

Send the header `X-API-Key: <key>` or `Authorization: Bearer <key>`. Verify the key is in your `.env` `API_KEYS` list and you've restarted the API container.
</details>

<details>
<summary><b>403 "Invalid API Key"</b></summary>

The key isn't in `API_KEYS`. After editing `.env`, restart with `docker compose restart llmapi`.
</details>

<details>
<summary><b>504 / model takes forever to respond</b></summary>

First request to a model triggers a load into VRAM and can take 30–60s. Increase `OLLAMA_TIMEOUT` in `.env` if needed.
</details>

<details>
<summary><b>Ollama can't reach GPU</b></summary>

Verify drivers and the NVIDIA Container Toolkit:
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```
If you don't have a GPU, remove the `deploy.resources` block from `docker-compose.yml`.
</details>

<details>
<summary><b>Embeddings return 500</b></summary>

Make sure an embedding model is pulled:
```bash
docker exec ollama ollama pull nomic-embed-text
```
Use the `input` field (not `prompt`). The gateway accepts both, but newer Ollama versions require `input`.
</details>

<details>
<summary><b>Traefik 504 in production</b></summary>

Check that the gateway container is on the same Docker network Traefik reads from. The `traefik.docker.network` label in `docker-compose.yml` must match the actual network name (`traefik-public` by default).
</details>

---

## Security checklist before going public

- [ ] Generate fresh API keys with `openssl rand -hex 32` — never commit them
- [ ] Confirm `.env` is in `.gitignore` (it is, by default)
- [ ] Set `REQUIRE_API_KEY=true`
- [ ] Restrict `CORS_ORIGINS` to your actual front-end domains
- [ ] Put the gateway behind HTTPS (Traefik + Let's Encrypt, Caddy, or Cloudflare)
- [ ] Don't expose port `11434` (Ollama direct) to the internet — only the gateway
- [ ] Rotate keys when offboarding clients
- [ ] Monitor logs for unusual traffic

---

## Contributing

Issues and pull requests are welcome. For substantial changes, please open an issue first to discuss the approach.

```bash
# Development setup
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## License

[MIT](LICENSE) — free for personal and commercial use.

---

## Acknowledgements

Built on top of [Ollama](https://ollama.com), [FastAPI](https://fastapi.tiangolo.com), [Streamlit](https://streamlit.io), and [Traefik](https://traefik.io).
