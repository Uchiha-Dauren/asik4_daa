"""Validate measured CSV, calculate five-run medians, and draw four plots."""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader((RESULTS / "results.csv").open()))
assert len(rows) == 570, f"Expected 570 measured runs; found {len(rows)}"
groups = defaultdict(list)
for r in rows:
    key = tuple(r[k] for k in ["algorithm", "input", "n", "m", "suite"])
    groups[key].append(r)
    assert float(r["time_ms"]) > 0
    assert int(r["total_comparisons"]) == int(r["search_comparisons"]) + int(r["lps_comparisons"])
    assert abs(float(r["batch_time_ms"]) / int(r["batch_iterations"]) - float(r["time_ms"])) < 1e-8

summary = []
for key, values in groups.items():
    assert sorted(int(r["run"]) for r in values) == [1, 2, 3, 4, 5]
    for field in ["state_visits", "search_comparisons", "lps_comparisons", "result", "input_sha256"]:
        assert len({r[field] for r in values}) == 1, (key, field)
    r = values[0]
    n, m = int(r["n"]), int(r["m"])
    # Independent consistency checks; measurements themselves come from Java counters.
    if r["algorithm"] in ["TableEditDistance", "TwoRowEditDistance"]:
        assert int(r["state_visits"]) == (n + 1) * (m + 1)
    if r["algorithm"] == "RecursiveEditDistance" and r["input"] == "identical":
        assert int(r["state_visits"]) == n + 1
    if r["algorithm"] == "NaiveSearch" and r["input"] == "near_match":
        assert int(r["total_comparisons"]) == (n - m + 1) * m
    if r["algorithm"] == "KmpSearch" and r["input"] == "near_match":
        assert int(r["total_comparisons"]) == 2 * n + m - 2
    item = dict(zip(["algorithm", "input", "n", "m", "suite"], key))
    item.update(median_time_ms=median(float(x["time_ms"]) for x in values),
                min_time_ms=min(float(x["time_ms"]) for x in values),
                max_time_ms=max(float(x["time_ms"]) for x in values))
    for field in ["state_visits", "search_comparisons", "lps_comparisons", "total_comparisons", "result"]:
        item[field] = int(r[field])
    summary.append(item)

# All algorithms in a family receive identical inputs and must return identical results.
inputs = defaultdict(list)
for r in rows:
    inputs[(r["suite"], r["input"], r["n"], r["m"])].append(r)
for values in inputs.values():
    assert len({r["input_sha256"] for r in values}) == 1
    assert len({r["result"] for r in values}) == 1

with (RESULTS / "summary.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "figure.facecolor": "white"})
names = {"RecursiveEditDistance": "Recursive", "TableEditDistance": "Table",
         "TwoRowEditDistance": "Two rows", "NaiveSearch": "Naive", "KmpSearch": "KMP (with LPS)"}
colors = {"RecursiveEditDistance": "#d35400", "TableEditDistance": "#2357a6",
          "TwoRowEditDistance": "#14816b", "NaiveSearch": "#d35400", "KmpSearch": "#2357a6"}

def points(suite, input_type, algorithm):
    return sorted((r for r in summary if r["suite"] == suite and r["input"] == input_type
                   and r["algorithm"] == algorithm), key=lambda r: int(r["n"]))

def line(ax, data, field, algorithm):
    # Different markers keep Table and Two rows visible when their counts overlap.
    marker = "x" if algorithm == "TwoRowEditDistance" else "o"
    ax.plot([int(r["n"]) for r in data], [r[field] for r in data],
            color=colors[algorithm], marker=marker, markersize=5, linewidth=1.6,
            linestyle="--" if algorithm == "TwoRowEditDistance" else "-", label=names[algorithm])
    ax.grid(True, alpha=0.20)

def save(fig, filename):
    fig.savefig(PLOTS / (filename + ".png"), dpi=190, bbox_inches="tight")
    fig.savefig(PLOTS / (filename + ".svg"), bbox_inches="tight")
    plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(10, 3.3), constrained_layout=True)
for ax, kind in zip(axes, ["identical", "random", "disjoint"]):
    for algorithm in ["RecursiveEditDistance", "TableEditDistance", "TwoRowEditDistance"]:
        line(ax, points("edit_small", kind, algorithm), "state_visits", algorithm)
    ax.set(title=kind.replace("_", " ").title(), xlabel="Length n = m (characters)", yscale="log")
    ax.set_xticks([2, 4, 6, 8, 10, 12])
axes[0].set_ylabel("Processed states (count; log scale)")
axes[0].legend(fontsize=8)
fig.suptitle("Edit distance: repeated states make recursion expensive", fontsize=13, fontweight="bold")
save(fig, "01_edit_states")

fig, axes = plt.subplots(1, 2, figsize=(10, 3.3), constrained_layout=True)
for algorithm in ["TableEditDistance", "TwoRowEditDistance"]:
    data = points("edit_large", "disjoint", algorithm)
    line(axes[0], data, "median_time_ms", algorithm)
    n = [int(r["n"]) for r in data]
    slots = [(x + 1)**2 if algorithm == "TableEditDistance" else 2*(x+1) for x in n]
    axes[1].plot(n, slots, "o-", color=colors[algorithm], label=names[algorithm])
for ax in axes:
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("Length n = m (characters; log scale)")
    ax.set_xticks(n)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=8)
axes[0].set(title="Disjoint input: median of 5 runs", ylabel="Time (ms / invocation; log scale)")
axes[1].set(title="Theoretical storage (not heap measurement)", ylabel="Retained int slots (count; log scale)")
fig.suptitle("Two-row DP retains fewer cells", fontsize=13, fontweight="bold")
save(fig, "02_dp_time_space")

for field, filename, title, ylabel in [
    ("total_comparisons", "03_search_comparisons", "Search comparisons: growing text and pattern", "Character comparisons (count; log scale)"),
    ("median_time_ms", "04_search_time", "Search time: median of 5 runs, including LPS", "Time (ms / invocation; log scale)")]:
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.3), constrained_layout=True)
    for ax, kind in zip(axes, ["random", "first_mismatch", "near_match"]):
        for algorithm in ["NaiveSearch", "KmpSearch"]:
            line(ax, points("search", kind, algorithm), field, algorithm)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set(title=kind.replace("_", " ").title(), xlabel="Text length n (characters)")
        ax.set_xticks([10000, 40000, 160000], ["10,000", "40,000", "160,000"])
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel(ylabel)
    axes[0].legend(fontsize=8)
    fig.suptitle(title + " (m = n / 1000)", fontsize=12, fontweight="bold")
    save(fig, filename)

print(f"Validated {len(rows)} rows; wrote {len(summary)} medians and 4 plots.")
