#!/bin/bash
set -e

# ================= CONFIG =================
SERVER_IP=127.0.0.1
PORT=9000
DURATION=10

MSG_SIZES=(64 256 1024 4096)
THREADS=(1 2 4 8)
MODES=(twocopy onecopy zerocopy)

CSV_FILE=results.csv
TMP_CSV=results_tmp.csv   # TEMP FILE IN PROJECT DIR
# ========================================

# ---------- CSV INITIALIZATION ----------
rm -f ${TMP_CSV} ${CSV_FILE}

echo "mode,msg_size,threads,throughput_mbps,latency_us,context_switches" > ${TMP_CSV}
# ---------------------------------------

# Build
make clean
make

for mode in "${MODES[@]}"; do
  for msg in "${MSG_SIZES[@]}"; do

    echo "Starting server: mode=${mode}, msg_size=${msg}"
    ./server ${mode} ${msg} &
    SERVER_PID=$!
    sleep 1

    for th in "${THREADS[@]}"; do
      echo "  Running client: threads=${th}"

      CLIENT_OUTPUT=$(perf stat -e context-switches \
        ./client ${SERVER_IP} ${PORT} ${th} ${DURATION} 2>&1)

      THROUGHPUT=$(echo "$CLIENT_OUTPUT" | grep "Throughput" | grep -oE '[0-9]+\.[0-9]+')
      LATENCY=$(echo "$CLIENT_OUTPUT" | grep "Avg latency" | grep -oE '[0-9]+\.[0-9]+')
      CSW=$(echo "$CLIENT_OUTPUT" | grep "context-switches" | awk '{print $1}' | tr -d ',')

      THROUGHPUT=${THROUGHPUT:-0}
      LATENCY=${LATENCY:-0}
      CSW=${CSW:-0}

      echo "${mode},${msg},${th},${THROUGHPUT},${LATENCY},${CSW}" >> ${TMP_CSV}
    done

    kill ${SERVER_PID}
    wait ${SERVER_PID} 2>/dev/null || true
    sleep 1
  done
done

# ---------- FINAL ATOMIC RENAME ----------
mv ${TMP_CSV} ${CSV_FILE}
# ---------------------------------------

echo "======================================"
echo "Experiments completed successfully."
echo "Final CSV written to ${CSV_FILE}"
echo "======================================"
