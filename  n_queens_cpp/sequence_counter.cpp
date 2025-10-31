#include <bits/stdc++.h>
#include <minisat/core/Solver.h>
using namespace Minisat;

void exactlyOnePerRow(Minisat::Solver &solver, std::vector<std::vector<Minisat::Var>> board) {
    std::vector<std::vector<Minisat::Var>> auxiliaries;
    int n = board.size();
    for (int i = 0; i < n; ++i) {
        std::vector<Minisat::Var> tmpAux;
        for (int j = 0; j < n - 1; ++j) {
            tmpAux.push_back(solver.newVar());
        }
        auxiliaries.push_back(tmpAux);
    }
    // Cardinality Constraint, for the problems to be satisfied:
    // Exactly one queen per row (at most 1 and at least one at the same time)
    // Exactly one queen per column (same thing)
    // At most one queen on diagonal
    // Exactly one per row:
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            // if X1 true then S1 must be true and otherwise
            // <=> x1 <=> s1
            // <=> (-x1 v s1) ^ (-s1 v x1)
            if (j == 0) {
                solver.addClause(~Minisat::mkLit(board[i][j]), Minisat::mkLit(auxiliaries[i][j]));
                solver.addClause(~Minisat::mkLit(auxiliaries[i][j]), Minisat::mkLit(board[i][j]));
                continue;
            } 
            // Xn has to be true or Sn-1 has to be true. But they cannot be both true (aka exactly one)
            if (j == n - 1) {
                solver.addClause(Minisat::mkLit(board[i][j]), Minisat::mkLit(auxiliaries[i][j-1]));
                solver.addClause(~Minisat::mkLit(board[i][j]), ~Minisat::mkLit(auxiliaries[i][j-1]));
                continue;
            }
            // if Xi or Si-1 true then Si must be true and otherwise. But Xi and Si-1 cannot both be true
            // <=> ((Xi v Si-1) <-> Si) ^ (-Xi v -Si-1)
            solver.addClause(~Minisat::mkLit(board[i][j]), Minisat::mkLit(auxiliaries[i][j]));
            solver.addClause(~Minisat::mkLit(auxiliaries[i][j-1]), Minisat::mkLit(auxiliaries[i][j]));
            solver.addClause(~Minisat::mkLit(auxiliaries[i][j]), Minisat::mkLit(board[i][j]), Minisat::mkLit(auxiliaries[i][j-1]));
            solver.addClause(~Minisat::mkLit(board[i][j]), ~Minisat::mkLit(auxiliaries[i][j-1])); 
        }
    }
}

void exactlyOnePerColumn(Minisat::Solver &solver, std::vector<std::vector<Minisat::Var>> board) {
    std::vector<std::vector<Minisat::Var>> auxiliaries;
    int n = board.size();

    for (int i = 0; i < n; ++i) {
        std::vector<Minisat::Var> tmpAux;
        for (int j = 0; j < n - 1; ++j) {
            tmpAux.push_back(solver.newVar());
        }
        auxiliaries.push_back(tmpAux);
    }
    // Cardinality Constraint, for the problems to be satisfied:
    // Exactly one queen per row (at most 1 and at least one at the same time)
    // Exactly one queen per column (same thing)
    // At most one queen on diagonal
    // Exactly one per row:
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            // if X1 true then S1 must be true and otherwise
            // <=> x1 <=> s1
            // <=> (-x1 v s1) ^ (-s1 v x1)
            if (j == 0) {
                solver.addClause(~Minisat::mkLit(board[j][i]), Minisat::mkLit(auxiliaries[i][j]));
                solver.addClause(~Minisat::mkLit(auxiliaries[i][j]), Minisat::mkLit(board[j][i]));
                continue;
            } 
            // Xn has to be true or Sn-1 has to be true. But they cannot be both true (aka exactly one)
            if (j == n - 1) {
                solver.addClause(Minisat::mkLit(board[j][i]), Minisat::mkLit(auxiliaries[i][j-1]));
                solver.addClause(~Minisat::mkLit(board[j][i]), ~Minisat::mkLit(auxiliaries[i][j-1]));
                continue;
            }
            // if Xi or Si-1 true then Si must be true and otherwise. But Xi and Si-1 cannot both be true
            // <=> ((Xi v Si-1) <-> Si) ^ (-Xi v -Si-1)
            solver.addClause(~Minisat::mkLit(board[j][i]), Minisat::mkLit(auxiliaries[i][j]));
            solver.addClause(~Minisat::mkLit(auxiliaries[i][j-1]), Minisat::mkLit(auxiliaries[i][j]));
            solver.addClause(~Minisat::mkLit(auxiliaries[i][j]), Minisat::mkLit(board[j][i]), Minisat::mkLit(auxiliaries[i][j-1]));
            solver.addClause(~Minisat::mkLit(board[j][i]), ~Minisat::mkLit(auxiliaries[i][j-1])); 
        }
    }
}

void atMostOnePerDiagonal(Minisat::Solver &solver, std::vector<std::vector<Minisat::Var>> board) {
    //at most one per diagonal 

    int n = board.size();

    //diagonal
    for (int diff = -(n - 2); diff < (n - 1); ++diff) {
        std::vector<Minisat::Var> diagonalVars;
        std::vector<Minisat::Var> diagonalAuxs;
        for (int i = 0; i < n; ++i) {
            int j = i - diff; // Calculate j based on i and the constant difference
            
            // Check if this (i, j) is a valid cell on the board
            if (j >= 0 && j < n) {
                diagonalVars.push_back(board[i][j]);
            }
        }
        for (int i = 0; i < diagonalVars.size() - 1; i++) {
            diagonalAuxs.push_back(solver.newVar());
        }
        for (int i = 0; i < diagonalVars.size(); i++) {
            if (i == 0) {
                solver.addClause(~Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i]));
                solver.addClause(~Minisat::mkLit(diagonalAuxs[i]), Minisat::mkLit(diagonalVars[i]));
                continue;
            }
            if (i == diagonalVars.size() - 1) {
                solver.addClause(~Minisat::mkLit(diagonalVars[i]), ~Minisat::mkLit(diagonalAuxs[i-1]));
                continue;
            }
            solver.addClause(~Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i]));
            solver.addClause(~Minisat::mkLit(diagonalAuxs[i-1]), Minisat::mkLit(diagonalAuxs[i]));
            solver.addClause(~Minisat::mkLit(diagonalAuxs[i]), Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i-1]));
            solver.addClause(~Minisat::mkLit(diagonalVars[i]), ~Minisat::mkLit(diagonalAuxs[i-1]));
        }
    }

    //anti diagonal
    for (int sum = 1; sum < 2 * (n - 1); ++sum) {
        std::vector<Minisat::Var> diagonalVars;
        std::vector<Minisat::Var> diagonalAuxs;
        for (int i = 0; i < n; ++i) {
            int j = sum - i; // Calculate j based on i and the constant sum
            
            // Check if this (i, j) is a valid cell on the board
            if (j >= 0 && j < n) {
                diagonalVars.push_back(board[i][j]);
            }
        }
        for (int i = 0; i < diagonalVars.size() - 1; i++) {
            diagonalAuxs.push_back(solver.newVar());
        }
        for (int i = 0; i < diagonalVars.size(); i++) {
            if (i == 0) {
                solver.addClause(~Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i]));
                solver.addClause(~Minisat::mkLit(diagonalAuxs[i]), Minisat::mkLit(diagonalVars[i]));
                continue;
            }
            if (i == diagonalVars.size() - 1) {
                solver.addClause(~Minisat::mkLit(diagonalVars[i]), ~Minisat::mkLit(diagonalAuxs[i-1]));
                continue;
            }
            solver.addClause(~Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i]));
            solver.addClause(~Minisat::mkLit(diagonalAuxs[i-1]), Minisat::mkLit(diagonalAuxs[i]));
            solver.addClause(~Minisat::mkLit(diagonalAuxs[i]), Minisat::mkLit(diagonalVars[i]), Minisat::mkLit(diagonalAuxs[i-1]));
            solver.addClause(~Minisat::mkLit(diagonalVars[i]), ~Minisat::mkLit(diagonalAuxs[i-1]));
        }
    
    }
}

int main() {
    // Size of the board is NxN, numbers of queens is n. Noted, for n = 2 and n = 3, no solutions exists.
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

    exactlyOnePerRow(solver, board);
    exactlyOnePerColumn(solver, board);
    atMostOnePerDiagonal(solver, board);

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
            } // <-- Error 1: Added the missing closing brace here
            std::cout << std::endl;
        }
    } else {
        std::cout << "unsatisfiable";
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "n=" << n << " Time: " << duration.count() << " ms\n";
    return 0;
}