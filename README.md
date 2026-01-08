🧠 Prompt Layer
Reusable Prompt Templates, Versioning & Observability for LLM Systems








A lightweight PromptOps layer to manage, version, validate, and monitor reusable LLM prompt templates — built using Python, Flask, YAML, Jinja2, and JSON Schema.

Treat prompts like code: versioned, validated, observable, and reusable.

🚀 Project Description (GitHub Summary)

Prompt Layer provides an API-driven abstraction over LLM prompts, enabling teams to:

Store prompts as structured YAML files

Render prompts dynamically with Jinja2

Enforce output schemas using JSON Schema

Track latency, versions, and usage metrics

Expose observability endpoints for production systems

This project is ideal for LLM applications, AI agents, RAG systems, and PromptOps workflows where prompt quality, consistency, and monitoring matter.

✨ Key Features
✅ Prompt Templates as Code

Prompts stored in prompts/*.yaml

Each prompt includes:

prompt_id

semantic version

description

Jinja2 template

example inputs

expected output schema

✅ Versioning & Metadata

Semantic version comparison using packaging.version

Fetch latest or specific prompt versions

Metadata-first design for future evaluation & A/B testing

✅ Dynamic Prompt Rendering

Render prompts dynamically through REST APIs

Jinja2-based templating for flexible input injection

✅ Usage Logging (Prompt Telemetry)

Append-only structured logs in prompt_usage.jsonl

Logs include:

timestamp

prompt id & version

latency

model info

custom metadata

✅ Schema Validation

Enforces JSON Schema validation on model outputs

Fails fast on malformed or hallucinated outputs

✅ Metrics & Observability

Auto-aggregated metrics:

total usage count

average latency

last seen timestamp

latest version

Available via /metrics

Optional persistence (prompt_metrics.json)

✅ Health & Debug Endpoints

/health — service heartbeat

/last-usage — last prompt execution snapshot

🧩 Project Structure
prompt-layer/
│
├── prompts/
│   ├── summarization.yaml
│   └── classification.yaml
│
├── src/
│   └── prompt_manager.py   # Core API, rendering, logging, metrics
│
├── prompt_usage.jsonl      # Append-only usage logs
├── prompt_metrics.json     # Persisted metrics (auto-generated)
└── README.md

🧠 Example Prompt Definition
prompt_id: summarization_short
version: "1.0.0"
description: Create a short (max 50 words) summary for provided text.
template: |
  Summarize the following text in one paragraph, maximum 50 words:
  {{ text }}
example_inputs:
  - text: "Long article text..."
expected_output_schema:
  type: object
  properties:
    summary:
      type: string
output_instructions: >
  Return a JSON object: { "summary": "<50-word summary>" }

⚙️ Setup & Run
1️⃣ Clone the Repo
git clone https://github.com/madhuram99/prompt-layer.git
cd prompt-layer

2️⃣ Install Dependencies
pip install flask pyyaml jinja2 jsonschema packaging

3️⃣ Run the API
python src/prompt_manager.py


🟢 Server runs at:
http://127.0.0.1:5000

🧪 API Usage Examples
🔹 Health Check
curl http://127.0.0.1:5000/health

🔹 Get Prompt Definition
curl http://127.0.0.1:5000/prompt/summarization_short

🔹 Render Prompt
curl -X POST http://127.0.0.1:5000/prompt/summarization_short/render \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","inputs":{"text":"OpenAI released a new model."}}'

🔹 Log Usage
curl -X POST http://127.0.0.1:5000/prompt/summarization_short/log \
  -H "Content-Type: application/json" \
  -d '{
    "version":"1.0.0",
    "input":{"text":"Long article"},
    "response":{"summary":"Short summary"},
    "latency_ms":243.5,
    "metadata":{"model":"gpt-5"}
  }'

🔹 Metrics Endpoint
curl http://127.0.0.1:5000/metrics
