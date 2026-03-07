from entities import EventCalendar, Rider, Driver, Trip, Queue, EventType
from typing import Tuple
from distributions import Distributions
import math

print("We're in simulation.py")

class Simulation:
    def __init__(self) -> None:
        self.simulation_length = 10
        self.current_time = 0
        self._counter = 1
        self.avg_speed = 20 # avg speed of cab
        
        self.event_calendar  = EventCalendar()
        self.rider_queue     = Queue[Rider]()
        self.driver_queue    = Queue[Driver]()

        # Metrics 
        self.total_riders = 0
        self.abandoned_riders = 0
        self.served_riders = 0

        self.total_wait_time = 0.0

        # add termination to event calendar
        self.event_calendar.add_event(self.simulation_length, event_type=EventType.TERMINATION)

        # create 1st rider
        rider_arrival_time = self.current_time + Distributions.generate_rider_interarival()
        rider_patience_time = rider_arrival_time + Distributions.generate_rider_patience()
        first_rider = Rider(arrival_time=rider_arrival_time,
                             origin=Distributions.generate_location(), 
                             destination=Distributions.generate_location(), 
                             patience_time=rider_patience_time)
        print("first rider arrival:", rider_arrival_time)

        # create 1st driver
        driver_arrival_time = self.current_time + Distributions.generate_driver_interarival()
        driver_shift_time   = driver_arrival_time + Distributions.generate_driver_shift_time()
        first_driver = Driver(driver_id=self._counter,
                               arrival_time=driver_arrival_time,
                               shift_end_time=driver_shift_time,
                               location=Distributions.generate_location())

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
    
    # def matching_algo(self):
    # while rider queue or driver queue is empty
    # keep running matching pattern algo
    # if matched, create Trip instance with rider_id, driver_id, trip_start_time, trip_end_time

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]):
        distance = math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
        return distance


    def matching_algo(self, current_time: float):
        # current_rider = Rider()
        while not self.driver_queue.is_empty() and not self.rider_queue.is_empty():
            current_rider = self.rider_queue.dequeue()
            # waiting time
            wait_time = current_time - current_rider.arrival_time
            self.total_wait_time += wait_time
            self.served_riders += 1
            matched_driver = Driver()
            min_distance_to_driver = float('inf')
            
            for current_driver in self.driver_queue.items.values():
                distance_to_driver = self.calculate_distance(loc1=current_driver.location, loc2=current_rider.origin)
                if distance_to_driver < min_distance_to_driver:
                    min_distance_to_driver = distance_to_driver
                    matched_driver = current_driver
            
            # Matched driver!
            print(f"Rider {current_rider.rider_id} matched with Driver {matched_driver.driver_id}")

            # Calculate Trip end times, update distance to be travelled by driver, 
            distance_driver_to_rider = min_distance_to_driver
            distance_trip            = self.calculate_distance(loc1=current_rider.origin, loc2=current_rider.destination)

            expected_time_driver_to_rider = distance_driver_to_rider/self.avg_speed
            expected_time_trip = distance_trip/self.avg_speed

            estimated_time_driver_to_rider = Distributions.estimated_trip_time(expected_trip_time=expected_time_driver_to_rider)
            estimated_time_trip            = Distributions.estimated_trip_time(expected_trip_time=expected_time_trip)
            
            total_trip_time = estimated_time_driver_to_rider + estimated_time_trip
            estimated_trip_end_time = current_time + total_trip_time

            matched_driver.update_busy_time(busy_time=total_trip_time)
            matched_driver.update_location(new_location=current_rider.destination)
            # Setup the Trip
            new_trip = Trip(driver=matched_driver,
                            rider=current_rider,
                            trip_start_time=current_time,
                            trip_end_time=estimated_trip_end_time,
                            trip_distance=distance_trip)

            # add to event calendar
            self.event_calendar.add_event(time=estimated_trip_end_time, event_type=EventType.TRIP_COMPLETION, data=new_trip)
            self.driver_queue.remove_by_id(item_id=matched_driver.driver_id)
        
        if self.driver_queue.is_empty() and not self.rider_queue.is_empty():
            print("Riders remain in queue")
        
        elif not self.driver_queue.is_empty() and self.rider_queue.is_empty():
            print("Drivers remain in queue")
        else:
            print("Queues served")



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
                print(f"Rider arrival: {next_event.data.rider_id}")
                self.total_riders += 1
                # add to rider queue
                self.rider_queue.enqueue(next_event.data.rider_id, next_event.data)
                print("start matching algo...")
                self.matching_algo(current_time=next_event.time)
                print("moving to next event.....")
                print("-----------------------------------")

                # Add new rider arrival
                # Add new driver arrival
                rider_arrival_time = self.current_time + Distributions.generate_rider_interarival()
                rider_patience_time = rider_arrival_time + Distributions.generate_rider_patience()
                new_rider = Rider(arrival_time=rider_arrival_time,
                                origin=Distributions.generate_location(), 
                                destination=Distributions.generate_location(), 
                                patience_time=rider_patience_time)
                
                # add to event calendar:
                # first rider arrival
                self.event_calendar.add_event(new_rider.arrival_time, event_type=EventType.RIDER_ARRIVAL, data=new_rider)
                # add abandon times as well
                self.event_calendar.add_event(new_rider.patience_time, event_type=EventType.RIDER_ABANDONS, data=new_rider)

            elif next_event.event_type == EventType.DRIVER_ARRIVAL:
                print(f"driver arrival: {next_event.data.driver_id}")
                # add driver to driver queue
                self.driver_queue.enqueue(next_event.data.driver_id, next_event.data)
                print("starting matching algo...")
                self.matching_algo(current_time=next_event.time)
                print("moving to next event..")
                print("-----------------------------------")
                # create 1st driver
                driver_arrival_time = self.current_time + Distributions.generate_driver_interarival()
                driver_shift_time   = driver_arrival_time + Distributions.generate_driver_shift_time()
                new_driver = Driver(driver_id=self._counter,
                                    arrival_time=driver_arrival_time,
                                    shift_end_time=driver_shift_time,
                                    location=Distributions.generate_location())
                self._counter += 1 # to assign id to next driver

                # first driver arrival
                self.event_calendar.add_event(new_driver.arrival_time, event_type=EventType.DRIVER_ARRIVAL, data=new_driver)
                # add driver shift end time
                self.event_calendar.add_event(new_driver.shift_end_time, event_type=EventType.DRIVER_SHIFT_ENDS, data=new_driver)

            elif next_event.event_type == EventType.TRIP_COMPLETION:
                print(f"Trip completion..")
                # Trip completion logic
                trip_data = next_event.data
                driver = trip_data.driver
                # if driver within shift time
                if driver.shift_end_time > trip_data.trip_end_time:
                    # add back to queue
                    self.driver_queue.enqueue(driver.driver_id, driver)
                    # driver.update_location(new_location=)
                # else:
                    # remove driver from system
                    # self.driver_queue.remove_by_id
                    
                print("-----------------------------------")
            
            elif next_event.event_type == EventType.RIDER_ABANDONS:
                # remove rider from queue if available
                remove = self.rider_queue.remove_by_id(next_event.data.rider_id)
                if remove:
                    print(f"Rider abandoned: {next_event.data.rider_id}")
                    self.abandoned_riders += 1
                else:
                    print(f"Rider {next_event.data.rider_id} already served!")

                print("-----------------------------------")
            
            elif next_event.event_type == EventType.DRIVER_SHIFT_ENDS:
                print(f"Driver shift end: {next_event.data.driver_id}")
                print("removing driver from queue...")
                remove = self.driver_queue.remove_by_id(next_event.data.driver_id)
                if remove:
                    print(f"Driver shift abandoning..")
                else:
                    print(f"Driver already out of system!")
                print("-----------------------------------")
            
            elif next_event.event_type == EventType.TERMINATION:
                print("Simulation Termination")

                # Rider abandonment rate
                if self.total_riders > 0:
                    rider_abandonment = self.abandoned_riders / self.total_riders
                else:
                    rider_abandonment = 0

                # Mean rider waiting time
                if self.served_riders > 0:
                    mean_waiting_time = self.total_wait_time / self.served_riders
                else:
                    mean_waiting_time = 0

                print("------ Simulation Metrics ------")
                print(f"Total riders: {self.total_riders}")
                print(f"Served riders: {self.served_riders}")
                print(f"Abandoned riders: {self.abandoned_riders}")
                print(f"Rider abandonment rate: {rider_abandonment:.4f}")
                print(f"Mean rider waiting time: {mean_waiting_time:.4f}")
                print("-----------------------------------")
                return
            else:
                print("Something wrong..")
                print("-----------------------------------")
            
        
        print(self.rider_queue)
        print(self.driver_queue)