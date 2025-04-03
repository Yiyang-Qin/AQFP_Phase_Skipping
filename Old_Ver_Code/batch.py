import numpy as np
import matplotlib.pyplot as plt
import time
import os
from AQFP_PhaseSkipping import Algorithm

# Parameters
# Benchmarks = ["c432", "c499", "c880","c1355", "c1908", "c2670", "c3540", "counter16", "counter32", "counter64", "counter128", "mult8"]  # List of benchmarks to run
Benchmarks = ["c7552"]  # List of benchmarks to run
# Benchmarks = ["c5315", "c6288"]  # List of benchmarks to run

Splitter_Fanout = 4  # Fanout limit
Phase_Skips = 2  # Maximum phase skips
Phases = 8  # Number of phases
num_runs = 10  # Number of times to run the algorithm

output_dir = "stats/skip_2"
os.makedirs(output_dir, exist_ok=True)

print("Running AQFP Optimization for multiple benchmarks...")

for benchmark in Benchmarks:
    costs = []
    times = []
    iterations = []
    failed_runs = 0

    print(f"Running benchmark: {benchmark}")

    lowest_cost = float("inf")
    best_iteration = -1

    for i in range(num_runs):
        try:
            print("Running batch No.", i, ": ")
            start_time = time.time()
            _, cost, iteration = Algorithm(benchmark, Splitter_Fanout, Phase_Skips + 1, Phases)
            end_time = time.time()
            run_time = end_time - start_time

            costs.append(cost)
            times.append(run_time)
            iterations.append(iteration)

            if cost < lowest_cost:
                lowest_cost = cost
                best_iteration = iteration

        except FileNotFoundError as e:
            print(f"Warning: Failed to run iteration {i + 1} for benchmark {benchmark} due to missing solution file.")
            failed_runs += 1
            continue

    # Compute statistics
    avg_cost = np.mean(costs)
    var_cost = np.var(costs)
    avg_time = np.mean(times)
    var_time = np.var(times)
    avg_iterations = np.mean(iterations)
    var_iterations = np.var(iterations)

    # Save results to a file
    # output_file = os.path.join(output_dir, f"{benchmark}_le_gt_threshold_95.log")
    output_file = os.path.join(output_dir, f"{benchmark}_shuffle_threshold_50_loops_3.log")
    # output_file = os.path.join(output_dir, f"{benchmark}_0.log")
    with open(output_file, "w") as f:
        f.write(f"Benchmark: {benchmark}\n")
        f.write(f"Runs: {num_runs}\n")
        f.write(f"Failed Runs: {failed_runs}\n")
        f.write(f"Costs: {costs}\n")
        f.write(f"Times: {[f'{t:.3f}' for t in times]}\n")
        f.write(f"Iterations: {iterations}\n")
        f.write(f"\nFinal Statistics:\n")
        f.write(f"Average Cost: {avg_cost:.2f}, Variance: {var_cost:.4f}\n")
        f.write(f"Average Time: {avg_time:.2f} seconds, Variance: {var_time:.4f}\n")
        f.write(f"Average Iterations: {avg_iterations:.2f}, Variance: {var_iterations:.4f}\n")
        f.write(f"Lowest Cost: {lowest_cost}, Best Iteration: {best_iteration}\n")

    print(f"Results saved to {output_file}")