"""
This module contains the State class and the enums used to define the state space.
"""

from enum import Enum


class ComparableEnum(Enum):
    """
    Modified enum class to easily apply rules on neighbors.
    """

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __add__(self, other):
        if self.__class__ is other.__class__:
            new_value = self.value + other.value
            max_value = max(member.value for member in self.__class__)
            return self.__class__(min(new_value, max_value))
        return NotImplemented

    def __sub__(self, other):
        if self.__class__ is other.__class__:
            new_value = self.value - other.value
            min_value = min(member.value for member in self.__class__)
            return self.__class__(max(new_value, min_value))
        return NotImplemented

    def __abs__(self):
        return abs(self.value)

    def __mul__(self, other):
        if self.__class__ is other.__class__:
            new_value = self.value * other.value
            max_value = max(member.value for member in self.__class__)
            return self.__class__(min(new_value, max_value))
        return NotImplemented

    def __truediv__(self, other):
        if self.__class__ is other.__class__:
            if other.value != 0:
                new_value = self.value / other.value
                min_value = min(member.value for member in self.__class__)
                max_value = max(member.value for member in self.__class__)
                return self.__class__(max(min(new_value, max_value), min_value))
        return NotImplemented

    def __floordiv__(self, other):
        if self.__class__ is other.__class__:
            if other.value != 0:
                new_value = self.value // other.value
                min_value = min(member.value for member in self.__class__)
                max_value = max(member.value for member in self.__class__)
                return self.__class__(max(min(new_value, max_value), min_value))
        return NotImplemented

    def __mod__(self, other):
        if self.__class__ is other.__class__:
            if other.value != 0:
                new_value = self.value % other.value
                return self.__class__(new_value)
        return NotImplemented

    def __pow__(self, power, modulo=None):
        if self.__class__ is power.__class__:
            new_value = pow(self.value, power.value, modulo)
            min_value = min(member.value for member in self.__class__)
            max_value = max(member.value for member in self.__class__)
            return self.__class__(max(min(new_value, max_value), min_value))
        return NotImplemented

    def __max__(self, other):
        if self.__class__ is other.__class__:
            return self.__class__(max(self.value, other.value))
        return NotImplemented

    def __min__(self, other):
        if self.__class__ is other.__class__:
            return self.__class__(min(self.value, other.value))
        return NotImplemented


class Rain(ComparableEnum):
    NONE = 0
    VERY_LIGHT = 1
    LIGHT = 2
    SHOWERS = 3
    RAINY = 4
    HEAVY = 5
    STORM = 6
    FLOOD = 7
    HURRICANE = 8
    HELL = 9


class Landscape(ComparableEnum):
    LAND = 1
    SEA = 2
    ICE = 3
    FOREST = 4
    CITY = 5
    MOUNTAIN = 6


class WindDirection(ComparableEnum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4
    NORTHEAST = 5
    SOUTHEAST = 6
    SOUTHWEST = 7
    NORTHWEST = 8
    NONE = 9


class WindSpeed(ComparableEnum):
    NONE = 0
    SOFT = 1
    BREEZE = 2
    LIGHT = 3
    WINDY = 4
    MODERATE = 5
    MEDIUM = 6
    STRONG = 7
    VERY_STRONG = 8
    HURRICANE = 9


class AirQuality(ComparableEnum):
    CLEAN = 0
    SMOG = 1
    LIGHT = 2
    MODERATE = 3
    MEDIUM = 4
    DAMAGING = 5
    HIGH = 6
    HEAVY = 7
    DEADLY = 8
    MAX = 9

    def __max__(self, other):
        if self.__class__ is other.__class__:
            return self.__class__(max(self.value, other.value))
        return NotImplemented

    __max__ = MAX


class Temperature(ComparableEnum):
    ZERO = 0
    FREEZING = 1
    VERY_COLD = 2
    COLD = 3
    MILD = 4
    NICE = 5
    WARM = 6
    HOT = 7
    HEATWAVE = 8
    HELL = 9
    VERY_HOT = 10
    MAX = 11
    MAX_PLUS = 12
    MAX_PLUS_PLUS = 13
    MAX_PLUS_PLUS_PLUS = 14


class State:
    """
    State class to hold various attributes of a cell.
    In the context of the Cellular Automata, this is the state of a cell.
    The states space is defined by the enums above:
    10 * 10 * 10 * 10 * 6 * 2 * 8 different states from combinations of:
    10 different temperatures,
    10 different wind speeds,
    10 different air qualities,
    10 different rainfalls,
    6 different landscapes.
    2 different cloud states.
    8 different wind directions.
    """

    def __init__(self, land_type, temperature=Temperature.MILD,
                 wind_speed=WindSpeed.NONE,
                 wind_direction=WindDirection.NORTH,
                 rainfall=Rain.NONE,
                 clouds=False, air_pollution=AirQuality.CLEAN):
        self.land_type = land_type
        self.temperature = temperature
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.rainfall = rainfall
        self.clouds = clouds
        self.air_pollution = air_pollution

    def __str__(self):
        return (f"Cell(Land: {self.land_type.name}, Temp: {self.temperature.name}, "
                f"Wind Speed: {self.wind_speed.name}, Wind Direction: {self.wind_direction.name}, "
                f"Rainfall: {self.rainfall}, Clouds: {'Yes' if self.clouds else 'No'}, "
                f"Pollution: {self.air_pollution})")

    def get_state_color(self):
        base_colors = {
            Landscape.SEA: (0, 0, 255),
            Landscape.LAND: (0, 255, 0),
            Landscape.ICE: (255, 255, 255),
            Landscape.FOREST: (0, 100, 0),
            Landscape.CITY: (128, 128, 128),
            Landscape.MOUNTAIN: (139, 69, 19)
        }

        temp_shade = {
            Temperature.VERY_COLD: (0, 0, 255),  # Blue for cold
            Temperature.COLD: (0, 0, 128),
            Temperature.ZERO: (0, 0, 0),  # No color change for zero
            Temperature.MILD: (128, 0, 0),
            Temperature.WARM: (255, 0, 0),  # Red for warm
            Temperature.HOT: (255, 0, 0)
        }

        pollution_shade = {
            AirQuality.CLEAN: 1,
            AirQuality.LIGHT: 0.9,
            AirQuality.MODERATE: 0.8,
            AirQuality.MEDIUM: 0.7,
            AirQuality.HEAVY: 0.8,
            AirQuality.DEADLY: 0.9  # Darker for high pollution
        }

        base_color = base_colors.get(self.land_type, (0, 0, 0))
        temp_color = temp_shade.get(self.temperature, (0, 0, 0))
        pollution_factor = pollution_shade.get(self.air_pollution, 1)

        print(f"temp_color: {temp_color}, pollution_factor: {pollution_factor}")  # Debugging line

        color = tuple(min(int(base * pollution_factor + temp), 255)
                      for base, temp in zip(base_color, temp_color))

        return '#{:02x}{:02x}{:02x}'.format(*color)