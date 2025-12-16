from pysat.solvers import Solver
from pysat.formula import CNF
import os 
from pysat.card import CardEnc
import threading
import signal

def alarm_handler(signum, frame):
    raise TimeoutError("Time limit reached!")

signal.signal(signal.SIGALRM, alarm_handler)


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
        self.parse_dataset(path)
        self.init_vars_matrix()
        self.add_domain_constraints()
        self.add_ordering_constraints()
        self.add_interference_constraints()
        print(f"Total Clauses: {len(self.cnf.clauses)}")

        n_freqs = len(self.freq_list)
         
        #create n z variables( zi mean that Fi is used somewhere)
        z_vars = [] 
        for k in range (n_freqs):
            self.current_max_id += 1
            z_vars.append(self.current_max_id)
        #create trash variables ( use to reduce the z variables that can be used)
        t_vars = []
        for k in range (n_freqs):
            self.current_max_id += 1
            t_vars.append(self.current_max_id)

        print(f"Created {len(z_vars)} Z vars and {len(t_vars)} trash vars.")

        count_links = 0
        for u_idx in range(len(self.variable_ids)):
            for k in range(n_freqs):
                lit_x = self.vars_matrix[u_idx][k]
                lit_z = z_vars[k]
                self.cnf.append([-lit_x, lit_z])
                count_links += 1
        print(f"Added {count_links} linking clauses (x -> z).")

        for k in range(n_freqs - 1):
            self.cnf.append([-t_vars[k], t_vars[k+1]])

        #to begin optimizing, we merge t_vars and z_vars together

        all_vars = z_vars + t_vars

        cnf_leq = CardEnc.atmost(lits=all_vars, bound=n_freqs, top_id=self.current_max_id)
        self.cnf.extend(cnf_leq.clauses)
        print("Start Optimizing")
        best_result = n_freqs + 1
        time_out = 30
        with Solver(name = 'Glucose4', bootstrap_with=self.cnf.clauses) as solver:
            while True:
                print(f"  > Solving... (Time limit: {time_out}s)")
                signal.alarm(time_out)
                try:
                    is_sat = solver.solve()
                    signal.alarm(0)
                    if (is_sat):
                        model = solver.get_model()
                        model_set = set(model)
                        current_result = sum(1 for z in z_vars if z in model_set)

                        print(f"\n[SAT] Found solution using {current_result} frequencies.")
                        
                        best_result = min(best_result, current_result)
                        target_result = current_result - 1;

                        if target_result < 1:
                            print('ideal solution reached')
                            break
                        
                        needed_trash_count = n_freqs - target_result
                        trash_id_to_force_true = n_freqs - needed_trash_count
                        print(f"  > Optimizing: Aiming for <= {target_result} freqs.")
                        print(f"  > Injecting {needed_trash_count} trash units (Force s[{trash_id_to_force_true}] = True)")
                        
                        # THÊM MỘT CLAUSE DUY NHẤT
                        solver.add_clause([t_vars[trash_id_to_force_true]])
                        continue
                    elif is_sat is False:
                        print(f"\n[UNSAT] Optimization finished. Best Minimum Order: {best_result}")
                        break
                except (TimeoutError, Exception) as e:
                    # 4. SAFETY: Turn off alarm immediately to prevent double-crashes
                    signal.alarm(0)
                    
                    # 5. Check if it was a Timeout OR a PySAT Interrupt
                    error_msg = str(e).lower()
                    if isinstance(e, TimeoutError) or "interrupt" in error_msg:
                        print(f"\n[TIMEOUT] Solver stopped after {time_out}s.")
                        print(f"Optimization stopped. Best result found so far: {best_result}")
                        break
                    else:
                        # If it's some other real crash (like MemoryError), re-raise it
                        raise e
                


    def add_domain_constraints(self):
        self.current_max_id = self.orders_matrix[-1][-1]
        for real_id in self.variable_ids:
            u = self.id_map[real_id]
            dom_id = self.variables[real_id]['dom']
            allowed_freqs = set(self.domains[dom_id])
            valid_lit = []
            
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

if (__name__ == "__main__"):
    n_str = input("Enter the datasets link ");
    print(f"Parsing data from {n_str}");
    print("Current Working Directory:", os.getcwd())
    print("Does path exist?", os.path.exists(n_str))
    solver = MOFAP_Solver()
    solver.solve(n_str)

