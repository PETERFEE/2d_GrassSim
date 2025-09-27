import pygame
import sys
import math
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# Colors (Pixel Art Style)
COLORS = {
    'grass': (34, 139, 34),
    'dirt': (139, 69, 19),
    'water': (0, 191, 255),
    'player': (255, 0, 0),
    'crop_growing': (0, 128, 0),
    'crop_ready': (255, 215, 0),
    'crop_dead': (139, 0, 0),
    'ui_bg': (50, 50, 50),
    'ui_text': (255, 255, 255),
    'selected': (255, 255, 0),
    'night': (20, 20, 40),
    'day': (135, 206, 235)
}


class CropType(Enum):
    NONE = 0
    TOMATO = 1
    CORN = 2
    CARROT = 3
    NATIVE_FLOWERS = 4
    DROUGHT_GRASS = 5


class ToolType(Enum):
    HOE = 1
    WATERING_CAN = 2
    SEEDS = 3
    HARVEST = 4


class WeatherType(Enum):
    SUNNY = 1
    RAINY = 2
    DROUGHT = 3


@dataclass
class Crop:
    type: CropType
    growth_stage: int
    water_level: int
    health: int
    planted_day: int

    def __init__(self, crop_type: CropType = CropType.NONE):
        self.type = crop_type
        self.growth_stage = 0
        self.water_level = 50
        self.health = 100
        self.planted_day = 0


@dataclass
class Player:
    x: float
    y: float
    inventory: Dict[str, int]
    money: int
    energy: int
    selected_tool: ToolType
    selected_seed: CropType

    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.inventory = {
            'tomato_seeds': 10,
            'corn_seeds': 10,
            'carrot_seeds': 10,
            'native_flower_seeds': 5,
            'drought_grass_seeds': 5,
            'tomatoes': 0,
            'corn': 0,
            'carrots': 0,
            'native_flowers': 0,
            'drought_grass': 0
        }
        self.money = 100
        self.energy = 100
        self.selected_tool = ToolType.HOE
        self.selected_seed = CropType.TOMATO


class GameState:
    def __init__(self):
        self.player = Player()
        self.farm_grid = [[Crop() for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.day = 1
        # Time of day is stored in minutes from midnight. Starts at 6:00 AM.
        self.time_of_day = 360
        self.weather = WeatherType.SUNNY
        self.aquifer_level = 100
        self.score = 0
        self.running = True
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Water conservation mechanics
        self.total_water_used = 0
        self.native_plant_bonus = 0
        self.drought_tolerance_bonus = 0


class PixelArtRenderer:
    def __init__(self, screen, game_state):
        self.screen = screen
        self.game_state = game_state
        self.grass_tile = self.load_grass_tile()

    def load_grass_tile(self):
        """Load grass texture based on current day number. Cycles through grass5.png, grass4.png, etc."""
        # Calculate which grass texture to use based on day number
        # Day 1 = grass5.png, Day 2 = grass4.png, Day 3 = grass3.png, etc.
        grass_number = 5 - ((self.game_state.day - 1) % 5)  # Cycles through 5,4,3,2,1
        
        try:
            return pygame.image.load(f'assets/tiles/grass{grass_number}.png')
        except pygame.error:
            print(f"Warning: Could not load grass{grass_number}.png, using fallback colored rectangle")
            # Create a fallback colored surface
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surface.fill(COLORS['grass'])
            return surface

    def refresh_grass_texture(self):
        """Reload the grass texture when day changes"""
        self.grass_tile = self.load_grass_tile()

    def draw_pixel_character(self, x: int, y: int, color: Tuple[int, int, int]):
        """Draw a simple pixel art character"""
        # Head
        pygame.draw.rect(self.screen, color, (x + 8, y + 4, 16, 16))
        # Body
        pygame.draw.rect(self.screen, color, (x + 10, y + 20, 12, 20))
        # Arms
        pygame.draw.rect(self.screen, color, (x + 4, y + 22, 6, 12))
        pygame.draw.rect(self.screen, color, (x + 22, y + 22, 6, 12))
        # Legs
        pygame.draw.rect(self.screen, color, (x + 10, y + 40, 6, 12))
        pygame.draw.rect(self.screen, color, (x + 16, y + 40, 6, 12))

    def draw_crop(self, x: int, y: int, crop: Crop):
        """Draw pixel art crops based on growth stage using grass.png as base"""
        # Always draw the grass tile as the base
        self.screen.blit(self.grass_tile, (x, y))

        if crop.type == CropType.NONE:
            return

        # NEW: Show health bar ONLY for non-grass crops
        if crop.type != CropType.DROUGHT_GRASS and crop.health < 100:
            health_ratio = crop.health / 100.0
            health_bar_width = int(TILE_SIZE * 0.8 * health_ratio)
            health_bar_color = (0, 255, 0) if health_ratio > 0.5 else (
                (255, 255, 0) if health_ratio > 0.2 else (255, 0, 0))
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (x + TILE_SIZE * 0.1 - 1, y + TILE_SIZE * 0.8 - 1, int(TILE_SIZE * 0.8) + 2, 7))
            pygame.draw.rect(self.screen, health_bar_color,
                             (x + TILE_SIZE * 0.1, y + TILE_SIZE * 0.8, health_bar_width, 5))

        # Draw crop based on type and growth stage on top of grass
        if crop.type == CropType.TOMATO:
            self.draw_tomato_crop(x, y, crop)
        elif crop.type == CropType.CORN:
            self.draw_corn_crop(x, y, crop)
        elif crop.type == CropType.CARROT:
            self.draw_carrot_crop(x, y, crop)
        elif crop.type == CropType.NATIVE_FLOWERS:
            self.draw_native_flowers(x, y, crop)
        elif crop.type == CropType.DROUGHT_GRASS:
            self.draw_drought_grass(x, y, crop)

    def draw_tomato_crop(self, x: int, y: int, crop: Crop):
        """Draw tomato crop pixel art"""
        if crop.growth_stage == 0:  # Seed
            pygame.draw.rect(self.screen, (139, 69, 19), (x + 14, y + 14, 4, 4))
        elif crop.growth_stage == 1:  # Sprout
            pygame.draw.rect(self.screen, (0, 100, 0), (x + 12, y + 12, 8, 8))
        elif crop.growth_stage == 2:  # Growing
            pygame.draw.rect(self.screen, (0, 128, 0), (x + 8, y + 8, 16, 16))
        elif crop.growth_stage == 3:  # Ready
            pygame.draw.rect(self.screen, (255, 0, 0), (x + 6, y + 6, 20, 20))

    def draw_corn_crop(self, x: int, y: int, crop: Crop):
        """Draw corn crop pixel art"""
        if crop.growth_stage == 0:  # Seed
            pygame.draw.rect(self.screen, (139, 69, 19), (x + 14, y + 14, 4, 4))
        elif crop.growth_stage == 1:  # Sprout
            pygame.draw.rect(self.screen, (0, 100, 0), (x + 12, y + 12, 8, 8))
        elif crop.growth_stage == 2:  # Growing
            pygame.draw.rect(self.screen, (0, 128, 0), (x + 8, y + 4, 16, 24))
        elif crop.growth_stage == 3:  # Ready
            pygame.draw.rect(self.screen, (255, 215, 0), (x + 6, y + 2, 20, 28))

    def draw_carrot_crop(self, x: int, y: int, crop: Crop):
        """Draw carrot crop pixel art"""
        if crop.growth_stage == 0:  # Seed
            pygame.draw.rect(self.screen, (139, 69, 19), (x + 14, y + 14, 4, 4))
        elif crop.growth_stage == 1:  # Sprout
            pygame.draw.rect(self.screen, (0, 100, 0), (x + 12, y + 12, 8, 8))
        elif crop.growth_stage == 2:  # Growing
            pygame.draw.rect(self.screen, (0, 128, 0), (x + 10, y + 10, 12, 12))
        elif crop.growth_stage == 3:  # Ready
            pygame.draw.rect(self.screen, (255, 140, 0), (x + 8, y + 8, 16, 16))

    def draw_native_flowers(self, x: int, y: int, crop: Crop):
        """Draw native flowers pixel art"""
        if crop.growth_stage == 0:  # Seed
            pygame.draw.rect(self.screen, (139, 69, 19), (x + 14, y + 14, 4, 4))
        elif crop.growth_stage == 1:  # Sprout
            pygame.draw.rect(self.screen, (0, 100, 0), (x + 12, y + 12, 8, 8))
        elif crop.growth_stage == 2:  # Growing
            pygame.draw.rect(self.screen, (0, 128, 0), (x + 8, y + 8, 16, 16))
        elif crop.growth_stage == 3:  # Ready
            # Colorful flowers
            pygame.draw.rect(self.screen, (255, 0, 255), (x + 6, y + 6, 20, 20))
            pygame.draw.rect(self.screen, (255, 255, 0), (x + 8, y + 8, 16, 16))

    def draw_drought_grass(self, x: int, y: int, crop: Crop):
        """Draw drought-resistant grass based on its 7-stage health."""
        health_colors = {
            7: (34, 139, 34),  # Lush Green
            6: (50, 150, 50),  # Healthy Green
            5: (107, 142, 35),  # Olive
            4: (154, 205, 50),  # Yellow Green
            3: (205, 133, 63),  # Light Brown
            2: (189, 183, 107),  # Khaki
            1: (139, 69, 19),  # Dead Brown
        }

        # Get the color for the current health, defaulting to dead color if not found
        color = health_colors.get(crop.health, health_colors[1])

        # Draw simple grass blades that change color
        pygame.draw.rect(self.screen, color, (x + 6, y + 6, 20, 20))
        pygame.draw.rect(self.screen, tuple(c * 0.8 for c in color), (x + 10, y + 10, 12, 12))  # Darker center


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RootDown Valley - Drought-Tolerant Farming")
        self.state = GameState()
        self.renderer = PixelArtRenderer(self.screen, self.state)

    def handle_input(self):
        """Handle player input for continuous movement"""
        keys = pygame.key.get_pressed()

        # Character movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.state.player.x = max(0, self.state.player.x - 2)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.state.player.x = min(SCREEN_WIDTH - TILE_SIZE, self.state.player.x + 2)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.state.player.y = max(0, self.state.player.y - 2)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.state.player.y = min(SCREEN_HEIGHT - TILE_SIZE, self.state.player.y + 2)

    def handle_events(self):
        """Handle discrete pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False

            elif event.type == pygame.KEYDOWN:
                # Tool selection
                if event.key == pygame.K_1:
                    self.state.player.selected_tool = ToolType.HOE
                elif event.key == pygame.K_2:
                    self.state.player.selected_tool = ToolType.WATERING_CAN
                elif event.key == pygame.K_3:
                    self.state.player.selected_tool = ToolType.SEEDS
                elif event.key == pygame.K_4:
                    self.state.player.selected_tool = ToolType.HARVEST

                # Seed selection
                elif event.key == pygame.K_q:
                    self.state.player.selected_seed = CropType.TOMATO
                elif event.key == pygame.K_e:
                    self.state.player.selected_seed = CropType.CORN
                elif event.key == pygame.K_r:
                    self.state.player.selected_seed = CropType.CARROT
                elif event.key == pygame.K_t:
                    self.state.player.selected_seed = CropType.NATIVE_FLOWERS
                elif event.key == pygame.K_y:
                    self.state.player.selected_seed = CropType.DROUGHT_GRASS

                # Action key
                elif event.key == pygame.K_SPACE:
                    self.perform_action()

                # Day management controls
                elif event.key == pygame.K_n:
                    self.next_day()  # Next day (single day advance)

    def perform_action(self):
        """Perform action based on selected tool"""
        # Center of the player for more accurate tile selection
        player_center_x = self.state.player.x + TILE_SIZE / 2
        player_center_y = self.state.player.y + TILE_SIZE / 2

        grid_x = int(player_center_x // TILE_SIZE)
        grid_y = int(player_center_y // TILE_SIZE)

        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            tile = self.state.farm_grid[grid_y][grid_x]

            if self.state.player.selected_tool == ToolType.HOE:
                if tile.type == CropType.NONE:
                    # You can add a visual indicator for tilled soil here if desired
                    self.state.player.energy -= 5

            elif self.state.player.selected_tool == ToolType.WATERING_CAN:
                if tile.type != CropType.NONE and tile.water_level < 100:
                    tile.water_level = min(100, tile.water_level + 20)
                    self.state.aquifer_level = max(0, self.state.aquifer_level - 5)
                    self.state.total_water_used += 5
                    self.state.player.energy -= 3

            elif self.state.player.selected_tool == ToolType.SEEDS:
                seed_name = f"{self.state.player.selected_seed.name.lower()}_seeds"
                # Check if soil is tilled (for now, just check if it's empty)
                if tile.type == CropType.NONE and self.state.player.inventory.get(seed_name, 0) > 0:
                    tile.type = self.state.player.selected_seed
                    tile.planted_day = self.state.day
                    tile.growth_stage = 0
                    tile.water_level = 50
                    # NEW: Set health based on crop type
                    if tile.type == CropType.DROUGHT_GRASS:
                        tile.health = 7  # Grass uses 7-stage health
                    else:
                        tile.health = 100  # Other crops use 100-point health
                    self.state.player.inventory[seed_name] -= 1
                    self.state.player.energy -= 2

            elif self.state.player.selected_tool == ToolType.HARVEST:
                if tile.type != CropType.NONE and tile.growth_stage >= 3:
                    crop_name = tile.type.name.lower()
                    if not crop_name.endswith('s'):
                        crop_name += 's'  # Ensure plural for inventory keys

                    if crop_name == "native_flowerss":  # Handle pluralization edge case
                        crop_name = "native_flowers"

                    self.state.player.inventory[crop_name] += 1
                    self.state.player.money += self.get_crop_value(tile.type)
                    # Reset the tile to a default state
                    self.state.farm_grid[grid_y][grid_x] = Crop()
                    self.state.player.energy -= 1

    def get_crop_value(self, crop_type: CropType) -> int:
        """Get the value of a harvested crop"""
        values = {
            CropType.TOMATO: 10,
            CropType.CORN: 15,
            CropType.CARROT: 8,
            CropType.NATIVE_FLOWERS: 25,
            CropType.DROUGHT_GRASS: 20
        }
        return values.get(crop_type, 5)

    def update_crops(self):
        """Update crop growth and health at the start of a new day"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                crop = self.state.farm_grid[y][x]
                if crop.type != CropType.NONE:
                    # NEW: Different health logic for grass vs. other crops
                    if crop.type == CropType.DROUGHT_GRASS:
                        # Grass health just decays by 1 stage each day
                        crop.health = max(0, crop.health - 1)
                    else:
                        # Logic for all other crops
                        days_planted = self.state.day - crop.planted_day
                        if days_planted > 0:
                            crop.growth_stage = min(3, days_planted // 2)

                        water_loss = self.get_water_loss(crop)
                        crop.water_level = max(0, crop.water_level - water_loss)

                        if crop.water_level < 20:
                            crop.health -= 10
                        elif crop.water_level > 80:
                            crop.health = min(100, crop.health + 5)

                        crop.health = max(0, crop.health - 2)

                    # Crop dies if health reaches 0 (works for both systems)
                    if crop.health <= 0:
                        self.state.farm_grid[y][x] = Crop()  # Reset the tile

    def get_water_loss(self, crop: Crop) -> int:
        """Calculate water loss based on crop type and weather"""
        base_loss = 5

        if self.state.weather == WeatherType.DROUGHT:
            base_loss *= 2
        elif self.state.weather == WeatherType.RAINY:
            base_loss = -10  # Rainy weather waters the plants

        drought_tolerance = {
            CropType.TOMATO: 1.0,
            CropType.CORN: 0.8,
            CropType.CARROT: 1.2,
            CropType.NATIVE_FLOWERS: 0.3,
            CropType.DROUGHT_GRASS: 0.2
        }

        return int(base_loss * drought_tolerance.get(crop.type, 1.0))

    def update_time(self):
        """Update the in-game time. Slower clock - 1 real minute = 1 in-game minute."""
        # Only advance time every other frame to slow it down by half
        if hasattr(self, '_time_counter'):
            self._time_counter += 1
        else:
            self._time_counter = 0
            
        if self._time_counter % 6 == 0:  # Advance time every 6 frames (10x slower)
            self.state.time_of_day += 1  # Advance one minute

        # Day ends at midnight (24 hours * 60 minutes = 1440 minutes)
        if self.state.time_of_day >= 24 * 60:
            self.next_day()

    def next_day(self):
        """Advance to the next day"""
        self.state.day += 1
        self.state.time_of_day = 360  # Reset time to 6:00 AM
        self.state.player.energy = 100

        # Refresh grass texture for the new day
        self.renderer.refresh_grass_texture()

        weather_roll = random.randint(1, 10)
        if weather_roll <= 6:
            self.state.weather = WeatherType.SUNNY
        elif weather_roll <= 8:
            self.state.weather = WeatherType.RAINY
        else:
            self.state.weather = WeatherType.DROUGHT

        self.update_crops()
        self.calculate_score()

    def calculate_score(self):
        """Calculate player score"""
        base_score = self.state.day * 10
        healthy_crops = sum(
            1 for row in self.state.farm_grid for crop in row if crop.type != CropType.NONE and crop.health > 50)
        health_bonus = healthy_crops * 5
        native_crops = sum(1 for row in self.state.farm_grid for crop in row if
                           crop.type in [CropType.NATIVE_FLOWERS, CropType.DROUGHT_GRASS])
        native_bonus = native_crops * 15
        water_penalty = self.state.total_water_used * 2
        self.state.score = max(0, base_score + self.state.player.money + health_bonus + native_bonus - water_penalty)

    def draw(self):
        """Draw the game"""
        is_night = (self.state.time_of_day // 60) >= 18 or (self.state.time_of_day // 60) < 6
        self.screen.fill(COLORS['night'] if is_night else COLORS['day'])

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                tile_x = x * TILE_SIZE
                tile_y = y * TILE_SIZE
                self.renderer.draw_crop(tile_x, tile_y, self.state.farm_grid[y][x])

        self.renderer.draw_pixel_character(int(self.state.player.x), int(self.state.player.y), COLORS['player'])
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        """Draw the game UI"""
        ui_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
        pygame.draw.rect(self.screen, COLORS['ui_bg'], ui_rect)
        pygame.draw.rect(self.screen, COLORS['ui_text'], ui_rect, 2)

        # NEW: Format and display the time
        hour = (self.state.time_of_day // 60) % 24
        minute = self.state.time_of_day % 60
        time_str = f"Time: {hour:02d}:{minute:02d}"

        stats = [
            f"Day: {self.state.day}",
            time_str,
            f"Money: ${self.state.player.money}",
            f"Energy: {self.state.player.energy}",
            f"Weather: {self.state.weather.name}"
        ]

        for i, stat in enumerate(stats):
            text = self.state.small_font.render(stat, True, COLORS['ui_text'])
            self.screen.blit(text, (10 + i * 150, 10))

        tools = ["1: Hoe", "2: Water", "3: Seeds", "4: Harvest"]
        for i, tool in enumerate(tools):
            color = COLORS['selected'] if i + 1 == self.state.player.selected_tool.value else COLORS['ui_text']
            text = self.state.small_font.render(tool, True, color)
            self.screen.blit(text, (10 + i * 100, 35))

        seeds = ["Q:Tom", "E:Corn", "R:Carr", "T:Flow", "Y:Grass"]
        seed_types = [CropType.TOMATO, CropType.CORN, CropType.CARROT, CropType.NATIVE_FLOWERS, CropType.DROUGHT_GRASS]
        for i, seed in enumerate(seeds):
            color = COLORS['selected'] if seed_types[i] == self.state.player.selected_seed else COLORS['ui_text']
            text = self.state.small_font.render(seed, True, color)
            self.screen.blit(text, (10 + i * 80, 55))

        instructions = ["WASD/Arrows: Move", "Space: Use Tool", "N: Next Day"]
        for i, instruction in enumerate(instructions):
            text = self.state.small_font.render(instruction, True, COLORS['ui_text'])
            self.screen.blit(text, (SCREEN_WIDTH - 200, 10 + i * 20))

    def update(self):
        """Handle all logic updates for each frame."""
        self.handle_input()
        self.update_time()

    def run(self):
        """Main game loop"""
        while self.state.running:
            self.handle_events()
            self.update()
            self.draw()
            self.state.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()