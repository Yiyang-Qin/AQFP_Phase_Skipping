import numpy as np
import matplotlib.pyplot as plt
import time
from AQFP_PhaseSkipping import Algorithm

# Parameters
Benchmarks = ["c6288"]  # Benchmark to run
Splitter_Fanout = 4  # Fanout limit
Phase_Skips = 1  # Maximum phase skips
Phases = 8  # Number of phases
num_runs = 10  # Number of times to run the algorithm

# Storage for results
costs = []
times = []
iterations = []

print("Running AQFP Optimization " + str(num_runs) + " times...")

for i in range(num_runs):
    start_time = time.time()
    _, cost, iteration = Algorithm(Benchmarks[0], Splitter_Fanout, Phase_Skips + 1, Phases)
    end_time = time.time()
    run_time = end_time - start_time

    costs.append(cost)
    times.append(run_time)
    iterations.append(iteration)

    # print(f"Run {i + 1}: Cost = {cost}, Time = {run_time:.2f} seconds")

# Print all costs after iterations
print("\nCosts from all runs:")
print(costs)
print([f'{t:.3f}' for t in times])
print(iterations)

# Compute statistics
avg_cost = np.mean(costs)
var_cost = np.var(costs)
avg_time = np.mean(times)
var_time = np.var(times)
avg_iterations = np.mean(iterations)
var_iterations = np.var(iterations)

print("\nFinal Statistics:")
print(f"Average Cost: {avg_cost:.2f}, Variance: {var_cost:.4f}")
print(f"Average Time: {avg_time:.2f} seconds, Variance: {var_time:.4f}")
print(f"Average Iterations: {avg_iterations:.2f}, Variance: {var_iterations:.4f}")

# Plot cost distribution
plt.figure(figsize=(10, 5))
plt.hist(costs, bins=5, edgecolor='black', alpha=0.7)
plt.xlabel("Cost")
plt.ylabel("Frequency")
plt.title("Distribution of Total Buffer/Splitter Costs")
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.show()

# Plot runtime distribution
plt.figure(figsize=(10, 5))
plt.hist(times, bins=5, edgecolor='black', alpha=0.7)
plt.xlabel("Running Time (seconds)")
plt.ylabel("Frequency")
plt.title("Distribution of Running Times")
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.show()

# Plot iteration distribution
plt.figure(figsize=(10, 5))
plt.hist(iterations, bins=5, edgecolor='black', alpha=0.7)
plt.xlabel("Iterations")
plt.ylabel("Frequency")
plt.title("Distribution of Iterations")
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.show()