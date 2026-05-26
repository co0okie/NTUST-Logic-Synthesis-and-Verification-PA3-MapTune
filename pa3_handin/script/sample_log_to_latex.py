#!/usr/bin/env python3

import re
import sys
import numpy as np
from scipy.spatial import ConvexHull

def generate_latex(sample_log):
    # 定義 Baseline 數據
    baselines = {
        's13207': (645.03, 1949.99),
        'c2670': (155.37, 461.66),
        'b20_1': (656.76, 5034.18)
    }

    # 儲存解析後的數據: data[benchmark][group_id] = [(delay, area), ...]
    data = {b: {1: [], 2: [], 3: []} for b in baselines.keys()}

    # 解析 sample.log
    try:
        with open(sample_log, 'r') as f:
            for line in f:
                # 匹配格式: [s13207.bench][7nm_75_1.genlib] Delay: 228.16 ps | Area: 2038.87
                match = re.search(r'\[(.*?)\.bench\]\[7nm_(\d+)_\d+\.genlib\] Delay:\s*([0-9.]+)\s*ps\s*\|\s*Area:\s*([0-9.]+)', line)
                if match:
                    bench = match.group(1)
                    sample_size = int(match.group(2))
                    delay = float(match.group(3))
                    area = float(match.group(4))

                    # 決定分組
                    if 75 <= sample_size <= 100:
                        group = 1
                    elif 101 <= sample_size <= 125:
                        group = 2
                    elif 126 <= sample_size <= 150:
                        group = 3
                    else:
                        continue

                    if bench in data:
                        data[bench][group].append((delay, area))
    except FileNotFoundError:
        print("找不到 sample.log")
        sys.exit(1)

    # LaTeX 樣式設定
    colors = {1: 'blue', 2: 'orange', 3: 'green!70!black'}
    labels = {1: '75-100 cells', 2: '101-125 cells', 3: '126-150 cells'}

    print("% 請在 preamble 加入: \\usepackage{pgfplots}")
    print("% \\pgfplotsset{compat=1.18}")
    print("\\begin{figure}[H]")
    print("\\centering")

    # 為每個 benchmark 生成子圖
    for bench in baselines.keys():
        bench_title = bench.replace('_', '\\_')
        print(f"\\begin{{minipage}}{{0.32\\textwidth}}")
        print(f"\\begin{{tikzpicture}}[scale=0.65]")
        print(f"\\begin{{axis}}[")
        print(f"    title={{{bench_title}}},")
        print(f"    xlabel={{Delay (ps)}},")
        print(f"    ylabel={{Area ($\\mu m^2$)}},")
        print(f"    legend pos=north east,")
        print(f"    legend style={{nodes={{scale=0.6, transform shape}}}},")
        print(f"    grid=both,")
        print(f"    grid style={{dashed, opacity=0.3}}")
        print(f"]")

        # 1. 畫 Convex Hull (設為 forget plot，不加入 legend)
        for group in [1, 2, 3]:
            pts = np.array(data[bench][group])
            if len(pts) >= 3:
                hull = ConvexHull(pts)
                hull_pts = pts[hull.vertices]
                # 閉合多邊形
                hull_pts = np.vstack((hull_pts, hull_pts[0]))
                
                coords = " ".join([f"({x:.2f}, {y:.2f})" for x, y in hull_pts])
                print(f"  \\addplot [color={colors[group]}, fill={colors[group]}, fill opacity=0.1, forget plot] coordinates {{ {coords} }};")

        # 2. 畫散點
        for group in [1, 2, 3]:
            pts = data[bench][group]
            if pts:
                coords = " ".join([f"({x:.2f}, {y:.2f})" for x, y in pts])
                print(f"  \\addplot [only marks, mark=*, mark size=1pt, color={colors[group]}, opacity=0.6] coordinates {{ {coords} }};")
                print(f"  \\addlegendentry{{{labels[group]}}}")

        # 3. 畫 Baseline (最後畫，確保蓋在最上層)
        bx, by = baselines[bench]
        print(f"  \\addplot [only marks, mark=star, mark size=3pt, color=red] coordinates {{ ({bx:.2f}, {by:.2f}) }};")
        print(f"  \\addlegendentry{{Baseline}}")

        print(f"\\end{{axis}}")
        print(f"\\end{{tikzpicture}}")
        print(f"\\end{{minipage}}")
        if bench != 'b20_1':
            print("\\hfill")

    print("\\caption{Area-Delay scatter plot for randomly sample of ASAP7 (7nm.lib)}")
    print("\\label{fig:random_sample}")
    print("\\end{figure}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} sample.log")
        sys.exit(1)
    generate_latex(sys.argv[1])