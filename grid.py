"""
This module holds the space defining the automation's lauout
"""
import copy
import csv
from CA import Cell
from state import State, Landscape, WindDirection, WindSpeed, Temperature, Rain, AirQuality
from GUI import SimulationGUI
import textwrap
import random
from PIL import Image
from PIL import ImageTk
import math


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

    def draw(self, canvas, cell_size=100):
        canvas.delete("all")
        cell_size = 1006 // max(self.rows, self.cols)

        for y in range(self.rows - 1, -1, -1):
            for x in range(self.cols - 1, -1, -1):
                cell = self.grid[x][y]
                base_color = cell.state.get_state_color()

                # Convert the base color from hex to RGB
                base_color = base_color.lstrip('#')
                base_color = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))

                # Create a gradient effect for 3D illusion
                for i in range(cell_size):
                    intensity = int(255 * (i / cell_size))
                    fill_color = tuple(min(intensity + base, 255) for base in base_color)
                    fill_color_str = '#{:02x}{:02x}{:02x}'.format(*fill_color)
                    canvas.create_rectangle(x * cell_size, y * cell_size + i,
                                            (x + 1) * cell_size, y * cell_size + i + 1,
                                            fill=fill_color_str, outline='')
                shadow_depth = cell_size//4
                # Draw a shadow for 3D illusion
                for i in range(shadow_depth):  # Increase shadow size
                    self.draw_shadow(canvas, cell, x, y, cell_size, shadow_depth, base_color, i)

                    # if clouds, draw random white ovals in light shade of blue
                    if cell.state.clouds and i % 2 == 0:
                        self.draw_clouds(canvas, cell, x, y, cell_size, base_color)


                    if cell.state.land_type == Landscape.CITY:
                        # Draw a city with gray buildings
                        self.draw_building(canvas, cell, x, y, cell_size, shadow_depth)

                    if cell.state.rainfall != Rain.NONE:
                        rain_color = (0, 0, 255)
                        rain_straight = cell.state.rainfall.value
                        rain_size = rain_straight
                        rain_color_str = '#{:02x}{:02x}{:02x}'.format(*rain_color)
                        # if has pollution, make rain color much darker and add pollution color
                        if cell.state.air_pollution != AirQuality.CLEAN:
                            pollution_color = get_pollution_color(cell.state.air_pollution)
                            rain_color = (0, 0, 20)
                            rain_color = tuple(min(c + 50, 255) for c in rain_color)
                            rain_color = tuple(max(c - 50, 0) for c in rain_color)
                            rain_color = tuple(min(c + 50, 255) for c in rain_color)
                            rain_color_str = '#{:02x}{:02x}{:02x}'.format(*rain_color)

                        # Adjust the number of raindrops based on the rainfall strength
                        for _ in range(int(rain_straight)):
                            rain_x = x * cell_size + random.randint(0, cell_size - rain_size)
                            rain_y = y * cell_size + random.randint(0, cell_size - rain_size)
                            # Add a random offset to the end position to make the rain fall in different directions
                            offset = random.randint(-rain_size, rain_size)
                            canvas.create_line(rain_x, rain_y,
                                               rain_x + offset, rain_y + rain_size,
                                               fill=rain_color_str, width=2)


                    if cell.state.land_type == Landscape.FOREST:
                        # Draw a forest with green trees
                        self.draw_tree(canvas, cell, x, y, cell_size, base_color)


                    if cell.state.land_type == Landscape.MOUNTAIN:
                        self.draw_mountains(canvas, cell, x, y, cell_size)

                    if cell.state.land_type == Landscape.ICE:
                        self.draw_ice(canvas, cell, x, y, cell_size)

                        if cell.state.land_type == Landscape.SEA:
                            # Draw a sea with a blue color
                            sea_color = (0, 0, 255)
                            sea_color_str = '#{:02x}{:02x}{:02x}'.format(*sea_color)
                            canvas.create_rectangle(x * cell_size, y * cell_size,
                                                    (x + 1) * cell_size, (y + 1) * cell_size,
                                                    fill=sea_color_str, outline='')
                self.draw_cell_details(canvas, cell, x * cell_size, y * cell_size, cell_size)

    def draw_shadow2(self, canvas, cell, x, y, size, shadow_size, base_color=(0, 0, 0), i = 0):
        # Get the color of the cell edge where the shadow begins
        edge_intensity = int(255 * ((size - shadow_size + i) / size))
        edge_color = tuple(min(edge_intensity + base, 255) for base in base_color)
        # Calculate the shadow color based on the edge color
        intensity = int(50 * ((shadow_size - i) / (shadow_size)))
        shadow_color = tuple(max(base - intensity, 0) for base in edge_color)
        # add dark blue shade to the shadow
        shadow_color_str = '#{:02x}{:02x}{:02x}'.format(*shadow_color)
        # Shadow on the right side of the cell
        canvas.create_rectangle((x + 1) * size - shadow_size + i, y * size,
                                (x + 1) * size - shadow_size + i + 1, (y + 1) * size,
                                fill=shadow_color_str, outline='')
        # Shadow on the bottom side of the cell
        canvas.create_rectangle(x * size, (y + 1) * size - shadow_size + i,
                                (x + 1) * size, (y + 1) * size - shadow_size + i + 1,
                                fill=shadow_color_str, outline='')

    def draw_shadow3(self, canvas, cell, x, y, size, shadow_size, base_color=(0, 0, 0), i = 0):
        """
        draw box
        """
        # Get the color of the cell edge where the shadow begins
        edge_intensity = int(255 * ((size - shadow_size + i) / size))
        edge_color = tuple(min(edge_intensity + base, 255) for base in base_color)
        # Calculate the shadow color based on the edge color
        intensity = int(250 * ((shadow_size - i) / (shadow_size)))
        shadow_color = tuple(max(base - intensity, 0) for base in edge_color)
        # add dark blue shade to the shadow
        shadow_color_str = '#{:02x}{:02x}{:02x}'.format(*shadow_color)
        # Shadow on the right side of the cell
        canvas.create_rectangle((x + 1) * size - shadow_size + i, y * size,
                                (x + 1) * size - shadow_size + i + 1, (y + 1) * size,
                                fill=shadow_color_str, outline='')
        # Shadow on the bottom side of the cell
        canvas.create_rectangle(x * size, (y + 1) * size - shadow_size + i,
                                (x + 1) * size, (y + 1) * size - shadow_size + i + 1,
                                fill=shadow_color_str, outline='')
        # Shadow on the left side of the cell
        canvas.create_rectangle(x * size, y * size,
                                x * size + shadow_size - i, (y + 1) * size,
                                fill=shadow_color_str, outline='')
        # Shadow on the top side of the cell
        canvas.create_rectangle(x * size, y * size,
                                (x + 1) * size, y * size + shadow_size - i,
                                fill=shadow_color_str, outline='')

    def draw_shadow(self, canvas, cell, x, y, size, shadow_size, base_color=(0, 0, 0), i = 0):
        # Get the color of the cell edge where the shadow begins

        edge_intensity = int(185 * ((size - shadow_size + i) / size))
        edge_color = tuple(min(edge_intensity + base, 255) for base in base_color)
        # Calculate the shadow color based on the edge color
        intensity = int(100 * ((shadow_size - i) / (shadow_size)))
        shadow_color = tuple(max(base - intensity, 0) for base in edge_color)
        # add dark blue shade to the shadow
        shadow_color_str = '#{:02x}{:02x}{:02x}'.format(*shadow_color)
        # Create 8 rectangles to form a hexagonal shadow
                # Shadow on the right side of the cell
        # Diagonal rectangle-like polygon
        # Create six polygons to form a hexagonal shadow
        for j in range(6):
            angle = math.pi / 3 * j
            dx = shadow_size * math.cos(angle) * (i) // 57  # Add an offset based on i
            dy = shadow_size * math.sin(angle) * (i) // 57  # Add an offset based on i
            canvas.create_polygon([(x + 0.5) * size + dx + shadow_size * math.cos(angle),
                                   (y + 0.5) * size + dy + shadow_size * math.sin(angle),
                                   (x + 0.5) * size + dx + shadow_size * math.cos(angle + math.pi / 3),
                                   (y + 0.5) * size + dy + shadow_size * math.sin(angle + math.pi / 3),
                                   (x + 0.5) * size + dx + shadow_size * math.cos(angle - math.pi / 3),
                                   (y + 0.5) * size + dy + shadow_size * math.sin(angle - math.pi / 3)],
                                  fill=shadow_color_str, outline='')
        self.draw_shadow3(canvas, cell, x, y, size, shadow_size, base_color, i)

    def draw_ice(self, canvas, cell, x, y, size):
        # Draw a snowflake with a hexagon shape
        snowflake_color = (240, 240, 255)  # Light shade of blue for a cooler look
        snowflake_color_str = '#{:02x}{:02x}{:02x}'.format(*snowflake_color)
        snowflake_size = size // 4  # Smaller snowflake size
        snowflake_x = x * size + size // 2 - snowflake_size // 2  # Center the snowflake in the cell
        snowflake_y = y * size + size // 2 - snowflake_size // 2  # Center the snowflake in the cell
        # Draw a hexagon with the peak at the top
        canvas.create_polygon(snowflake_x, snowflake_y,
                              snowflake_x + snowflake_size, snowflake_y,
                              snowflake_x + 3 * snowflake_size // 2, snowflake_y + snowflake_size,
                              snowflake_x + snowflake_size, snowflake_y + 2 * snowflake_size,
                              snowflake_x, snowflake_y + 2 * snowflake_size,
                              snowflake_x - snowflake_size // 2, snowflake_y + snowflake_size,
                              fill=snowflake_color_str, outline='')

    def draw_mountains(self, canvas, cell, x, y, size):
         # Draw a mountain with a triangle shape
        mountain_color = (205, 133, 63)  # Lighter shade of brown for a cooler look
        mountain_color_str = '#{:02x}{:02x}{:02x}'.format(*mountain_color)
        mountain_height = size // 3  # Smaller mountain height
        mountain_base = size // 3  # Smaller mountain base
        mountain_x = x * size + size // 2 - mountain_base // 2  # Center the mountain in the cell
        mountain_y = y * size + size - mountain_height
        # Draw a triangle with the peak at the top
        canvas.create_polygon(mountain_x, mountain_y,
                              mountain_x + mountain_base, mountain_y,
                              mountain_x + mountain_base // 2, mountain_y - mountain_height,
                              fill=mountain_color_str, outline='')

    def draw_tree(self, canvas, cell, x, y, size, base_color=(0, 100, 0)):
        tree_color = (0, 100, 0)
        tree_color_str = '#{:02x}{:02x}{:02x}'.format(*tree_color)
        tree_size = size // 4  # Smaller tree size
        tree_x = x * size + size // 2 - tree_size // 2  # Center the tree in the cell
        tree_y = y * size + size // 2 - tree_size // 2  # Center the tree in the cell
        # Draw a tree with a rectangle for the trunk and a circle for the crown
        canvas.create_rectangle(tree_x + tree_size // 3, tree_y + tree_size,
                            tree_x + 2 * tree_size // 3, tree_y + 2 * tree_size,
                            fill='brown', outline='')
        canvas.create_oval(tree_x, tree_y,
                        tree_x + tree_size, tree_y + tree_size,
                        fill=tree_color_str, outline='')

        # self.draw_apple_logo(canvas, cell, x, y, size, base_color)

    def draw_apple_logo(self, canvas, cell, x, y, size, base_color=(0, 100, 0)):
        # Define the size and position of the apple
        apple_size = size // 4
        apple_x = x * size + size // 2 - apple_size // 2
        apple_y = y * size + size // 2 - apple_size // 2

        # Draw the main body of the apple
        canvas.create_oval(apple_x, apple_y, apple_x + apple_size, apple_y + apple_size, fill='red', outline='')

        # Draw the top indent of the apple
        indent_size = apple_size // 4
        indent_x1 = apple_x + apple_size // 2 - indent_size // 2
        indent_y1 = apple_y
        indent_x2 = apple_x + apple_size // 2 + indent_size // 2
        indent_y2 = apple_y + indent_size
        canvas.create_arc(indent_x1, indent_y1, indent_x2, indent_y2, start=0, extent=180, fill='red', outline='')
        canvas.create_arc(indent_x1, indent_y1, indent_x2, indent_y2, start=180, extent=180, fill='red', outline='')
        # Define the size and position of the bite
        bite_size = apple_size // 2
        bite_x = apple_x + apple_size - bite_size // 2
        bite_y = apple_y + bite_size // 2

        # Create a gradient effect for the bite
        for i in range(bite_size):
            for j in range(bite_size):
                # Calculate the distance from the center of the bite
                distance = ((i - bite_size // 2) ** 2 + (j - bite_size // 2) ** 2) ** 0.5

                # Only draw the pixel if it's inside the bite
                if distance <= bite_size // 2:
                    intensity = int(255 * (i / bite_size))
                    fill_color = tuple(min(intensity + base, 255) for base in base_color)
                    fill_color_str = '#{:02x}{:02x}{:02x}'.format(*fill_color)
                    canvas.create_rectangle(bite_x + j, bite_y + i,
                                            bite_x + j + 1, bite_y + i + 1,
                                            fill=fill_color_str, outline='')


    def draw_building(self, canvas, cell, x, y, size, shadow_size):
        building_color = (128, 128, 128)
        building_color_str = '#{:02x}{:02x}{:02x}'.format(*building_color)
        building_size = size // 4
        building_x = x * size + size // 2 - building_size // 2  # Center the building in the cell
        building_y = y * size + size // 2 - building_size // 2 + shadow_size  # Center the building in the cell
        canvas.create_rectangle(building_x, building_y,
                            building_x + building_size, building_y + building_size,
                            fill=building_color_str, outline='')

    def draw_clouds(self, canvas, cell, x, y, size, base_color):
        cloud_color = (255, 255, 255)  # White cloud color
        light_base_color = tuple(base + random.randint(0, 50) for base in base_color)  # Light shade of base color
        # make sure values are within 0-255
        light_base_color = tuple(min(max(c, 0), 255) for c in light_base_color)
        cloud_size = random.randint(size // 10, size // 8)  # Smaller cloud size
        cloud_x = x * size + random.randint(0, size - cloud_size)  # Random cloud position
        cloud_y = y * size + random.randint(0, size - cloud_size)  # Random cloud position
        # Blend the cloud color with a light shade of the base color
        blended_color = tuple(int((c1 + c2) / 2) for c1, c2 in zip(cloud_color, light_base_color))
        blended_color_str = '#{:02x}{:02x}{:02x}'.format(*blended_color)
        canvas.create_oval(cloud_x, cloud_y,
                           cloud_x + cloud_size, cloud_y + cloud_size,
                           fill=blended_color_str, outline='')

    def draw_cell_details(self, canvas, cell, x, y, size):
        details_y = y + 22
        text_gap = 16
        font = ('Arial', 10)
        # Larger, bold font for wind information
        wind_font = ('Arial', 10, 'bold')
        shadow_size = size // 4  # Size of the shadow
        text_center = x + 22+ (size - shadow_size) // 2  # Center of the cell excluding the shadow
        text_width = size - 2 * shadow_size  # Width of the cell excluding the shadow

        wrapper = textwrap.TextWrapper(width=text_width)

        land_type_text = f"{cell.state.land_type.name if cell.state.land_type else 'UNKNOWN'}"
        land_type_text = wrapper.fill(land_type_text)
        canvas.create_text(text_center, details_y + text_gap,
                           text=land_type_text, fill='black', font=font)

        temp_text = f"Temp: {cell.state.temperature.name}"
        temp_text = wrapper.fill(temp_text)
        canvas.create_text(text_center, details_y + 2 * text_gap,
                           text=temp_text, fill='black', font=font)

        wind_dir_arrow = get_wind_direction_arrow(cell.state.wind_direction)
        wind_text = f"Wind: {cell.state.wind_speed.name}, Dir: {wind_dir_arrow}"
        wind_text = wrapper.fill(wind_text)
        canvas.create_text(text_center, details_y + 3 * text_gap,
                           text=wind_text, fill='black', font=wind_font)  # larger bold font

        # clouds in new line
        clouds_text = f"Clouds: {cell.state.clouds}"
        clouds_text = wrapper.fill(clouds_text)
        canvas.create_text(text_center, details_y + 4 * text_gap,
                           text=clouds_text, fill='black', font=font)

        rain_text = f"Rain: {cell.state.rainfall.name}"
        rain_text = wrapper.fill(rain_text)
        canvas.create_text(text_center, details_y + 5 * text_gap,
                           text=rain_text, fill='blue', font=font)

        pollution_color = get_pollution_color(cell.state.air_pollution)
        pollution_text = f"Pollution: {cell.state.air_pollution.name}"
        pollution_text = wrapper.fill(pollution_text)
        canvas.create_text(text_center, details_y + 6 * text_gap,
                           text=pollution_text, fill=pollution_color, font=font)
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


def main():
    world = Grid(6, 6)
    world.apply_initial_conditions_csv('enums.csv')
    simulation = SimulationGUI(world)
    simulation.run()


if __name__ == "__main__":
    main()
