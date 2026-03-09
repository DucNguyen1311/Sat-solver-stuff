import os
import time
import gurobipy as gp
from gurobipy import GRB

class MOFAP_Solver_Gurobi:
    def __init__(self):
        self.domains = {} 
        self.variables = {}
        self.constraints = []
        self.variable_ids = []
        self.freq_list = []

    def solve(self, path, time_limit=600, target_val=None):
        start_time = time.time()
        print(f"\n[INFO] Starting solver for: {os.path.basename(path)}")
        
        self.parse_dataset(path)
        print(f"[INFO] Dataset parsed: {len(self.variable_ids)} vars, {len(self.domains)} domains, {len(self.constraints)} ctrs")
        
        all_freqs = set()
        for f_list in self.domains.values(): all_freqs.update(f_list)
        self.freq_list = sorted(list(all_freqs))
        
        try:
            with gp.Env() as env, gp.Model("MOFAP_Gurobi", env=env) as model:
                model.Params.OutputFlag = 0
                model.Params.TimeLimit = time_limit
                
                if target_val is not None:
                    print(f"[INFO] Target objective set to: {target_val}")
                    model.Params.BestObjStop = target_val
                    model.Params.Cutoff = target_val + 0.5

                print("[INFO] Building model components...")
                x = {}
                for v_id in self.variable_ids:
                    dom_id = self.variables[v_id]['dom']
                    for f in self.domains[dom_id]:
                        x[(v_id, f)] = model.addVar(vtype=GRB.BINARY, name=f'x_{v_id}_{f}')
                
                z = {f: model.addVar(vtype=GRB.BINARY, name=f'z_{f}') for f in self.freq_list}

                for v_id in self.variable_ids:
                    dom_id = self.variables[v_id]['dom']
                    valid_freqs = self.domains[dom_id]
                    model.addConstr(gp.quicksum(x[(v_id, f)] for f in valid_freqs) == 1)
                    fixed_val = self.variables[v_id]['fixed']
                    if fixed_val is not None and fixed_val in valid_freqs:
                        model.addConstr(x[(v_id, fixed_val)] == 1)

                for v_id in self.variable_ids:
                    dom_id = self.variables[v_id]['dom']
                    for f in self.domains[dom_id]:
                        model.addConstr(x[(v_id, f)] <= z[f])

                for ctr in self.constraints:
                    v1, v2, op, diff = ctr['v1'], ctr['v2'], ctr['op'], ctr['diff']
                    dom1, dom2 = self.domains[self.variables[v1]['dom']], self.domains[self.variables[v2]['dom']]
                    if op == '=':
                        for f1 in dom1:
                            targets = [tf for tf in [f1-diff, f1+diff] if tf in dom2]
                            if not targets: model.addConstr(x[(v1, f1)] == 0)
                            else: model.addConstr(x[(v1, f1)] <= gp.quicksum(x[(v2, tf)] for tf in targets))
                    elif op == '>':
                        for f1 in dom1:
                            for f2 in dom2:
                                if abs(f1 - f2) <= diff: model.addConstr(x[(v1, f1)] + x[(v2, f2)] <= 1)

                model.setObjective(gp.quicksum(z[f] for f in self.freq_list), GRB.MINIMIZE)
                
                print("[INFO] Optimizing model...")
                model.optimize()
                duration = time.time() - start_time
                if model.SolCount > 0:
                    val = int(round(model.ObjVal))
                    print(f"[SUCCESS] Solution found. Objective: {val} (Time: {duration:.2f}s)")
                    return val, duration
                
                print(f"[WARN] No solution found (Time: {duration:.2f}s)")
                return -1, duration

        except gp.GurobiError as e:
            print(f"[ERROR] Gurobi Error: {e}")
            return -1, time.time() - start_time

    def parse_dataset(self, path):
        self.parse_domains(path)
        self.parse_variables(path)
        self.parse_constraints(path)
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
        print(f"[FILE] Reading SAT targets from {filepath}")
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4 and parts[1].lower() == "optimal":
                    try:
                        targets[parts[0].lower()] = int(parts[3])
                    except (ValueError, IndexError): continue
    return targets

if __name__ == "__main__":
    base_path = input("Enter directory: ").strip()
    sat_file = "results.txt"
    out_target = "gurobi_match_sat.txt"
    out_marathon = "gurobi_600s_marathon.txt"
    
    sat_targets = get_sat_targets(sat_file)
    print(f"[INIT] Loaded {len(sat_targets)} SAT targets.", flush=True)
    
    scenarios = ["scen01", "scen02", "scen03", "scen04", "scen11", "graph01", "graph02", "graph08", "graph09", "graph14"]

    # --- LOOP 1: TARGET MATCHING ---
    print("\n" + "="*30)
    print("PHASE 1: TARGET MATCHING")
    print("="*30)
    # for scen in scenarios:
    #     fp = os.path.join(base_path, scen)
    #     if not os.path.exists(fp): fp += ".txt"
    #     if not os.path.exists(fp): continue

    #     target = sat_targets.get(scen.lower())
    #     if target:
    #         val, dur = MOFAP_Solver_Gurobi().solve(fp, 600, target)
    #         with open(out_target, "a") as f: 
    #             f.write(f"{scen.upper()} target={target} reached={val} time={dur:.2f}s\n")
    #     else:
    #         print(f"[SKIP] No SAT target found for {scen}")

    # --- LOOP 2: MARATHON (600s) ---
    print("\n" + "="*30)
    print("PHASE 2: MARATHON SEARCH")
    print("="*30)
    for scen in scenarios:
        fp = os.path.join(base_path, scen)
        if not os.path.exists(fp): fp += ".txt"
        if not os.path.exists(fp): continue

        val, dur = MOFAP_Solver_Gurobi().solve(fp, 600, None)
        with open(out_marathon, "a") as f: 
            f.write(f"{scen.upper()} best={val} time={dur:.2f}s\n")