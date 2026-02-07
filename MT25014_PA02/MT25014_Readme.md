## MT25014
# Network I/O Performance Analysis - MT25014

## 📋 Project Overview

This project implements and analyzes three network I/O data transfer mechanisms in a client-server architecture:
- **Mode 0 (A1)**: Two-Copy Implementation (Baseline blocking I/O)
- **Mode 1 (A2)**: One-Copy Implementation (sendmsg with scatter-gather I/O)
- **Mode 2 (A3)**: Zero-Copy Implementation (MSG_ZEROCOPY flag)

The goal is to measure and compare throughput, latency, CPU efficiency, and cache behavior across different message sizes and thread counts.

---

## 🎯 Key Findings

### Peak Performance
| Mode | Best Throughput | Configuration |
|------|-----------------|---------------|
| **Two-Copy (A1)** | **345.3 Gbps** | 262KB, 4 threads |
| **One-Copy (A2)** | **340.0 Gbps** | 262KB, 4 threads |
| **Zero-Copy (A3)** | **236.8 Gbps** | 262KB, 4 threads |

### Latency Winners
- **Lowest Latency**: Mode 0 (Two-Copy) - **3.30 μs** @ 16KB, 1 thread
- **Most Predictable**: Mode 1 (One-Copy) - Avg 31.30 μs
- **Highest Latency**: Mode 2 (Zero-Copy) - Avg 141.92 μs (due to completion notification overhead)

### Cache Efficiency
- **Mode 2 (Zero-Copy)**: 454K LLC misses (93% reduction vs traditional methods)
- **Mode 0 (Two-Copy)**: 6.79M LLC misses
- **Mode 1 (One-Copy)**: 6.54M LLC misses

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────┐
│                     Network Namespace                    │
├──────────────────────┬──────────────────────────────────┤
│   ns_srv (10.0.0.1)  │       ns_cli (10.0.0.2)          │
│   ┌──────────────┐   │   ┌──────────────────────────┐   │
│   │   Server     │   │   │   Client (Multi-thread)  │   │
│   │              │◄──┼───┤   Thread 1, 2, ..., N    │   │
│   │ - Mode 0/1/2 │   │   │   Each maintains socket  │   │
│   │ - Perf Stats │   │   │   + Latency tracking     │   │
│   └──────────────┘   │   └──────────────────────────┘   │
└──────────────────────┴──────────────────────────────────┘
```

### Implementation Details

#### Mode 0: Two-Copy (Baseline)
```c
// Pre-allocate flat buffer (Copy 1: fields → flat_buf)
char *flat_buf = malloc(msg_size);
for (i=0; i<NUM_FIELDS; i++)
    memcpy(flat_buf + offset, msg.fields[i], field_size);

// Copy 2: flat_buf → kernel space
send(fd, flat_buf, msg_size, 0);
```

#### Mode 1: One-Copy (sendmsg)
```c
// Single copy: fields → kernel via scatter-gather I/O
struct iovec iov[NUM_FIELDS];
for (i=0; i<NUM_FIELDS; i++) {
    iov[i].iov_base = msg.fields[i];
    iov[i].iov_len = field_size;
}
msgh.msg_iov = iov;
sendmsg(fd, &msgh, 0);  // Kernel gathers directly from user buffers
```

#### Mode 2: Zero-Copy (MSG_ZEROCOPY)
```c
// Enable zero-copy
setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));

// DMA-based transfer (no CPU copying)
sendmsg(fd, &msgh, MSG_ZEROCOPY);
// Note: Requires completion notification handling
```

---

## 📊 Experimental Setup

### Test Parameters
- **Message Sizes**: 16 KB, 64 KB, 256 KB, 1 MB
- **Thread Counts**: 1, 2, 4, 8
- **Duration**: 10 seconds per test
- **Network**: Virtual ethernet pair (veth) in isolated namespaces

### Hardware Environment
- **System**: ThinkCentre M70s Gen 3
- **CPU**: Intel 12th Gen (Hybrid Architecture - P-cores + E-cores)
- **OS**: Linux (Ubuntu 24.04)
- **Kernel**: 6.x with io_uring support

### Metrics Collected
1. **Throughput** (Gbps) - Total bytes transferred / time
2. **Latency** (μs) - Per-message round-trip time
3. **CPU Cycles** - Total cycles consumed (via perf)
4. **L1 Cache Misses** - L1 data cache misses
5. **LLC Misses** - Last Level Cache misses
6. **Context Switches** - Thread scheduling events

---

## 🚀 Quick Start

### Prerequisites
```bash
sudo apt update
sudo apt install build-essential linux-tools-generic linux-tools-$(uname -r)
```

### Setup Network Namespaces
```bash
# Create namespaces
sudo ip netns add ns_srv
sudo ip netns add ns_cli

# Create veth pair
sudo ip link add veth_srv type veth peer name veth_cli

# Assign to namespaces
sudo ip link set veth_srv netns ns_srv
sudo ip link set veth_cli netns ns_cli

# Configure IPs
sudo ip netns exec ns_srv ip addr add 10.0.0.1/24 dev veth_srv
sudo ip netns exec ns_cli ip addr add 10.0.0.2/24 dev veth_cli

# Bring interfaces up
sudo ip netns exec ns_srv ip link set veth_srv up
sudo ip netns exec ns_cli ip link set veth_cli up
sudo ip netns exec ns_srv ip link set lo up
sudo ip netns exec ns_cli ip link set lo up
```

### Build and Run

```bash
# Compile
make clean && make all

# Run automated experiments (Part C)
chmod +x MT25014_Part_C_RunExperiments.sh
sudo ./MT25014_Part_C_RunExperiments.sh

# Generate plots (Part D)
python3 MT25014_Part_D_Plots.py
```

### Manual Test (Single Configuration)
```bash
# Terminal 1: Start server
sudo ip netns exec ns_srv ./server 0 65536 20

# Terminal 2: Run client
sudo ip netns exec ns_cli ./client 10.0.0.1 65536 4 10
# Output: bytes_transferred,avg_latency_us
```

---

## 📈 Results Analysis

### 1. Throughput vs Message Size (4 Threads)

**Observations:**
- **Sweet Spot**: 256KB messages achieve peak throughput (345 Gbps)
- **Small Messages (16KB)**: CPU overhead dominates, ~85-134 Gbps
- **Large Messages (1MB)**: Throughput drops due to:
  - Increased context switches
  - Cache thrashing
  - Network buffer management overhead

**Mode Comparison:**
- Modes 0 & 1 nearly identical for medium/large messages
- Mode 2 (Zero-copy) underperforms by ~30% due to:
  - Completion notification overhead
  - Buffer pinning/unpinning costs
  - Better suited for very large (>10MB) transfers

### 2. Latency vs Thread Count (64KB Messages)

**Key Insights:**
| Threads | Mode 0 | Mode 1 | Mode 2 |
|---------|--------|--------|--------|
| 1       | 6.7 μs | 6.8 μs | 7.5 μs |
| 2       | 7.1 μs | 7.3 μs | 7.7 μs |
| 4       | 7.5 μs | 7.6 μs | 8.5 μs |
| 8       | 43.0 μs| 24.2 μs| 16.5 μs|

**Why does Mode 2 win at 8 threads?**
- Lower context switch overhead (201K vs 295K)
- Reduced CPU contention
- Kernel handles buffer management more efficiently under load

### 3. Cache Efficiency Analysis

**LLC Misses (4 threads, varying message size):**

| Size | Mode 0 | Mode 1 | Mode 2 |
|------|--------|--------|--------|
| 16KB | 45K    | 62K    | 40K    |
| 64KB | 242K   | 125K   | 335K   |
| 256KB| 173K   | 174K   | 234K   |
| 1MB  | 3.86M  | 4.22M  | 820K   |

**Conclusion**: Zero-copy shines with large messages (1MB: 79% fewer misses)

### 4. CPU Cycles per Byte

**Efficiency Ranking (lower is better):**
1. **1MB messages**: ~0.04-0.06 cycles/byte (all modes similar)
2. **256KB messages**: ~0.15 cycles/byte
3. **64KB messages**: ~0.5 cycles/byte
4. **16KB messages**: ~2.6 cycles/byte (high overhead/payload ratio)

**Insight**: Fixed per-message costs (syscall, scheduling) dominate small transfers

---

## 🔍 Detailed Analysis

### Why doesn't Zero-Copy always win?

**Zero-copy overhead for typical network transfers:**
1. **Page Pinning**: Kernel must pin user memory pages (prevent swap)
2. **Completion Queue**: Application must poll for send completion
3. **Small Buffer Penalty**: Fixed costs don't amortize well for <1MB
4. **NIC DMA Setup**: Hardware descriptor preparation overhead

**When zero-copy wins:**
- Message sizes > 10 MB
- High-throughput streaming (e.g., video/file transfers)
- Memory-constrained systems

### Context Switch Analysis

| Mode | Avg Context Switches | Why? |
|------|---------------------|------|
| Mode 0 | 4,320 | Frequent blocking on send() |
| Mode 1 | 6,215 | Similar to Mode 0 |
| Mode 2 | 24,831 | Completion notifications trigger extra scheduling |

**At 8 threads, Mode 2 has 56K switches** - but still wins on latency due to better resource utilization!

### Thread Scalability

**Speedup Factor (1 thread → 8 threads):**
- Mode 0: **1.62x** (poor scaling due to socket lock contention)
- Mode 1: **1.88x** (better scatter-gather efficiency)
- Mode 2: **2.21x** (best scaling - kernel manages buffers independently)

**Why not 8x speedup?**
- Single TCP connection bottleneck
- Shared network interface contention
- Cache coherency overhead

---

## 📁 Project Structure

```
MT25014_Network_IO_Analysis/
├── MT25014_Part_A_Common.h          # Shared definitions
├── MT25014_Part_A_Server.c          # Server implementation (3 modes)
├── MT25014_Part_A_Client.c          # Client implementation (multithreaded)
├── MT25014_Part_C_RunExperiments.sh # Automated test harness
├── MT25014_Part_D_Plots.py          # Visualization script
├── Makefile                          # Build system
├── README.md                         # This file
└── Results/
    ├── MT25014_Part_C_results.csv   # Raw experimental data
    ├── MT25014_Throughput.png       # Throughput analysis
    ├── MT25014_Latency.png          # Latency analysis
    ├── MT25014_CacheMisses.png      # Cache behavior
    └── MT25014_CyclesPerByte.png    # CPU efficiency
```

---

## 🛠️ Implementation Highlights

### Server (MT25014_Part_A_Server.c)

**Thread-per-client model:**
```c
void *handle_client(void *args) {
    // Initialize message buffers (8 fields)
    Message msg;
    for(int i=0; i<NUM_FIELDS; i++)
        msg.fields[i] = malloc(field_size);
    
    // Mode-specific sending logic
    while (duration_not_expired) {
        switch(mode) {
            case 0: send(fd, flat_buf, size, 0); break;
            case 1: sendmsg(fd, &msgh, 0); break;
            case 2: sendmsg(fd, &msgh, MSG_ZEROCOPY); break;
        }
    }
}
```

**Key Features:**
- Heap-allocated message fields (simulates real-world memory patterns)
- Pre-allocated flat buffer for Mode 0 (optimization)
- Zero-copy socket option configuration
- Duration-based testing (no fixed message count)

### Client (MT25014_Part_A_Client.c)

**Multithreaded receiver with latency tracking:**
```c
void *receive_data(void *args) {
    while (running) {
        gettimeofday(&start, NULL);
        recv(fd, buf, msg_size, 0);
        gettimeofday(&end, NULL);
        
        latency = (end - start) in microseconds;
        
        // Thread-safe counters
        pthread_mutex_lock(&mutex);
        total_bytes += received;
        total_latency += latency;
        msg_count++;
        pthread_mutex_unlock(&mutex);
    }
}
```

**Output Format**: `bytes_transferred,avg_latency_us`

---

## 🧪 Experiment Automation (Part C)

### Script Features

1. **Parameterized Testing**: All combinations of modes/sizes/threads
2. **Perf Integration**: Automated performance counter collection
3. **Clean Isolation**: Kills stray processes, resets state
4. **CSV Output**: Machine-readable results
5. **Retry Logic**: Handles transient failures

### Sample CSV Output

```csv
Mode,Size,Threads,Throughput_Gbps,Latency_us,Cycles,L1_Misses,LLC_Misses,ContextSwitches
0,262144,4,345.295,6.33,175785772631,9269430289,172605,530
1,262144,4,339.999,6.42,173886804028,9175977411,174478,1501
2,262144,4,236.78,11.50,144755931832,6156791294,233524,28048
```

---

## 📊 Visualization (Part D)

### Generated Plots

1. **Throughput vs Message Size**: Shows optimal buffer size (256KB)
2. **Latency vs Thread Count**: Demonstrates contention effects
3. **LLC Misses**: Cache efficiency comparison
4. **Cycles per Byte**: CPU efficiency metric

### How to Regenerate

```bash
python3 MT25014_Part_D_Plots.py
# Outputs: MT25014_Throughput.png, MT25014_Latency.png, etc.
```

---

## 🎓 Learning Outcomes

### Key Takeaways

1. **No Silver Bullet**: Each mode has trade-offs
   - Traditional copy: Low latency, high CPU/cache cost
   - Zero-copy: Low CPU, but high fixed overhead

2. **Message Size Matters**: 
   - Small (<64KB): Traditional wins
   - Medium (256KB-1MB): All similar
   - Large (>10MB): Zero-copy wins

3. **Concurrency is Complex**:
   - More threads ≠ proportional speedup
   - Socket/cache contention limits gains
   - Context switches become significant overhead

4. **Measurement Accuracy**:
   - Perf counters essential for understanding
   - Application-level metrics can mislead
   - Always measure under realistic conditions

### Real-World Applications

- **Web Servers**: Use traditional send() for small HTTP responses
- **Video Streaming**: Use zero-copy for large chunks
- **Database Systems**: sendmsg() for scattered result sets
- **Game Servers**: Optimize for latency (traditional methods)

---

## 🐛 Troubleshooting

### Common Issues

**1. "perf: Permission denied"**
```bash
sudo sysctl -w kernel.perf_event_paranoid=-1
# OR run entire script with sudo
```

**2. "Cannot find cpu_core/cycles/"**
- Your CPU doesn't have hybrid architecture
- Use generic event names: `cycles` instead of `cpu_core/cycles/`

**3. "Network unreachable"**
```bash
# Check namespace connectivity
sudo ip netns exec ns_cli ping -c 1 10.0.0.1
# Recreate namespaces if needed (see Setup section)
```

**4. Zero throughput in results**
- Server didn't start in time → Increase `sleep 3` to `sleep 5`
- Firewall blocking → Disable iptables in namespaces

---

## 📚 References

### Linux Network I/O APIs
- `send()`: [man7.org/linux/man-pages/man2/send.2.html](https://man7.org/linux/man-pages/man2/send.2.html)
- `sendmsg()`: [man7.org/linux/man-pages/man2/sendmsg.2.html](https://man7.org/linux/man-pages/man2/sendmsg.2.html)
- `MSG_ZEROCOPY`: [kernel.org/doc/html/latest/networking/msg_zerocopy.html](https://www.kernel.org/doc/html/latest/networking/msg_zerocopy.html)

### Performance Analysis
- `perf` tool: [perf.wiki.kernel.org](https://perf.wiki.kernel.org/)
- Network namespaces: [man7.org/linux/man-pages/man8/ip-netns.8.html](https://man7.org/linux/man-pages/man8/ip-netns.8.html)

### Papers
- "Zero-Copy TCP in Solaris" - Chu et al.
- "The Linux TCP/IP Stack: Networking for Embedded Systems" - Benvenuti

---

## 👤 Author

**Roll No**: MT25014  
**Course**: Network Systems / High-Performance Computing  
**Term**: 2024-25

---

## 📄 License

This project is submitted as part of academic coursework. All code is original implementation following assignment specifications.

---

## 🔗 Quick Links

- [📊 View Results CSV](MT25014_Part_C_results.csv)
- [📈 Throughput Plot](MT25014_Throughput.png)
- [⏱️ Latency Plot](MT25014_Latency.png)
- [💾 Cache Analysis](MT25014_CacheMisses.png)
- [⚡ CPU Efficiency](MT25014_CyclesPerByte.png)

---

**Last Updated**: February 2025
