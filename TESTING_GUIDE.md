# Testing Guide

End-to-end test suite for the Ollama API Gateway. Replace `BASE_URL` and `API_KEY` below with your own values.

```bash
export BASE_URL="http://localhost:8002"        # or https://api.example.com
export API_KEY="your-api-key"
```

---

## 1. Health checks (no auth)

### 1.1 Basic health
```bash
curl $BASE_URL/api/v1/health
```
**Expected:** `{"status":"healthy","ollama_reachable":true,...}`

### 1.2 Root endpoint
```bash
curl $BASE_URL/
```
**Expected:** JSON with API info and endpoint links

### 1.3 Detailed status (auth required)
```bash
curl $BASE_URL/api/v1/health/status -H "X-API-Key: $API_KEY"
```

---

## 2. Authentication

### 2.1 Missing key → 401
```bash
curl -s -o /dev/null -w "%{http_code}\n" $BASE_URL/api/v1/models
```
**Expected:** `401`

### 2.2 Invalid key → 403
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "X-API-Key: invalid-key" \
  $BASE_URL/api/v1/models
```
**Expected:** `403`

### 2.3 Valid key (X-API-Key header) → 200
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "X-API-Key: $API_KEY" \
  $BASE_URL/api/v1/models
```
**Expected:** `200`

### 2.4 Valid key (Bearer token) → 200
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $API_KEY" \
  $BASE_URL/api/v1/models
```
**Expected:** `200`

---

## 3. Model management

### 3.1 List all models
```bash
curl -s $BASE_URL/api/v1/models -H "X-API-Key: $API_KEY" | python3 -m json.tool
```

### 3.2 Filter by type
```bash
curl -s "$BASE_URL/api/v1/models?type=embedding" -H "X-API-Key: $API_KEY"
curl -s "$BASE_URL/api/v1/models?type=text"      -H "X-API-Key: $API_KEY"
curl -s "$BASE_URL/api/v1/models?type=vision"    -H "X-API-Key: $API_KEY"
```

### 3.3 Catalog (grouped)
```bash
curl -s $BASE_URL/api/v1/models/catalog -H "X-API-Key: $API_KEY"
```

### 3.4 Model info
```bash
curl -s $BASE_URL/api/v1/models/llama3.2/info -H "X-API-Key: $API_KEY"
```

### 3.5 Classify
```bash
curl -s -X POST $BASE_URL/api/v1/models/classify \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "nomic-embed-text"}'
```

---

## 4. Chat completion

### 4.1 Basic chat
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Say hello in one word"}]
  }'
```

### 4.2 With system prompt
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "system", "content": "You are a pirate. Respond in pirate speak."},
      {"role": "user", "content": "How are you today?"}
    ],
    "temperature": 0.9
  }'
```

### 4.3 With sampling parameters
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "temperature": 0.1,
    "max_tokens": 50,
    "top_p": 0.9
  }'
```

### 4.4 Streaming
```bash
curl -s -X POST $BASE_URL/api/v1/chat/stream \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Count from 1 to 5"}]
  }'
```
**Expected:** Tokens arrive incrementally (SSE)

### 4.5 Multi-turn
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "user", "content": "My name is Alex"},
      {"role": "assistant", "content": "Hello Alex! Nice to meet you."},
      {"role": "user", "content": "What is my name?"}
    ]
  }'
```
**Expected:** Response references "Alex"

---

## 5. Embeddings

### 5.1 Single
```bash
curl -s -X POST $BASE_URL/api/v1/embeddings \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "input": "Hello world"}'
```

### 5.2 Verify dimensions
```bash
curl -s -X POST $BASE_URL/api/v1/embeddings \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "input": "Test"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Dimensions: {len(d[\"embeddings\"][0])}')"
```
**Expected:** `Dimensions: 768` (for nomic-embed-text)

### 5.3 Batch
```bash
curl -s -X POST $BASE_URL/api/v1/embeddings/batch \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "inputs": ["First document", "Second document", "Third document"]
  }'
```

### 5.4 Legacy `prompt` field (backward compat)
```bash
curl -s -X POST $BASE_URL/api/v1/embeddings \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "prompt": "Legacy format"}'
```

---

## 6. Vision (requires a vision model)

```bash
docker exec ollama ollama pull llava
```

### 6.1 Vision chat
```bash
IMAGE=$(base64 -w 0 test_image.jpg)

curl -s -X POST $BASE_URL/api/v1/vision/chat \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llava\",
    \"prompt\": \"What do you see?\",
    \"images\": [\"$IMAGE\"]
  }"
```

### 6.2 Vision streaming
```bash
curl -s -X POST $BASE_URL/api/v1/vision/stream \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llava\",
    \"prompt\": \"Describe this image\",
    \"images\": [\"$IMAGE\"]
  }"
```

---

## 7. Error handling

### 7.1 Missing required fields → 422
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 7.2 Invalid model → 500
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "fake-model", "messages": [{"role": "user", "content": "test"}]}'
```

### 7.3 Out-of-range temperature → 422
```bash
curl -s -X POST $BASE_URL/api/v1/chat/completions \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "test"}], "temperature": 5.0}'
```

---

## 8. Python test runner

Save as `test_api.py` and run with `python test_api.py`:

```python
import os
import sys
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8002")
API_KEY = os.environ["API_KEY"]
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

passed = failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name} - {e}")
        failed += 1

def health():
    r = requests.get(f"{BASE_URL}/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"

def auth_required():
    r = requests.get(f"{BASE_URL}/api/v1/models")
    assert r.status_code == 401

def invalid_key():
    r = requests.get(f"{BASE_URL}/api/v1/models", headers={"X-API-Key": "bad"})
    assert r.status_code == 403

def models_list():
    r = requests.get(f"{BASE_URL}/api/v1/models", headers=HEADERS)
    assert r.status_code == 200 and r.json()["total"] > 0

def chat():
    r = requests.post(f"{BASE_URL}/api/v1/chat/completions", headers=HEADERS, json={
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "Say hi"}],
    })
    assert r.status_code == 200 and "message" in r.json()

def chat_stream():
    r = requests.post(f"{BASE_URL}/api/v1/chat/stream", headers=HEADERS, json={
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "Say ok"}],
    }, stream=True)
    assert r.status_code == 200
    assert sum(1 for _ in r.iter_content(chunk_size=None)) > 0

def embedding():
    r = requests.post(f"{BASE_URL}/api/v1/embeddings", headers=HEADERS, json={
        "model": "nomic-embed-text", "input": "test",
    })
    assert r.status_code == 200
    assert len(r.json()["embeddings"][0]) == 768

def embedding_batch():
    r = requests.post(f"{BASE_URL}/api/v1/embeddings/batch", headers=HEADERS, json={
        "model": "nomic-embed-text",
        "inputs": ["a", "b", "c"],
    })
    assert r.status_code == 200 and len(r.json()["embeddings"]) == 3

def model_catalog():
    r = requests.get(f"{BASE_URL}/api/v1/models/catalog", headers=HEADERS)
    assert r.status_code == 200

def model_info():
    r = requests.get(f"{BASE_URL}/api/v1/models/llama3.2/info", headers=HEADERS)
    assert r.status_code == 200

print("Running Ollama API Gateway tests")
print("=" * 40)
test("Health check",         health)
test("Auth required (401)",  auth_required)
test("Invalid key (403)",    invalid_key)
test("Models list",          models_list)
test("Model catalog",        model_catalog)
test("Model info",           model_info)
test("Chat completion",      chat)
test("Chat streaming",       chat_stream)
test("Embedding (single)",   embedding)
test("Embedding (batch)",    embedding_batch)
print("=" * 40)
print(f"Result: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
```

---

## 9. Docker health checks

```bash
# Container status
docker compose ps

# Logs
docker compose logs -f llmapi
docker compose logs -f ollama
docker compose logs -f ollamaui

# Restart a service
docker compose restart llmapi

# List pulled models
docker exec ollama ollama list

# Pull a new model
docker exec ollama ollama pull <model-name>
```

---

## 10. SSL / Traefik verification (production)

```bash
# Check HTTPS works
curl -I https://api.example.com/api/v1/health

# Inspect cert
openssl s_client -connect api.example.com:443 -servername api.example.com < /dev/null 2>/dev/null \
  | openssl x509 -noout -dates

# Check all routes
for d in api ui ollama; do
  printf "%s.example.com: " "$d"
  curl -s -o /dev/null -w "%{http_code}\n" https://$d.example.com/
done
```
