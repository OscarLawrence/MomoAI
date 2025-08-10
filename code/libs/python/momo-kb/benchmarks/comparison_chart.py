#!/usr/bin/env python3
"""
Create visual comparison charts for benchmark results.
"""

import matplotlib.pyplot as plt
import numpy as np


def create_performance_comparison():
    """Create performance comparison charts."""

    # Operation Latency Comparison
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # 1. Operation Latency
    systems = ["Momo KB", "Neo4j", "PostgreSQL", "SQLite"]
    latencies = [0.009, 0.1, 1.0, 0.5]
    colors = ["#2E8B57", "#FF6B6B", "#4ECDC4", "#45B7D1"]

    bars1 = ax1.bar(systems, latencies, color=colors)
    ax1.set_ylabel("Latency (ms)")
    ax1.set_title("Node Insert Latency Comparison")
    ax1.set_yscale("log")

    # Add value labels on bars
    for bar, value in zip(bars1, latencies):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value}ms",
            ha="center",
            va="bottom",
        )

    # 2. Throughput Comparison
    systems2 = ["Momo KB", "Typical Graph DB", "Typical Document DB"]
    throughputs = [99082, 5000, 25000]  # ops/sec
    colors2 = ["#2E8B57", "#FF6B6B", "#4ECDC4"]

    bars2 = ax2.bar(systems2, throughputs, color=colors2)
    ax2.set_ylabel("Operations per Second")
    ax2.set_title("Bulk Insert Throughput Comparison")

    for bar, value in zip(bars2, throughputs):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value:,}",
            ha="center",
            va="bottom",
        )

    # 3. Query Performance
    query_systems = ["Momo KB", "Redis GET", "Elasticsearch"]
    query_latencies = [1.6, 0.1, 10.0]
    colors3 = ["#2E8B57", "#FF6B6B", "#4ECDC4"]

    bars3 = ax3.bar(query_systems, query_latencies, color=colors3)
    ax3.set_ylabel("Query Latency (ms)")
    ax3.set_title("Query Performance Comparison")

    for bar, value in zip(bars3, query_latencies):
        height = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value}ms",
            ha="center",
            va="bottom",
        )

    # 4. Memory Efficiency
    memory_systems = ["Momo KB", "Typical Graph DB", "Typical Document DB"]
    memory_per_node = [1.1, 3.0, 2.5]  # KB per node
    colors4 = ["#2E8B57", "#FF6B6B", "#4ECDC4"]

    bars4 = ax4.bar(memory_systems, memory_per_node, color=colors4)
    ax4.set_ylabel("Memory per Node (KB)")
    ax4.set_title("Memory Efficiency Comparison")

    for bar, value in zip(bars4, memory_per_node):
        height = bar.get_height()
        ax4.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{value} KB",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig("benchmarks/performance_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()


def create_scaling_chart():
    """Create scaling characteristics chart."""

    # Data from benchmark results
    sizes = [100, 500, 1000, 5000, 10000]
    insert_rates = [105286, 106290, 106933, 88032, 87191]
    query_rates = [312112, 327758, 322576, 346463, 304099]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Insert Rate Scaling
    ax1.plot(sizes, insert_rates, "o-", color="#2E8B57", linewidth=2, markersize=8)
    ax1.set_xlabel("Dataset Size (nodes)")
    ax1.set_ylabel("Insert Rate (ops/sec)")
    ax1.set_title("Insert Performance Scaling")
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale("log")

    # Query Rate Scaling
    ax2.plot(sizes, query_rates, "s-", color="#FF6B6B", linewidth=2, markersize=8)
    ax2.set_xlabel("Dataset Size (nodes)")
    ax2.set_ylabel("Query Rate (results/sec)")
    ax2.set_title("Query Performance Scaling")
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale("log")

    plt.tight_layout()
    plt.savefig("benchmarks/scaling_characteristics.png", dpi=300, bbox_inches="tight")
    plt.show()


def create_feature_matrix():
    """Create feature comparison matrix."""

    features = [
        "Sub-ms Operations",
        "Immutable Data",
        "Rollback System",
        "Multi-Tier Storage",
        "Async Operations",
        "Memory Efficiency",
        "Bulk Throughput",
        "Query Performance",
        "Multi-Agent Ready",
    ]

    systems = ["Momo KB", "Neo4j", "PostgreSQL", "Redis", "Elasticsearch"]

    # Feature matrix (1 = excellent, 0.5 = good, 0 = poor/missing)
    matrix = np.array(
        [
            [1.0, 0.5, 0.0, 0.5, 0.0],  # Sub-ms Operations
            [1.0, 0.0, 0.0, 0.0, 0.0],  # Immutable Data
            [1.0, 0.0, 0.0, 0.0, 0.0],  # Rollback System
            [1.0, 0.0, 0.0, 0.0, 0.0],  # Multi-Tier Storage
            [1.0, 0.5, 0.5, 1.0, 0.5],  # Async Operations
            [1.0, 0.5, 0.5, 1.0, 0.5],  # Memory Efficiency
            [1.0, 0.5, 0.5, 1.0, 0.5],  # Bulk Throughput
            [0.5, 1.0, 0.5, 1.0, 1.0],  # Query Performance
            [1.0, 0.5, 0.0, 0.5, 0.5],  # Multi-Agent Ready
        ]
    )

    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(systems)))
    ax.set_yticks(np.arange(len(features)))
    ax.set_xticklabels(systems)
    ax.set_yticklabels(features)

    # Rotate the tick labels and set their alignment
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add text annotations
    for i in range(len(features)):
        for j in range(len(systems)):
            value = matrix[i, j]
            if value == 1.0:
                text = "✓"
                color = "white"
            elif value == 0.5:
                text = "~"
                color = "black"
            else:
                text = "✗"
                color = "white"
            ax.text(
                j,
                i,
                text,
                ha="center",
                va="center",
                color=color,
                fontsize=14,
                fontweight="bold",
            )

    ax.set_title("Feature Comparison Matrix", fontsize=16, fontweight="bold", pad=20)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label("Feature Support Level", rotation=270, labelpad=20)

    plt.tight_layout()
    plt.savefig("benchmarks/feature_matrix.png", dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    print("📊 Creating performance comparison charts...")

    try:
        create_performance_comparison()
        print("✅ Performance comparison chart saved")

        create_scaling_chart()
        print("✅ Scaling characteristics chart saved")

        create_feature_matrix()
        print("✅ Feature matrix chart saved")

        print("\n🎯 Charts saved to benchmarks/ directory")

    except ImportError:
        print("⚠️  matplotlib not available. Install with: uv add matplotlib")
        print("📊 Benchmark analysis available in benchmarks/analysis.md")
