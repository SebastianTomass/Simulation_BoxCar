import random
from typing import Tuple

class Distributions:
    def __init__(self) -> None:
        pass

    # ----------------------------
    # Revised arrival / duration assumptions
    # ----------------------------
    @staticmethod
    def generate_rider_interarival() -> float:
        # Revised rider rate = 34.60 / hour
        return random.expovariate(34.60)

    @staticmethod
    def generate_rider_patience() -> float:
        # Keep BoxCar assumption
        return random.expovariate(5)

    @staticmethod
    def generate_driver_interarival() -> float:
        # Revised driver rate = 4.74 / hour
        return random.expovariate(4.74)

    @staticmethod
    def generate_driver_shift_time() -> float:
        # Revised driver online duration
        return random.uniform(6, 8)

    @staticmethod
    def estimated_trip_time(expected_trip_time: float) -> float:
        # Revised travel-time variability
        return random.uniform(0.7 * expected_trip_time, 1.3 * expected_trip_time)

    # ----------------------------
    # Quadrant-based spatial model
    # ----------------------------
    @staticmethod
    def _choose_quadrant(probabilities: Tuple[float, float, float, float]) -> str:
        """
        Order:
        UL, LL, UR, LR
        """
        quadrants = ["UL", "LL", "UR", "LR"]
        return random.choices(quadrants, weights=probabilities, k=1)[0]

    @staticmethod
    def _sample_point_in_quadrant(quadrant: str) -> Tuple[float, float]:
        if quadrant == "UL":
            x = random.uniform(0, 10)
            y = random.uniform(10, 20)
        elif quadrant == "LL":
            x = random.uniform(0, 10)
            y = random.uniform(0, 10)
        elif quadrant == "UR":
            x = random.uniform(10, 20)
            y = random.uniform(10, 20)
        elif quadrant == "LR":
            x = random.uniform(10, 20)
            y = random.uniform(0, 10)
        else:
            raise ValueError("Invalid quadrant")
        return (x, y)

    @staticmethod
    def generate_rider_pickup_location() -> Tuple[float, float]:
        # UL, LL, UR, LR
        probs = (0.446, 0.206, 0.266, 0.082)
        q = Distributions._choose_quadrant(probs)
        return Distributions._sample_point_in_quadrant(q)

    @staticmethod
    def generate_rider_dropoff_location() -> Tuple[float, float]:
        # UL, LL, UR, LR
        probs = (0.289, 0.101, 0.493, 0.118)
        q = Distributions._choose_quadrant(probs)
        return Distributions._sample_point_in_quadrant(q)

    @staticmethod
    def generate_driver_initial_location() -> Tuple[float, float]:
        # UL, LL, UR, LR
        probs = (0.322, 0.184, 0.320, 0.174)
        q = Distributions._choose_quadrant(probs)
        return Distributions._sample_point_in_quadrant(q)
    
    @staticmethod
    def generate_reposition_target_location() -> Tuple[float, float]:
        # send idle drivers toward the upper-left quadrant
        return Distributions._sample_point_in_quadrant("UL")