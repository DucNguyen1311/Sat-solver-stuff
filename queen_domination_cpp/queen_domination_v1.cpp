#include <bits/stdc++.h>
#include <minisat/core/Solver.h>
using namespace Minisat;

int incrementalSearch(int k, int n) {
    Minisat::Solver solver;
    std::vector<std::vector<Minisat::Var>> board;
    // initiate the board, each square represent whether that square is conquered (a queen sitting on it or attacking it)
    for (int i = 0; i < n; i++) {
        std::vector<Minisat::Var> tmp;
        for (int j = 0; j < n;j ++) {
            tmp.push_back(solver.newVar());
        }
        board.push_back(tmp);
    }
    
    // Generate the Domination Constraint
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            Minisat::vec<Minisat::Lit> attackList;

            // adding it self as a queen sitting in a square means conquer it.
            attackList.push(Minisat::mkLit(board[i][j]));

            //add all attacking square its rows and column, excluding for itself (already added)
            for (int k = 0; k < n; k++) {
                if (k == j) continue;
                attackList.push(Minisat::mkLit(board[i][k]));
                attackList.push(Minisat::mkLit(board[k][j]));
            }
            //add all attacking square in its diagonal. 
            for (int k = 1; k < n; k++) {
                if (j + k < n && i + k < n) {
                    attackList.push(Minisat::mkLit(board[i + k][j + k]));
                } if (j - k >= 0 && i - k >= 0) {
                    attackList.push(Minisat::mkLit(board[i - k][j - k]));
                } if (j + k < n && i - k >= 0) {
                    attackList.push(Minisat::mkLit(board[i - k][j + k]));
                } if (j - k >= 0 && i + k < n) {
                    attackList.push(Minisat::mkLit(board[i + k][j - k]));
                }
            }

            solver.addClause(attackList);
        }
    }
    //k means we add an at most k constraint on the number of queens place on the board
    //for this example, we will use sequence counter encoding.
    std::vector<std::vector<Minisat::Var>> auxVars;
    std::vector<Minisat::Var> squares;
    // flatten the board
    for (std::vector<Minisat::Var> rows : board) {
        for (Minisat::Var square : rows) {
            squares.push_back(square);
        }
    }

    // initiate the auxVars
    for (int i = 0; i < n * n - 1; i++) {
        std::vector<Minisat::Var> tmp;
        for (int j = 0; j < k; j++) {
            tmp.push_back(solver.newVar());
        }
        auxVars.push_back(tmp);
    }

    // ininitiate for n = 1, if the first square is true then the first auxilary varible is true
    solver.addClause(~Minisat::mkLit(squares[0]), Minisat::mkLit(auxVars[0][0]));
    
    // for the first auxilary varibles row, there are only 1 square so if j > 0 then it is false
    for(int j = 1; j < k; j++) {
        solver.addClause(~Minisat::mkLit(auxVars[0][j]));
    }
    // creating the rest of the counter
    for (int i = 1; i < n * n - 1; i++) {
        // for the first collumn, if the square is true or the previous auxVar is true then the current auxVar is true
        solver.addClause(~Minisat::mkLit(squares[i]), Minisat::mkLit(auxVars[i][0]));
        solver.addClause(~Minisat::mkLit(auxVars[i - 1][0]), Minisat::mkLit(auxVars[i][0]));
        // for the rest of the collumns, if the square and the diagonal previous auxVar is true or the previous auxVar is true then the current auxVar is true
        for (int j = 1; j < k; j++) {
            solver.addClause(~Minisat::mkLit(squares[i]), ~Minisat::mkLit(auxVars[i - 1][j - 1]), Minisat::mkLit(auxVars[i][j]));
            solver.addClause(~Minisat::mkLit(auxVars[i - 1][j]), Minisat::mkLit(auxVars[i][j]));
        }
        // for the at most k constraint, if square i is true then auxVar[i-1][k] must be false
        solver.addClause(~Minisat::mkLit(squares[i]), ~Minisat::mkLit(auxVars[i - 1][k - 1]));
    }
    // for the last square, if that square is true then the previous auxVar[k-1] must be false
    solver.addClause(~Minisat::mkLit(squares[n * n - 1]), ~Minisat::mkLit(auxVars[n * n - 2][k - 1]));

    //solve the problem
    bool isSat = solver.solve();

    if (isSat) {
        std::cout << "satisfiable" << std::endl;
        for (int i = 0; i < board.size(); i++) {
            for (int j = 0; j < board.size(); j++) {
                if (solver.modelValue(board[i][j]) == l_True) {
                    std::cout << "♛ ";
                } else {
                    std::cout << ". ";
                }
            }
            std::cout << std::endl;
        }
        return 1;
    } else {
        return 0;
    }
    return 0;
}


// main function start here
int main() {
    //Size of the board is NxN. 
    int n;
    std::cout << "Enter the size of the board (n x n): ";
    std::cin>>n;
    auto start = std::chrono::high_resolution_clock::now();
    for (int k = 1; k <= n * n; k++) {
        int result = incrementalSearch(k, n);
        if (result == 1) {
            auto end = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = end - start;
            std::cout << "Solved in " << elapsed.count() << " seconds." << std::endl;
            break;
        }
    }

}