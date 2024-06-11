"""
This file contains the main simulation loop and the PygameSimulationGUI class.
"""
import pygame
import sys
import asyncio
from pygame.locals import *
from grid import Grid
from state import *
from CA import *
from rules import TransitionRules
import random
import os

DAYS_PER_YEAR = 365

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')  # Remove '#' at the start of the string
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_ice(screen, rect):
    for _ in range(50):  # Increase the number of ice crystals
        start_pos = (rect.x + random.randint(0, rect.width), rect.y + random.randint(0, rect.height))
        end_pos = (start_pos[0] + random.randint(-3, 3), start_pos[1] + random.randint(-3, 3))  # Decrease the size of the ice crystals
        crystal_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))  # Add some randomness to the color of the ice crystals
        pygame.draw.line(screen, crystal_color, start_pos, end_pos, 1)  # Decrease the thickness of the ice crystals

def draw_clouds(screen, rect, base_color, size, x, y):
    return
    base_color = hex_to_rgb(base_color)
    cloud_color = (255, 255, 255)  # White cloud color
    light_base_color = tuple(base + random.randint(0, 50) for base in base_color)  # Light shade of base color
    # make sure values are within 0-255
    light_base_color = tuple(min(max(c, 0), 255) for c in light_base_color)
    cloud_size = random.randint(size // 10 +2, size // 8+10)  # Smaller cloud size
    cloud_x = x * size + random.randint(2, int(size * 0.8 - cloud_size)+2)  # Random cloud position
    cloud_y = y * size + random.randint(2, int(size * 0.8 - cloud_size)+2)
    # Blend the cloud color with a light shade of the base color
    blended_color = tuple(int((c1 + c2) / 2) for c1, c2 in zip(cloud_color, light_base_color))
    pygame.draw.ellipse(screen, blended_color, (cloud_x, cloud_y, cloud_size, cloud_size))


def draw_rain(screen, rect, intensity, direction):
    direction_map = {
        "NORTH": (0, -1),
        "SOUTH": (0, 1),
        "EAST": (1, 0),
        "WEST": (-1, 0),
        "NORTHEAST": (1, -1),
        "NORTHWEST": (-1, -1),
        "SOUTHEAST": (1, 1),
        "SOUTHWEST": (-1, 1)
    }

    for _ in range(intensity):
        # Vary the color slightly for each raindrop
        rain_color = (0, 0, random.randint(200, 255))

        start_pos = (rect.x + random.randint(0, rect.width), rect.y + random.randint(0, rect.height))
        direction_vector = direction_map.get(direction, (0, 0))

        # Add some randomness to the direction
        direction_vector = (direction_vector[0] + random.uniform(-0.5, 0.5), direction_vector[1] + random.uniform(-0.5, 0.5))

        # Vary the length and thickness of the raindrops based on the direction
        length = random.randint(10, 20)
        if direction in ["EAST", "WEST", "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST"]:
            length = random.randint(5, 10)
        thickness = 2 if direction in ["NORTH", "SOUTH"] else 1

        end_pos = (start_pos[0] + direction_vector[0] * length, start_pos[1] + direction_vector[1] * length)
        pygame.draw.line(screen, rain_color, start_pos, end_pos, thickness)

def draw_3d_rect_stripes(screen, rect, color_hex):
    color = hex_to_rgb(color_hex)
    darker_color = [max(0, c - 50) for c in color]
    lighter_color = [min(255, c + 50) for c in color]

    gradient_name = f"{color_hex}_gradient_stripes.png"
    gradient_path = os.path.join("gradient_images", gradient_name)

    if not os.path.exists(gradient_path):
        # Create surfaces for the darker and lighter colors
        darker_surface = pygame.Surface((rect.width, rect.height))
        lighter_surface = pygame.Surface((rect.width, rect.height))
        darker_surface.fill(darker_color)
        lighter_surface.fill(lighter_color)

        # Create a gradient surface by blending the darker and lighter surfaces
        gradient_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            alpha = int((1 - y / rect.height) * 255)  # Calculate the alpha value based on the y-coordinate
            line_surface = pygame.Surface((rect.width, 1))  # Create a new surface for each line in the gradient

            # Alternate between darker and lighter colors to create a slot-like effect
            if y // 10 % 2 == 0:
                line_surface.fill(lighter_color)  # Fill the line surface with the lighter color
            else:
                line_surface.fill(darker_color)  # Fill the line surface with the darker color

            line_surface.set_alpha(alpha)  # Set the transparency of the line surface
            gradient_surface.blit(line_surface, (0, y))  # Blit the line surface onto the gradient surface

        # Save the gradient surface as an image
        pygame.image.save(gradient_surface, gradient_path)

    # Load the gradient image and draw it onto the screen
    gradient_image = pygame.image.load(gradient_path)
    screen.blit(gradient_image, rect)

def draw_3d_rect(screen, rect, color_hex):
    color = hex_to_rgb(color_hex)
    darker_color = [max(0, c - 100) for c in color]  # Increase the difference for a stronger 3D effect
    lighter_color = [min(255, c + 100) for c in color]  # Increase the difference for a stronger 3D effect

    gradient_name = f"{color_hex}_gradient.png"
    gradient_path = os.path.join("gradient_images", gradient_name)

    if not os.path.exists(gradient_path):
        # Create a gradient surface
        gradient_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        # color it with the darker color
        gradient_surface.fill(darker_color)

        for y in range(rect.height):
            for x in range(rect.width):
                # Calculate distance to the edges of the rectangle
                dist_x = min(x / rect.width, 1 - x / rect.width)
                dist_y = min(y / rect.height, 1 - y / rect.height)
                dist = 1 - min(dist_x, dist_y)

                # Define a threshold where the gradient stops
                threshold = 0.9

                if dist < threshold:
                    # If the distance is less than the threshold, use the lighter color
                    continue
                else:
                    # If the distance is greater than the threshold, interpolate between the darker and lighter color
                    dist = (dist - threshold) / (1 - threshold)  # Normalize dist to the range [0, 1]
                    color = [int(light * (1 - dist) + dark * dist) for light, dark in zip(lighter_color, darker_color)]

                gradient_surface.set_at((x, y), color)  # Set the pixel color on the gradient surface

        # Save the gradient surface as an image
        pygame.image.save(gradient_surface, gradient_path)

    # Load the gradient image and draw it onto the screen
    gradient_image = pygame.image.load(gradient_path)
    screen.blit(gradient_image, rect)


class PygameSimulationGUI:
    def __init__(self, world, width=1400, height=1000):
        # Initialize Pygame
        pygame.display.set_caption("Simulation with Visual Effects")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # Initialize world and GUI state
        self.world = world
        self.dirty = True
        self.is_simulation_running = False
        self.days = 0
        self.years = 0
        self.clean_checkboxes = True

        # Initialize stats and tooltips
        self.stats_history = [[], [], [], []]  # Initialize to empty lists
        self.tooltip_font = pygame.font.Font('Roboto-Regular.ttf', 13)
        self.hovered_cell = None
        self.scroll_offset = 0

        # Initialize images
        self.cell_images = self.load_images()

        # Initialize buttons
        button_spacing = 150
        base_x = 800
        base_y = 300
        self.start_button = pygame.Rect(base_x, base_y, 150, 50)
        self.next_day_button = pygame.Rect(
            base_x + button_spacing, base_y, 150, 50)
        self.export_button = pygame.Rect(
            base_x + 2 * button_spacing, base_y, 150, 50)
        self.reset_button = pygame.Rect(
            base_x + 3 * button_spacing, base_y, 150, 50)

        # Initialize checkboxes
        self.rule_checkboxes = self.setup_rules_checkboxes()

    def reset(self):
        self.world.reset()
        self.days = 0
        self.years = 0

    def get_status_text(self):
        return f"Year: {self.years}, Day: {self.days}"

    async def toggle_simulation(self):
        self.is_simulation_running = not self.is_simulation_running
        while self.is_simulation_running:
            await asyncio.sleep(0)
            self.next_day()

    def next_day(self):
        self.dirty = True
        self.world.next_day()
        self.update_date()

    def update_date(self):
        self.days += 1
        if self.days >= DAYS_PER_YEAR:
            self.years += 1
            self.days = 0

    def draw_buttons(self):
        pygame.draw.rect(self.screen, (0, 128, 0), self.start_button)
        pygame.draw.rect(self.screen, (128, 0, 0), self.next_day_button)
        pygame.draw.rect(self.screen, (0, 0, 128), self.export_button)
        pygame.draw.rect(self.screen, (128, 128, 0), self.reset_button)

        font = pygame.font.Font(None, 36)
        start_text = "Pause" if self.is_simulation_running else "Start"
        start_surface = font.render(start_text, True, (255, 255, 255))
        next_day_surface = font.render("Next Day", True, (255, 255, 255))
        export_surface = font.render("Export", True, (255, 255, 255))
        reset_surface = font.render("Reset", True, (255, 255, 255))
        # Set up buttons
        button_spacing = 150
        button_width = 150
        button_height = 50
        base_x = 800
        base_y = 300

        self.screen.blit(start_surface, (base_x + button_width / 2 - start_surface.get_width() /
                         2, base_y + button_height / 2 - start_surface.get_height() / 2))
        self.screen.blit(next_day_surface, (base_x + button_spacing + button_width / 2 -
                         next_day_surface.get_width() / 2, base_y + button_height / 2 - next_day_surface.get_height() / 2))
        self.screen.blit(export_surface, (base_x + 2 * button_spacing + button_width / 2 -
                         export_surface.get_width() / 2, base_y + button_height / 2 - export_surface.get_height() / 2))
        self.screen.blit(reset_surface, (base_x + 3 * button_spacing + button_width / 2 -
                         reset_surface.get_width() / 2, base_y + button_height / 2 - reset_surface.get_height() / 2))

    def load_images(self):
        cell_width, cell_height = 800 / self.world.cols, self.screen.get_height() / self.world.rows
        cell_images = {}
        for land_type in [Landscape.SEA, Landscape.LAND, Landscape.ICE, Landscape.FOREST, Landscape.CITY]:
            image = pygame.image.load(
                f'./gradient_images/{land_type.name}.png').convert_alpha()
            original_width, original_height = image.get_size()
            aspect_ratio = original_height / original_width
            new_height = int(cell_width * aspect_ratio)

            temp_width = cell_width
            temp_height = cell_height

            if new_height > cell_height:
                aspect_ratio = original_width / original_height
                temp_width = int(cell_height * aspect_ratio)
            else:
                temp_height = new_height

            temp_width = int(temp_width * 0.6)
            temp_height = int(temp_height * 0.6)

            pos_x = (cell_width - temp_width) // 2
            pos_y = (cell_height - temp_height) // 2

            scaled_image = pygame.transform.scale(
                image, (temp_width, temp_height))
            # Store the position as a tuple
            cell_images[land_type] = [scaled_image, (pos_x, pos_y)]
        return cell_images

    def draw_grid(self):
        rows, cols = self.world.rows, self.world.cols
        cell_width, cell_height = 800 / cols, self.screen.get_height() / rows

        for y in range(rows):
            for x in range(cols):
                cell = self.world.grid[y][x]
                rect = pygame.Rect(x * cell_width, y *
                                   cell_height, cell_width, cell_height)
                draw_3d_rect(self.screen, rect, cell.state.get_state_color())
                pack = self.cell_images[cell.state.land_type]
                try:
                    surface, (pos_x, pos_y) = pack
                    self.screen.blit(
                        surface, (x * cell_width + pos_x, y * cell_height + pos_y + 20))
                except TypeError:
                    print(pack)
                if cell.state.land_type == Landscape.ICE:
                    draw_ice(self.screen, rect)
                elif cell.state.land_type == Landscape.CITY:
                    draw_rain(self.screen, rect, 10, "SOUTH")
                    draw_clouds(self.screen, rect,
                                cell.state.get_state_color(), cell_width, x, y)

    def handle_events(self):
        cell_width, cell_height = 800 / self.world.cols, self.screen.get_height() / self.world.rows
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # check if scroll event
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                if self.rule_checkboxes[0]['rect'].y <= 350:
                    self.clean_checkboxes = True
                    self.scroll_offset += 1
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                if self.rule_checkboxes[-1]['rect'].y > self.screen.get_height() - 50:
                    self.clean_checkboxes = True
                    self.scroll_offset -= 1

            elif event.type == pygame.MOUSEMOTION:
                self.dirty = True

                x, y = pygame.mouse.get_pos()
                cell_x, cell_y = int(x // cell_width), int(y // cell_height)
                if cell_y < self.world.rows and cell_x < self.world.cols:
                    self.hovered_cell = self.world.grid[cell_y][cell_x]
                else:
                    self.hovered_cell = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.dirty = True
                if self.start_button.collidepoint(event.pos):
                    asyncio.create_task(self.toggle_simulation())
                elif self.next_day_button.collidepoint(event.pos):
                    self.next_day()
                elif self.export_button.collidepoint(event.pos):
                    pass
                elif self.reset_button.collidepoint(event.pos):
                    self.reset()
                else:
                    self.handle_rule_checkbox_click(event.pos)
                    self.clean_checkboxes = True

    def handle_rule_checkbox_click(self, pos):
        for checkbox in self.rule_checkboxes:
            if checkbox['rect'].collidepoint(pos):
                checkbox['checked'] = not checkbox['checked']
                self.update_rule_state(checkbox['rule'], checkbox['checked'])

    def update_rule_state(self, rule, checked):
        rule['enabled'] = checked

    def setup_rules_checkboxes(self):
        rule_checkboxes = []
        for rule in TransitionRules.rules:
            rule_checkboxes.append({'rule': rule, 'checked': rule['enabled'], 'rect': pygame.Rect(
                800, 350 + len(rule_checkboxes) * 50, 600, 50)})
        return rule_checkboxes

    def draw_checkboxes(self):
        scroll_offset = self.scroll_offset
        font = self.tooltip_font
        mx, my = pygame.mouse.get_pos()
        screen_height = self.screen.get_height()  # Get the height of the screen

        for i, checkbox in enumerate(self.rule_checkboxes):
            checkbox['rect'].y += scroll_offset * 10

            # Check if the checkbox is on the screen
            if checkbox['rect'].y < 350 or checkbox['rect'].y > screen_height:
                continue  # Skip this checkbox if it's not on the screen

            if not checkbox['rect'].collidepoint((mx, my)):
                # Use different colors for checked and unchecked checkboxes
                color_hex = '#008080' if checkbox['checked'] else '#800000'
                draw_3d_rect(self.screen, checkbox['rect'], color_hex)
            text = font.render(
                checkbox['rule']['name'], True, (255, 255, 255), wraplength=450)
            self.screen.blit(
                text, (checkbox['rect'].x + 71, checkbox['rect'].y + 10))

        self.scroll_offset = 0
        self.clean_checkboxes = False

    def draw_tooltip(self):
        if self.hovered_cell is not None:
            tooltip_text = f"Land: {self.hovered_cell.state.land_type.name}\n" \
                           f"Temp: {self.hovered_cell.state.temperature.name}\n" \
                           f"Pollution: {self.hovered_cell.state.air_pollution.name}\n" \
                           f"Wind: {self.hovered_cell.state.wind_direction.name}"
            tooltip_surf = self.tooltip_font.render(
                tooltip_text, True, (255, 255, 255))
            mx, my = pygame.mouse.get_pos()

            # Create a new Surface for the tooltip background
            bg_surf = pygame.Surface(
                (tooltip_surf.get_width() + 20, tooltip_surf.get_height() + 20))

            # Fill the new Surface with a semi-transparent color
            bg_surf.fill((0, 0, 0, 128))  # RGBA color
            bg_surf.set_alpha(128)  # Set the alpha value

            # Blit the new Surface onto the screen
            self.screen.blit(bg_surf, (mx, my))

            # Blit the tooltip text onto the screen
            self.screen.blit(tooltip_surf, (mx + 10, my + 10))

    def draw_date(self):
        font = pygame.font.Font('Roboto-Regular.ttf', 20)
        stat = self.get_world_stats()
        # Turquoise, Hot Pink, Medium Purple, Orange
        colors = [(64, 224, 208), (255, 105, 180),
                  (147, 112, 219), (255, 165, 0)]
        labels = ["Average Temp", "Average Wind",
                  "Average Rainfall", "Average Pollution"]
        rect = pygame.Rect(800, 0, 600, 300)
        draw_3d_rect_stripes(self.screen, rect, '#003366')
        self.draw_title(font)
        self.draw_stats_lines(font, stat, colors)
        self.draw_legend(font, labels, stat, colors)

    def get_world_stats(self):
        return self.world.avg_temperature, self.world.avg_wind_speed, self.world.avg_rainfall, self.world.avg_pollution

    def draw_title(self, font):
        title_text = self.get_status_text()
        title_surf = font.render(title_text, True, (255, 255, 255))
        self.screen.blit(title_surf, (800 + 225, 10))

    def draw_stats_lines(self, font, stat, colors):
        for i, curr_stat in enumerate(stat):
            # Add current stat to history
            self.stats_history[i].append((self.days, curr_stat))
            # If there is more than one stat in history
            if len(self.stats_history[i]) > 1:
                # Draw line for each pair of stats in history
                for j in range(len(self.stats_history[i]) - 1):
                    pygame.draw.line(self.screen, colors[i],
                                     (800 + 100 + self.stats_history[i][j][0],
                                      180 + self.stats_history[i][j][1] * 10),
                                     (800 + 100 + self.stats_history[i][j + 1][0],
                                      180 + self.stats_history[i][j + 1][1] * 10),
                                     2)

    def draw_legend(self, font, labels, stat, colors):
        max_label_width = max(font.size(label)[0] for label in labels) + 50
        max_stat_width = max(font.size(f"{s:.2f}")[0] for s in stat) + 50
        for i, label in enumerate(labels):
            label_text = font.render(label, True, colors[i])
            stat_text = font.render(f"{stat[i]:.2f}", True, colors[i])
            # Adjusted y-coordinate to make room for title
            self.screen.blit(label_text, (800 + 150, 40 + i * 30))
            self.screen.blit(stat_text, (800 + 150 + max_label_width +
                             max_stat_width - font.size(f"{stat[i]:.2f}")[0], 40 + i * 30))

    async def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_grid()
        self.draw_checkboxes()
        self.draw_buttons()
        self.draw_tooltip()
        self.draw_date()

    async def run(self):
        while True:
            self.handle_events()
            await self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    pygame.init()
    # init mixer and set music
    pygame.mixer.init()
    pygame.mixer.music.load('hope.mp3')
    pygame.mixer.music.play(-1)
    world = Grid(6, 6)  # You would use your actual world object here
    world.apply_initial_conditions_csv('enums.csv')

    gui = PygameSimulationGUI(world)
    asyncio.run(gui.run())
