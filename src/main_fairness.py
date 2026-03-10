import random
from statistics import mean, stdev
from simulation2 import Simulation

def main():
    n_replications = 30
    run_length = 1000

    results = []

    for seed in range(n_replications):
        random.seed(seed)
        simulation = Simulation(
            simulation_length=run_length,
            verbose=False,
            fairness_dispatch_enabled=True,
            repositioning_enabled=False
        )
        simulation.run()
        results.append(simulation.get_kpis())

    metrics = {
        "Abandonment rate": [r['abandonment_rate'] for r in results],
        "Avg pickup wait (hours)": [r['avg_pickup_wait_hours'] for r in results],
        "Avg rider system time (hours)": [r['avg_system_time_hours'] for r in results],
        "Avg driver earnings/hour": [r['avg_driver_earnings_per_hour'] for r in results],
        "Fairness CV": [r['fairness_cv'] for r in results],
        "Avg driver idle proportion": [r['avg_driver_idle_proportion'] for r in results],
    }

    print("===== IMPROVED MODEL: FAIRNESS-AWARE DISPATCH =====")
    print(f"Replications: {n_replications}")
    print(f"Run length: {run_length} hours")

    for name, vals in metrics.items():
        print(f"{name}: mean={mean(vals):.4f}, sd={stdev(vals):.4f}")

if __name__ == "__main__":
    main()