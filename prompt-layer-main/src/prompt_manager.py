

"""
prompt_manager.py
- Loads YAML prompt templates from ../prompts/*.yaml
- Provides:
    - get_prompt(prompt_id, version=None) -> dict
    - log_usage(...) -> dict (writes a line to ../prompt_usage.jsonl)
    - render_prompt(prompt_id, inputs, version=None) -> str
- Also provides a tiny Flask API when run as __main__:
    GET  /prompt/<prompt_id>?version=<version>
    POST /prompt/<prompt_id>/log  (body: JSON usage payload)
    POST /prompt/<prompt_id>/render (render a prompt with inputs)
    GET  /metrics  (aggregate prompt usage metrics)
    GET  /health   (basic health check)
"""

import os
import glob
import yaml
import json
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections import defaultdict
from statistics import mean

from flask import Flask, jsonify, request, abort

# Additional libs (install: jinja2 jsonschema packaging)
from jinja2 import Template, StrictUndefined
from jsonschema import validate as jsonschema_validate, ValidationError
from packaging.version import parse as parse_version

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # prompt-layer/
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
USAGE_LOG_PATH = os.path.join(BASE_DIR, "prompt_usage.jsonl")

# in-memory index: { prompt_id: [versions...] } where each entry is the parsed YAML dict
_PROMPT_INDEX: Dict[str, List[Dict[str, Any]]] = {}


def _load_prompts():
    """Load all YAML prompts from PROMPTS_DIR into _PROMPT_INDEX (called at import)."""
    global _PROMPT_INDEX
    _PROMPT_INDEX = {}
    pattern = os.path.join(PROMPTS_DIR, "*.yaml")
    for path in glob.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data or "prompt_id" not in data:
                    print(f"Skipping {path}: missing prompt_id")
                    continue
                pid = str(data["prompt_id"])
                version = str(data.get("version", "0.0.0"))
                entry = dict(data)
                entry["_source_file"] = os.path.basename(path)
                # timezone-aware timestamp
                entry["_loaded_at"] = datetime.now(timezone.utc).isoformat()
                # ensure metadata fields exist
                entry.setdefault("example_inputs", [])
                entry.setdefault("expected_output_schema", {})
                _PROMPT_INDEX.setdefault(pid, []).append(entry)
        except Exception as e:
            print(f"Failed to load {path}: {e}")

    # sort version list by semantic version (newest first)
    for pid, versions in _PROMPT_INDEX.items():
        try:
            versions.sort(key=lambda x: parse_version(str(x.get("version", "0.0.0"))), reverse=True)
        except Exception:
            # fallback to lexical if parse fails for some reason
            versions.sort(key=lambda x: str(x.get("version", "")), reverse=True)


# load on import
_load_prompts()


def get_prompt(prompt_id: str, version: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch prompt metadata and template by prompt_id, optionally by version.
    Returns a dict, or raises KeyError if not found.
    """
    if prompt_id not in _PROMPT_INDEX:
        raise KeyError(f"prompt_id '{prompt_id}' not found")
    candidates = _PROMPT_INDEX[prompt_id]
    if version is None:
        # return highest-sorted version (first in list after semantic sort)
        return dict(candidates[0])
    # find exact version
    for v in candidates:
        if str(v.get("version")) == str(version):
            return dict(v)
    raise KeyError(f"prompt_id '{prompt_id}' with version '{version}' not found")


def _ensure_usage_file_exists():
    if not os.path.exists(USAGE_LOG_PATH):
        # create parent dir if needed
        os.makedirs(os.path.dirname(USAGE_LOG_PATH), exist_ok=True)
        with open(USAGE_LOG_PATH, "w", encoding="utf-8") as f:
            pass


def render_prompt(prompt_id: str, inputs: Dict[str, Any], version: Optional[str] = None) -> str:
    """
    Render the prompt template for given prompt_id/version using Jinja2.
    Returns the rendered prompt string.
    Raises KeyError if prompt not found, or jinja2 exceptions for missing keys.
    """
    prompt = get_prompt(prompt_id, version)
    template_text = prompt.get("template", "")
    tmpl = Template(template_text, undefined=StrictUndefined)
    rendered = tmpl.render(**(inputs or {}))
    return rendered


def log_usage(prompt_id: str,
              version: str,
              input_data: Dict[str, Any],
              response: Dict[str, Any],
              latency_ms: float,
              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Append a usage record to prompt_usage.jsonl and return the record.
    Also validates `response` against expected_output_schema if available and
    records validation result in metadata.validation_error (if any).
    Fields written: timestamp, prompt_id, version, input, response, latency_ms, metadata
    """
    _ensure_usage_file_exists()

    validation_error = None
    # try to fetch prompt metadata to get expected_output_schema
    try:
        prompt_meta = get_prompt(prompt_id, version)
        schema = prompt_meta.get("expected_output_schema")
        if schema:
            try:
                jsonschema_validate(instance=response, schema=schema)
            except ValidationError as ve:
                validation_error = str(ve)
    except KeyError:
        # prompt not found — mark in validation_error for traceability
        validation_error = (validation_error or "") + " prompt metadata not found."

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_id": prompt_id,
        "version": version,
        "input": input_data,
        "response": response,
        "latency_ms": float(latency_ms),
        "metadata": metadata or {}
    }

    if validation_error:
        record["metadata"] = dict(record["metadata"])
        record["metadata"]["validation_error"] = validation_error

    # append as JSON line
    with open(USAGE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# ---- Tiny HTTP API (Flask) ----
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def api_health():
    """
    Basic health endpoint. Returns ok if the service can access prompts directory.
    """
    ok = os.path.isdir(PROMPTS_DIR)
    return jsonify({"status": "ok" if ok else "error", "prompts_dir_exists": ok}), (200 if ok else 500)


@app.route("/prompt/<prompt_id>", methods=["GET"])
def api_get_prompt(prompt_id):
    version = request.args.get("version")
    try:
        prompt = get_prompt(prompt_id, version)
    except KeyError:
        abort(404, description="Prompt not found")
    return jsonify(prompt)


@app.route("/prompt/<prompt_id>/render", methods=["POST"])
def api_render_prompt(prompt_id):
    """
    POST /prompt/<prompt_id>/render
    body: { "version": "1.0.0", "inputs": { ... } }
    returns: { "rendered": "..." }
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        abort(400, description="Missing JSON body")
    version = body.get("version")
    inputs = body.get("inputs", {})
    try:
        rendered = render_prompt(prompt_id, inputs, version)
    except KeyError:
        abort(404, description="Prompt or version not found")
    except Exception as e:
        abort(400, description=f"Template render error: {e}")
    return jsonify({"rendered": rendered})


@app.route("/prompt/<prompt_id>/log", methods=["POST"])
def api_log_usage(prompt_id):
    body = request.get_json(force=True, silent=True)
    if not body:
        abort(400, description="Missing JSON body")
    version = body.get("version")
    input_data = body.get("input", {})
    response = body.get("response", {})
    latency_ms = body.get("latency_ms", None)
    metadata = body.get("metadata", {})

    if version is None or latency_ms is None:
        abort(400, description="Missing required fields: version, latency_ms")

    # optional: verify prompt exists (fail fast)
    try:
        _ = get_prompt(prompt_id, version)
    except KeyError:
        abort(404, description="Prompt or version not found")

    rec = log_usage(prompt_id=prompt_id,
                    version=version,
                    input_data=input_data,
                    response=response,
                    latency_ms=latency_ms,
                    metadata=metadata)
    return jsonify({"status": "ok", "record": rec})


@app.route("/metrics", methods=["GET"])
def api_metrics():
    """
    Return aggregated metrics from prompt_usage.jsonl:
    {
      "<prompt_id>": {
         "count": int,
         "avg_latency_ms": float|null,
         "last_seen": "2025-10-28T09:30:43Z"|null,
         "latest_version": "1.0.0"|null
      }, ...
    }
    """
    if not os.path.exists(USAGE_LOG_PATH):
        return jsonify({"metrics": {}, "note": "no usage file found"}), 200

    agg = defaultdict(lambda: {"latencies": [], "count": 0, "last_seen": None, "latest_version": None})
    try:
        with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    # skip malformed JSON lines
                    continue

                pid = rec.get("prompt_id") or "<unknown>"
                latency = rec.get("latency_ms")
                ts = rec.get("timestamp")
                ver = rec.get("version")

                entry = agg[pid]
                if isinstance(latency, (int, float)):
                    entry["latencies"].append(float(latency))
                entry["count"] += 1

                # update last_seen if timestamp is newer (string comparison OK for ISO8601)
                if ts and (entry["last_seen"] is None or ts > entry["last_seen"]):
                    entry["last_seen"] = ts

                # update latest_version using semantic comparison when possible
                if ver:
                    try:
                        if entry["latest_version"] is None or parse_version(str(ver)) > parse_version(str(entry["latest_version"])):
                            entry["latest_version"] = ver
                    except Exception:
                        # fallback to lexical compare if parse fails
                        if entry["latest_version"] is None or str(ver) > str(entry["latest_version"]):
                            entry["latest_version"] = ver
    except Exception as e:
        return jsonify({"error": f"failed to read usage file: {e}"}), 500

    metrics = {}
    for pid, data in agg.items():
        avg_latency = mean(data["latencies"]) if data["latencies"] else None
        metrics[pid] = {
            "count": data["count"],
            "avg_latency_ms": avg_latency,
            "last_seen": data["last_seen"],
            "latest_version": data["latest_version"]
        }

    return jsonify({"metrics": metrics}), 200


if __name__ == "__main__":
    # development server - change host/port via PROMPT_MANAGER_PORT env var if needed
    port = int(os.environ.get("PROMPT_MANAGER_PORT", "5000"))
    host = os.environ.get("PROMPT_MANAGER_HOST", "127.0.0.1")
    print(f"Starting prompt manager API on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
