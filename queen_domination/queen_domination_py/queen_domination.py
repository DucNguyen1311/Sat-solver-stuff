from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose4
from pysat.formula import CNF, IDPool

def generate_vars(n):
    board = [];
    for i in range(n):
        row = [];
        for j in range(n):
            row.append(i * n + j + 1);
        board.append(row);
    return board;

def flatten(board):
    vars = [];
    for row in board:
        for var in row:
            vars.append(var);
    return vars;

def incremental_search(board, all_vars, at_most_k):
    # incrementally search for the minimun number of queens needed to dominate an nxn board
    solver = Glucose4();
    n = len(board);
    vpool = IDPool(start_from = max(all_vars) + 1);

    # add the domination constraints
    for i in range(n):
        for j in range(n):
            clause = [];
            clause.append(board[i][j]);
            for k in range (n):
                if (k != j):
                    clause.append(board[i][k]);
                if (k != i):
                    clause.append(board[k][j]);
            
            for g in range (1, n):
                if (i + g < n and j + g < n):
                    clause.append(board[i + g][j + g]);
                if (i + g < n and j - g >= 0):
                    clause.append(board[i + g][j - g]);
                if (i - g >= 0 and j + g < n):
                    clause.append(board[i - g][j + g]);
                if (i - g >= 0 and j - g >= 0):
                    clause.append(board[i - g][j - g]);
            
            solver.add_clause(clause);

    at_most_k_secCount = CardEnc.atmost(lits = all_vars, bound = at_most_k, vpool= vpool, encoding = EncType.seqcounter);
    solver.append_formula(at_most_k_secCount);
    return solver;

def solve(n):
    board = generate_vars(n);
    all_vars = flatten(board);
    left = 1;
    right = n * n;
    result = -1;

    while (left <= right):
        mid = (left + right) // 2;
        if (incremental_search(board, all_vars, mid).solve()):
            result = mid;
            right = mid - 1;
        else:
            left = mid + 1;
    sat_result = incremental_search(board, all_vars, result);

    if (sat_result.solve()):
        model = sat_result.get_model()
        # Iterate through the rows
        for i in range(n):
            row_output = "";
            for j in range(n):
                var_id = board[i][j];
                if (var_id in model): 
                    row_output += "♛ ";
                else:
                    row_output += ". ";
            print(row_output);
        print("satisfiable");
    
if (__name__ == "__main__"):
    n_str = input("Enter the board size (N): ");

    try:
        n = int(n_str);
        print(f"Board size N set to: {n}")
    except ValueError:
        print("Invalid input. Please enter an integer.")
        n = 0;

    solve(n);



