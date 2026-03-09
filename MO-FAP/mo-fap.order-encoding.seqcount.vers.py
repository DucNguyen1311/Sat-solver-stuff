from pysat.solvers import Solver
from pysat.formula import CNF
import os 
from pysat.card import CardEnc
import threading
import time
import traceback


class MOFAP_Solver:
    def __init__(self):
        self.domains = {}
        self.variables = {}
        self.constraints = []
        self.variable_ids = []
        self.vars_matrix = []
        self.orders_matrix = []
        self.id_map = {}
        self.freq_map = {}
        self.freq_list = []
        self.cnf = CNF()
        self.current_max_id = 0

    def solve(self, path):
        start_time = time.time()
        self.parse_dataset(path)
        self.init_vars_matrix()
        self.add_domain_constraints()
        self.add_ordering_constraints()
        self.add_interference_constraints()
        print(f"Total Clauses: {len(self.cnf.clauses)}")

        n_freqs = len(self.freq_list)
        
        z_vars = [] 
        for k in range(n_freqs):
            self.current_max_id += 1
            z_vars.append(self.current_max_id)
        
        count_links = 0
        for u_idx in range(len(self.variable_ids)):
            for k in range(n_freqs):
                lit_x = self.vars_matrix[u_idx][k]
                lit_z = z_vars[k]
                self.cnf.append([-lit_x, lit_z])
                count_links += 1
        
        S = []
        for i in range(n_freqs):
            row = []
            for j in range(n_freqs):
                self.current_max_id += 1
                row.append(self.current_max_id)
            S.append(row)
            
        self.cnf.append([-z_vars[0], S[0][0]])

        for i in range(1, n_freqs):
            self.cnf.append([-z_vars[i], S[i][0]])
            self.cnf.append([-S[i-1][0], S[i][0]])
        
            for j in range(1, n_freqs):
                self.cnf.append([-z_vars[i], -S[i-1][j-1], S[i][j]])
                self.cnf.append([-S[i-1][j], S[i][j]])
        
        best_result = n_freqs + 1
        time_out = 600
        last_sat_time = 0  
        
        # 1. MARK THE START: This is exactly when the solver begins working
        solver_start_time = time.time()
        
        with Solver(name='Glucose42', bootstrap_with=self.cnf.clauses) as solver:
            while True:
                elapsed_so_far = time.time() - solver_start_time
                print(f"  > Solving... (Elapsed: {elapsed_so_far:.2f}s, Timeout Limit: {time_out}s)")
                
                timer = threading.Timer(time_out, solver.interrupt)
                timer.start()
                is_sat = solver.solve_limited(assumptions=[], expect_interrupt=True)
                timer.cancel()
                
                if is_sat:
                    last_sat_time = time.time() - solver_start_time
                    
                    model = solver.get_model()
                    model_set = set(model)
                    current_result = sum(1 for z in z_vars if z in model_set)

                    print(f"\n[SAT] Found {current_result} freqs at {last_sat_time:.2f}s.")
                    
                    best_result = current_result

                    target_result = current_result - 1
                    if target_result < 1:
                        print('Ideal solution reached.')
                        break
                    solver.add_clause([-S[n_freqs-1][target_result]])
                    
                    continue

                elif is_sat is False:
                    print(f"\n[UNSAT] Proven optimal. Best: {best_result}")
                    break

                elif is_sat is None:
                    print(f"\n[TIMEOUT] Hit {time_out}s limit. Best: {best_result}")
                    break
        
        total_duration = time.time() - solver_start_time
        
        return best_result, total_duration, last_sat_time
                


    def add_domain_constraints(self):
        self.current_max_id = self.orders_matrix[-1][-1]
        for real_id in self.variable_ids:
            u = self.id_map[real_id]
            dom_id = self.variables[real_id]['dom']
            fixed = self.variables[real_id]['fixed']
            allowed_freqs = set(self.domains[dom_id])
            valid_lit = []

            if (fixed is not None):
                lit = self.vars_matrix[u][self.freq_map[fixed]]
                self.cnf.append([lit])
            
            for freq_val in self.freq_list:
                f_idx = self.freq_map[freq_val]
                lit = self.vars_matrix[u][f_idx]
                if freq_val in allowed_freqs:
                    valid_lit.append(lit)
                else:
                    self.cnf.append([-lit])
            
            if valid_lit: 
                const = CardEnc.equals(lits=valid_lit, bound=1, top_id=self.current_max_id)
                self.cnf.extend(const.clauses)
                self.current_max_id = max(self.current_max_id, const.nv)

    def add_ordering_constraints(self):
        n_vars = len(self.variable_ids)
        n_freqs = len(self.freq_list)
        for i in range (n_vars):
            for j in range (n_freqs):
                varX = self.vars_matrix[i][j]
                varY = self.orders_matrix[i][j]

                if (j == n_freqs - 1):
                    self.cnf.append([-varX, varY])
                    self.cnf.append([varX, -varY])
                    continue

                varZ = self.orders_matrix[i][j + 1]

                if (j == n_freqs - 1):
                    self.cnf.append([-varX, varY])
                    self.cnf.append([varX,-varY])
                    continue;
                
                if (j == 0):
                    self.cnf.append([varY])

                self.cnf.append([-varX, varY])
                self.cnf.append([-varX, -varZ])
                self.cnf.append([varX, -varY, varZ])
                self.cnf.append([varY, -varZ])

    def add_interference_constraints(self):
        for constraint in self.constraints:
            varX = self.id_map[constraint['v1']]
            varY = self.id_map[constraint['v2']]
            operator = constraint['op']
            diff = constraint['diff']
            pairs = [(varX, varY), (varY, varX)]
            n_freqs = len(self.freq_list)
            for varX, varY in pairs:
                #get all available freqs, map each of them with the constraints
                for i in range(n_freqs):
                    lit_x_j = self.vars_matrix[varX][i]
                    val_x = self.freq_list[i]
                    if operator == '=':
                        clause = [-lit_x_j]
                        target_1 = val_x - diff
                        target_2 = val_x + diff

                        if target_1 in self.freq_map:
                            clause.append(self.vars_matrix[varY][self.freq_map[target_1]])
                        if target_2 in self.freq_map:
                            clause.append(self.vars_matrix[varY][self.freq_map[target_2]])

                        self.cnf.append(clause)
                    elif operator == '>':
                        effective_diff = diff + 1 # in case there exist a value exactly equal diff + f2 in freq map.
                        lower_bound_index = -1
                        target_lower = val_x - effective_diff
                        upper_bound_index = -1
                        target_higher = val_x + effective_diff
                        #traverse all frequency, find the last frequency smaller than target lower, and the first bigger than target upper
                        for k, freq_val in enumerate(self.freq_list):
                            if freq_val <= target_lower:
                                lower_bound_index = k
                            if freq_val >= target_higher and upper_bound_index == -1:
                                upper_bound_index = k
                                break
                        clause = [-lit_x_j]
                        is_valid = False

                        if lower_bound_index != -1:
                            next_index = lower_bound_index + 1
                            clause.append(-self.orders_matrix[varY][next_index])
                            is_valid = True
                        if  upper_bound_index != -1:
                            clause.append(self.orders_matrix[varY][upper_bound_index])
                            is_valid = True
                        if not is_valid: #if frequency j is choosen for tower x, there exist no freq for tower y to choose -> UNSAT if choose so we ban
                            self.cnf.append([-lit_x_j])
                        else: 
                            self.cnf.append(clause)          

    def init_vars_matrix(self):
        n_vars = len(self.variable_ids)
        
        self.id_map = {r_id: i for i, r_id in enumerate(self.variable_ids)}
        
        all_freqs = set()
        for f_list in self.domains.values():
            all_freqs.update(f_list)
        self.freq_list = sorted(list(all_freqs))
        
        n_freqs = len(self.freq_list)
        self.freq_map = {f: j for j, f in enumerate(self.freq_list)}
        
        print("Solver Initialized:")
        print(f"  > Variables: {n_vars} (Mapped 0 to {n_vars-1})")
        print(f"  > Global Spectrum: {n_freqs} Unique Frequencies")
        
        self.vars_matrix = [[0] * n_freqs for _ in range(n_vars)]
        self.orders_matrix = [[0] * n_freqs for _ in range(n_vars)]
        current_lit = 1
        for i in range(n_vars):
            for j in range(n_freqs):
                self.vars_matrix[i][j] = current_lit
                current_lit += 1
        
        for i in range(n_vars):
            for j in range(n_freqs):
                self.orders_matrix[i][j] = current_lit
                current_lit += 1

    def parse_dataset(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")

        self.parse_domains(path)
        self.parse_variables(path)
        self.parse_constraints(path)
        self.variable_ids = sorted(list(self.variables.keys()))

    def parse_domains(self, path):
        file_path = os.path.join(path, "DOM.TXT")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            return

        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                d_id = int(parts[0])
                freqs = [int(x) for x in parts[2:]]
                self.domains[d_id] = freqs

    def parse_variables(self, path):
        file_path = os.path.join(path, "VAR.TXT")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            return

        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts: 
                    continue
                v_id = int(parts[0])
                d_id = int(parts[1])
                fixed_value = None
                if len(parts) >= 4:
                    mobility = int(parts[3])
                    initial_val = int(parts[2])
                    if mobility == 0:
                        fixed_value = initial_val
                self.variables[v_id] = {'dom': d_id, 'fixed': fixed_value}

    def parse_constraints(self, path):
        file_path = os.path.join(path, "CTR.TXT")
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            return

        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts: 
                    continue
                v1 = int(parts[0])
                v2 = int(parts[1])
                operator = parts[3]
                deviation = int(parts[4])
                is_hard = True
                if len(parts) >= 6:
                    weight = int(parts[5])
                    if weight > 0:
                        is_hard = False
                self.constraints.append({
                    'v1': v1, 'v2': v2, 'op': operator, 
                    'diff': deviation, 'hard': is_hard
                })

if __name__ == "__main__":
    import os

    # 1. SETUP PATHS
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "seq-count.results.txt")
    
    # 2. WIPE THE FILE CLEAN (The Fix)
    # Opening in 'w' mode instantly deletes all old content
    print(f"Cleaning previous results from: {output_file}", flush=True)
    with open(output_file, "w") as f:
        f.write("--- ORDER ENCODING WEIGHT ADDING USING SEQUENCE COUNTER BENCHMARK ---\n")

    # 3. GET INPUTS
    base_path = input("Enter the directory containing datasets: ").strip()
    scenarios = ["scen01", "scen02", "scen03", "scen04", "scen11", "graph01", "graph02", "graph08", "graph09", "graph14"]

    # 4. RUN LOOP (Append Mode)
    for scen in scenarios:
        file_path = os.path.join(base_path, f"{scen}.txt")
        if not os.path.exists(file_path):
             file_path = os.path.join(base_path, scen)

        if os.path.exists(file_path):
            try:
                print("-" * 40, flush=True)
                print(f"Processing: {scen}", flush=True)
                
                solver = MOFAP_Solver()
                best_val, effective_time, optimal_time = solver.solve(file_path)
                
                result_line = (
                    f"{scen.upper()} "
                    f"optimal = {best_val} "
                    f"total time = {effective_time:.2f}s "
                    f"effective time = {optimal_time:.2f}s"
                )
                print(f"Result: {result_line}", flush=True)

                # 5. SAFE SAVE (Append)
                # We use 'a' here so if Scen03 crashes, Scen01 and 02 are already saved.
                with open(output_file, "a") as f:
                    f.write(result_line + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                
            except Exception as e:
                print(f"[ERROR] {scen}: {e}", flush=True)
                import traceback
                traceback.print_exc()

