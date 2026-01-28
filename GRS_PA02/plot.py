import pandas as pd
import matplotlib.pyplot as plt

# ================================
# Load CSV
# ================================
CSV_FILE = "results.csv"

df = pd.read_csv(CSV_FILE)

# Clean column names (safety)
df.columns = (
    df.columns
    .str.strip()
    .str.replace("\ufeff", "", regex=False)
)

print("Detected columns:", list(df.columns))

# ================================
# Convert data types
# ================================
df["msg_size"] = df["msg_size"].astype(int)
df["threads"] = df["threads"].astype(int)
df["throughput_mbps"] = df["throughput_mbps"].astype(float)
df["latency_us"] = df["latency_us"].astype(float)
df["context_switches"] = df["context_switches"].astype(int)

modes = ["twocopy", "onecopy", "zerocopy"]

# ================================
# Plot 1: Throughput vs Threads (msg_size = 1024)
# ================================
plt.figure()
for mode in modes:
    sub = df[(df["mode"] == mode) & (df["msg_size"] == 1024)]
    plt.plot(sub["threads"], sub["throughput_mbps"], marker="o", label=mode)

plt.xlabel("Threads")
plt.ylabel("Throughput (Mbps)")
plt.title("Throughput vs Threads (Message Size = 1024 bytes)")
plt.legend()
plt.grid(True)
plt.savefig("plot_throughput_vs_threads.png", dpi=300)
plt.close()

# ================================
# Plot 2: Throughput vs Message Size (threads = 4)
# ================================
plt.figure()
for mode in modes:
    sub = df[(df["mode"] == mode) & (df["threads"] == 4)]
    plt.plot(sub["msg_size"], sub["throughput_mbps"], marker="o", label=mode)

plt.xlabel("Message Size (bytes)")
plt.ylabel("Throughput (Mbps)")
plt.title("Throughput vs Message Size (Threads = 4)")
plt.legend()
plt.grid(True)
plt.savefig("plot_throughput_vs_msgsize.png", dpi=300)
plt.close()

# ================================
# Plot 3: Latency vs Threads (msg_size = 1024)
# ================================
plt.figure()
for mode in modes:
    sub = df[(df["mode"] == mode) & (df["msg_size"] == 1024)]
    plt.plot(sub["threads"], sub["latency_us"], marker="o", label=mode)

plt.xlabel("Threads")
plt.ylabel("Latency (µs)")
plt.title("Latency vs Threads (Message Size = 1024 bytes)")
plt.legend()
plt.grid(True)
plt.savefig("plot_latency_vs_threads.png", dpi=300)
plt.close()

# ================================
# Plot 4: Context Switches vs Threads (msg_size = 1024)
# ================================
plt.figure()
for mode in modes:
    sub = df[(df["mode"] == mode) & (df["msg_size"] == 1024)]
    plt.plot(sub["threads"], sub["context_switches"], marker="o", label=mode)

plt.xlabel("Threads")
plt.ylabel("Context Switches")
plt.title("Context Switches vs Threads (Message Size = 1024 bytes)")
plt.legend()
plt.grid(True)
plt.savefig("plot_context_switches_vs_threads.png", dpi=300)
plt.close()

print("All plots generated successfully.")
