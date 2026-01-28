import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ================================
# SYSTEM CONFIGURATION
# ================================
SYSTEM_CONFIG = """
System: VirtualBox VM
CPU: 2-core (or specify your CPU)
RAM: 8GB (or specify your RAM)
Kernel: Linux 5.x (or specify)
"""

# ================================
# Load CSV
# ================================
CSV_FILE = "results.csv"
df = pd.read_csv(CSV_FILE)

# Clean column names
df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
print("Detected columns:", list(df.columns))
print(f"Total rows: {len(df)}")

# ================================
# Convert data types
# ================================
df["msg_size"] = df["msg_size"].astype(int)
df["threads"] = df["threads"].astype(int)
df["throughput_gbps"] = df["throughput_gbps"].astype(float)
df["latency_us"] = df["latency_us"].astype(float)
df["cpu_cycles"] = df["cpu_cycles"].astype(int)
df["l1_misses"] = df["l1_misses"].astype(int)
df["llc_misses"] = df["llc_misses"].astype(int)
df["context_switches"] = df["context_switches"].astype(int)

modes = ["twocopy", "onecopy", "zerocopy"]
colors = {"twocopy": "red", "onecopy": "blue", "zerocopy": "green"}
markers = {"twocopy": "o", "onecopy": "s", "zerocopy": "^"}

# ================================
# PLOT 1: Throughput vs Message Size
# ================================
print("\nGenerating Plot 1: Throughput vs Message Size...")
plt.figure(figsize=(10, 6))

for mode in modes:
    sub = df[df["mode"] == mode].groupby("msg_size")["throughput_gbps"].mean().reset_index()
    plt.plot(
        sub["msg_size"], 
        sub["throughput_gbps"], 
        marker=markers[mode], 
        color=colors[mode],
        linewidth=2,
        markersize=8,
        label=mode
    )

plt.xlabel("Message Size (bytes)", fontsize=12, fontweight='bold')
plt.ylabel("Throughput (Gbps)", fontsize=12, fontweight='bold')
plt.title("Throughput vs Message Size\n(Averaged across all thread counts)", fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xscale('log', base=2)
plt.xticks(df["msg_size"].unique(), df["msg_size"].unique())

plt.text(0.02, 0.98, SYSTEM_CONFIG.strip(), 
         transform=plt.gca().transAxes,
         fontsize=8, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig("plot_throughput_vs_msgsize.png", dpi=300, bbox_inches='tight')
plt.close()
print("✓ Saved: plot_throughput_vs_msgsize.png")

# ================================
# PLOT 2: Latency vs Thread Count
# ================================
print("\nGenerating Plot 2: Latency vs Thread Count...")
plt.figure(figsize=(10, 6))

for mode in modes:
    sub = df[df["mode"] == mode].groupby("threads")["latency_us"].mean().reset_index()
    plt.plot(
        sub["threads"], 
        sub["latency_us"], 
        marker=markers[mode], 
        color=colors[mode],
        linewidth=2,
        markersize=8,
        label=mode
    )

plt.xlabel("Thread Count", fontsize=12, fontweight='bold')
plt.ylabel("Latency (µs)", fontsize=12, fontweight='bold')
plt.title("Latency vs Thread Count\n(Averaged across all message sizes)", fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xticks(df["threads"].unique())

plt.text(0.02, 0.98, SYSTEM_CONFIG.strip(), 
         transform=plt.gca().transAxes,
         fontsize=8, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig("plot_latency_vs_threads.png", dpi=300, bbox_inches='tight')
plt.close()
print("✓ Saved: plot_latency_vs_threads.png")

# ================================
# PLOT 3: Cache Misses vs Message Size
# ================================
print("\nGenerating Plot 3: Cache Misses vs Message Size...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

for mode in modes:
    sub = df[df["mode"] == mode].groupby("msg_size")["l1_misses"].mean().reset_index()
    ax1.plot(
        sub["msg_size"], 
        sub["l1_misses"], 
        marker=markers[mode], 
        color=colors[mode],
        linewidth=2,
        markersize=8,
        label=mode
    )

ax1.set_xlabel("Message Size (bytes)", fontsize=12, fontweight='bold')
ax1.set_ylabel("L1 Cache Misses", fontsize=12, fontweight='bold')
ax1.set_title("L1 Cache Misses vs Message Size", fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log', base=2)
ax1.set_xticks(df["msg_size"].unique())
ax1.set_xticklabels(df["msg_size"].unique())

for mode in modes:
    sub = df[df["mode"] == mode].groupby("msg_size")["llc_misses"].mean().reset_index()
    ax2.plot(
        sub["msg_size"], 
        sub["llc_misses"], 
        marker=markers[mode], 
        color=colors[mode],
        linewidth=2,
        markersize=8,
        label=mode
    )

ax2.set_xlabel("Message Size (bytes)", fontsize=12, fontweight='bold')
ax2.set_ylabel("LLC Cache Misses", fontsize=12, fontweight='bold')
ax2.set_title("LLC Cache Misses vs Message Size", fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log', base=2)
ax2.set_xticks(df["msg_size"].unique())
ax2.set_xticklabels(df["msg_size"].unique())

fig.text(0.02, 0.02, SYSTEM_CONFIG.strip(), 
         fontsize=8, verticalalignment='bottom',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig("plot_cache_misses_vs_msgsize.png", dpi=300, bbox_inches='tight')
plt.close()
print("✓ Saved: plot_cache_misses_vs_msgsize.png")

# ================================
# PLOT 4: CPU Cycles per Byte Transferred
# ================================
print("\nGenerating Plot 4: CPU Cycles per Byte...")

df["cycles_per_byte"] = df["cpu_cycles"] / (df["throughput_gbps"] * 1e9 * 10)

plt.figure(figsize=(10, 6))

for mode in modes:
    sub = df[df["mode"] == mode].groupby("msg_size")["cycles_per_byte"].mean().reset_index()
    plt.plot(
        sub["msg_size"], 
        sub["cycles_per_byte"], 
        marker=markers[mode], 
        color=colors[mode],
        linewidth=2,
        markersize=8,
        label=mode
    )

plt.xlabel("Message Size (bytes)", fontsize=12, fontweight='bold')
plt.ylabel("CPU Cycles per Byte", fontsize=12, fontweight='bold')
plt.title("CPU Cycles per Byte Transferred vs Message Size\n(Averaged across all thread counts)", 
          fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xscale('log', base=2)
plt.xticks(df["msg_size"].unique(), df["msg_size"].unique())

plt.text(0.02, 0.98, SYSTEM_CONFIG.strip(), 
         transform=plt.gca().transAxes,
         fontsize=8, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig("plot_cpu_cycles_per_byte.png", dpi=300, bbox_inches='tight')
plt.close()
print("✓ Saved: plot_cpu_cycles_per_byte.png")

# ================================
# Summary Statistics
# ================================
print("\n" + "="*50)
print("SUMMARY STATISTICS")
print("="*50)

for mode in modes:
    mode_data = df[df["mode"] == mode]
    print(f"\n{mode.upper()}:")
    print(f"  Avg Throughput: {mode_data['throughput_gbps'].mean():.4f} Gbps")
    print(f"  Avg Latency: {mode_data['latency_us'].mean():.2f} µs")
    print(f"  Avg CPU Cycles: {mode_data['cpu_cycles'].mean():.0f}")
    print(f"  Avg L1 Misses: {mode_data['l1_misses'].mean():.0f}")
    print(f"  Avg LLC Misses: {mode_data['llc_misses'].mean():.0f}")
    print(f"  Avg Context Switches: {mode_data['context_switches'].mean():.0f}")

print("\n" + "="*50)
print("✅ ALL PLOTS GENERATED SUCCESSFULLY")
print("="*50)
print("\nGenerated files:")
print("  1. plot_throughput_vs_msgsize.png")
print("  2. plot_latency_vs_threads.png")
print("  3. plot_cache_misses_vs_msgsize.png")
print("  4. plot_cpu_cycles_per_byte.png")