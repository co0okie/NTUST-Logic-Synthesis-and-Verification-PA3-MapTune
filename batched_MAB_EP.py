import random
import sys
import os 
import numpy as np
import subprocess
from subprocess import PIPE
import re
import time

genlib_origin = sys.argv[-1]
lib_origin = genlib_origin[:-7] + '.lib'
design = sys.argv[-2]
sample_gate = int(sys.argv[-3])
lib_path = "gen_newlibs/"

start_time = time.time()

def run_abc(input_lib, input_genlib, input_design):
    os.makedirs("temp_blifs", exist_ok=True)
    
    genlib_basename = os.path.basename(input_genlib)
    design_basename = os.path.basename(input_design)
    temp_blif = f"temp_blifs/{design_basename}_temp.blif"
    
    abc_cmd = f"read {input_genlib}; read {input_design}; map; write {temp_blif}; read {input_lib}; read -m {temp_blif}; ps; topo; upsize; dnsize; stime;"
    
    try:
        res = subprocess.check_output(['abc', '-c', abc_cmd], text=True)
    except subprocess.CalledProcessError as e:
        print("ABC error:", e)
        return float("NaN"), float("NaN")
        
    match_d = re.search(r"Delay\s*=\s*([\d.]+)\s*ps", res)
    match_a = re.search(r"Area\s*=\s*([\d.]+)", res)
    
    delay = float(match_d.group(1)) if match_d else float("NaN")
    area = float(match_a.group(1)) if match_a else float("NaN")
    
    return delay, area

def read_genlib_origin(genlib_origin):
    f_keep = []
    f_lines = []
    
    keep_identifiers = (
        "GATE BUF", "GATE INV",
        "GATE sky130_fd_sc_hd__buf", "GATE sky130_fd_sc_hd__inv",
        "GATE gf180mcu_fd_sc_mcu7t5v0__buf", "GATE gf180mcu_fd_sc_mcu7t5v0__inv"
    )
    
    with open(genlib_origin, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("GATE"):
                if line.startswith(keep_identifiers):
                    f_keep.append(line)
                else:
                    f_lines.append(line)
    return f_keep, f_lines

f_keep, f_lines = read_genlib_origin(genlib_origin)

# Mapper call
def technology_mapper(partial_cell_library):
    lines_partial = [f_lines[i] for i in partial_cell_library]
    lines_partial = lines_partial + f_keep

    output_genlib_file = lib_path + design + "_" + str(len(lines_partial)) + "_bs_ep_samplelib.genlib"
    with open(output_genlib_file, 'w') as out_gen:
        for line in lines_partial:
            out_gen.write(line + '\n')
    out_gen.close()

    return run_abc(lib_origin, output_genlib_file, design)


print(f"select {sample_gate} cells from {len(f_lines)} cells")
print(f"keep {len(f_keep)} cells")

max_delay, max_area = run_abc(lib_origin, genlib_origin, design)

print("Baseline Delay:", max_delay)
print("Baseline Area:", max_area)

# Reward calculation
def calculate_reward(max_delay, max_area, delay, area):
    normalized_delay = delay / max_delay
    normalized_area = area / max_area

    return -np.sqrt(normalized_delay * normalized_area) 

class EpsilonGreedyMAB:
    def __init__(self, num_arms, epsilon, sample_gate, batch_size):
        self.num_arms = num_arms
        self.epsilon = epsilon
        self.q_values = [0.0] * num_arms
        self.counts = [0] * num_arms
        self.sample_gate = sample_gate
        self.batch_size = batch_size

    def select_batch_actions(self):
        batches = []
        for _ in range(self.batch_size):
            selected_cells = set()
            while len(selected_cells) < self.sample_gate:
                if random.random() > self.epsilon:
                    select = np.argmax(self.q_values)
                else:
                    select = random.randint(0, self.num_arms - 1)
                selected_cells.add(select)
            batches.append(list(selected_cells))
        return batches

    def update_batch(self, batch_actions, rewards):
        for selected_arm, reward in zip(batch_actions, rewards):
            for arm in selected_arm:
                self.counts[arm] += 1
                self.q_values[arm] = (self.q_values[arm] * (self.counts[arm] - 1) + reward) / self.counts[arm]

# Main batched MAB loop
batch_size = 10 


# Initialization
num_cells_select = sample_gate
with open(genlib_origin, 'r') as f:
        #f_lines = [line.strip() for line in f if line.startswith("GATE") and not any(substr in line for substr in ["BUF", "INV", "inv", "buf"])]
        f_lines = [line.strip() for line in f if line.startswith("GATE") and not line.startswith("GATE BUF") and not line.startswith("GATE INV") and not line.startswith("GATE sky130_fd_sc_hd__buf") and not line.startswith("GATE sky130_fd_sc_hd__inv") and not line.startswith("GATE gf180mcu_fd_sc_mcu7t5v0__buf") and not line.startswith("GATE gf180mcu_fd_sc_mcu7t5v0__inv") and not line.startswith("GATE gf180mcu_fd_sc_mcu7t5v0__buf") and not line.startswith("GATE gf180mcu_fd_sc_mcu7t5v0__inv")]
f.close()
num_arms=len(f_lines)
mab = EpsilonGreedyMAB(num_arms, 0.2, sample_gate, batch_size)
best_cells = []
best_result = (float('inf'), float('inf'))  
best_reward = -float('inf')  # Track best reward

# Main Loop
num_iterations = 100  

for i in range(num_iterations):
    print(f"Batch iteration: {i}")
    batch_actions = mab.select_batch_actions()
    batch_rewards = []
    for selected_cells in batch_actions:
        delay, area = technology_mapper(selected_cells)
        if np.isnan(delay) or np.isnan(area):
            reward = -float('inf')
        else:
            reward = calculate_reward(max_delay, max_area, delay, area)
        if reward > best_reward:
            best_reward = reward
            best_result = (delay, area)
            best_cells = selected_cells

        batch_rewards.append(reward)
    print("Current best reward: ", best_reward)
    print("Current best result: ", best_result)
        # Update best results tracking here as needed
    mab.update_batch(batch_actions, batch_rewards)

print("Best Delay:", best_result[0])
print("Best Area:", best_result[1])
print("Best Reward:", best_reward)
print("Total time:", time.time() - start_time)


total_cells = len(f_lines)

iteration = 0
no_better_reward_round = 0
best_cells = set(best_cells)
best = (best_reward, best_result[0], best_result[1], best_cells)
current = best
while no_better_reward_round < 2:
    iteration += 1
    print(f"{iteration:>3}: ", end="")
                
    round_best = (-float('inf'), float('inf'), float('inf'), [])  # (reward, delay, area, selected_cells)

    for cell in range(total_cells):
        if cell in current[3]:
            selected_cells = current[3] - {cell}
        else:
            if len(current[3]) >= sample_gate:
                continue
            selected_cells = current[3] | {cell}

        delay, area = technology_mapper(selected_cells)
        
        if np.isnan(delay) or np.isnan(area):
            reward = -float('inf')
        else:
            reward = calculate_reward(max_delay, max_area, delay, area)
            
        if reward > round_best[0]:
            round_best = (reward, delay, area, selected_cells)
            
        if reward > best[0]:
            best = (reward, delay, area, selected_cells)
            current = best
            print(f"success, best reward: {best[0]:.4f}, delay: {best[1]}, area: {best[2]}, cells count: {len(best[3])}")
            no_better_reward_round = 0
            break
    else: # finish without break (finding new record), jump to round best solution
        current = round_best
        print(f"fail, round best reward: {round_best[0]:.4f}, delay: {round_best[1]}, area: {round_best[2]}, cells count: {len(round_best[3])}")
        no_better_reward_round += 1

print("Best Reward:", best[0])
print("Best Delay:", best[1])
print("Best Area:", best[2])
print("Best Cells Count:", len(best[3]))
print("Total time:", time.time() - start_time)