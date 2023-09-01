"""
Main document to run baseline optimization, experiments and tests.
"""
import cProfile
import os

from experimentation import baseline_optimization

if __name__ == '__main__':

    DEBUG = True
    if DEBUG:
        nfe = 5000
        epsilon_list = [3.8, 0.8, 0.3, 1.9, 0.2, 4.2]
        convergence_freq = 250
        description = "None_profiletest"
        principle = "None"
    else:
        nfe = int(os.environ.get("NFE"))
        epsilon_list = [float(epsilon) for epsilon in os.environ.get("EPSILON_LIST").split()]
        convergence_freq = int(os.environ.get("CONVERGENCE_FREQ"))
        description = os.environ.get("DESCRIPTION")
        principle = os.environ.get("PRINCIPLE")

    # Create a profiler object
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    # call the baseline optimization function 'run()' with the provided experiment input
    baseline_optimization.run(nfe, epsilon_list, convergence_freq, description, principle)

    # Stop profiling
    profiler.disable()

    # create the folder if it does not exist
    output_directory = "outputs/profiling"
    os.makedirs(output_directory, exist_ok=True)

    # save the profiling data to a file
    profiler.dump_stats(f"{output_directory}/profiling_data.prof")