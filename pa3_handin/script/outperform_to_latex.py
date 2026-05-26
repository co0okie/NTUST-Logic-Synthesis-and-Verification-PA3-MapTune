import sys
import re
from collections import defaultdict

def generate_latex_table():
    data = []
    current_entry = {}
    
    # 用來計算某個欄位出現的次數，以區分是 MapTune 還是你的方法
    counts = {'delay': 0, 'area': 0, 'reward': 0, 'time': 0}
    
    # 從 stdin 逐行讀取
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        # 匹配檔名格式: benchmark_library_budget.log
        # 例如: b20_1_nan45_16.log
        m_file = re.match(r'^([a-zA-Z0-9_]+)_([a-zA-Z0-9_]+)_(\d+)\.log$', line)
        if m_file:
            if current_entry:
                data.append(current_entry)
            current_entry = {
                'benchmark': m_file.group(1).replace('_', '\\_'), # 替換底線以防 LaTeX 報錯
                'library': m_file.group(2).replace('_', '\\_'),
                's_maptune': int(m_file.group(3))
            }
            counts = {k: 0 for k in counts} # 重置計數器
            continue
            
        # 解析數據行
        lower_line = line.lower()
        if lower_line.startswith("best delay:"):
            val = float(line.split(":")[1])
            if counts['delay'] == 0: current_entry['mt_delay'] = val
            else: current_entry['my_delay'] = val
            counts['delay'] += 1
            
        elif lower_line.startswith("best area:"):
            val = float(line.split(":")[1])
            if counts['area'] == 0: current_entry['mt_area'] = val
            else: current_entry['my_area'] = val
            counts['area'] += 1
            
        elif lower_line.startswith("best reward:"):
            val = float(line.split(":")[1])
            if counts['reward'] == 0: current_entry['mt_reward'] = val
            else: current_entry['my_reward'] = val
            counts['reward'] += 1
            
        elif lower_line.startswith("total time:"):
            val = float(line.split(":")[1])
            if counts['time'] == 0: 
                current_entry['mt_time'] = val
            else: 
                current_entry['my_time'] = val - current_entry['mt_time']
            counts['time'] += 1
            
        elif lower_line.startswith("best cells count:"):
            current_entry['s_new'] = int(line.split(":")[1])

    # 把最後一筆資料加進去
    if current_entry:
        data.append(current_entry)

    # 根據 benchmark 和 library 分組，以便推算 30%, 50%, 70%
    grouped_data = defaultdict(list)
    for row in data:
        grouped_data[(row['benchmark'], row['library'])].append(row)

    # 開始印出 LaTeX 程式碼
    print(r"\begin{table*}[htbp]")
    print(r"\centering")
    print(r"\caption{Performance Comparison between MapTune and Proposed Local Search}")
    print(r"\resizebox{\textwidth}{!}{")
    print(r"\begin{tabular}{llc|rrrrr|rrrrr}")
    print(r"\toprule")
    print(r"\multirow{2}{*}{\textbf{Benchmark}} & \multirow{2}{*}{\textbf{Library}} & \multirow{2}{*}{\textbf{Budget}} & \multicolumn{5}{c|}{\textbf{MapTune}} & \multicolumn{5}{c}{\textbf{Proposed Method}} \\")
    print(r"\cmidrule(lr){4-8} \cmidrule(l){9-13}")
    print(r"& & & Delay (ps) & Area ($\mu m^2$) & Reward & $|S_{MapTune}|$ & Time(s) & Delay (ps) & Area ($\mu m^2$) & Reward & $|S_{new}|$ & Time(s) \\")

    budget_labels = ["30\\%", "50\\%", "70\\%"]
    
    for (bench, lib), rows in grouped_data.items():
        # 依照 s_maptune 由小到大排序，對應 30%, 50%, 70%
        rows.sort(key=lambda x: x['s_maptune'])
        
        # 在每個 library 區塊之間加上一條虛線或淡線區隔
        print(r"\midrule")
        
        for i, row in enumerate(rows):
            # 處理跨行顯示的 benchmark 和 library (只在第一行顯示名稱)
            b_str = bench if i == 0 else ""
            l_str = lib if i == 0 else ""
            budg_str = budget_labels[i] if i < len(budget_labels) else ""
            
            print(f"{b_str:12} & {l_str:12} & {budg_str} & "
                  f"{row['mt_delay']:.2f} & {row['mt_area']:.2f} & {row['mt_reward']:.4f} & {row['s_maptune']:<4} & {row['mt_time']:.2f} & "
                  f"{row['my_delay']:.2f} & {row['my_area']:.2f} & {row['my_reward']:.4f} & {row.get('s_new', '-'):<4} & {row['my_time']:.2f} \\\\")

    # 收尾
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"}")
    print(r"\label{tab:optimization_results}")
    print(r"\end{table*}")

if __name__ == "__main__":
    generate_latex_table()