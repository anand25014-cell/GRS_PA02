#!/bin/bash
set -e

# ================= CONFIG =================
SERVER_IP=127.0.0.1
PORT=9000
DURATION=10
MSG_SIZES=(64 256 1024 4096)          # 4 message sizes ✓
THREADS=(1 2 4 8)                      # 4 thread counts ✓
MODES=(twocopy onecopy zerocopy)
CSV_FILE=results.csv
TMP_CSV=results_tmp.csv
LOG_FILE=experiment_debug.log
# ========================================

# ========== DETECT PERF CAPABILITIES ==========
echo "Detecting available performance counters..."

if ! command -v perf &> /dev/null; then
    echo "ERROR: perf not found. Install with: sudo apt-get install linux-tools-common linux-tools-generic"
    exit 1
fi

# Test hardware counters
set +e
TEST_OUTPUT=$(perf stat -e cycles,L1-dcache-load-misses,LLC-load-misses true 2>&1)
HW_RESULT=$?
set -e

if [ $HW_RESULT -eq 0 ] && echo "$TEST_OUTPUT" | grep -q "[0-9] cycles"; then
    echo "✅ Hardware performance counters available"
    USE_HW_COUNTERS=1
else
    echo "⚠️  Hardware counters unavailable - will use alternative metrics"
    USE_HW_COUNTERS=0
fi

echo "=============================================="
# ==============================================

# CSV HEADER - ONLY REQUIRED METRICS
CSV_HEADER="mode,msg_size,threads,throughput_gbps,latency_us,cpu_cycles,l1_misses,llc_misses,context_switches"

# Initialize CSV and log
rm -f "${TMP_CSV}" "${CSV_FILE}" "${LOG_FILE}"
echo "${CSV_HEADER}" > "${TMP_CSV}"
echo "Experiment started at $(date)" > "${LOG_FILE}"

# Build
make clean
make

for mode in "${MODES[@]}"; do
  for msg in "${MSG_SIZES[@]}"; do
    echo ""
    echo "Starting server: mode=${mode}, msg_size=${msg}"
    ./server "${mode}" "${msg}" &
    SERVER_PID=$!
    sleep 1

    for th in "${THREADS[@]}"; do
      echo "  Running client: threads=${th}"
      
      # Run with perf
      set +e
      if [ $USE_HW_COUNTERS -eq 1 ]; then
          # Hardware counters available
          CLIENT_OUTPUT=$(perf stat -e "cycles,L1-dcache-load-misses,LLC-load-misses,context-switches" \
            ./client "${SERVER_IP}" "${PORT}" "${th}" "${DURATION}" "${msg}" 2>&1)
      else
          # Fallback: use software counters
          CLIENT_OUTPUT=$(perf stat -e "task-clock,page-faults,context-switches" \
            ./client "${SERVER_IP}" "${PORT}" "${th}" "${DURATION}" "${msg}" 2>&1)
      fi
      PERF_EXIT=$?
      set -e
      
      # Log raw output
      echo "=== Test: ${mode} ${msg} ${th} ===" >> "${LOG_FILE}"
      echo "$CLIENT_OUTPUT" >> "${LOG_FILE}"
      echo "" >> "${LOG_FILE}"

      # Extract application metrics
      THROUGHPUT_MBPS=$(echo "$CLIENT_OUTPUT" | grep "Throughput" | grep -oE '[0-9]+(\.[0-9]+)?' | head -1)
      LATENCY=$(echo "$CLIENT_OUTPUT" | grep "Avg latency" | grep -oE '[0-9]+(\.[0-9]+)?' | head -1)
      
      # Convert Mbps to Gbps (divide by 1000)
      if [ -n "$THROUGHPUT_MBPS" ] && [ "$THROUGHPUT_MBPS" != "0" ]; then
          THROUGHPUT_GBPS=$(echo "scale=3; $THROUGHPUT_MBPS / 1000" | bc)
      else
          THROUGHPUT_GBPS=0
      fi

      if [ $USE_HW_COUNTERS -eq 1 ]; then
          # Extract hardware counter metrics
          CPU_CYCLES=$(echo "$CLIENT_OUTPUT" | grep -i "cycles" | grep -v "%" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
          L1_MISSES=$(echo "$CLIENT_OUTPUT" | grep -i "L1-dcache-load-misses" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
          LLC_MISSES=$(echo "$CLIENT_OUTPUT" | grep -i "LLC-load-misses" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
          CSW=$(echo "$CLIENT_OUTPUT" | grep -i "context-switches" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
      else
          # Use estimates/alternatives when hardware counters unavailable
          TASK_CLOCK=$(echo "$CLIENT_OUTPUT" | grep -i "task-clock" | grep -oE '[0-9,]+(\.[0-9]+)?' | head -1 | tr -d ',')
          PAGE_FAULTS=$(echo "$CLIENT_OUTPUT" | grep -i "page-faults" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
          CSW=$(echo "$CLIENT_OUTPUT" | grep -i "context-switches" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
          
          # Estimate CPU cycles from task-clock (rough approximation at 2.4 GHz)
          if [ -n "$TASK_CLOCK" ] && [ "$TASK_CLOCK" != "0" ]; then
              CPU_CYCLES=$(echo "scale=0; $TASK_CLOCK * 2400000" | bc)
          else
              CPU_CYCLES=0
          fi
          
          # Mark cache misses as unavailable (0)
          L1_MISSES=0
          LLC_MISSES=0
      fi
      
      # Default values
      THROUGHPUT_GBPS=${THROUGHPUT_GBPS:-0}
      LATENCY=${LATENCY:-0}
      CPU_CYCLES=${CPU_CYCLES:-0}
      L1_MISSES=${L1_MISSES:-0}
      LLC_MISSES=${LLC_MISSES:-0}
      CSW=${CSW:-0}
      
      # Warning for missing hardware counters
      if [[ $USE_HW_COUNTERS -eq 0 ]] && [[ "$L1_MISSES" == "0" ]] && [[ "$LLC_MISSES" == "0" ]]; then
          echo "    ⚠️  Cache miss data unavailable (VM limitation)"
      fi
      
      # Write to CSV - ONLY REQUIRED METRICS
      echo "${mode},${msg},${th},${THROUGHPUT_GBPS},${LATENCY},${CPU_CYCLES},${L1_MISSES},${LLC_MISSES},${CSW}" >> "${TMP_CSV}"
      
      echo "    -> Throughput: ${THROUGHPUT_GBPS} Gbps, Latency: ${LATENCY} µs"
    done

    # Stop server
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
    sleep 1
  done
done

# Finalize
mv "${TMP_CSV}" "${CSV_FILE}"

echo ""
echo "======================================"
echo "Experiments completed successfully."
echo "Final CSV: ${CSV_FILE}"
echo "Debug log: ${LOG_FILE}"
echo ""
echo "CSV Format:"
echo "  - Throughput: Gbps (converted from Mbps)"
echo "  - Latency: µs"
echo "  - CPU cycles: from perf stat"
echo "  - L1 misses: from perf stat"
echo "  - LLC misses: from perf stat"
echo "  - Context switches: from perf stat"
if [ $USE_HW_COUNTERS -eq 0 ]; then
    echo ""
    echo "NOTE: Hardware counters unavailable."
    echo "      Cache misses will be 0."
    echo "      CPU cycles estimated from task-clock."
fi
echo "======================================"