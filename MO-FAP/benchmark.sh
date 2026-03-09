#!/bin/bash

# Path to your project folder
PROJECT_DIR="/home/ducnguyen/Work/SAT SOLVER STUFF/MO-FAP"

# 1. Initialize Conda
source "$(conda info --base)/etc/profile.d/conda.sh"

# 2. Activate environment
echo "Activating conda environment: cplex_env..."
conda activate cplex_env

# 3. Move to the project directory
cd "$PROJECT_DIR" || exit

# 4. Run CPLEX Phase
echo "Starting CPLEX Phase..."
# We use the actual filenames on your disk here
python -u cplex.standard.py <<EOF
../BENCHMARK
EOF

echo "CPLEX Phase Complete."
echo "-----------------------------------"

# 5. Run Gurobi Phase
echo "Starting Gurobi Phase..."
python -u gurobi.standard.py <<EOF
../BENCHMARK
EOF

echo "Gurobi Phase Complete. All benchmarks finished."