import os
import time
from docplex.mp.model import Model

class MOFAP_Solver_CPLEX:
    def __init__(self):
        self.domains = {} 
        self.variables = {}
        self.constraints = []
        self.variable_ids = []
        self.id_map = {}
        self.freq_list = []
        self.model = None

    def solve(self, path, time_limit=600, target_val=None):
        start_time = time.time()
        self.parse_dataset(path)
        self.prepare_data_structures()
        self.model = Model(name='MOFAP_CPLEX')
        
        print(f"  [CPLEX] Building model for {os.path.basename(path)}...", flush=True)
        
        x = {} 
        for v_id in self.variable_ids:
            dom_id = self.variables[v_id]['dom']
            for f in self.domains[dom_id]:
                x[(v_id, f)] = self.model.binary_var(name=f'x_{v_id}_{f}')
        
        z = {f: self.model.binary_var(name=f'z_{f}') for f in self.freq_list}

        for v_id in self.variable_ids:
            dom_id = self.variables[v_id]['dom']
            valid_freqs = self.domains[dom_id]
            self.model.add_constraint(self.model.sum(x[(v_id, f)] for f in valid_freqs) == 1)
            fixed_val = self.variables[v_id]['fixed']
            if fixed_val is not None and fixed_val in valid_freqs:
                self.model.add_constraint(x[(v_id, fixed_val)] == 1)

        for v_id in self.variable_ids:
            dom_id = self.variables[v_id]['dom']
            for f in self.domains[dom_id]:
                self.model.add_constraint(x[(v_id, f)] <= z[f])

        for ctr in self.constraints:
            v1, v2, op, diff = ctr['v1'], ctr['v2'], ctr['op'], ctr['diff']
            dom1, dom2 = self.domains[self.variables[v1]['dom']], self.domains[self.variables[v2]['dom']]
            if op == '=':
                for f1 in dom1:
                    target_freqs = [tf for tf in [f1-diff, f1+diff] if tf in dom2]
                    if not target_freqs: self.model.add_constraint(x[(v1, f1)] == 0)
                    else: self.model.add_constraint(x[(v1, f1)] <= self.model.sum(x[(v2, tf)] for tf in target_freqs))
            elif op == '>':
                for f1 in dom1:
                    for f2 in dom2:
                        if abs(f1 - f2) <= diff: self.model.add_constraint(x[(v1, f1)] + x[(v2, f2)] <= 1)

        self.model.minimize(self.model.sum(z[f] for f in self.freq_list))
        self.model.parameters.timelimit = time_limit
        
        if target_val is not None:
            # Setting cutoff to ignore solutions worse than the SAT result
            self.model.parameters.mip.tolerances.uppercutoff = target_val + 0.5
            # Fix: Use absmipgap to stop exactly on the integer value
            self.model.parameters.mip.tolerances.absmipgap = 0.0

        solution = self.model.solve(log_output=False)
        solve_duration = time.time() - start_time
        
        if solution:
            return int(round(solution.objective_value)), solve_duration
        else:
            return -1, solve_duration

    def prepare_data_structures(self):
        all_freqs = set()
        for f_list in self.domains.values(): all_freqs.update(f_list)
        self.freq_list = sorted(list(all_freqs))
        self.id_map = {r_id: i for i, r_id in enumerate(self.variable_ids)}

    def parse_dataset(self, path):
        self.parse_domains(path); self.parse_variables(path); self.parse_constraints(path)
        self.variable_ids = sorted(list(self.variables.keys()))

    def parse_domains(self, path):
        fp = os.path.join(path, "DOM.TXT")
        if not os.path.exists(fp): return
        with open(fp, 'r') as f:
            for line in f:
                p = line.strip().split()
                if p: self.domains[int(p[0])] = [int(x) for x in p[2:]]

    def parse_variables(self, path):
        fp = os.path.join(path, "VAR.TXT")
        if not os.path.exists(fp): return
        with open(fp, 'r') as f:
            for line in f:
                p = line.strip().split()
                if p:
                    v_id, d_id = int(p[0]), int(p[1])
                    fixed = int(p[2]) if len(p) >= 4 and int(p[3]) == 0 else None
                    self.variables[v_id] = {'dom': d_id, 'fixed': fixed}

    def parse_constraints(self, path):
        fp = os.path.join(path, "CTR.TXT")
        if not os.path.exists(fp): return
        with open(fp, 'r') as f:
            for line in f:
                p = line.strip().split()
                if p: self.constraints.append({'v1': int(p[0]), 'v2': int(p[1]), 'op': p[3], 'diff': int(p[4])})

def get_sat_targets(filepath):
    targets = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                # Correct index: 0=SCEN, 1=optimal, 2==, 3=Value
                if len(parts) >= 4 and parts[1].lower() == "optimal":
                    try:
                        targets[parts[0].lower()] = int(parts[3])
                    except (ValueError, IndexError):
                        continue
    return targets

if __name__ == "__main__":
    base_path = input("Enter directory: ").strip()
    sat_results_file = "results.txt"
    target_file = "cplex_match_sat.txt"
    marathon_file = "cplex_600s_marathon.txt"
    
    sat_targets = get_sat_targets(sat_results_file)
    print(f"Loaded {len(sat_targets)} SAT targets from {sat_results_file}.", flush=True)
    
    scenarios = ["scen01", "scen02", "scen03", "scen04", "scen11", "graph01", "graph02", "graph08", "graph09", "graph14"]

    for scen in scenarios:
        file_path = os.path.join(base_path, scen)
        if not os.path.exists(file_path): file_path += ".txt"
        if not os.path.exists(file_path): 
            print(f"[SKIP] File not found: {scen}", flush=True)
            continue

        print(f"\n--- Processing: {scen.upper()} ---", flush=True)

        # 1. Target Run
        target_val = sat_targets.get(scen.lower())
        if target_val:
            print(f"  [MATCH] Aiming for SAT result: {target_val}...", flush=True)
            solver = MOFAP_Solver_CPLEX()
            val, duration = solver.solve(file_path, time_limit=600, target_val=target_val)
            print(f"  [RESULT] Reached {val} in {duration:.2f}s", flush=True)
            with open(target_file, "a") as f:
                f.write(f"{scen.upper()} target={target_val} reached={val} time={duration:.2f}s\n")
        
        # 2. Marathon Run
        print(f"  [MARATHON] Running 600s limit...", flush=True)
        solver = MOFAP_Solver_CPLEX()
        val, duration = solver.solve(file_path, time_limit=600, target_val=None)
        print(f"  [RESULT] Best found {val} in {duration:.2f}s", flush=True)
        with open(marathon_file, "a") as f:
            f.write(f"{scen.upper()} best_val={val} total_time={duration:.2f}s\n")