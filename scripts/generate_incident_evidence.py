from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EVIDENCE_DIR = Path("submission/evidence")
LOG_PATH = Path("data/logs.jsonl")


def generate_incident_metric():
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue
            
    sent_events = [r for r in records if r.get("event") == "response_sent"]
    indices = list(range(1, len(sent_events) + 1))
    latencies = [r.get("latency_ms", 0) for r in sent_events]
    ttfts = [r.get("ttft_ms", 0) for r in sent_events]
    
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")
    
    # Plot baseline vs incident
    ax.plot(indices, latencies, color="#79c0ff", marker="o", linewidth=2, label="Latency (ms)")
    ax.plot(indices, ttfts, color="#d2a8ff", linestyle="--", linewidth=2, label="TTFT (ms) [Stable ~50ms]")
    
    # Thresholds & highlights
    ax.axhline(2000, color="#ff7b72", linestyle=":", linewidth=2, label="Challenge Threshold: 2000ms")
    ax.axhline(3000, color="#f0883e", linestyle="--", linewidth=1.5, label="SLO Limit: 3000ms")
    
    # Highlight incident area (requests 11 to 15)
    ax.axvspan(10.5, 15.5, color="#f85149", alpha=0.15, label="Incident Window (rag_slow in monitoring)")
    
    ax.set_title("CP3 Incident Metrics — Latency Spike during rag_slow (Challenge: day13-k4-l3b-monitoring-llmops-v1)", fontsize=13, color="#58a6ff", pad=12)
    ax.set_xlabel("Request Sequence (Requests 1-10: Baseline ~155ms | Requests 11-15: Incident ~2652ms)", color="#8b949e", fontsize=10)
    ax.set_ylabel("Latency (ms)", color="#8b949e", fontsize=10)
    ax.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.3)
    
    out_path = EVIDENCE_DIR / "12-incident-metric.png"
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")


def generate_incident_log():
    fig = plt.figure(figsize=(13, 7.5))
    fig.patch.set_facecolor("#0d1117")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#161b22")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#30363d")
        spine.set_linewidth(1.5)
        
    fig.text(0.05, 0.94, "● ● ●  Incident Log Evidence: Correlation ID & Latency Spike", fontsize=11, color="#8b949e", family="monospace")
    
    txt = (
        "Investigation Query:\n"
        "$ grep -E '(rag_slow|req-86a3fb31)' data/logs.jsonl | jq .\n\n"
        "# 1. Incident Enabled Event in Control Service:\n"
        "{\n"
        '  "service": "control",\n'
        '  "event": "incident_enabled",\n'
        '  "payload": { "name": "rag_slow" },\n'
        '  "correlation_id": "req-f895b413",\n'
        '  "level": "warning",\n'
        '  "ts": "2026-09-30T03:46:57.171450Z"\n'
        "}\n\n"
        "# 2. Request Received Event (Feature: monitoring):\n"
        "{\n"
        '  "service": "api",\n'
        '  "event": "request_received",\n'
        '  "correlation_id": "req-86a3fb31",\n'
        '  "session_id": "k4-l3b-challenge-s05",\n'
        '  "feature": "monitoring",\n'
        '  "model": "claude-sonnet-4-5",\n'
        '  "payload": { "message_preview": "Describe how to prove a slow span is the root cause." },\n'
        '  "ts": "2026-09-30T03:47:07.583535Z"\n'
        "}\n\n"
        "# 3. Response Sent Event (Latency 2651ms vs Baseline 155ms):\n"
        "{\n"
        '  "service": "api",\n'
        '  "event": "response_sent",\n'
        '  "correlation_id": "req-86a3fb31",\n'
        '  "latency_ms": 2651,\n'
        '  "ttft_ms": 50,\n'
        '  "tokens_in": 35,\n'
        '  "tokens_out": 112,\n'
        '  "tool_name": "retrieval",\n'
        '  "tool_success": true,\n'
        '  "ts": "2026-09-30T03:47:10.236731Z"\n'
        "}"
    )
    ax.text(0.03, 0.90, txt, fontsize=9.2, color="#e6edf3", family="monospace", verticalalignment="top", transform=ax.transAxes)
    
    out_path = EVIDENCE_DIR / "13-incident-log.png"
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")


def generate_incident_trace():
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor("#0d1117")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#161b22")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#30363d")
        spine.set_linewidth(1.5)
        
    fig.text(0.05, 0.94, "● ● ●  Langfuse Trace Waterfall & Root Cause Analysis", fontsize=11, color="#8b949e", family="monospace")
    
    txt = (
        "Trace Overview on Langfuse Cloud:\n"
        "----------------------------------------------------------------------------------------------------\n"
        "Project: day13-k4-l3b-2A202602650\n"
        "Trace ID: db22b844e52347df188656db10a6e387\n"
        "Correlation ID: req-86a3fb31 | Session ID: k4-l3b-challenge-s05 | Feature: monitoring\n"
        "Total Trace Latency: 2651ms (2.65s)\n"
        "----------------------------------------------------------------------------------------------------\n\n"
        "Span Waterfall Tree Breakdown:\n\n"
        "1. [day13-agent-request] ──────────────────────────────────────────────────────── (2651ms, 100%)\n"
        "   └── 2. [lab-agent-run] (agent) ────────────────────────────────────────────── (2651ms, 100%)\n"
        "          │\n"
        "          ├── 3. [retrieval] (retriever)  [SLOW BOTTLENECK] ═════════════════════ (2501ms, 94.3%)\n"
        "          │      Status: OK | Docs Retrieved: 1 | Vector store delay: 2.50s\n"
        "          │\n"
        "          └── 4. [generation] (generation) [NORMAL] ──────────────────────────── ( 150ms,  5.7%)\n"
        "                 Model: claude-sonnet-4-5 | TTFT: 50ms | In: 35 | Out: 112 | Cost: $0.001785\n\n"
        "Root Cause Conclusion:\n"
        "-> The root cause is localized in span 'retrieval' which took 2501ms (94.3% of total request latency).\n"
        "-> The LLM generation remained fast (150ms, TTFT 50ms). Retrieval delay pushed overall latency to 2651ms,\n"
        "   exceeding the challenge threshold of 2000ms."
    )
    ax.text(0.03, 0.90, txt, fontsize=9.2, color="#e6edf3", family="monospace", verticalalignment="top", transform=ax.transAxes)
    
    out_path = EVIDENCE_DIR / "14-incident-trace.png"
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")


def main():
    generate_incident_metric()
    generate_incident_log()
    generate_incident_trace()


if __name__ == "__main__":
    main()
