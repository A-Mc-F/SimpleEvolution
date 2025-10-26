from __future__ import annotations
import math
import tkinter as tk
import bot
import reward
import simulator

# Global Variables
WINDOW_WIDTH_P = 700

FRAME_RATE = 24.0
FRAME_INTERVAL = 1.0 / FRAME_RATE


class Display:
    def __init__(self, simulator: simulator.Simulator):
        self.simulator = simulator
        # variables
        self.pixels_per_unit = WINDOW_WIDTH_P / self.simulator.world.width
        self.window_width_pixels = WINDOW_WIDTH_P
        self.window_height_pixels = self.simulator.world.height * self.pixels_per_unit

        self.dynamic_visual_objects = []
        self.object_names = []

        # Create the main window
        self.window = tk.Tk()
        self.window.title("  Simple Evolution")

        # Create canvas to show the environment
        self.canvas = tk.Canvas(
            self.window,
            bg="green4",
            width=self.window_width_pixels,
            height=self.window_height_pixels,
        )

        self.canvas.pack()

    def _generateUnitLines(self, spacing, colour):
        # vertical
        i = spacing
        while i <= self.simulator.world.width:
            self.canvas.create_line(
                self._convertToPixels(i),
                self._convertToPixels(0),
                self._convertToPixels(i),
                self._convertToPixels(self.simulator.world.height),
                fill=colour,
            )
            i += spacing

        # horizontal
        i = spacing
        while i <= self.simulator.world.height:
            self.canvas.create_line(
                self._convertToPixels(0),
                self._convertToPixels(i),
                self._convertToPixels(self.simulator.world.width),
                self._convertToPixels(i),
                fill=colour,
            )

            i += spacing

    def _convertToPixels(self, value) -> int:
        """converts a position in the world to a pixel position on the window
        index 0 and 1 are outside of the range of the canvas
        a position of 0 should not show, however a position of 0.01 will
        decimals are rounded to the nearest whole number, 0.4 -> 0, 0.5 -> 1
        2 is the first index which will show on the canvas
        calculated pixel -> index -> pixel number
        0.1-1 -> 2 -> 1, 1.1-2 -> 3 -> 2 and so on.
        """
        return math.ceil(value * self.pixels_per_unit) + 1

    def updateDisplay(self):
        self.canvas.delete("all")

        # draw lines to indicate the units
        # individual units
        long_edge_length = max(self.simulator.world.height, self.simulator.world.width)
        small_spacing = math.ceil(long_edge_length / 20.0)
        large_spacing = small_spacing * 10
        self._generateUnitLines(small_spacing, "light grey")
        # 10s of units
        # these are done seperately so that they overlay the grey lines underneath
        self._generateUnitLines(large_spacing, "orange red")

        for object in self.simulator.sim_objects:
            if type(object) == bot.Bot:
                self.dynamic_visual_objects.append(BotVisual(self, object))
            if type(object) == reward.Reward:
                self.dynamic_visual_objects.append(RewardVisual(self, object))

        v_object: BotVisual
        for v_object in self.dynamic_visual_objects:
            v_object.draw()

        self.window.update()

    def run(self):
        while True:
            self.updateDisplay()


class RewardVisual:
    def __init__(self, visualiser: Display, reward: reward.Reward):
        self.display = visualiser
        self.reward = reward
        self.canvasCircleObject = None

    def _createCircle(self):
        """
        Creates a circle with the centre in the x and y position and a radius
        returns the circle object.
        """
        # point 1
        UL_x = (
            self.display._convertToPixels(
                self.reward.position[0] - self.reward.attributes.radius
            )
            + 1
        )
        UL_y = (
            self.display._convertToPixels(
                self.reward.position[1] - self.reward.attributes.radius
            )
            + 1
        )
        # point 2
        LR_x = self.display._convertToPixels(
            self.reward.position[0] + self.reward.attributes.radius
        )
        LR_y = self.display._convertToPixels(
            self.reward.position[1] + self.reward.attributes.radius
        )

        return self.display.canvas.create_oval(
            UL_x, UL_y, LR_x, LR_y, fill=self.reward.attributes.colourHEX
        )

    def draw(self):
        """
        Moves the circle object from the position given,
        radius is subtracted because the display works from
        the top left corner
        """
        if self.canvasCircleObject == None:
            self.canvasCircleObject = self._createCircle()

        self.display.canvas.moveto(
            self.canvasCircleObject,
            self.display._convertToPixels(
                self.reward.position[0] - self.reward.attributes.radius
            ),
            self.display._convertToPixels(
                self.reward.position[1] - self.reward.attributes.radius
            ),
        )

    def changeColour(self):
        self.display.canvas.itemconfig(
            self.canvasCircleObject, fill=self.reward.attributes.colourHEX
        )

    def delete(self):
        """
        removes the object from the view space
        """
        self.display.canvas.delete(self.canvasCircleObject)


class BotVisual:
    def __init__(self, visualiser: Display, bot: bot.Bot):
        self.display = visualiser
        self.bot = bot
        self.body_circle = None
        self.eye_circle = None

    def _createVisuals(self):
        """
        Creates a circle with the centre in the x and y position and a radius
        returns the circle object.
        """
        r = self.bot.attributes.radius
        # point 1
        UL_x = 1
        UL_y = 1
        # point 2
        LR_x = self.display._convertToPixels(r * 2)
        LR_y = self.display._convertToPixels(r * 2)

        self.body_circle = self.display.canvas.create_oval(
            UL_x, UL_y, LR_x, LR_y, fill=self.bot.attributes.colourHEX
        )

        # point 1
        UL_x = 1
        UL_y = 1
        # point 2
        LR_x = self.display._convertToPixels(r / 2.0)
        LR_y = self.display._convertToPixels(r / 2.0)
        self.eye_circle = self.display.canvas.create_oval(
            UL_x, UL_y, LR_x, LR_y, fill="black", outline="white"
        )

    def draw(self):
        """
        Moves the circle object from the position given,
        radius is subtracted because the display works from
        the top left corner
        """
        if self.body_circle == None:
            self._createVisuals()

        pos_x = self.bot.position[0]
        pos_y = self.bot.position[1]
        r = self.bot.attributes.radius
        self.display.canvas.moveto(
            self.body_circle,
            self.display._convertToPixels(pos_x - r),
            self.display._convertToPixels(pos_y - r),
        )
        self.display.canvas.moveto(
            self.eye_circle,
            self.display._convertToPixels(
                pos_x + r * math.cos(self.bot.direction) * 0.8
            ),
            self.display._convertToPixels(
                pos_y - r * math.sin(self.bot.direction) * 0.8
            ),
        )

    def changeColour(self):
        self.display.canvas.itemconfig(
            self.body_circle, fill=self.bot.attributes.colourHEX
        )

    def delete(self):
        """
        removes the object from the view space
        """
        self.display.canvas.delete(self.body_circle, self.eye_circle)


def RGBtoHEX(RGB: list[float]) -> str:
    return "#%02x%02x%02x" % (int(RGB[0] * 255), int(RGB[1] * 255), int(RGB[2] * 255))


def HEXtoRGB(HEX: str) -> list[float]:
    RGB = []
    for i in range(1, len(HEX), 2):
        RGB.append(int(HEX[i : i + 2], 16) / 255.0)
    return RGB


def main():
    window = Display()
    circle = RewardVisual(window)
    circle.position = [5.0, 5.0]
    circle.draw()

    i = 0.0
    while True:
        i += 1
        circle.colourHEX = RGBtoHEX([(i / (10.0**3.0)) % 1.0, 0.5, 0.2])
        circle.changeColour()
        window.run()


if __name__ == "__main__":
    main()
