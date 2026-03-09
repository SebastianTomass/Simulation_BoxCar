# main() file
import random
from statistics import mean, stdev
from simulation import Simulation

def main():
    n_replications = 30
    run_length = 1000

    results = []

    for seed in range(n_replications):
        random.seed(seed)
        simulation = Simulation(simulation_length=run_length, verbose=False)
        simulation.run()
        results.append(simulation.get_kpis())

    print("===== MEAN KPI OVER REPLICATIONS =====")
    print(f"Replications: {n_replications}")
    print(f"Run length: {run_length} hours")

    ab_rates = [r['abandonment_rate'] for r in results]
    pickup_waits = [r['avg_pickup_wait_hours'] for r in results]
    system_times = [r['avg_system_time_hours'] for r in results]
    earnings = [r['avg_driver_earnings_per_hour'] for r in results]
    fairness = [r['fairness_cv'] for r in results]
    idle_props = [r['avg_driver_idle_proportion'] for r in results]

    print(f"Abandonment rate: mean={mean(ab_rates):.4f}, sd={stdev(ab_rates):.4f}")
    print(f"Avg pickup wait (hours): mean={mean(pickup_waits):.4f}, sd={stdev(pickup_waits):.4f}")
    print(f"Avg rider system time (hours): mean={mean(system_times):.4f}, sd={stdev(system_times):.4f}")
    print(f"Avg driver earnings/hour: mean={mean(earnings):.4f}, sd={stdev(earnings):.4f}")
    print(f"Fairness CV: mean={mean(fairness):.4f}, sd={stdev(fairness):.4f}")
    print(f"Avg driver idle proportion: mean={mean(idle_props):.4f}, sd={stdev(idle_props):.4f}")

if __name__ == "__main__":
    main()