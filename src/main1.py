# main() file
import random
from statistics import mean
from simulation1 import Simulation

def main():
    n_replications = 30
    run_length = 1000

    results = []

    for seed in range(n_replications):
        random.seed(seed)
        simulation = Simulation(simulation_length=run_length, verbose=False)
        simulation.run()
        results.append(simulation.get_kpis())

    print("===== MEAN KPI OVER REPLICATIONS: REVISED MODEL =====")
    print(f"Replications: {n_replications}")
    print(f"Run length: {run_length} hours")
    print(f"Mean abandonment rate: {mean(r['abandonment_rate'] for r in results):.4f}")
    print(f"Mean avg pickup wait (hours): {mean(r['avg_pickup_wait_hours'] for r in results):.4f}")
    print(f"Mean avg rider system time (hours): {mean(r['avg_system_time_hours'] for r in results):.4f}")
    print(f"Mean avg driver earnings/hour: {mean(r['avg_driver_earnings_per_hour'] for r in results):.4f}")
    print(f"Mean fairness CV: {mean(r['fairness_cv'] for r in results):.4f}")
    print(f"Mean avg driver idle proportion: {mean(r['avg_driver_idle_proportion'] for r in results):.4f}")

if __name__ == "__main__":
    main()