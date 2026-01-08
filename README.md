# 🧠 prompts-layer

### Reusable Prompt Templates, Versioning & Observability for LLM Systems

A lightweight **PromptOps** layer designed to manage, version, validate, and monitor reusable LLM prompt templates. Built using **Python, Flask, YAML, Jinja2, and JSON Schema**, it allows you to treat prompts like code: versioned, validated, and observable.



---

## 🚀 Project Description
**prompts-layer** provides an API-driven abstraction over LLM prompts, enabling developers and AI engineers to:
* **Store** prompts as structured YAML files.
* **Render** prompts dynamically with Jinja2.
* **Enforce** output schemas using JSON Schema.
* **Track** latency, versions, and usage metrics in real-time.

This project is ideal for LLM applications, AI agents, RAG systems, and PromptOps workflows where consistency and monitoring are critical.

---

## ✨ Key Features

* **✅ Prompt Templates as Code**: Store prompts in `prompts/*.yaml` with built-in semantic versioning and metadata.
* **✅ Dynamic Rendering**: Flexible input injection using Jinja2-based templating.
* **✅ Usage Logging**: Append-only structured logs (`prompt_usage.jsonl`) for telemetry.
* **✅ Schema Validation**: Enforce JSON Schema on model outputs to prevent hallucinated structures.
* **✅ Metrics & Observability**: Auto-aggregated metrics (avg latency, usage counts, last seen) available via `/metrics`.
* **✅ Versioning**: Native support for semantic version comparison via `packaging.version`.

---

## 🧩 Project Structure

```text
prompts-layer/
│
├── prompts/
│   ├── summarization.yaml    # Prompt definitions (YAML)
│   └── classification.yaml
│
├── src/
│   └── prompt_manager.py     # Core API, rendering, and logic
│
├── prompt_usage.jsonl        # Append-only usage logs (Telemetry)
├── prompt_metrics.json       # Persisted metrics (Auto-generated)
└── README.md

🧠 Example Prompt Definitionprompts/summarization_short.yamlYAMLprompt_id: summarization_short
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
⚙️ Setup & Run1️⃣ Clone the RepoBashgit clone [https://github.com/madhuram99/prompts-layer.git](https://github.com/madhuram99/prompts-layer.git)
cd prompts-layer
2️⃣ Install DependenciesBashpip install flask pyyaml jinja2 jsonschema packaging
3️⃣ Run the APIBashpython src/prompt_manager.py
🟢 Server starts at: http://127.0.0.1:5000🧪 API Usage ExamplesActionCommandHealth Checkcurl http://127.0.0.1:5000/healthGet Definitioncurl http://127.0.0.1:5000/prompt/summarization_shortRender Promptcurl -X POST http://127.0.0.1:5000/prompt/summarization_short/render -H "Content-Type: application/json" -d '{"version":"1.0.0","inputs":{"text":"LLM Ops is evolving."}}'Log Usagecurl -X POST http://127.0.0.1:5000/prompt/summarization_short/log -H "Content-Type: application/json" -d '{"version":"1.0.0","latency_ms":243.5,"metadata":{"model":"gpt-5"}}'View Metricscurl http://127.0.0.1:5000/metrics🧑‍💻 AuthorMadhuram Rathi 🌐 GitHub • 💼 LinkedIn🏷️ LicenseMIT License © 2026 Madhuram Rathi
