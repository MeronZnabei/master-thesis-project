"""
## Script for Convergence Metrics Calculations

This script performs convergence metrics calculations for hypervolume, epsilon progress, and generational distance. It utilizes the EMA Workbench library and a custom Nile model.

### Functions:

- **`get_principle(s)`**: Extracts the principle name from the experiment string.
- **`create_em_model(principle)`**: Creates an EMA Workbench model instance based on the specified principle.
- **`run()`**: Performs convergence metrics calculations for different experiments containing different seeds.

### Usage:

- Define the subfolder names corresponding to different experiments.
- For each experiment, the principle is extracted, and an EMA Workbench model is created.
- Convergence metrics calculations (hypervolume, epsilon progress, and generational distance) are performed for each experiment.

"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ema_workbench import (
    Model,
    RealParameter,
    ScalarOutcome,
    HypervolumeMetric,
    GenerationalDistanceMetric
)
from ema_workbench.em_framework import ArchiveLogger
from ema_workbench.em_framework.optimization import to_problem
from tqdm import tqdm
from experimentation import data_generation
from model.model_nile import ModelNile

def get_principle(s):
    """
    Extract the principle name from the experiment string.
    """
    for principle in ["None", "uwf", "pwf", "gini"]:
        if principle in s:
            return principle
    raise ValueError("Invalid string, principle not recognized.")

def create_em_model(principle):
    """
    Create an EMA Workbench model instance based on the specified principle.
    """
    nile_model = ModelNile(principle=principle)
    nile_model = data_generation.generate_input_data(nile_model, sim_horizon=20)
    
    em_model = Model("NileProblem", function=nile_model)

    parameter_count = nile_model.overarching_policy.get_total_parameter_count()
    n_inputs = nile_model.overarching_policy.functions["release"].n_inputs
    n_outputs = nile_model.overarching_policy.functions["release"].n_outputs
    p_per_RBF = 2 * n_inputs + n_outputs

    lever_list = []
    for i in range(parameter_count):
        modulus = (i - n_outputs) % p_per_RBF
        if (
            (i >= n_outputs)
            and (modulus < (p_per_RBF - n_outputs))
            and (modulus % 2 == 0)
        ):  # centers:
            lever_list.append(RealParameter(f"v{i}", -1, 1))
        else:  # linear parameters for each release, radii, and weights of RBFs:
            lever_list.append(RealParameter(f"v{i}", 0, 1))

    em_model.levers = lever_list

    # specify outcomes
    em_model.outcomes = [
        ScalarOutcome("egypt_agg_deficit_ratio", ScalarOutcome.MINIMIZE),
        ScalarOutcome("egypt_90p_deficit_ratio", ScalarOutcome.MINIMIZE),
        ScalarOutcome("egypt_low_had_frequency", ScalarOutcome.MINIMIZE),
        ScalarOutcome("sudan_agg_deficit_ratio", ScalarOutcome.MINIMIZE),
        ScalarOutcome("sudan_90p_deficit_ratio", ScalarOutcome.MINIMIZE),
        ScalarOutcome("ethiopia_agg_deficit_ratio", ScalarOutcome.MINIMIZE),
    ]
    if principle != "None":
        em_model.outcomes.extend([ScalarOutcome("principle_result", ScalarOutcome.MAXIMIZE)])
    
    return em_model

def run(description:str, experiments:list, n_seeds:int):
    """
    Perform convergence metrics calculations for
    the hypervolumne, epsilon progress and generational distance.
    """
    for experiment in experiments:
        subfolderpath = f"outputs/{experiment}"
        principle = get_principle(experiment)
        em_model = create_em_model(principle)
        problem = to_problem(em_model, searchover="levers")

        # Dictionaries to store results and convergences for different seeds
        results_seeds = {}
        convergences_seeds = {}
        archives_seeds = {}

        for seed in range(n_seeds):
            # Construct the file paths for the results and convergence CSV files for the current experiment.
            results_filepath = f"{subfolderpath}/baseline_results_{experiment}_s{seed}.csv"
            convergence_filepath = f"{subfolderpath}/baseline_convergence_{experiment}_s{seed}.csv"

            # Read the CSV files into DataFrames.
            results_seeds[seed] = pd.read_csv(results_filepath, index_col=0)
            convergences_seeds[seed] = pd.read_csv(convergence_filepath, index_col=[0])

            # Load archives
            archive_path = f"{subfolderpath}/archive_logs/{seed}.tar.gz"
            archives = ArchiveLogger.load_archives(archive_path)

            # Drop the first column from each archive dataframe
            for key in archives:
                archives[key] = archives[key].iloc[:, 1:]
            
            # Append the loaded archives to the main list.
            archives_seeds[seed] = archives

        # Read reference sets from CSV files
        reference_set_filepath = f"{subfolderpath}/baseline_results_{experiment}.csv"
        reference_set = pd.read_csv(reference_set_filepath, index_col=0)

        # Calculate Hypervolume and Generational Distance metrics
        hv = HypervolumeMetric(reference_set, problem)
        gd = GenerationalDistanceMetric(reference_set, problem, d=1)

        metrics_seeds = []

        for seed, archive in archives_seeds.items():
            metrics = []
            for nfe, arch in tqdm(archive.items(), desc="Processing NFEs"):
                scores = {
                    "generational_distance": gd.calculate(arch),
                    "hypervolume": hv.calculate(arch),
                    "nfe": int(nfe)
                }
                metrics.append(scores)
            metrics = pd.DataFrame.from_dict(metrics)
            # Sort metrics by number of function evaluations
            metrics.sort_values(by="nfe", inplace=True)
            metrics_seeds.append(metrics)
            convergence_filename = f"{subfolderpath}/convergence_results_seed{seed}.csv"
            metrics.to_csv(convergence_filename)

        print("--- experiment:", {experiment}, " ---")
        print("em_model and problem created with principle ", {principle}, "and ", len(em_model.outcomes), "outcomes.")
        print(f"Number of elements in 'results': {len(results_seeds)}")
        print(f"Number of elements in 'convergences': {len(convergences_seeds)}")
        print(f"Total number of archives: {len(archives_seeds)}")
        for seed, archive in archives_seeds.items():
            print(f"Archive {seed}: {len(archive)} items")
        print("The number of solutions in the reference set after filtering:", len(reference_set))

        fig, axes = plt.subplots(nrows=3, figsize=(8, 6), sharex=True)
        ax1, ax2, ax3 = axes

        for seed in range(n_seeds):

            ax1.plot(metrics_seeds[seed].nfe, metrics_seeds[seed].hypervolume)
            ax1.set_ylabel("hypervolume")
            
            ax2.plot(convergences_seeds[seed].nfe, convergences_seeds[seed].epsilon_progress)
            ax2.set_ylabel("$\epsilon$ progress")

            ax3.plot(metrics_seeds[seed].nfe, metrics_seeds[seed].generational_distance)
            ax3.set_ylabel("generational distance")

        for ax in axes:
            ax.set_xlabel("nfe")

        sns.despine(fig)

        # Save the figure as a PNG file
        fig.savefig(f"{subfolderpath}/convergence_plot_{description}.png")     

        plt.close(fig)