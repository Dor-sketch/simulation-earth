"""
This module contains the rules for the simulation.
The rules are defined as a list of dictionaries, each dictionary contains the following keys:
- name: the name of the rule
- enabled: whether the rule is enabled or not - can be changed by the user runtime
- condition: lambada function that receives a neighborhood and returns a boolean value
- action: lambada function that receives a neighborhood and applies the rule's
    action on the cell in the center of the neighborhood

The rules were designed to be as dynamic as possible, so that they can be easily added, removed or modified.
For exaple, the rules avoids setting attributes to the cell, but instead increase or decrease the attribute's value.
That way more than one rule can affect the same attribute in the same iteration.

Note:
While searching for a better way to define the rules, I found the the namedtuple class.
In the end I stuck with the dictionary approach because it allowed dynamic rule enabling/disabling.
namedtuple are immutable, so I couldn't change the enabled value of a rule after it was created.
The namedtuple approach is commented below.
"""
import copy
from state import Landscape, WindDirection, WindSpeed, Temperature, Rain, AirQuality


def get_wind_direction_from_to(from_direction):
    # Maps each direction to the direction it's coming from
    direction_map = {
        WindDirection.NORTH: WindDirection.SOUTH,
        WindDirection.SOUTH: WindDirection.NORTH,
        WindDirection.EAST: WindDirection.WEST,
        WindDirection.WEST: WindDirection.EAST,
        WindDirection.NORTHEAST: WindDirection.SOUTHWEST,
        WindDirection.SOUTHEAST: WindDirection.NORTHWEST,
        WindDirection.SOUTHWEST: WindDirection.NORTHEAST,
        WindDirection.NORTHWEST: WindDirection.SOUTHEAST,
    }
    return direction_map.get(from_direction, WindDirection.NONE)


def change_wind_direction(neighborhood):
    # if wind toward edge, change direction to opposite direction
    if neighborhood['center'].wind_direction not in neighborhood:
        # check if there is a neighbor with opposite direction that has wind towards the cell
        for direction, neighbor in neighborhood.items():
            if direction == 'center':
                continue
            if neighbor and neighbor.wind_direction != get_wind_direction_from_to(direction):
                return get_wind_direction_from_to(direction)
        # move to the highest temperature neighbor
        neighbor_with_highest_temperature = max(
            neighborhood.values(), key=lambda neighbor: neighbor.temperature)
        if neighbor_with_highest_temperature.wind_direction != WindDirection.NONE \
                and neighbor_with_highest_temperature.wind_direction in neighborhood:
            return neighbor_with_highest_temperature.wind_direction

    # if there is a neighbor with no wind, change the wind direction to his direction
    for direction, neighbor in neighborhood.items():
        if direction == 'center':
            continue
        if neighbor and neighbor.wind_speed == WindSpeed.NONE:
            return neighbor.wind_direction

    # if wind is blowing toward a cell with opposite direction, change the wind direction to the opposite direction if there is one
    for direction, neighbor in neighborhood.items():
        if direction == 'center':
            continue
        if neighbor and neighbor.wind_direction == get_wind_direction_from_to(direction):
            if neighborhood.get(get_wind_direction_from_to(direction), None):
                return get_wind_direction_from_to(direction)

    # Get the neighbor with the highest temperature
    neighbor_with_highest_temperature = max(
        neighborhood.values(), key=lambda neighbor: neighbor.temperature)

    # Set the wind direction to the direction of the neighbor with the highest temperature
    return neighbor_with_highest_temperature.wind_direction


def spread_pollution_based_on_wind(neighborhood):
    # Check the wind direction from the neighbor to the cell
    wind_direction = get_wind_direction_from_to(
        neighborhood['center'].wind_direction)

    # If the wind is blowing from the neighbor to the cell, spread the pollution
    if neighborhood.get(wind_direction, None) and neighborhood.get(wind_direction, None).wind_speed > WindSpeed.NONE:
        return neighborhood['center'].air_pollution + AirQuality(1)

    # Otherwise, reduce the pollution
    return neighborhood['center'].air_pollution - AirQuality(1)


def is_wind_blowing_towards_cell(neighborhood):
    opposite_directions = {
        WindDirection.NORTH: WindDirection.SOUTH,
        WindDirection.SOUTH: WindDirection.NORTH,
        WindDirection.EAST: WindDirection.WEST,
        WindDirection.WEST: WindDirection.EAST,
        WindDirection.NORTHEAST: WindDirection.SOUTHWEST,
        WindDirection.SOUTHEAST: WindDirection.NORTHWEST,
        WindDirection.SOUTHWEST: WindDirection.NORTHEAST,
        WindDirection.NORTHWEST: WindDirection.SOUTHEAST,
    }
    # check if the wind is blowing towards the cell in the center from one of its neighbors
    for direction, neighbor in neighborhood.items():
        if direction == 'center':
            continue
        if neighbor and neighbor.wind_direction == opposite_directions.get(direction, WindDirection.NONE):
            return True

    return False


def calculate_wind_speed_change(neighborhood):
    # Calculate wind speed based on neighbors
    for direction, neighbor in neighborhood.items():
        if direction == 'center':
            continue
        if neighbor and is_wind_blowing_towards_cell(neighborhood):
            # Increase wind speed if wind is blowing towards the cell
            return neighborhood['center'].wind_speed + WindSpeed(2)

    # If no wind is blowing towards the cell, decrease its wind speed
    return neighborhood['center'].wind_speed - WindSpeed(1)


class TransitionRules:
    """
    This class contains the rules for the simulation.
    The rules use the context manager protocol to create a neighborhood for the cell.
    The neighborhood is a dictionary of the cell's neighbors, with the cell in the center.
    The rules are applied on the cell in the center of the neighborhood.
    Lambda functions are used to define the rules, so that they can be easily added,
    removed or modified in the rules list.
    """
    rules = [
        # ================ Wind ================
        {
            'name': 'WIND: Dynamic direction Adjustment',
            'enabled': True,
            # Always true, as we always want to adjust wind direction
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_direction', change_wind_direction(neighborhood))
        },
        {
            'name': 'WIND: Dynamic speed Adjustment',
            'enabled': True,
            # Always true, as we always want to adjust wind speed
            'condition': lambda neighborhood: neighborhood['center'].wind_speed > WindSpeed.NONE or is_wind_blowing_towards_cell(neighborhood),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', calculate_wind_speed_change(neighborhood))
        },
        {
            'name': 'WIND: comes from world edges if no wind towards cell',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].wind_speed == WindSpeed.NONE and is_wind_blowing_towards_cell(neighborhood) is False,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', WindSpeed.STRONG)
        },
        {
            'name': 'WIND: Adjust Based on Land Type',
            'enabled': True,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed',
                                                   WindSpeed.STRONG if neighborhood['center'].land_type == Landscape.SEA and all(neighbors.wind_direction == neighborhood['center'].wind_direction for neighbors in neighborhood.values()) and neighborhood['center'].wind_speed == WindSpeed.NONE
                                                   else max(WindSpeed.NONE, neighborhood['center'].wind_speed - WindSpeed(1)) if neighborhood['center'].land_type == Landscape.FOREST
                                                   else neighborhood['center'].wind_speed + WindSpeed(1) if any(neighbor.wind_direction == neighborhood['center'].wind_direction and neighbor.wind_speed > neighborhood['center'].wind_speed for neighbor in neighborhood.values())
                                                   else neighborhood['center'].wind_speed)
        },
        {
            'name': 'WIND: fades if no neighbors have wind and wind speed is greater than 1 or if strongest wind in the neighborhood from center',
            'enabled': True,
            'condition': lambda neighborhood: all(neighbor.wind_speed == WindSpeed.NONE for neighbor in neighborhood.values()) and neighborhood['center'].wind_speed > WindSpeed.NONE or neighborhood['center'].wind_speed == max(neighborhood.values(), key=lambda neighbor: neighbor.wind_speed).wind_speed,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', neighborhood['center'].wind_speed - WindSpeed(1))
        },
        {
            'name': 'WIND: stops if neighbors have no wind or winds come from opposite directions',
            'enabled': True,
            'condition': lambda neighborhood: all(neighbor.wind_speed == WindSpeed.NONE for neighbor in neighborhood.values()) or is_wind_blowing_towards_cell(neighborhood) == False,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', WindSpeed.NONE)
        },
        {
            'name': 'WIND: Conflicts if my neighbors from the same direction dont have wind, reduce my wind',
            'enabled': True,
            'condition': lambda neighborhood: all(neighbor.wind_speed == WindSpeed.NONE for neighbor in neighborhood.values() if neighbor.wind_direction == neighborhood['center'].wind_direction),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', neighborhood['center'].wind_speed - WindSpeed(1))
        },

        # ================ Clouds ================
        {
            'name': 'CLOUDS: Add if one neighbor has clouds and wind direction is towards current cell',
            'enabled': True,
            'condition': lambda neighborhood: any(neighbor.clouds == True for neighbor in neighborhood.values()) and is_wind_blowing_towards_cell(neighborhood),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },
        {
            'name': 'CLOUDS: stop if no neighbors have clouds and current cell has wind',
            'enabled': True,
            'condition': lambda neighborhood: all(neighbor.clouds == False for neighbor in neighborhood.values()) and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', False)
        },
        {
            'name': 'CLOUDS: Formation above the sea when wind speed is above none and temperature is above freezing',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].wind_speed > WindSpeed.NONE and neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].land_type == Landscape.SEA,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },
        {
            'name': 'CLOUDS: moves with the wind',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].clouds is False and is_wind_blowing_towards_cell(neighborhood),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },
        {
            'name': 'CLOUDS: Forests burn cause clouds',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.LAND and neighborhood['center'].temperature > Temperature.ZERO,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },
        # {
        #     'name': 'CLOUDS: Dissipation if no neighbors have clouds and wind speed is greater than 1 or if strongest wind in the neighborhood from center',
        #     'enabled': True,
        #     'condition': lambda neighborhood: neighborhood['center'].clouds and neighborhood['center'].wind_speed > WindSpeed.MODERATE \
        #     and all(neighbor.clouds == False for neighbor in neighborhood.values()) \
        #     or neighborhood['center'].wind_speed == max(neighborhood.values(), key=lambda neighbor: neighbor.wind_speed).wind_speed,
        #     'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', False)
        # },
        {
            'name': 'Clouds: come from the direction of the neighbor with the highest temperature',
            'enabled': True,
            'condition': lambda neighborhood: any(neighbor.temperature > neighborhood['center'].temperature for neighbor in neighborhood.values()),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },

        # ================== Rain ==================
        {
            'name': 'RAIN: stop if no nabors have clouds and current cell has wind',
            'enabled': True,
            'condition': lambda neighborhood: all(neighbor.clouds == False for neighbor in neighborhood.values()) and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', Rain(0))

        },
        {
            'name': 'RAIN: Add if has clouds and wind speed is above none',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].wind_speed > WindSpeed.NONE and neighborhood['center'].clouds == True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', getattr(neighborhood['center'], 'rainfall', 0) + Rain(1))
        },
        {
            'name': 'RAIN: Add if current cell has clouds and at least one neighbor has rain',
            'enabled': True,
            'condition': lambda neighborhood: any(neighbor.rainfall > Rain(0) for neighbor in neighborhood.values()) and neighborhood['center'].clouds == True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', getattr(neighborhood['center'], 'rainfall', 0) + Rain(2))
        },
        {
            'name': 'Rain: Cessation',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].rainfall > Rain.NONE and (neighborhood['center'].wind_speed > WindSpeed.MODERATE or neighborhood['center'].clouds == False),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', Rain.NONE)
        },
        {
            'name': 'Rain: Initiation',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].clouds and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', Rain.SHOWERS)
        },
        {
            'name': 'Rain: Ajdust Based on Temperature',
            'enabled': True,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', Rain(0) if neighborhood['center'].temperature < Temperature.FREEZING else Rain(1) if neighborhood['center'].temperature < Temperature.WARM else Rain(2))
        },

        # ================== AirQuality ==================
        {
            'name': 'AIR: Rain reduces pollution',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution > AirQuality.CLEAN and neighborhood['center'].rainfall > Rain.NONE,
            # Note the enum handles the min / max values
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', max(AirQuality.CLEAN, neighborhood['center'].air_pollution - AirQuality(max(neighborhood['center'].rainfall.value % len(AirQuality), 1))))
        },
        {
            'name': 'AIR: Cities creates pollution add by the number of city neighbors',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.CITY,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', neighborhood['center'].air_pollution + AirQuality(len([neighbor for neighbor in neighborhood.values() if neighbor and neighbor.land_type == Landscape.CITY])))
        },
        {
            'name': 'AIR: Increase pollution based on neighbors pollution and wind direction',
            'enabled': True,
            'condition': lambda neighborhood: any(neighbor.air_pollution > AirQuality(0) for neighbor in neighborhood.values()) and is_wind_blowing_towards_cell(neighborhood),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', neighborhood['center'].air_pollution + AirQuality(max(neighbor.air_pollution.value for neighbor in neighborhood.values())))
        },
        {
            'name': 'AIR: Reduce pollution based on wind speed',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution > AirQuality.CLEAN and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', neighborhood['center'].air_pollution - AirQuality(1))
        },
        {
            'name': 'AIR: Pollution Dispersion',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution > AirQuality.CLEAN and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', spread_pollution_based_on_wind(neighborhood))
        },
        {
            'name': 'AIR: Pollution Dispersion Based on Wind',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution > AirQuality.CLEAN and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', spread_pollution_based_on_wind(neighborhood))
        },

        # ================== Temperature ==================
        {
            'name': 'TEMP: Pollution increases',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution > AirQuality.CLEAN,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature + Temperature(max(neighborhood['center'].air_pollution.value, len(Temperature) - 1)))
        },
        {
            'name': 'TEMP: Forest reduces temperature if at least 3 neighbors have temperature above warm or if its temperature is above warm',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.FOREST and (neighborhood['center'].temperature >= Temperature.WARM or sum(neighbor.temperature > Temperature.WARM for neighbor in neighborhood.values()) >= 3),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature - Temperature(1))
        },
        {
            'name': 'TEMP: low neighbors reduces temperature',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.wind_speed > WindSpeed.NONE for neighbor in neighborhood.values()),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature - Temperature(1))
        },
        {
            'name': 'TEMP: Clouds reduce temperature',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].clouds == True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature - Temperature(1))
        },


        # ================== Land Type ==================
        {
            'name': 'Ice melts if at least 6 neighbors have temperature above freezing or if its temperature is above freezing',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.ICE and (neighborhood['center'].temperature > Temperature.ZERO or sum(neighbor.temperature > Temperature.FREEZING for neighbor in neighborhood.values()) >= 6),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.SEA)
        },
        {
            'name': 'Ice melting cause clouds',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.SEA and neighborhood['center'].temperature > Temperature.ZERO,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'clouds', True)
        },
        {
            'name': 'Forests burn if at least 3 neighbors have temperature above warm or if its temperature is above warm',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].land_type == Landscape.FOREST and (neighborhood['center'].temperature >= Temperature.WARM or sum(neighbor.temperature > Temperature.WARM for neighbor in neighborhood.values()) >= 3),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.LAND)
        },
        {
            'name': 'Land become sea if temperature is above freezing and wind speed is above none and neighbor is sea and current cell is land and rainfall is above 3',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.SEA for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND and neighborhood['center'].rainfall > Rain.STORM,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.SEA)
        },
        {
            'name': 'Sea become land if temperature is HEATWAVE or if doesnt have at least 2 city neighbors',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature == Temperature.HEATWAVE or neighborhood['center'].temperature == Temperature.HOT and sum(neighbor.land_type == Landscape.CITY for neighbor in neighborhood.values()) < 2,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.LAND)
        },
        {
            'name': 'Land become city if temperature is above freezing and wind speed is below Heavy and neighbor cell is forest or see or ciry and current cell is land',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed < WindSpeed.VERY_STRONG and any(neighbor.land_type == Landscape.CITY or neighbor.land_type == Landscape.FOREST or neighbor.land_type == Landscape.SEA for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.CITY)
        },
        {
            'name': 'City become land if temperature is HEATWAVE or if doesnt have at least 2 city neighbors or if pollution is max',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].air_pollution >= AirQuality.MAX or neighborhood['center'].temperature == Temperature.HEATWAVE or
            neighborhood['center'].temperature >= Temperature.HEATWAVE or neighborhood['center'].temperature == Temperature.HOT and sum(
                neighbor.land_type == Landscape.CITY for neighbor in neighborhood.values()) < 2,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.LAND)
        },

        {
            'name': 'Sea become land if temperature is high, no clouds and no rain',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.HOT and neighborhood['center'].clouds == False and neighborhood['center'].rainfall == Rain.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.LAND)
        },
        {
            'name': 'Land become sea if temperature is above freezing and wind speed is above none and neighbor is sea and current cell is land and rainfall is above 3',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.SEA for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND and neighborhood['center'].rainfall > Rain.STORM,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.SEA)
        },
        {
            'name': 'Land become city if temperature is above freezing and wind speed is below Heavy and neighbor cell is forest or see or ciry and current cell is land',
            'enabled': False,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed < WindSpeed.VERY_STRONG and any(neighbor.land_type == Landscape.CITY or neighbor.land_type == Landscape.FOREST or neighbor.land_type == Landscape.SEA for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.CITY)
        },
        {
            'name': 'City become land if temperature is HEATWAVE or if doesnt have at least 2 city neighbors',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature == Temperature.HEATWAVE or neighborhood['center'].temperature == Temperature.HOT and sum(neighbor.land_type == Landscape.CITY for neighbor in neighborhood.values()) < 2,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.LAND)
        },
        {
            'name': 'Land become forest if temperature is above freezing and wind speed is above none and neighbor is forest and current cell is land',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.FOREST for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.FOREST)
        },
        {
            'name': 'land become forest if temperature is above freezing and wind speed is above none and neighbor is forest and current cell is land',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.FOREST for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.FOREST)
        },
        {
            'name': 'Sea become ice if temperature is below freezing and wind speed is above none and neighbor is ice',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature < Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.ICE for neighbor in neighborhood.values()),
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.ICE)
        },
        {
            'name': 'Forest become ice if temperature is zero and wind speed is above none',
            'enabled': False,
            'condition': lambda neighborhood: neighborhood['center'].temperature == Temperature.ZERO and neighborhood['center'].wind_speed > WindSpeed.NONE,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.ICE)
        },
        {
            'name': 'land become sea if temperature is above freezing and wind speed is above none and neighbor is sea and current cell is land and rainfall is above 3',
            'enabled': True,
            'condition': lambda neighborhood: neighborhood['center'].temperature > Temperature.FREEZING and neighborhood['center'].wind_speed > WindSpeed.NONE and any(neighbor.land_type == Landscape.SEA for neighbor in neighborhood.values()) and neighborhood['center'].land_type == Landscape.LAND and neighborhood['center'].rainfall > Rain.STORM,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'land_type', Landscape.SEA)
        },

        # ================== User Testing Rules ==================
        {
            'name': 'manually increase pollution to deadly',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', AirQuality.DEADLY)
        },
        {
            'name': 'manually clear the air',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', AirQuality.CLEAN)
        },
        {
            'name': 'manually increase wind speed by 1',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', neighborhood['center'].wind_speed + WindSpeed(1))
        },
        {
            'name': 'manually decrease wind speed by 1',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'wind_speed', neighborhood['center'].wind_speed - WindSpeed(1))
        },
        {
            'name': 'manually increase temperature by 1',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature + Temperature(1))
        },
        {
            'name': 'manually increase temperature by 2',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'temperature', neighborhood['center'].temperature + Temperature(2))
        },
        {
            'name': 'manually make it rain',
            'enabled': False,
            'condition': lambda neighborhood: True,
            'action': lambda neighborhood: setattr(neighborhood['center'], 'rainfall', Rain.SHOWERS)
        },
    ]

    def __init__(self, cell=None):
        self.enabled_rules = [rule for rule in self.rules if rule['enabled']]
        self.cell = cell
        self.neighborhood = None

    def __enter__(self):
        # Setup code for the context manager (e.g., creating the neighborhood)
        self.neighborhood = {}
        for direction, neighbor in self.cell.neighbors.items():
            if neighbor:
                self.neighborhood[direction] = copy.deepcopy(neighbor.state)
            else:
                self.neighborhood[direction] = None
        self.neighborhood['center'] = copy.deepcopy(self.cell.state)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def apply_rules(self):
        for rule in self.enabled_rules:
            if rule['condition'](self.neighborhood):
                rule['action'](self.neighborhood)
        return self.neighborhood.get('center', None)


# from collections import namedtuple
# Rule = namedtuple('Rule', ['name', 'enabled', 'condition', 'action'])
# rules = [
#     # ================ Catagory ================
#     Rule(
#         name = 'change wind direction to the direction of the neighbor with no wind or highest temperature',
#         enabled = True,
#         condition = lambda neighborhood: any(neighbor.temperature > neighborhood['center'].temperature for neighbor in neighborhood.values()),
#         action = change_wind_direction
#     ),
#     Rule(
#         name= 'Manually clear all pollution',
#         enabled= False,
#         condition= lambda neighborhood: True,
#         action= lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', AirQuality.CLEAN)
#     ),
#     Rule(
#         name= 'Manully increase pollution to deadly',
#         enabled= False,
#         condition= lambda neighborhood: True,
#         action= lambda neighborhood: setattr(neighborhood['center'], 'air_pollution', AirQuality.DEADLY)
#     ),
# ]
