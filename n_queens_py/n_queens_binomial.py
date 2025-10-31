from pysat.solvers import Glucose4

def generate_vars(n):
    board = [];
    for i in range(n):
        row = [];
        for j in range(n):
            row.append(i * n + j + 1);
        board.append(row);
    return board;
            
def generate_clauses(n, board):
    clauses = [];

     # Exactly one queen in each row
    for i in range(n):
        clauses.append(board[i]);
        for j in range(n):
            for k in range(j + 1, n):
                clauses.append([-board[i][j], -board[i][k]]);

    # Exactly one queen in each column
    for j in range(n):
        clauses.append([board[i][j] for i in range(n)]);
        for i in range(n):
            for k in range(i + 1, n):
                clauses.append([-board[i][j], -board[k][j]]);
    
    # At most one queen in each diagonal
    for i in range(n):
        for j in range(n):
            for k in range(1, n):
                if (i + k < n and j + k < n):
                    clauses.append([-board[i][j], -board[i + k][j + k]]);
                if (i + k < n and j - k >= 0):
                    clauses.append([-board[i][j], -board[i + k][j - k]]);
    return clauses;

def solve(n):
    board = generate_vars(n);
    clauses = generate_clauses(n, board);
    solver = Glucose4();
    for clause in clauses:
        solver.add_clause(clause);
    
    if (solver.solve()):
        model = solver.get_model()
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
    else:
        print("unsatisfiable");

if __name__ == "__main__":
    n_str = input("Enter the board size (N): ");

    try:
        n = int(n_str);
        print(f"Board size N set to: {n}")
    except ValueError:
        print("Invalid input. Please enter an integer.")
        n = 0;

    solve(n);


