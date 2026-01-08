🧠 Prompt Layer — Reusable Prompt Templates, Versioning & Metrics:

A lightweight PromptOps layer for managing, versioning, and monitoring reusable LLM prompt templates — built with Python, Flask, YAML, and Jinja2.

Treat prompts like code — with metadata, schema validation, version control, and performance tracking.


🚀 Features:

✅ Prompt Templates as Code

Store prompts in prompts/*.yaml

Each prompt includes metadata, version, examples, and output schema.

✅ Versioning & Metadata

Semantic version sort using packaging.version

Example inputs and expected output schemas for each prompt

✅ Dynamic Rendering

Render Jinja2 templates dynamically via REST API

✅ Usage Logging

Logs every prompt call to prompt_usage.jsonl

Tracks: timestamp, version, latency, model, metadata, etc.

✅ Schema Validation

Validates model responses against JSON Schema

✅ Metrics & Observability

Aggregates metrics (count, avg latency, last seen)

Exposes via /metrics

Optionally persists to prompt_metrics.json

✅ Health & Debug Endpoints

/health — quick API heartbeat

/last-usage — get the most recent log entry


🧩 Project Structure:
prompt-layer/
│
├── prompts/
│   ├── summarization.yaml
│   └── classification.yaml
│
├── src/
│   └── prompt_manager.py        # Main API server + utilities
│
├── prompt_usage.jsonl           # Appended usage logs
├── prompt_metrics.json          # Persisted metrics (auto-generated)
└── README.md


🧠 Example Prompt (prompts/summarization.yaml):
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


⚙️ Setup
1️⃣ Clone the repo:
git clone https://github.com/Shank312/prompt-layer.git
cd prompt-layer


2️⃣ Install dependencies:
pip install flask pyyaml jinja2 jsonschema packaging


3️⃣ Run the API:
python src/prompt_manager.py

🟢 Server starts at:
http://127.0.0.1:5000


🧪 Example Usage:
🔹 Health Check:
curl "http://127.0.0.1:5000/health"

Response
{"status": "ok", "prompts_dir_exists": true}

🔹 Get Prompt Definition:
curl "http://127.0.0.1:5000/prompt/summarization_short"

🔹 Render Prompt:
curl -X POST "http://127.0.0.1:5000/prompt/summarization_short/render" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","inputs":{"text":"OpenAI released a new AI model today."}}'

Output:
{
  "rendered": "Summarize the following text in one paragraph, maximum 50 words:\nOpenAI released a new AI model today."
}

🔹 Log Usage:
curl -X POST "http://127.0.0.1:5000/prompt/summarization_short/log" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.0.0","input":{"text":"Long article..."},"response":{"summary":"Short summary."},"latency_ms":243.5,"metadata":{"model":"gpt-5"}}'

🔹 View Metrics:
curl "http://127.0.0.1:5000/metrics"

Output:
{
  "metrics": {
    "summarization_short": {
      "avg_latency_ms": 278.1,
      "count": 2,
      "last_seen": "2025-10-30T10:20:01.888609+00:00",
      "latest_version": "1.0.0"
    }
  }
}


🧾 Example Screenshot:

Below: API in action — /health, /render, /log, /metrics tested locally.
(Screenshot from Git Bash — color-coded commands & outputs for clarity)


🧠 Key Design Choices

Jinja2 for flexible prompt rendering

YAML for human-readable prompt storage

JSON Schema for response validation

JSONL Logging for structured, append-only analytics

Persistent Metrics File for fast /metrics access


🧭 Next Steps

 Add API key authentication

 Build /dashboard web UI with charts

 Integrate OpenAI API for prompt evaluation

 Add CLI tool: prompt-cli render <id>

 Dockerize for local + cloud deployment


 💬 Contributing:

Contributions welcome!

Fork the repo

Create a feature branch

Submit a pull request


 🧑‍💻 Author

Shankar Kumar
🌐 GitHub• 💼 LinkedIn


 🏷️ License

MIT License © 2025 Shankar Kumar
Free for educational, research, and commercial use.
