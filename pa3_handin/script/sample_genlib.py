#!/usr/bin/env python3

import sys
import random

def sample_genlib(input_genlib, output_genlib, total_target_count):
    f_keep = []
    f_lines = []
    
    # 將所有必須保留的 BUF/INV 開頭特徵寫成一個 tuple
    # tuple 可以直接傳給 startswith()，這是比 any() 更精簡且高效的寫法
    keep_identifiers = (
        "GATE BUF", "GATE INV",
        "GATE sky130_fd_sc_hd__buf", "GATE sky130_fd_sc_hd__inv",
        "GATE gf180mcu_fd_sc_mcu7t5v0__buf", "GATE gf180mcu_fd_sc_mcu7t5v0__inv"
    )
    
    # 讀取一次檔案，同時分流
    with open(input_genlib, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("GATE"):
                if line.startswith(keep_identifiers):
                    f_keep.append(line)
                else:
                    f_lines.append(line)

    num_keep = len(f_keep)
    # 計算還差幾個才達到目標總數
    num_random_needed = total_target_count - num_keep
    
    if num_random_needed < 0:
        print(f"警告：強制保留的細胞數量 ({num_keep}) 已大於或等於目標總數 ({total_target_count})")
        num_random_needed = 0
    elif num_random_needed > len(f_lines):
        print("警告：目標抽樣數大於可用的總細胞數！")
        num_random_needed = len(f_lines)

    # 進行隨機抽樣 (不重複抽樣)
    sampled_lines = random.sample(f_lines, num_random_needed)
    
    # 合併結果並寫出
    final_lines = f_keep + sampled_lines
    with open(output_genlib, 'w') as out_gen:
        for line in final_lines:
            out_gen.write(line + '\n')
            
    print(f"產生完畢: {output_genlib} (總數量: {len(final_lines)} = 保留 {num_keep} + 隨機 {num_random_needed})")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"{sys.argv[0]} <input.genlib> <output.genlib> <目標總數>")
        sys.exit(1)
        
    sample_genlib(sys.argv[1], sys.argv[2], int(sys.argv[3]))