#!/usr/bin/env python3

import sys
import os
import subprocess
import re

def run_abc(input_lib, input_genlib, input_design):
    # 防呆：確保暫存資料夾存在，避免 ABC 寫入時報錯
    os.makedirs("temp_blifs", exist_ok=True)
    
    genlib_basename = os.path.basename(input_genlib)
    design_basename = os.path.basename(input_design)
    temp_blif = f"temp_blifs/{design_basename}_temp.blif"
    
    # 組合 ABC 指令 (沿用原作者的兩階段 Mapping 邏輯)
    abc_cmd = f"read {input_genlib}; read {input_design}; map; write {temp_blif}; read {input_lib}; read -m {temp_blif}; ps; topo; upsize; dnsize; stime;"
    
    try:
        # text=True 可以直接回傳 string，不需要再 str(res)
        res = subprocess.check_output(['abc', '-c', abc_cmd], text=True)
    except subprocess.CalledProcessError as e:
        print("ABC 執行失敗:", e)
        return float("NaN"), float("NaN")
        
    # 解析 Area 與 Delay
    match_d = re.search(r"Delay\s*=\s*([\d.]+)\s*ps", res)
    match_a = re.search(r"Area\s*=\s*([\d.]+)", res)
    
    delay = float(match_d.group(1)) if match_d else float("NaN")
    area = float(match_a.group(1)) if match_a else float("NaN")
    
    print(f"[{design_basename}][{genlib_basename}] Delay: {delay} ps | Area: {area}")
    return delay, area

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"用法: {sys.argv[0]} <input.lib> <input.genlib> <input.design>")
        sys.exit(1)
        
    run_abc(sys.argv[1], sys.argv[2], sys.argv[3])