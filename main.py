"""
Main document to run baseline optimization, experiments and tests.
"""
import os

from experimentation import baseline_optimization

if __name__ == '__main__':

    DEBUG = False
    if DEBUG:
        nfe = 10000
        epsilon_list = [3.8, 0.8, 0.3, 1.9, 0.2, 4.2]     # delete/add an epsilon when switched from None to a principle
        convergence_freq = 5000
        description = "None_testd"
        principle = "None"           # possible principles uwf, swf, pwf, gini, None
    else:
        # Access the environment variables for input parameters
        nfe = int(os.environ.get("NFE"))
        epsilon_list = [float(epsilon) for epsilon in os.environ.get("EPSILON_LIST").split()]
        convergence_freq = int(os.environ.get("CONVERGENCE_FREQ"))
        description = os.environ.get("DESCRIPTION")
        principle = os.environ.get("PRINCIPLE")

    # call the baseline optimization function 'run()' with the provided experiment input
    baseline_optimization.run(nfe, epsilon_list, convergence_freq, description, principle)
