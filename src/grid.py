"""
This module holds the space defining the automation's lauout
"""
import copy
import csv
from CA import Cell
from state import State, Landscape, WindDirection, WindSpeed, Temperature, Rain, AirQuality


def get_wind_direction_arrow(wind_direction):
    direction_arrows = {
        WindDirection.NORTH: '↑',
        WindDirection.NORTHEAST: '↗',
        WindDirection.EAST: '→',
        WindDirection.SOUTHEAST: '↘',
        WindDirection.SOUTH: '↓',
        WindDirection.SOUTHWEST: '↙',
        WindDirection.WEST: '←',
        WindDirection.NORTHWEST: '↖',
    }
    return direction_arrows.get(wind_direction, '')


def get_pollution_color(pollution_level):
    if pollution_level == AirQuality.CLEAN:
        return 'green'
    elif pollution_level == AirQuality.LIGHT:
        return 'yellow'
    elif pollution_level == AirQuality.MEDIUM:
        return 'orange'
    else:
        return 'red'


class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell(State(Landscape.LAND))
                      for _ in range(cols)] for _ in range(rows)]
        self.set_neighbors_for_cells()
        self.statistics = {
            'temperature': [],
            'wind_speed': [],
            'rainfall': [],
            'pollution': []
        }
        self.z_score_temperature = []
        self.z_score_wind_speed = []
        self.z_score_rainfall = []
        self.z_score_pollution = []
        self.days = 1  # number of days passed - samples for statistics
        self.calculate_statistics()

    def get_average_temperature(self):
        return 'gen. avg. temp = {:0.2f} '.format(self.avg_temperature) + \
            '| {} |\n'.format(Temperature(round(self.avg_temperature)).name) + \
            '| z-score = {:0.2f} '.format(self.z_score_temperature[-1]) + \
            '| dev. = {:0.2f} |'.format(self.std_dev_temperature)

    def get_average_wind_speed(self):
        return 'avg. wind speed {:0.2f} '.format(self.avg_wind_speed) + \
            '| {} |\n'.format(WindSpeed(round(self.avg_wind_speed)).name) + \
            '| z-score = {:0.2f} |'.format(self.z_score_wind_speed[-1]) + \
            '| dev. = {:0.2f} |'.format(self.std_dev_wind_speed)

    def get_average_rainfall(self):
        return '{:0.2f} '.format(self.avg_rainfall) + \
            '| {} |\n'.format(Rain(round(self.avg_rainfall)).name) + \
            '| z-score = {:0.2f} |'.format(self.z_score_rainfall[-1]) + \
            '| dev. = {:0.2f} |'.format(self.std_dev_rainfall)

    def get_average_pollution(self):
        return 'avg. Pollution = {:0.2f}'.format(self.avg_pollution) + \
            '| {} |\n'.format(AirQuality(round(self.avg_pollution)).name) + \
            '| z-score = {:0.2f} |'.format(self.z_score_pollution[-1]) + \
            '| dev. = {:0.2f} |'.format(self.std_dev_pollution)

    def calculate_statistics(self):
        total_temperature, total_wind_speed, total_rainfall, total_pollution = 0.0, 0.0, 0.0, 0.0
        temp_squared, wind_squared, rain_squared, pollution_squared = 0.0, 0.0, 0.0, 0.0
        num_cells = self.rows * self.cols

        for row in self.grid:
            for cell in row:
                total_temperature += cell.state.temperature.value
                total_wind_speed += cell.state.wind_speed.value
                total_rainfall += cell.state.rainfall.value
                total_pollution += cell.state.air_pollution.value

                temp_squared += cell.state.temperature.value ** 2
                wind_squared += cell.state.wind_speed.value ** 2
                rain_squared += cell.state.rainfall.value ** 2
                pollution_squared += cell.state.air_pollution.value ** 2

        self.avg_temperature = total_temperature / num_cells
        self.avg_wind_speed = total_wind_speed / num_cells
        self.avg_rainfall = total_rainfall / num_cells
        self.avg_pollution = total_pollution / num_cells

        self.std_dev_temperature = (
            (temp_squared / num_cells - self.avg_temperature ** 2) ** 0.5)
        self.std_dev_wind_speed = (
            (wind_squared / num_cells - self.avg_wind_speed ** 2) ** 0.5)
        self.std_dev_rainfall = (
            (rain_squared / num_cells - self.avg_rainfall ** 2) ** 0.5)
        self.std_dev_pollution = (
            (pollution_squared / num_cells - self.avg_pollution ** 2) ** 0.5)

        self.statistics['temperature'].append(self.avg_temperature)
        self.statistics['wind_speed'].append(self.avg_wind_speed)
        self.statistics['rainfall'].append(self.avg_rainfall)
        self.statistics['pollution'].append(self.avg_pollution)

        if self.std_dev_temperature == 0:
            self.std_dev_temperature = 1
        if self.std_dev_wind_speed == 0:
            self.std_dev_wind_speed = 1
        if self.std_dev_rainfall == 0:
            self.std_dev_rainfall = 1
        if self.std_dev_pollution == 0:
            self.std_dev_pollution = 1

        self.z_score_temperature.append(
            self.avg_temperature - self.std_dev_temperature / self.days)
        self.z_score_wind_speed.append(
            self.avg_wind_speed - self.std_dev_wind_speed / self.days)
        self.z_score_rainfall.append(
            self.avg_rainfall - self.std_dev_rainfall / self.days)
        self.z_score_pollution.append(
            self.avg_pollution - self.std_dev_pollution / self.days)

    def set_neighbors_for_cells(self):
        directions = {
            (-1, -1): WindDirection.NORTHWEST,
            (-1, 0): WindDirection.NORTH,
            (-1, 1): WindDirection.NORTHEAST,
            (0, -1): WindDirection.WEST,
            (0, 1): WindDirection.EAST,
            (1, -1): WindDirection.SOUTHWEST,
            (1, 0): WindDirection.SOUTH,
            (1, 1): WindDirection.SOUTHEAST
        }

        for x in range(self.rows):
            for y in range(self.cols):
                neighbors = {}
                for dx, dy in directions.keys():
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.rows and 0 <= ny < self.cols:
                        neighbors[directions[(dx, dy)]] = self.grid[nx][ny]
                self.grid[x][y].set_neighbors(neighbors)

    def next_day(self):
        new_grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        for row in range(self.rows):
            for col in range(self.cols):
                cell = copy.deepcopy(self.grid[row][col])
                cell.state = cell.update_state()

                new_grid[row][col] = cell
        self.days = self.days + 1
        self.grid = new_grid
        self.calculate_statistics()

    def apply_initial_conditions_csv(self, initial_conditions_file=None,
                                     initial_conditions=None):
        if initial_conditions_file is not None:
            initial_conditions = self.load_initial_conditions_csv(
                initial_conditions_file)
        if initial_conditions is None:
            raise ValueError(
                "Must provide either initial_conditions_file or initial_conditions")

        for condition in initial_conditions:
            try:
                x, y = condition['x'], condition['y']
                self.grid[x][y] = condition['cell']
            except KeyError as e:
                print(
                    f"Error applying initial conditions for cell at ({x}, {y}): Missing key {e}")
            except ValueError as e:
                print(
                    f"Error applying initial conditions for cell at ({x}, {y}): Invalid value - {e}")
            except Exception as e:
                print(
                    f"Unexpected error applying initial conditions for cell at ({x}, {y}): {e}")
        self.set_neighbors_for_cells()
        self.calculate_statistics()

    def export_state_to_csv(self, file_path):
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = ['x', 'y', 'land_type', 'temperature',
                          'wind_speed', 'rainfall', 'air_pollution']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for x in range(self.rows):
                for y in range(self.cols):
                    cell = self.grid[x][y]
                    writer.writerow({
                        'x': x, 'y': y,
                        'land_type': cell.state.land_type.name,
                        'temperature': cell.state.temperature.value,
                        'wind_speed': cell.state.wind_speed.name,
                        'rainfall': cell.state.rainfall.value,
                        'air_pollution': cell.state.air_pollution.value
                    })

    def __str__(self):
        return '\n\n'.join([f"Row {i}\n" + '\n'.join([str(cell) for cell in row])
                            for i, row in enumerate(self.grid, start=1)])

    def reset(self):
        self.grid = [[Cell(State(Landscape.LAND))
                      for _ in range(self.cols)] for _ in range(self.rows)]
        self.set_neighbors_for_cells()
        self.statistics = {
            'temperature': [],
            'wind_speed': [],
            'rainfall': [],
            'pollution': []
        }
        self.z_score_temperature = []
        self.z_score_wind_speed = []
        self.z_score_rainfall = []
        self.z_score_pollution = []
        self.days = 1
        self.apply_initial_conditions_csv('enums.csv')

    def load_initial_conditions_csv(self, file_path='enums.csv'):
        conditions = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Remove spaces from keys and values
                row = {key.strip(): value.strip()
                       for key, value in row.items()}
                try:
                    x = int(row['x'])
                    y = int(row['y'])
                    land_type = Landscape[row['land_type']]
                    temperature = Temperature[row['temperature']]
                    wind_speed = WindSpeed[row['wind_speed']]
                    wind_direction = WindDirection[row['wind_direction']]
                    rainfall = Rain[row['rainfall']]
                    clouds = False  # Default or loaded from CSV if available
                    air_pollution = AirQuality[row['air_pollution']]

                    # Create a State object with the loaded attributes
                    state = State(
                        land_type,
                        temperature,
                        wind_speed,
                        wind_direction,
                        rainfall, clouds, air_pollution)

                    # Create a Cell object with the loaded State
                    cell = Cell(state)

                    conditions.append({
                        'x': x,
                        'y': y,
                        'cell': cell
                    })
                except KeyError as e:
                    print(f"Error processing row: {row}, Error: {e}")
                except ValueError as e:
                    print(f"Error processing row: {row}, Error: {e}")
        return conditions

