# import random
from typing import Tuple, Dict, Optional, TypeVar, Generic, Any
from uuid import uuid4, UUID
import heapq
from enum import Enum, auto
from dataclasses import dataclass, field

class Rider:
    def __init__(
            self, 
            arrival_time: float = 0,
            origin: Tuple[float, float] = (0.0, 0.0), 
            destination: Tuple[float, float] = (0.0, 0.0), 
            patience_time: float = 0 ) -> None:
        self.arrival_time  = arrival_time
        self.rider_id      = uuid4()                      # Random UUID to rider
        self.origin        = origin                       # random origin (X0, Y0)
        self.destination   = destination                  # random desitnation (X1, Y1)
        self.patience_time = patience_time                # random patience times


class Driver:
    def __init__(
            self, 
            arrival_time: float = 0, 
            shift_end_time: float = 0, 
            driver_id: int = 0, 
            location: Tuple[float, float] = (0.0, 0.0) ) -> None:
        
        self.arrival_time = arrival_time
        self.driver_id = driver_id
        self.location: Tuple[float, float]  = location
        self.earnings  = 0
        self.distance_travelled = 0
        self.busy_time = 0
        self.num_trips = 0
        self.shift_end_time = shift_end_time
        self.offline_pending = False
        self.actual_offline_time = None
    
    def update_location(self, new_location: Tuple[float, float]) -> None:
        self.location = new_location

    def update_busy_time(self, busy_time: float) -> None:
        self.busy_time += busy_time



class Trip:
    def __init__(self,
                 driver: Driver,
                 rider: Rider,
                 trip_start_time: float,
                 pickup_time: float,
                 pickup_distance: float,
                 trip_distance: float) -> None:
        self.driver = driver
        self.rider = rider
        self.trip_start_time = trip_start_time
        self.pickup_time = pickup_time
        self.pickup_distance = pickup_distance
        self.trip_distance = trip_distance


T = TypeVar('T')
class Queue(Generic[T]):
    def __init__(self) -> None:
        # Using a dictionary to maintain insertion order and allow O(1) lookups
        self.items: Dict[Any, T] = {}

    def enqueue(self, item_id: Any, item: T) -> None:
        """Adds an item to the back of the queue using its ID as the key."""
        self.items[item_id] = item

    def dequeue(self) -> Optional[T]:
        """Removes and returns the item at the front of the queue in O(1) time."""
        if not self.is_empty():
            # next(iter()) grabs the very first key that was inserted
            first_id = next(iter(self.items))
            return self.items.pop(first_id)
        return None

    def remove_by_id(self, item_id: Any) -> Optional[T]:
        """Finds and removes an item instantly in O(1) time."""
        # pop() safely removes the key and returns the value, or returns None if not found
        return self.items.pop(item_id, None)

    def is_empty(self) -> bool:
        """Returns True if the queue is empty."""
        return len(self.items) == 0

    def size(self) -> int:
        """Returns the current number of items in the queue."""
        return len(self.items)

    def top(self) -> Optional[T]:
        """Looks at the first item in the queue without removing it."""
        if not self.is_empty():
            first_id = next(iter(self.items))
            return self.items[first_id]
        return None


# 1. Define the specific events you requested
class EventType(Enum):
    TERMINATION = auto()
    DRIVER_REACHES_PICKUP = auto()
    DRIVER_REACHES_DROPOFF = auto()
    RIDER_ARRIVAL = auto()
    DRIVER_ARRIVAL = auto()
    RIDER_ABANDONS = auto()
    DRIVER_SHIFT_ENDS = auto()

# 2. Define the Event object
@dataclass(order=True)
class Event:
    time: float
    # We use compare=False so the heap only sorts by the 'time' attribute.
    # The 'event_id' is used as a tie-breaker if two events happen at the exact same time.
    event_id: int 
    event_type: EventType = field(compare=False)
    data: Any = field(default=None, compare=False)

# 3. Define the Event Calendar
class EventCalendar:
    def __init__(self) -> None:
        self._events = []
        self._counter = 0  # Used to generate unique event_ids for tie-breaking

    def add_event(self, time: float, event_type: EventType, data: Any = None) -> None:
        """Schedules a new event on the calendar."""
        self._counter += 1
        new_event = Event(time=time, event_id=self._counter, event_type=event_type, data=data)
        heapq.heappush(self._events, new_event)

    def next_event(self) -> Optional[Event]:
        """Pops and returns the chronologically next event to process."""
        if not self.is_empty():
            return heapq.heappop(self._events)
        return None

    def is_empty(self) -> bool:
        """Returns True if there are no pending events."""
        return len(self._events) == 0

    def size(self) -> int:
        """Returns the number of scheduled events."""
        return len(self._events)