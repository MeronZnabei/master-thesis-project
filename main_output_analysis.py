import os

from output_analysis import convergence

if __name__ == '__main__':

    DEBUG =True
    if DEBUG:
        experiment_name = "principles"
        experiments = ["nfe50000_uwf_001_demand", "nfe50000_pwf_100_demand", "nfe50000_gini_01_demand"]     # delete/add an epsilon when switched from None to a principle
        n_seeds = 5
    else:
        # Access the environment variables for input parameters
        experiment_name = os.environ.get("experiment_name")
        experiments = [str(epsilon) for epsilon in os.environ.get("experiments").split()]

    # calculate convergence metrics for the experiments
    convergence.run(experiment_name, experiments, n_seeds)