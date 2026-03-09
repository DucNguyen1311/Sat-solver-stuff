import gurobipy as gp
from gurobipy import GRB

def solve_model():
    """
    Solves a sample optimization problem using provided Gurobi WLS options.
    """
    try:
        # 1. Create the Environment (using 'with' ensures it is closed/released automatically)
        with gp.Env() as env:
            # 2. Create the Model within that specific environment
            with gp.Model("test_model", env=env) as m:
                
                # 3. Variable definition (using list comprehension for scalability)
                vars = m.addVars(['x', 'y'], name="v")

                # 4. Objective: Maximize x + y
                m.setObjective(vars['x'] + vars['y'], GRB.MAXIMIZE)

                # 5. Constraints
                m.addConstr(vars['x'] + 2 * vars['y'] <= 4, name="c0")

                # 6. Optimization
                m.optimize()

                # 7. Output processing
                if m.Status == GRB.OPTIMAL:
                    for v in m.getVars():
                        print(f"{v.VarName}: {v.X}")
                    print(f"Optimal Objective: {m.ObjVal}")
                else:
                    print(f"Optimization ended with status: {m.Status}")

    except gp.GurobiError as e:
        print(f"Gurobi Error: {e.message}")
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    
    solve_model()