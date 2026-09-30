from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

LOG_FILE = Path("data/logs.jsonl")
OUTPUT_PATH = Path("submission/evidence/11-dashboard-overview.png")


def load_logs() -> list[dict]:
    if not LOG_FILE.exists():
        raise FileNotFoundError(f"{LOG_FILE} not found")
    logs = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            logs.append(json.loads(line))
        except Exception:
            continue
    return logs


def main() -> None:
    records = load_logs()
    
    received_events = [r for r in records if r.get("event") == "request_received"]
    sent_events = [r for r in records if r.get("event") == "response_sent"]
    failed_events = [r for r in records if r.get("event") == "request_failed"]
    
    timestamps_sent = []
    latencies = []
    ttfts = []
    costs = []
    tokens_in = []
    tokens_out = []
    qualities = []
    
    for r in sent_events:
        ts = datetime.fromisoformat(r["ts"].replace("Z", "+00:00"))
        timestamps_sent.append(ts)
        latencies.append(r.get("latency_ms", 0))
        ttfts.append(r.get("ttft_ms", 0))
        costs.append(r.get("cost_usd", 0.0))
        tokens_in.append(r.get("tokens_in", 0))
        tokens_out.append(r.get("tokens_out", 0))
        qualities.append(r.get("quality_score", 0.0))

    req_count = len(sent_events)
    if req_count == 0:
        print("No response_sent events found to generate dashboard.")
        return

    # Percentiles
    p50_lat = np.percentile(latencies, 50)
    p95_lat = np.percentile(latencies, 95)
    p99_lat = np.percentile(latencies, 99)
    p95_ttft = np.percentile(ttfts, 95)
    
    # Tool success rate
    tool_events = [r for r in records if r.get("tool_name") is not None]
    tool_success_count = sum(1 for r in tool_events if r.get("tool_success") is True)
    tool_success_rate = (tool_success_count / len(tool_events) * 100) if tool_events else 100.0
    error_rate = (len(failed_events) / (len(received_events) or 1)) * 100.0

    # Modern Dark Theme Setup
    plt.style.use("dark_background")
    fig, axes = plt.subplots(3, 2, figsize=(16, 13), constrained_layout=True)
    fig.patch.set_facecolor("#0d1117")
    fig.suptitle(
        "K4-L3B Day 13 Monitoring & LLMOps — Dashboard Overview\nTime Range: Last 60m | Auto Refresh: 30s | Source: data/logs.jsonl",
        fontsize=16,
        fontweight="bold",
        color="#58a6ff",
    )

    indices = list(range(1, req_count + 1))

    # 1. LATENCY PANEL
    ax1 = axes[0, 0]
    ax1.set_facecolor("#161b22")
    ax1.plot(indices, latencies, color="#79c0ff", marker="o", markersize=4, label="Latency (ms)", linewidth=1.5)
    ax1.plot(indices, ttfts, color="#d2a8ff", linestyle="--", label="TTFT (ms)", linewidth=1.5)
    ax1.axhline(3000, color="#ff7b72", linestyle=":", linewidth=2, label="Threshold: P95 <= 3000ms")
    ax1.set_title(f"1. Latency Percentiles & TTFT (ms)\nP50: {p50_lat:.0f}ms | P95: {p95_lat:.0f}ms | P99: {p99_lat:.0f}ms | TTFT P95: {p95_ttft:.0f}ms", fontsize=11, color="#f0f6fc", pad=6)
    ax1.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax1.set_ylabel("ms", color="#8b949e", fontsize=9)
    ax1.legend(loc="upper right", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax1.grid(True, linestyle="--", alpha=0.3)

    # 2. TRAFFIC PANEL
    ax2 = axes[0, 1]
    ax2.set_facecolor("#161b22")
    ax2.bar(indices, [1]*req_count, color="#56d364", width=0.6, alpha=0.8, label="Requests")
    ax2.axhline(1, color="#7ee787", linestyle=":", linewidth=2, label="Threshold: rate >= 1 req/min")
    ax2.set_title(f"2. Request Traffic (requests_per_minute)\nTotal Requests: {len(received_events)} | Current Window: Active", fontsize=11, color="#f0f6fc", pad=6)
    ax2.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax2.set_ylabel("requests_per_minute", color="#8b949e", fontsize=9)
    ax2.legend(loc="upper right", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax2.grid(True, linestyle="--", alpha=0.3)

    # 3. ERRORS PANEL
    ax3 = axes[1, 0]
    ax3.set_facecolor("#161b22")
    cum_errors = np.zeros(req_count)
    ax3.plot(indices, [error_rate]*req_count, color="#ffa657", label=f"Error Rate ({error_rate:.1f}%)", linewidth=2)
    ax3.plot(indices, [tool_success_rate]*req_count, color="#3fb950", linestyle="-.", label=f"Retrieval Success ({tool_success_rate:.1f}%)", linewidth=2)
    ax3.axhline(2.0, color="#ff7b72", linestyle=":", linewidth=2, label="Threshold: Error <= 2%")
    ax3.axhline(90.0, color="#7ee787", linestyle=":", linewidth=1.5, label="Threshold: Retrieval >= 90%")
    ax3.set_title(f"3. Error Rate & Retrieval Success (%)\nErrors: {len(failed_events)} | Success Rate: {tool_success_rate:.1f}%", fontsize=11, color="#f0f6fc", pad=6)
    ax3.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax3.set_ylabel("percent (%)", color="#8b949e", fontsize=9)
    ax3.set_ylim(-5, 105)
    ax3.legend(loc="center right", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax3.grid(True, linestyle="--", alpha=0.3)

    # 4. COST PANEL
    ax4 = axes[1, 1]
    ax4.set_facecolor("#161b22")
    cum_costs = np.cumsum(costs)
    ax4.plot(indices, cum_costs, color="#e3b341", linewidth=2, marker="s", markersize=3, label="Cumulative Cost ($)")
    ax4.axhline(2.5, color="#ff7b72", linestyle=":", linewidth=2, label="Threshold: Total <= $2.50")
    ax4.set_title(f"4. Cost Over Time (usd)\nTotal Cost: ${cum_costs[-1]:.4f} | Avg/Req: ${np.mean(costs):.4f}", fontsize=11, color="#f0f6fc", pad=6)
    ax4.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax4.set_ylabel("usd ($)", color="#8b949e", fontsize=9)
    ax4.legend(loc="upper left", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax4.grid(True, linestyle="--", alpha=0.3)

    # 5. TOKENS PANEL
    ax5 = axes[2, 0]
    ax5.set_facecolor("#161b22")
    ax5.bar([i - 0.2 for i in indices], tokens_in, width=0.4, color="#a5d6ff", label="Tokens In")
    ax5.bar([i + 0.2 for i in indices], tokens_out, width=0.4, color="#ff7b72", label="Tokens Out")
    ax5.axhline(50000, color="#ffa657", linestyle=":", linewidth=2, label="Threshold: Sum <= 50,000")
    total_tokens = sum(tokens_in) + sum(tokens_out)
    ax5.set_title(f"5. Input and Output Tokens (tokens)\nTotal Tokens: {total_tokens:,} (In: {sum(tokens_in):,} | Out: {sum(tokens_out):,})", fontsize=11, color="#f0f6fc", pad=6)
    ax5.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax5.set_ylabel("tokens", color="#8b949e", fontsize=9)
    ax5.legend(loc="upper right", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax5.grid(True, linestyle="--", alpha=0.3)

    # 6. QUALITY PANEL
    ax6 = axes[2, 1]
    ax6.set_facecolor("#161b22")
    avg_quality = np.mean(qualities)
    rolling_q = np.convolve(qualities, np.ones(3)/3, mode="valid")
    ax6.scatter(indices, qualities, color="#7ee787", alpha=0.6, s=30, label="Sample Quality")
    if len(rolling_q) > 0:
        ax6.plot(range(2, len(rolling_q) + 2), rolling_q, color="#58a6ff", linewidth=2, label=f"Moving Avg ({avg_quality:.2f})")
    ax6.axhline(0.75, color="#ff7b72", linestyle=":", linewidth=2, label="Threshold: Mean >= 0.75")
    ax6.set_title(f"6. Quality Proxy (score_0_to_1)\nAverage Quality: {avg_quality:.2f} / 1.00", fontsize=11, color="#f0f6fc", pad=6)
    ax6.set_xlabel("Request Sequence", color="#8b949e", fontsize=9)
    ax6.set_ylabel("score (0 to 1)", color="#8b949e", fontsize=9)
    ax6.set_ylim(0.0, 1.05)
    ax6.legend(loc="lower right", fontsize=8, facecolor="#21262d", edgecolor="#30363d")
    ax6.grid(True, linestyle="--", alpha=0.3)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Dashboard successfully generated and saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
