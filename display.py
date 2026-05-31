from __future__ import annotations
import pygame
from abc import ABC, abstractmethod
import math

from world import World
from brain import Brain

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # from simulator import Simulator
    from neuron import Neuron
    from bot import Bot
    from simulator import Simulator

# Global Variables
WINDOW_WIDTH_PIX = 1200
WINDOW_HEIGHT_PIX = 600

DEFAULT_TITLE = "Simple Evolution"

# Color mappings for pygame (RGB tuples)
COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "light_grey": (211, 211, 211),
    "light_blue": (173, 216, 230),
    "red": (255, 0, 0),
    "ghost_white": (248, 248, 255),
    "red2": (238, 0, 0),
    "blue2": (0, 0, 238),
    "dark_orange": (255, 140, 0),
    "pink": (255, 192, 203),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "purple": (128, 0, 128),
}


class Display:
    def __init__(self, simulator):
        self.simulator = simulator
        pygame.init()
        pygame.display.set_allow_screensaver(False)

        # Create main window
        screen = pygame.display.set_mode((WINDOW_WIDTH_PIX, WINDOW_HEIGHT_PIX))

        # Define regions
        world_rect = pygame.Rect(0, 0, WINDOW_WIDTH_PIX // 2, WINDOW_HEIGHT_PIX)
        brain_rect = pygame.Rect(
            WINDOW_WIDTH_PIX / 2, 0, WINDOW_WIDTH_PIX // 2, WINDOW_HEIGHT_PIX
        )

        # Create subsurfaces
        world_surface = screen.subsurface(world_rect)
        brain_surface = screen.subsurface(brain_rect)

        # Pass world_surface to your Display class, brain_surface to BrainDisplay
        self.selected_bot = None
        self._setup_event_handling()

        self.world_display = WorldDisplay(
            simulator=self.simulator, surface=world_surface, parent=self
        )
        self.brain_display = BrainDisplay(surface=brain_surface)

        self._update_title()

    def update(self):
        self.world_display.update()
        try:
            if self.selected_bot:
                selected_bot = self.selected_bot
            else:
                selected_bot = next(
                    (
                        obj
                        for obj in self.simulator.sim_objects
                        if hasattr(obj, "brain") and hasattr(obj, "visual")
                    ),
                    None,
                )
            if selected_bot is not None:
                self.brain_display.connectBot(selected_bot)
                self.brain_display.update()
        except Exception as err:
            pass
            # print(err)
        pygame.display.flip()

    def _setup_event_handling(self):
        """Setup keyboard event handlers"""
        self.key_handlers = {
            pygame.K_UP: self._on_speed_up,
            pygame.K_DOWN: self._on_speed_down,
        }

    def _on_speed_up(self):
        if not self.simulator:
            return
        self.simulator.time_multiplier = min(
            self.simulator.time_multiplier * 1.25, 20.0
        )
        self._update_title()

    def _on_speed_down(self):
        if not self.simulator:
            return
        self.simulator.time_multiplier = max(self.simulator.time_multiplier / 1.25, 0.0)
        self._update_title()

    def _update_title(self):
        title = DEFAULT_TITLE
        if self.simulator is not None:
            title = f"{DEFAULT_TITLE} | speed x{self.simulator.time_multiplier:.2f}"
        pygame.display.set_caption(title)


# neuron size in units
NEURON_RADIUS_MIN = 0.08
NEURON_RADIUS_MAX = 0.2

CONNECTION_MULTIPLIER = 12


class BrainDisplay:
    def __init__(self, surface: pygame.Surface):
        self.screen = surface
        self.connected_brain: Brain = None

        # work out how much space is required to show all the neurons
        # window should be a square
        self.vis_side_length = 15

        # calculate the size and layout of the window
        self.pixels_per_unit = self.screen.get_width() // self.vis_side_length

    def _neuron_value_to_radius(self, value):
        """
        Figures out what the radius of the displayed neuron should be based on the value (0 to 1)
        based on the min an max radi set as global variables
        """
        new_radius = (NEURON_RADIUS_MAX - NEURON_RADIUS_MIN) * value + NEURON_RADIUS_MIN
        return new_radius

    def draw_connections(self, neuron: Neuron, surface):
        origin_X = neuron.location[0]
        origin_Y = neuron.location[1]
        for other_neuron, weight in zip(neuron.inputs, neuron.weights):
            destination_X = other_neuron.location[0]
            destination_Y = other_neuron.location[1]

            x_positions = [
                destination_X,
                destination_X + self.connected_brain.side_length,
                destination_X - self.connected_brain.side_length,
            ]

            y_positions = [
                destination_Y,
                destination_Y + self.connected_brain.side_length,
                destination_Y - self.connected_brain.side_length,
            ]

            x_distances = [pos - origin_X for pos in x_positions]
            y_distances = [pos - origin_Y for pos in y_positions]

            x_dist_abs = [abs(val) for val in x_distances]
            y_dist_abs = [abs(val) for val in y_distances]

            idx = x_dist_abs.index(min(x_dist_abs))
            idy = y_dist_abs.index(min(y_dist_abs))

            line_width = max(
                1, int(abs(CONNECTION_MULTIPLIER * weight * other_neuron.getValue()))
            )

            if idx == 0 and idy == 0:  # neither loop
                pygame.draw.line(
                    surface,
                    COLORS["blue2"],
                    (
                        self._convertToPixels(origin_X + 1),
                        self._convertToPixels(origin_Y + 1),
                    ),
                    (
                        self._convertToPixels(destination_X + 1),
                        self._convertToPixels(destination_Y + 1),
                    ),
                    line_width,
                )
                continue

            m = (
                (y_positions[idy] - origin_Y) / (x_positions[idx] - origin_X)
                if (x_positions[idx] - origin_X) != 0
                else 0
            )
            c = origin_Y - m * origin_X

            if idx != 0 and idy == 0:  # only x loops
                if idx == 1:
                    x_loop_o = self.connected_brain.side_length
                    x_loop_d = 0
                else:
                    x_loop_o = 0
                    x_loop_d = self.connected_brain.side_length
                y_loop_o = m * x_loop_o + c
                y_loop_d = y_loop_o
            elif idx == 0 and idy != 0:  # only y loops
                if idy == 1:
                    y_loop_o = self.connected_brain.side_length
                    y_loop_d = 0
                else:
                    y_loop_o = 0
                    y_loop_d = self.connected_brain.side_length
                x_loop_o = (y_loop_o - c) / m if m != 0 else 0
                x_loop_d = x_loop_o
            else:  # both loop
                pygame.draw.line(
                    surface,
                    COLORS["blue2"],
                    (
                        self._convertToPixels(origin_X + 1),
                        self._convertToPixels(origin_Y + 1),
                    ),
                    (
                        self._convertToPixels(destination_X + 1),
                        self._convertToPixels(destination_Y + 1),
                    ),
                    line_width,
                )
                continue

            pygame.draw.line(
                surface,
                COLORS["blue2"],
                (
                    self._convertToPixels(origin_X + 1),
                    self._convertToPixels(origin_Y + 1),
                ),
                (
                    self._convertToPixels(x_loop_o + 1),
                    self._convertToPixels(y_loop_o + 1),
                ),
                line_width,
            )
            pygame.draw.line(
                surface,
                COLORS["blue2"],
                (
                    self._convertToPixels(x_loop_d + 1),
                    self._convertToPixels(y_loop_d + 1),
                ),
                (
                    self._convertToPixels(destination_X + 1),
                    self._convertToPixels(destination_Y + 1),
                ),
                line_width,
            )

    def connectBot(self, connection_bot: Bot):
        # keeps a connection to the bot
        self.connected_bot = connection_bot
        self.connected_brain = connection_bot.brain
        if not hasattr(self, "font"):
            self.font = pygame.font.SysFont(None, 16)

        # work out how much space is required to show all the neurons
        # window should be a square
        self.vis_side_length = self.connected_brain.side_length + 2

        # calculate the size and layout of the window
        self.pixels_per_unit = (
            self.screen.get_width() // self.connected_bot.brain.side_length
        )

    def connectBrain(self, new_brain):
        # For backward compatibility, create a dummy bot
        class DummyBot:
            def __init__(self, brain, name="Test Brain"):
                self.brain = brain
                self.attributes = type("obj", (object,), {"name": name})()
                self.energy = type(
                    "obj", (object,), {"level": 50.0, "maximum": 100.0}
                )()
                self.age = 0.0
                self.pose = [0, 0]
                self.total_rewards_collected = 0

        dummy_bot = DummyBot(new_brain)
        self.connectBot(dummy_bot)

    def _generateUnitLines(self, spacing, world_width, world_height, colour_key):
        """Generate unit grid lines - returns list of line coordinates"""
        colour = COLORS.get(colour_key, COLORS["white"])
        lines = []

        # vertical
        i = 1
        while i <= world_width:
            lines.append(("vertical", i, 0, i, world_height, colour))
            i += spacing

        # horizontal
        i = 1
        while i <= world_height:
            lines.append(("horizontal", 0, i, world_width, i, colour))
            i += spacing

        return lines

    def update(self):
        # Note: Don't handle pygame events here - the main Display window handles them
        # This prevents conflicts between windows fighting for the event queue

        # Clear screen
        self.screen.fill(COLORS["black"])

        # Draw grid lines
        grid_lines = []
        # individual units
        grid_lines.extend(
            self._generateUnitLines(
                1, self.vis_side_length, self.vis_side_length, "light_grey"
            )
        )
        # 10s of units
        grid_lines.extend(
            self._generateUnitLines(
                10, self.vis_side_length, self.vis_side_length, "light_blue"
            )
        )

        for line_info in grid_lines:
            if line_info[0] in ["vertical", "horizontal"]:
                _, x1, y1, x2, y2, colour = line_info
                pygame.draw.line(
                    self.screen,
                    colour,
                    (self._convertToPixels(x1), self._convertToPixels(y1)),
                    (self._convertToPixels(x2), self._convertToPixels(y2)),
                    1,
                )

        # Draw brain boundary
        rect_x1 = self._convertToPixels(1)
        rect_y1 = self._convertToPixels(1)
        rect_x2 = self._convertToPixels(self.vis_side_length - 1)
        rect_y2 = self._convertToPixels(self.vis_side_length - 1)
        pygame.draw.rect(
            self.screen,
            COLORS["red"],
            (rect_x1, rect_y1, rect_x2 - rect_x1, rect_y2 - rect_y1),
            2,
        )

        # Draw lines first so they are underneath the neurons
        if self.connected_brain:
            for neuron in self.connected_brain.neurons:
                self.draw_connections(neuron, self.screen)

            # Create the circles for the neurons
            for neuron in self.connected_brain.neurons:
                fillColour = COLORS["ghost_white"]

                if neuron.output_factor <= 0:
                    outlineColour = COLORS["red2"]
                else:
                    outlineColour = COLORS["blue2"]

                if neuron.name == "EP":
                    pass
                elif neuron.name == "DP":
                    pass
                elif neuron.name == "PPx":
                    pass
                elif neuron.name == "PPy":
                    pass
                elif neuron.name == "VF":
                    fillColour = COLORS["dark_orange"]
                elif neuron.name == "AVF":
                    fillColour = COLORS["pink"]
                elif neuron.name == "EA":
                    pass
                elif neuron.name.startswith("Eye Segment"):
                    if neuron.name.endswith("R"):
                        fillColour = COLORS["red"]
                    elif neuron.name.endswith("G"):
                        fillColour = COLORS["green"]
                    elif neuron.name.endswith("B"):
                        fillColour = COLORS["blue"]
                    elif neuron.name.endswith("Dis"):
                        fillColour = COLORS["purple"]

                self.createNeuronCircle(neuron, fillColour, outlineColour)

            # Display energy level on the left side
            if self.connected_bot:
                text = [
                    f"Energy: {self.connected_bot.energy.level:.2f}/{self.connected_bot.energy.maximum:.2f}",
                    f"Age: {self.connected_bot.age:.2f}",
                    f"Pose: {self.connected_bot.pose}",
                    f"Rewards: {self.connected_bot.total_rewards_collected}",
                ]

                y_pos = 10
                for line in text:
                    text_surface = self.font.render(line, True, COLORS["white"])
                    self.screen.blit(text_surface, (10, y_pos))
                    y_pos += 15

    def createNeuronCircle(self, neuron: Neuron, fillColour, outlineColour):
        """Creates a circle for a neuron"""
        radius = self._neuron_value_to_radius(neuron.getValue())
        center_x = self._convertToPixels(neuron.location[0] + 1)
        center_y = self._convertToPixels(neuron.location[1] + 1)
        pixel_radius = int(radius * self.pixels_per_unit)

        # Draw filled circle
        pygame.draw.circle(
            self.screen,
            fillColour,
            (center_x, center_y),
            max(1, pixel_radius),
        )
        # Draw outline
        pygame.draw.circle(
            self.screen,
            outlineColour,
            (center_x, center_y),
            max(1, pixel_radius),
            2,
        )

    def _convertToPixels(self, value) -> int:
        """Converts a position in the world to a pixel position on the window"""
        return int(math.ceil(value * self.pixels_per_unit) + 1)

    def quit(self):
        self.running = False
        pygame.quit()


DEFAULT_WORLD_BG_COLOUR = (50, 150, 50)  # RGB format for pygame


class WorldDisplay:
    def __init__(
        self,
        simulator: Simulator,
        surface: pygame.Surface,
        parent: Display,
    ):
        self.simulator = simulator
        self.surface = surface
        self.parent = parent
        self._pixels_per_unit = self.surface.get_width() / self.simulator.world.width

        self.bg_colour = DEFAULT_WORLD_BG_COLOUR

    def _convert_to_pixels(self, value) -> int:
        """Converts a position in the world to a pixel position on the window"""
        return int(value * self._pixels_per_unit)

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.parent is not None:
                    self.parent.simulator.status = False
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.parent is not None and event.key in self.parent.key_handlers:
                    self.parent.key_handlers[event.key]()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos)

    def _handle_click(self, pos):
        """Handle mouse click events"""
        click_x, click_y = pos

        for obj in self.simulator.sim_objects:
            if not hasattr(obj, "visual") or not hasattr(obj, "pose"):
                continue

            if hasattr(obj.visual, "contains_point") and obj.visual.contains_point(
                self, pos
            ):
                if self.parent is not None:
                    self.parent.selected_bot = obj
                return

    def update(self):
        """Render the scene"""
        self.handle_events()

        # Clear screen
        self.surface.fill(self.bg_colour)

        # Draw grid lines
        # Create grid
        long_edge_length = max(self.simulator.world.height, self.simulator.world.width)
        small_spacing = math.ceil(long_edge_length / 20.0)
        large_spacing = small_spacing * 10
        create_grid_lines(
            self.surface, small_spacing, (255, 255, 255), self._convert_to_pixels
        )
        create_grid_lines(
            self.surface, large_spacing, (255, 0, 0), self._convert_to_pixels
        )

        for obj in self.simulator.sim_objects:
            obj.visual.draw(self)

        self._draw_selected_highlight()

    def _draw_selected_highlight(self):
        if self.parent is None or self.parent.selected_bot is None:
            return

        selected = self.parent.selected_bot
        if selected not in self.simulator.sim_objects:
            self.parent.selected_bot = None
            return

        x = self._convert_to_pixels(selected.pose.x)
        y = self._convert_to_pixels(selected.pose.y)
        radius = max(3, self._convert_to_pixels(selected.attributes.radius) + 3)

        pygame.draw.circle(self.surface, COLORS["white"], (x, y), radius, 2)


class Visual(ABC):
    @abstractmethod
    def draw(self, display): ...


def RGBtoHEX(RGB: list[float]) -> str:
    return "#%02x%02x%02x" % (int(RGB[0] * 255), int(RGB[1] * 255), int(RGB[2] * 255))


def HEXtoRGB(HEX: str) -> list[float]:
    """Convert HEX color to RGB float values (0-1)"""
    RGB = []
    for i in range(1, len(HEX), 2):
        RGB.append(int(HEX[i : i + 2], 16) / 255.0)
    return RGB


def HEXtoRGB_pygame(HEX: str) -> tuple:
    """Convert HEX color to RGB tuple (0-255) for pygame"""
    if not HEX or len(HEX) < 7:
        return (255, 255, 255)

    r = int(HEX[1:3], 16)
    g = int(HEX[3:5], 16)
    b = int(HEX[5:7], 16)
    return (r, g, b)


from pygame import Surface


def circle_w_outline(display, pos_x, pos_y, radius, colour, colour_ol="#000000"):

    x = display._convert_to_pixels(pos_x)
    y = display._convert_to_pixels(pos_y)
    r = display._convert_to_pixels(radius)

    pygame.draw.circle(
        display.surface,
        colour,
        (x, y),
        r,
    )
    pygame.draw.circle(display.surface, colour_ol, (x, y), r, 1)


def create_grid_lines(display: Surface, spacing, colour, pixel_conversion):
    """Generate grid lines"""
    rgb_colour = HEXtoRGB_pygame(colour)

    spacing = pixel_conversion(spacing)

    # Vertical lines
    for space in range(spacing, display.get_width(), spacing):
        pygame.draw.line(
            display,
            rgb_colour,
            (space, 0),
            (space, display.get_height()),
            1,
        )

    # Horizontal lines
    for space in range(spacing, display.get_height(), spacing):
        pygame.draw.line(
            display,
            rgb_colour,
            (0, space),
            (display.get_width(), space),
            1,
        )
