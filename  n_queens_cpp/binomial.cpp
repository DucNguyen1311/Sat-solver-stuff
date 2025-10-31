#include <bits/stdc++.h>
#include <minisat/core/Solver.h>



int main() {
    //Size of the board is NxN, numbers of queens is n. Noted, for n = 2 and n = 3, no solutions exists.
    int n;
    Minisat::Solver solver;
    std::vector<std::vector<Minisat::Var>> board;
    std::cin >> n;
    auto start = std::chrono::high_resolution_clock::now();
    // initiate the board, each square represent whether a queen is present.
    for (int i = 0; i < n; i++) {
        std::vector<Minisat::Var> tmp;
        for (int j = 0; j < n;j ++) {
            tmp.push_back(solver.newVar());
        }
        board.push_back(tmp);
    }

    //Cardinality Constraint, for the problems to be satisfied:
    // Exactly one queen per row (at most 1 and at least one at the same time)
    // Exactly one queen per column (same thing)
    //At most one queen on diagonal

    //Exactly one per row:
        //At least one per row:
    for (int i = 0; i < n; i++) {
        Minisat::vec<Minisat::Lit> tmp;
        for (int j = 0; j < n; j++) {
            tmp.push(Minisat::mkLit(board[i][j]));
        }
        solver.addClause(tmp);
    }
        //At most one per row:
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = j+1; k < n; k++) {
                solver.addClause(~Minisat::mkLit(board[i][j]), ~Minisat::mkLit(board[i][k]));
            }
        }
    }

    //Exactly one per column:
        //At least one per column:
    for (int i = 0; i < n; i++) {
        Minisat::vec<Minisat::Lit> tmp;
        for (int j = 0; j < n; j++) {
            tmp.push(Minisat::mkLit(board[j][i]));
        }
        solver.addClause(tmp);
    }
        //At most one per column:
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = j+1; k < n; k++) {
                solver.addClause(~Minisat::mkLit(board[j][i]), ~Minisat::mkLit(board[k][i]));
            }
        }
    }

    //At most one queen on diagonal
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 1; k < n; k++) {
                if (i + k < n && j + k < n) {
                    solver.addClause(~Minisat::mkLit(board[i][j]), ~Minisat::mkLit(board[i+k][j+k]));
                }
                if (i + k < n && j - k >= 0) {
                    solver.addClause(~Minisat::mkLit(board[i][j]), ~Minisat::mkLit(board[i+k][j-k]));
                }
            }
        }
    }

    bool isSat = solver.solve();

    if (isSat) {
        std::cout << "satisfiable" << std::endl;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (solver.modelValue(board[i][j]) == l_True) {
                    std::cout << "♛ ";
                } else {
                    std::cout << ". ";
                }
            } // <--- ADD THIS CLOSING BRACE
            std::cout << std::endl; // This should be inside the outer loop
        }
    } else {
        std::cout << "unsatisfiable";
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "n=" << n << " Time: " << duration.count() << " ms\n";
    return 0;
}