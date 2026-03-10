from entities2 import EventCalendar, Rider, Driver, Trip, Queue, EventType
from distributions2 import Distributions
from typing import Tuple
import math

print("We're in simulation.py")

class Simulation:
    def __init__(self, simulation_length: float = 1000, verbose: bool = False, fairness_dispatch_enabled: bool = True, k_nearest: int = 3, repositioning_enabled: bool = True) -> None:
        self.simulation_length = simulation_length
        self.verbose = verbose
        self.current_time = 0
        self._counter = 1
        self.avg_speed = 20 # avg speed of cab
        
        self.event_calendar  = EventCalendar()
        self.rider_queue     = Queue[Rider]()
        self.driver_queue    = Queue[Driver]()

        self.total_rider_requests = 0
        self.total_completed_rides = 0
        self.total_abandonments = 0

        self.total_pickup_wait_time = 0.0
        self.total_system_time = 0.0

        self.fairness_dispatch_enabled = fairness_dispatch_enabled
        self.k_nearest = k_nearest
        self.repositioning_enabled = repositioning_enabled

        self.all_drivers = {}

        # add termination to event calendar
        self.event_calendar.add_event(self.simulation_length, event_type=EventType.TERMINATION)

        # create 1st rider
        rider_arrival_time = self.current_time + Distributions.generate_rider_interarival()
        rider_patience_time = rider_arrival_time + Distributions.generate_rider_patience()
        first_rider = Rider(
            arrival_time=rider_arrival_time,
            origin=Distributions.generate_rider_pickup_location(),
            destination=Distributions.generate_rider_dropoff_location(),
            patience_time=rider_patience_time
        )

        # create 1st driver
        driver_arrival_time = self.current_time + Distributions.generate_driver_interarival()
        driver_shift_time   = driver_arrival_time + Distributions.generate_driver_shift_time()
        first_driver = Driver(
            driver_id=self._counter,
            arrival_time=driver_arrival_time,
            shift_end_time=driver_shift_time,
            location=Distributions.generate_driver_initial_location()
        )
        
        self.all_drivers[first_driver.driver_id] = first_driver

        # add to event calendar:
        # first rider arrival
        self.event_calendar.add_event(first_rider.arrival_time, event_type=EventType.RIDER_ARRIVAL, data=first_rider)
        # add abandon times as well
        self.event_calendar.add_event(first_rider.patience_time, event_type=EventType.RIDER_ABANDONS, data=first_rider)
        
        # first driver arrival
        self.event_calendar.add_event(first_driver.arrival_time, event_type=EventType.DRIVER_ARRIVAL, data=first_driver)
        # add driver shift end time
        self.event_calendar.add_event(first_driver.shift_end_time, event_type=EventType.DRIVER_SHIFT_ENDS, data=first_driver)

        self._counter += 1
    
    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    # def matching_algo(self):
    # while rider queue or driver queue is empty
    # keep running matching pattern algo
    # if matched, create Trip instance with rider_id, driver_id, trip_start_time, trip_end_time

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]):
        distance = math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
        return distance

    def driver_earnings_rate(self, driver: Driver, current_time: float) -> float:
        online_time = max(current_time - driver.arrival_time, 1e-8)
        return driver.earnings / online_time

    def should_reposition(self, driver: Driver) -> bool:
        x, y = driver.location
        # reposition only if driver is in upper-right quadrant
        return x >= 10 and y >= 10

    def matching_algo(self, current_time: float):
        while not self.driver_queue.is_empty() and not self.rider_queue.is_empty():
            current_rider = self.rider_queue.dequeue()

            candidates = []
            for current_driver in self.driver_queue.items.values():
                d = self.calculate_distance(
                    loc1=current_driver.location,
                    loc2=current_rider.origin
                )
                candidates.append((d, current_driver))

            if not candidates:
                self.rider_queue.enqueue(current_rider.rider_id, current_rider)
                return

            # sort by distance first
            candidates.sort(key=lambda x: x[0])

            if self.fairness_dispatch_enabled:
                k = min(self.k_nearest, len(candidates))
                shortlist = candidates[:k]

                # among the k nearest, choose the driver with the lowest earnings/hour so far
                matched_distance, matched_driver = min(
                    shortlist,
                    key=lambda x: (self.driver_earnings_rate(x[1], current_time), x[0])
                )
            else:
                matched_distance, matched_driver = candidates[0]

            self.log(f"Rider {current_rider.rider_id} matched with Driver {matched_driver.driver_id}")

            pickup_distance = matched_distance
            trip_distance = self.calculate_distance(
                loc1=current_rider.origin,
                loc2=current_rider.destination
            )

            expected_time_driver_to_rider = pickup_distance / self.avg_speed
            estimated_time_driver_to_rider = Distributions.estimated_trip_time(
                expected_trip_time=expected_time_driver_to_rider
            )

            pickup_time = current_time + estimated_time_driver_to_rider

            new_trip = Trip(
                driver=matched_driver,
                rider=current_rider,
                trip_start_time=current_time,
                pickup_time=pickup_time,
                pickup_distance=pickup_distance,
                trip_distance=trip_distance
            )

            self.event_calendar.add_event(
                time=pickup_time,
                event_type=EventType.DRIVER_REACHES_PICKUP,
                data=new_trip
            )

            self.driver_queue.remove_by_id(item_id=matched_driver.driver_id)

    def get_kpis(self) -> dict:
        total = self.total_rider_requests
        completed = self.total_completed_rides
        abandoned = self.total_abandonments

        abandonment_rate = abandoned / total if total > 0 else 0.0
        avg_pickup_wait = self.total_pickup_wait_time / completed if completed > 0 else 0.0
        avg_system_time = self.total_system_time / completed if completed > 0 else 0.0

        earnings_per_hour = []
        idle_proportions = []

        for driver in self.all_drivers.values():
            offline_time = driver.actual_offline_time if driver.actual_offline_time is not None else self.current_time
            online_time = max(0.0, offline_time - driver.arrival_time)

            if online_time > 0:
                earnings_per_hour.append(driver.earnings / online_time)
                idle_proportions.append(max(0.0, online_time - driver.busy_time) / online_time)

        avg_driver_earnings_per_hour = (
            sum(earnings_per_hour) / len(earnings_per_hour)
            if earnings_per_hour else 0.0
        )

        avg_idle_proportion = (
            sum(idle_proportions) / len(idle_proportions)
            if idle_proportions else 0.0
        )

        if earnings_per_hour:
            mean_eph = avg_driver_earnings_per_hour
            std_eph = (sum((x - mean_eph) ** 2 for x in earnings_per_hour) / len(earnings_per_hour)) ** 0.5
            fairness_cv = std_eph / mean_eph if mean_eph > 0 else 0.0
        else:
            fairness_cv = 0.0

        return {
            "total_rider_requests": total,
            "completed_rides": completed,
            "abandonments": abandoned,
            "abandonment_rate": abandonment_rate,
            "avg_pickup_wait_hours": avg_pickup_wait,
            "avg_system_time_hours": avg_system_time,
            "avg_driver_earnings_per_hour": avg_driver_earnings_per_hour,
            "fairness_cv": fairness_cv,
            "avg_driver_idle_proportion": avg_idle_proportion,
        }

    def print_kpis(self) -> None:
        kpis = self.get_kpis()

        print("===== KPI SUMMARY =====")
        print(f"Total rider requests: {kpis['total_rider_requests']}")
        print(f"Completed rides: {kpis['completed_rides']}")
        print(f"Abandonments: {kpis['abandonments']}")
        print(f"Abandonment rate: {kpis['abandonment_rate']:.4f}")
        print(f"Average pickup wait (hours): {kpis['avg_pickup_wait_hours']:.4f}")
        print(f"Average rider system time (hours): {kpis['avg_system_time_hours']:.4f}")
        print(f"Average driver earnings per hour: {kpis['avg_driver_earnings_per_hour']:.4f}")
        print(f"Fairness (CV of earnings/hour): {kpis['fairness_cv']:.4f}")
        print(f"Average driver idle proportion: {kpis['avg_driver_idle_proportion']:.4f}")

    def run(self) -> None:
        # print(self.event_calendar.size())

        # print(self.rider_queue.items)
        # print(self.driver_queue.items)

        while  not self.event_calendar.is_empty():
            next_event = self.event_calendar.next_event()

            self.current_time = next_event.time
            if next_event.event_type == EventType.RIDER_ARRIVAL:
                # Start matching algo
                # matching algo until rider queue or driver queue is empty
                self.log(f"Rider arrival: {next_event.data.rider_id}")
                self.total_rider_requests += 1
                # add to rider queue
                self.rider_queue.enqueue(next_event.data.rider_id, next_event.data)
                self.log("start matching algo...")
                self.matching_algo(current_time=next_event.time)
                self.log("moving to next event.....")
                self.log("-----------------------------------")

                # Add new rider arrival
                # Add new driver arrival
                rider_arrival_time = self.current_time + Distributions.generate_rider_interarival()
                rider_patience_time = rider_arrival_time + Distributions.generate_rider_patience()
                new_rider = Rider(
                    arrival_time=rider_arrival_time,
                    origin=Distributions.generate_rider_pickup_location(),
                    destination=Distributions.generate_rider_dropoff_location(),
                    patience_time=rider_patience_time
                )
                
                # add to event calendar:
                # first rider arrival
                self.event_calendar.add_event(new_rider.arrival_time, event_type=EventType.RIDER_ARRIVAL, data=new_rider)
                # add abandon times as well
                self.event_calendar.add_event(new_rider.patience_time, event_type=EventType.RIDER_ABANDONS, data=new_rider)

            elif next_event.event_type == EventType.DRIVER_ARRIVAL:
                self.log(f"driver arrival: {next_event.data.driver_id}")
                # add driver to driver queue
                self.driver_queue.enqueue(next_event.data.driver_id, next_event.data)
                self.log("starting matching algo...")
                self.matching_algo(current_time=next_event.time)
                self.log("moving to next event..")
                self.log("-----------------------------------")
                # create 1st driver
                driver_arrival_time = self.current_time + Distributions.generate_driver_interarival()
                driver_shift_time   = driver_arrival_time + Distributions.generate_driver_shift_time()
                new_driver = Driver(
                    driver_id=self._counter,
                    arrival_time=driver_arrival_time,
                    shift_end_time=driver_shift_time,
                    location=Distributions.generate_driver_initial_location()
                )
                self.all_drivers[new_driver.driver_id] = new_driver
                self._counter += 1 # to assign id to next driver

                # first driver arrival
                self.event_calendar.add_event(new_driver.arrival_time, event_type=EventType.DRIVER_ARRIVAL, data=new_driver)
                # add driver shift end time
                self.event_calendar.add_event(new_driver.shift_end_time, event_type=EventType.DRIVER_SHIFT_ENDS, data=new_driver)

            elif next_event.event_type == EventType.DRIVER_REACHES_PICKUP:
                self.log("Driver reaches pickup..")
                trip_data = next_event.data
                driver = trip_data.driver
                rider = trip_data.rider

                # driver has now actually reached the rider
                driver.update_location(new_location=rider.origin)

                self.total_pickup_wait_time += (self.current_time - rider.arrival_time)

                # compute rider leg travel time
                expected_time_trip = trip_data.trip_distance / self.avg_speed
                estimated_time_trip = Distributions.estimated_trip_time(
                    expected_trip_time=expected_time_trip
                )

                dropoff_time = self.current_time + estimated_time_trip

                # store total busy time now that both legs are known
                total_trip_time = (trip_data.pickup_time - trip_data.trip_start_time) + estimated_time_trip
                driver.update_busy_time(busy_time=total_trip_time)

                self.event_calendar.add_event(
                    time=dropoff_time,
                    event_type=EventType.DRIVER_REACHES_DROPOFF,
                    data=trip_data
                )

                self.log("-----------------------------------")

            elif next_event.event_type == EventType.DRIVER_REACHES_DROPOFF:
                self.log("Driver reaches dropoff..")
                trip_data = next_event.data
                driver = trip_data.driver
                rider = trip_data.rider

                # driver has now actually arrived at destination
                driver.update_location(new_location=rider.destination)

                self.total_completed_rides += 1
                self.total_system_time += (self.current_time - rider.arrival_time)

                # update driver trip stats
                driver.distance_travelled += (trip_data.pickup_distance + trip_data.trip_distance)
                driver.num_trips += 1

                # earnings/costs
                fare = 3 + 2 * trip_data.trip_distance
                petrol_cost = 0.20 * (trip_data.pickup_distance + trip_data.trip_distance)
                driver.earnings += (fare - petrol_cost)

                # decide what happens to driver next
                if driver.offline_pending or self.current_time >= driver.shift_end_time:
                    driver.actual_offline_time = self.current_time
                    self.log(f"Driver {driver.driver_id} goes offline after trip")

                else:
                    # if riders are already waiting, do normal matching immediately
                    if not self.rider_queue.is_empty():
                        self.driver_queue.enqueue(driver.driver_id, driver)
                        self.matching_algo(current_time=self.current_time)

                    # if no riders are waiting, consider repositioning
                    elif self.repositioning_enabled and self.should_reposition(driver):
                        target_location = Distributions.generate_reposition_target_location()
                        reposition_distance = self.calculate_distance(driver.location, target_location)

                        expected_reposition_time = reposition_distance / self.avg_speed
                        reposition_time = Distributions.estimated_trip_time(
                            expected_trip_time=expected_reposition_time
                        )

                        # repositioning is not rest time, so count it as busy/unavailable time
                        driver.update_busy_time(reposition_time)

                        self.event_calendar.add_event(
                            time=self.current_time + reposition_time,
                            event_type=EventType.DRIVER_REPOSITION_COMPLETE,
                            data=(driver, target_location, reposition_distance)
                        )

                        self.log(f"Driver {driver.driver_id} repositioning to {target_location}")

                    else:
                        self.driver_queue.enqueue(driver.driver_id, driver)
                        self.matching_algo(current_time=self.current_time)

            elif next_event.event_type == EventType.DRIVER_REPOSITION_COMPLETE:
                self.log("Driver reposition complete..")

                driver, target_location, reposition_distance = next_event.data

                # reposition has now finished
                driver.update_location(new_location=target_location)

                # repositioning uses fuel and distance
                driver.distance_travelled += reposition_distance
                driver.earnings -= 0.20 * reposition_distance

                if driver.offline_pending or self.current_time >= driver.shift_end_time:
                    driver.actual_offline_time = self.current_time
                    self.log(f"Driver {driver.driver_id} goes offline after reposition")
                else:
                    self.driver_queue.enqueue(driver.driver_id, driver)
                    self.matching_algo(current_time=self.current_time)

                self.log("-----------------------------------")            
            
            elif next_event.event_type == EventType.RIDER_ABANDONS:
                # remove rider from queue if available
                remove = self.rider_queue.remove_by_id(next_event.data.rider_id)
                if remove:
                    self.total_abandonments += 1
                    self.log(f"Rider abandoned: {next_event.data.rider_id}")
                else:
                    self.log(f"Rider {next_event.data.rider_id} already matched or completed")

                self.log("-----------------------------------")
            
            elif next_event.event_type == EventType.DRIVER_SHIFT_ENDS:
                self.log("Driver shift ends..")
                driver = next_event.data

                if driver.driver_id in self.driver_queue.items:
                    self.driver_queue.remove_by_id(driver.driver_id)
                    driver.actual_offline_time = self.current_time
                    self.log(f"Driver {driver.driver_id} leaves immediately")
                else:
                    driver.offline_pending = True
                    self.log(f"Driver {driver.driver_id} will leave after current trip")

                self.log("-----------------------------------")
            
            elif next_event.event_type == EventType.TERMINATION:
                if self.verbose:
                    self.log("Simulation Termination")
                    self.log("-----------------------------------")
                return
            
            else:
                self.log("Something wrong..")
                self.log("-----------------------------------")
            
        
        print(self.rider_queue)
        print(self.driver_queue)