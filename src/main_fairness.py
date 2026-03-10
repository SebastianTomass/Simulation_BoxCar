import random
import math
from statistics import mean, stdev
from simulation2 import Simulation

def summarize_metric(values):
    n = len(values)
    m = mean(values)
    s = stdev(values) if n > 1 else 0.0
    half_width = 1.96 * s / math.sqrt(n) if n > 1 else 0.0
    return {
        "mean": m,
        "sd": s,
        "ci_low": m - half_width,
        "ci_high": m + half_width,
    }

def print_metric_summary(name, values):
    summary = summarize_metric(values)
    print(
        f"{name}: "
        f"mean={summary['mean']:.4f}, "
        f"sd={summary['sd']:.4f}, "
        f"95% CI=({summary['ci_low']:.4f}, {summary['ci_high']:.4f})"
    )

def main():
    n_replications = 30
    run_length = 1000

    results = []

    for seed in range(n_replications):
        random.seed(seed)
        simulation = Simulation(simulation_length=run_length, verbose=False)
        simulation.run()
        results.append(simulation.get_kpis())

    print("===== KPI SUMMARY OVER REPLICATIONS: FAIRNESS EXTENSION =====")
    print(f"Replications: {n_replications}")
    print(f"Run length: {run_length} hours")

    print_metric_summary("Abandonment rate", [r["abandonment_rate"] for r in results])
    print_metric_summary("Avg pickup wait (hours)", [r["avg_pickup_wait_hours"] for r in results])
    print_metric_summary("Avg rider system time (hours)", [r["avg_system_time_hours"] for r in results])
    print_metric_summary("Avg driver earnings/hour", [r["avg_driver_earnings_per_hour"] for r in results])
    print_metric_summary("Fairness CV", [r["fairness_cv"] for r in results])
    print_metric_summary("Avg driver idle proportion", [r["avg_driver_idle_proportion"] for r in results])

if __name__ == "__main__":
    main()