#!/bin/sh
#
#SBATCH --job-name="python_reservoir_sim"
#SBATCH --partition=compute
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48
#SBATCH --mem-per-cpu=1G
#SBATCH --account=research-tpm-mas

module load 2022r2
module load python/3.8.12

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

# Set the desired input parameters as environment variables
export NFE=75000
export EPSILON_LIST="0.001 0.0001 0.0001 0.001 0.0001 0.001"
export CONVERGENCE_FREQ=750
export DESCRIPTION="small"

srun python3 main.py $NFE "$EPSILON_LIST" $CONVERGENCE_FREQ "$DESCRIPTION"
