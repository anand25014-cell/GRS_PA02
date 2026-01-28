# GRS_PA02
# PA02 – Analysis of Network I/O Primitives using perf

**Course:** Graduate Systems (CSE638)  
**Assignment:** PA02  
**Name:** Anand Pandey  
**Roll Number:** <YOUR_ROLL_NUMBER>  

---

## 📌 Overview

This project experimentally studies the cost of data movement in TCP network I/O by implementing and comparing:

1. **Two-copy socket communication** (baseline)
2. **One-copy optimized communication**
3. **Zero-copy communication**

A multithreaded client–server application was developed in C. Experiments were automated using a Bash script, and performance was measured using application-level metrics and the Linux `perf` tool.

---

## 🎯 Objectives

- Understand where memory copies occur in TCP socket communication
- Compare two-copy, one-copy, and zero-copy approaches
- Measure throughput, latency, and context switches
- Analyze the impact of message size and thread count
- Explain why zero-copy does not always provide the best performance

---

## 🧪 Experimental Setup

- **Operating System:** Linux (Ubuntu)
- **Environment:** VirtualBox Virtual Machine
- **Compiler:** `gcc -O2 -pthread`
- **Profiling Tool:** `perf`
- **Plotting:** Python (`matplotlib`, `pandas`)

⚠️ **Note:** Hardware PMU counters (CPU cycles, cache misses) were unavailable due to virtualization. Software counters and application-level metrics were used.

---

## 🧩 Implementation Details

### Server
- TCP-based, multithreaded
- One thread per client
- Transfers fixed-size messages repeatedly
- Each message consists of **8 dynamically allocated string fields**
- Supports three modes:
  - `twocopy`
  - `onecopy`
  - `zerocopy`

### Client
- Multithreaded
- Sends data continuously for a fixed duration
- Thread count and duration are runtime configurable
- Measures throughput and average latency

---

## 🔁 Communication Modes

### 1️⃣ Two-Copy (Baseline)
- Uses `send()` / `recv()`
- Copies data:
  - User space → Kernel space
  - Kernel space → NIC
- Includes an extra user-space copy during message assembly

### 2️⃣ One-Copy
- Uses `sendmsg()` with scatter-gather (`iovec`)
- Eliminates the intermediate user-space copy
- Kernel copy still exists

### 3️⃣ Zero-Copy
- Uses `sendmsg()` with `MSG_ZEROCOPY`
- Kernel pins user pages and performs DMA directly
- Introduces kernel bookkeeping overhead

---

## 📊 Metrics Collected

| Metric | Method |
|------|------|
| Throughput (Mbps) | Application-level |
| Latency (µs) | Application-level |
| Context switches | `perf stat` |
| CPU cycles | Not supported (VM limitation) |
| Cache misses | Not supported (VM limitation) |

---

## ⚙️ Automated Experiments

The script `run_experiments.sh`:
- Compiles the client and server
- Runs experiments for:
  - Message sizes: `64B, 256B, 1024B, 4096B`
  - Thread counts: `1, 2, 4, 8`
  - Modes: `twocopy, onecopy, zerocopy`
- Collects results into a CSV file
- Requires no manual intervention after start

---

## ▶️ How to Build

```bash
make clean
make
