# plot_pa02_hardcoded.py
# Hardcoded PA02 plots (matplotlib-only)
# Run: python3 plot_pa02_hardcoded.py

import matplotlib.pyplot as plt
import platform

# =========================
# System info
# =========================
sys_info = f"{platform.system()} {platform.release()} | {platform.machine()}"

# =========================
# Mode mapping
# =========================
mode_map = {
    0: "Two-Copy",
    1: "One-Copy",
    2: "Zero-Copy"
}

# =========================
# Hardcoded data (CSV)
# =========================

Mode = [
0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0,
1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1,
2,2,2,2, 2,2,2,2, 2,2,2,2, 2,2,2,2
]

Size = [
16384,16384,16384,16384,
65536,65536,65536,65536,
262144,262144,262144,262144,
1048576,1048576,1048576,1048576,

16384,16384,16384,16384,
65536,65536,65536,65536,
262144,262144,262144,262144,
1048576,1048576,1048576,1048576,

16384,16384,16384,16384,
65536,65536,65536,65536,
262144,262144,262144,262144,
1048576,1048576,1048576,1048576
]

Threads = [
1,2,4,8, 1,2,4,8, 1,2,4,8, 1,2,4,8,
1,2,4,8, 1,2,4,8, 1,2,4,8, 1,2,4,8,
1,2,4,8, 1,2,4,8, 1,2,4,8, 1,2,4,8
]

Throughput_Gbps = [
71.056542,136.353703,246.631576,147.563452,
66.336692,127.463325,242.898226,365.262326,
86.444500,166.791426,312.953903,107.324584,
71.239308,135.733442,252.541245,66.488102,

71.308699,136.239618,257.525625,121.298957,
75.364722,144.491675,275.127048,241.337415,
101.212225,192.936725,355.466634,85.368660,
102.599071,192.729105,166.016001,47.192625,

34.818352,67.463798,130.059914,202.752117,
61.077258,117.743198,220.289605,110.010435,
77.578685,151.775702,283.316204,62.559773,
66.464828,54.791811,50.508653,37.633483
]

Latency_us = [
1.81,1.89,2.09,7.03,
7.87,8.19,8.60,11.41,
6.67,6.90,7.76,84.57,
7.37,7.75,8.39,110.72,

1.80,1.89,2.00,8.57,
6.92,7.22,7.58,17.23,
5.29,5.73,6.06,136.54,
5.14,5.61,17.51,704.47,

2.65,2.74,2.85,3.70,
5.72,5.94,6.37,31.32,
8.45,8.50,9.15,228.37,
11.42,159.12,652.37,1315.06
]

Cycles = [
17664684144,33478807625,67808531645,88985832070,
17807890056,32108373028,69174773667,132342224502,
17732271114,33747332889,68393165178,99840766558,
17513677339,34096154393,68928309791,129623814789,

17680472927,33269324295,68114919333,97925066190,
17714500734,33926231862,68410540266,104969552708,
17702936672,34033335325,67241696238,92143525341,
17688151755,34894015099,53015585956,111490068352,

17018244591,34099485163,68139683507,134492017483,
17628067066,33924292584,66574374355,32233749514,
16693355992,34606220364,66095599774,10632024467,
12357367887,2705519374,2860262624,7894083506
]

L1Misses = [
1345183760,2582003459,4566879241,3030479333,
1618274482,3119506960,5932261644,10425582789,
1955536152,3783484564,7084169334,2613885504,
986310004,1871768651,3404175641,1392526421,

878384036,1672261662,3192713075,1826326322,
1063205247,2038663940,3887512480,3954651303,
1348163670,2570731204,4778618748,1088670055,
1075848055,1998396106,1847868112,576337567,

504915167,973464913,1872286815,3330695033,
888859245,1711854236,3201406348,1032904772,
1021192311,1992215023,3720636739,85420666,
582687915,60159409,17657557,21859307
]

LLCMisses = [
9209755,319534623,112768306,182696513,
19421637,434523932,122019856,31561712,
51019232,385784762,45152726,224452895,
201083144,158475804,107244558,399584479,

20742838,143076661,63632037,269934218,
58027356,26485575,33982104,182208563,
26743977,63981170,117614164,259570635,
92182433,88550736,215752889,224534976,

46967233,35209197,33589951,7497394,
19845929,45806534,74722642,34362031,
42109526,126060614,105014715,17943020,
36587665,9794737,6935290,12519877
]

ContextSwitches = [
33,69,466,16978,
25,49,263,3809,
297,298,299,12890,
22,106,118,4694,

89,653,405,11162,
145,458,167,12694,
759,812,1107,14948,
34,266,7512,6810,

1041,718,469,683,
678,629,1232,63850,
281,683,1627,67976,
6009,30259,30290,22639
]
n = len(Mode)

# =========================
# Helper: index filter
# =========================
def indices_where(cond):
    return [i for i in range(n) if cond(i)]

# =========================
# Common plotting helpers
# =========================
color_map = {
    0: "tab:blue",    # Two-Copy
    1: "tab:orange",  # One-Copy
    2: "tab:green"    # Zero-Copy
}

linestyle_map = {
    1: "-",
    2: "--",
    4: "-.",
    8: ":"
}

marker_map = {
    16384: "o",
    65536: "s",
    262144: "^",
    1048576: "D"
}

# =========================
# PLOT 1: Throughput vs Message Size
# (All Modes × All Threads, clubbed)
# =========================
plt.figure(figsize=(10,8))

for m in sorted(set(Mode)):
    for t in sorted(set(Threads)):
        idx = indices_where(lambda i: Mode[i] == m and Threads[i] == t)
        x = [Size[i] for i in idx]
        y = [Throughput_Gbps[i] for i in idx]
        x, y = zip(*sorted(zip(x, y)))

        plt.plot(
            x, y,
            color=color_map[m],
            linestyle=linestyle_map[t],
            marker='o',
            linewidth=2,
            label=f"{mode_map[m]} | Threads={t}"
        )

plt.xscale('log', base=2)
plt.xlabel("Message Size (bytes)", fontsize=12)
plt.ylabel("Throughput (Gbps)", fontsize=12)
plt.title("Throughput vs Message Size (All Modes & Threads)\n" + sys_info, fontsize=13)
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

plt.legend(fontsize=9, ncol=3, loc='best')

plt.tight_layout()
plt.savefig("throughput_vs_msgsize_all.png", dpi=300)
plt.close()


# =========================
# PLOT 2: Latency vs Threads
# (All Modes × All Message Sizes, clubbed)
# =========================
plt.figure(figsize=(10,8))

for m in sorted(set(Mode)):
    for sz in sorted(set(Size)):
        idx = indices_where(lambda i: Mode[i] == m and Size[i] == sz)
        x = [Threads[i] for i in idx]
        y = [Latency_us[i] for i in idx]
        x, y = zip(*sorted(zip(x, y)))

        plt.plot(
            x, y,
            color=color_map[m],
            marker=marker_map[sz],
            linewidth=2,
            label=f"{mode_map[m]} | Size={sz}"
        )

plt.xlabel("Thread Count", fontsize=12)
plt.ylabel("Latency (µs)", fontsize=12)
plt.title("Latency vs Thread Count (All Modes & Sizes)\n" + sys_info, fontsize=13)
plt.grid(True, alpha=0.7)

plt.legend(fontsize=9, ncol=3, loc='best')

plt.tight_layout()
plt.savefig("latency_vs_threads_all.png", dpi=300)
plt.close()


# =========================
# PLOT 3: LLC Misses vs Message Size
# (All Modes × All Threads, clubbed)
# =========================
plt.figure(figsize=(10,8))

for m in sorted(set(Mode)):
    for t in sorted(set(Threads)):
        idx = indices_where(lambda i: Mode[i] == m and Threads[i] == t)
        x = [Size[i] for i in idx]
        y = [LLCMisses[i] for i in idx]
        x, y = zip(*sorted(zip(x, y)))

        plt.plot(
            x, y,
            color=color_map[m],
            linestyle=linestyle_map[t],
            marker='o',
            linewidth=2,
            label=f"{mode_map[m]} | Threads={t}"
        )

plt.xscale('log', base=2)
plt.xlabel("Message Size (bytes)", fontsize=12)
plt.ylabel("LLC Cache Misses", fontsize=12)
plt.title("LLC Misses vs Message Size (All Modes & Threads)\n" + sys_info, fontsize=13)
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

plt.legend(fontsize=9, ncol=3, loc='best')

plt.tight_layout()
plt.savefig("llc_misses_vs_msgsize_all.png", dpi=300)
plt.close()


# =========================
# PLOT 4: Cycles per Byte (Relative to Two-Copy)
# (All Modes × All Threads)
# =========================
plt.figure(figsize=(10,8))

for t in sorted(set(Threads)):
    # Get baseline (Two-Copy, Mode=0) for this thread count
    base_idx = indices_where(lambda i: Mode[i] == 0 and Threads[i] == t)
    base_sizes = [Size[i] for i in base_idx]
    base_cycles_per_byte = {Size[i]: Cycles[i] / Size[i] for i in base_idx}
    
    for m in sorted(set(Mode)):
        idx = indices_where(lambda i: Mode[i] == m and Threads[i] == t)
        x = [Size[i] for i in idx]
        y_raw = [Cycles[i] / Size[i] for i in idx]
        
        # Normalize relative to Two-Copy baseline
        y = [y_raw[j] / base_cycles_per_byte[x[j]] for j in range(len(y_raw))]
        x, y = zip(*sorted(zip(x, y)))

        plt.plot(
            x, y,
            color=color_map[m],
            linestyle=linestyle_map[t],
            marker='o',
            linewidth=2,
            label=f"{mode_map[m]} | Threads={t}"
        )

plt.xscale('log', base=2)
plt.xlabel("Message Size (bytes)", fontsize=12)
plt.ylabel("Cycles per Byte (Relative to Two-Copy)", fontsize=12)
plt.title("CPU Cycles per Byte (Relative, All Modes & Threads)\n" + sys_info, fontsize=13)
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

plt.legend(fontsize=9, ncol=3, loc='best')

plt.tight_layout()
plt.savefig("cycles_per_byte_relative_all.png", dpi=300)
plt.close()


print("Done. Generated plots:")
print(" - throughput_vs_msgsize_all.png")
print(" - latency_vs_threads_all.png")
print(" - llc_misses_vs_msgsize_all.png")
print(" - cycles_per_byte_relative_all.png")
