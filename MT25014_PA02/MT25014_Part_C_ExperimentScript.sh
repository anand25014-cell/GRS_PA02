
#!/usr/bin/env bash


set -e  # Exit on any error

trap cleanup EXIT


echo "========================================="
echo "  Network I/O Performance Experiments"
echo "========================================="

# Step 1: Compile
echo ""
echo "=== Step 1: Compiling ==="
make clean
make all

if [ ! -f "./server" ] || [ ! -f "./client" ]; then
    echo "ERROR: Compilation failed!"
    exit 1
fi
echo "✓ Compilation successful"

# Configuration
MODES="0 1 2"  # 0=two-copy, 1=one-copy, 2=zero-copy
SIZES="16384 65536 262144 1048576"  # 16KB, 64KB, 256KB, 1MB
THREADS="1 2 4 8"
DURATION=5
ROLL_NUM="MT25014"  # REPLACE WITH YOUR ROLL NUMBER
OUT="${ROLL_NUM}_Part_C_results.csv"

# Step 2: Cleanup
echo ""
echo "=== Step 2: Cleanup ==="
sudo killall -9 server client 2>/dev/null || true
rm -f perf_*.txt bytes_*.tmp
echo "✓ Cleanup complete"

# Step 3: Initialize CSV
echo ""
echo "=== Step 3: Running Experiments ==="
echo "Mode,Size,Threads,Throughput_Gbps,Latency_us,Cycles,L1Misses,LLCMisses,ContextSwitches" > $OUT

# Step 4: Run experiments
CURRENT=0

for mode in $MODES; do
    for size in $SIZES; do
        for thread in $THREADS; do
            CURRENT=$((CURRENT + 1))
            echo ""
            echo "[$CURRENT/48] Mode:$mode | Size:$size | Threads:$thread"
            
            # Generate unique filenames
            PERF_FILE="perf_mode${mode}_size${size}_th${thread}.txt"
            BYTES_FILE="bytes_mode${mode}_size${size}_th${thread}.tmp"

            # Start SERVER with perf profiling
            # FIXED: Using correct LLC event names for your system
            perf stat -x, \
                -e cycles,L1-dcache-load-misses,longest_lat_cache.miss,context-switches \
                -o $PERF_FILE \
                ./server $mode $size $((DURATION + 2)) 2>/dev/null &
            SRV_PID=$!
            
            # Wait for server to be ready
            sleep 2
            
            # Run CLIENT (measures throughput and latency)
            timeout $((DURATION + 5)) ./client 127.0.0.1 $size $thread $DURATION > $BYTES_FILE 2>/dev/null || true
            
            # Give server time to finish
            sleep 1
            
            # Gracefully stop server
            sudo kill -INT $SRV_PID 2>/dev/null || true
            wait $SRV_PID 2>/dev/null || true
            
            # Parse client output (format: bytes,latency_us)
            if [ -f "$BYTES_FILE" ]; then
                CLIENT_OUT=$(cat $BYTES_FILE)
                RAW_BYTES=$(echo $CLIENT_OUT | cut -d',' -f1)
                LATENCY=$(echo $CLIENT_OUT | cut -d',' -f2)
            else
                RAW_BYTES=0
                LATENCY=0
            fi
            
            # Validate and set defaults
            RAW_BYTES=${RAW_BYTES:-0}
            LATENCY=${LATENCY:-0}
            
            # Calculate throughput in Gbps
            if command -v bc &> /dev/null; then
                THROUGHPUT=$(echo "scale=6; ($RAW_BYTES * 8) / ($DURATION * 1000000000)" | bc)
            else
                THROUGHPUT=$(awk "BEGIN {printf \"%.6f\", ($RAW_BYTES * 8) / ($DURATION * 1000000000)}")
            fi
            
            # Parse perf metrics from SERVER
            # FIXED: Using correct event name for LLC
            if [ -f "$PERF_FILE" ]; then
                CYC=$(grep "cycles" $PERF_FILE | awk -F, '/^[0-9]/ {print $1}' | head -1)
                L1M=$(grep "L1-dcache-load-misses" $PERF_FILE | awk -F, '/^[0-9]/ {print $1}' | head -1)
                LLC=$(grep "longest_lat_cache.miss" $PERF_FILE | awk -F, '/^[0-9]/ {print $1}' | head -1)
                CS=$(grep "context-switches" $PERF_FILE | awk -F, '/^[0-9]/ {print $1}' | head -1)
            else
                CYC=0
                L1M=0
                LLC=0
                CS=0
            fi
            
            # Set defaults if empty
            CYC=${CYC:-0}
            L1M=${L1M:-0}
            LLC=${LLC:-0}
            CS=${CS:-0}
            
            # Append to CSV
            echo "$mode,$size,$thread,$THROUGHPUT,$LATENCY,$CYC,$L1M,$LLC,$CS" >> $OUT
            
            # Display summary
            echo "  ✓ Throughput: $THROUGHPUT Gbps"
            echo "  ✓ Latency: $LATENCY μs"
            echo "  ✓ Cycles: $CYC | LLC Misses: $LLC"
            
            # Cleanup temp files for this run
            sleep 1
        done
    done
done

# Step 6: Run Python Plotting Script
echo ""
echo "=== Running Plotting Script ==="

PY_SCRIPT="MT25014_Part_D_PlottingScript.py"

if [ -f "$PY_SCRIPT" ]; then
    echo "Found $PY_SCRIPT"
    
    # Run plotting script
    python3 $PY_SCRIPT
    
    echo "✓ Plotting completed"
else
    echo "ERROR: $PY_SCRIPT not found!"
fi

# Step 5: Summary
echo ""
echo "========================================="
echo "  Experiments Complete!"
echo "========================================="
echo "Results saved to: $OUT"
echo "Perf files saved as: perf_*.txt"
echo ""
echo "Next steps:"
echo "  1. Check $OUT for all measurements"
echo "  2. Create plotting scripts with hardcoded values"
echo "  3. Generate plots and analysis"
echo ""
echo ""
echo "=== Final Cleanup ==="
rm -f perf_*.txt bytes_*.tmp 2>/dev/null
echo "✓ Temporary perf and tmp files removed"
