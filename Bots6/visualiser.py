import math
import tkinter as tk
import world

# Global Variables
Window_width_pixels = 750


class Display:
    def __init__(self, world=world.World()):
        self.world = world
        # variables
        self.pixels_per_unit = Window_width_pixels / self.world.width
        self.window_width_pixels = Window_width_pixels
        self.window_height_pixels = self.world.height * self.pixels_per_unit

        # Create the main window
        self.window = tk.Tk()
        self.window.title("  Simple Evolution")
        # self.window.bind("<keypress>", self._onKeypress)

        # Create canvas to show the environment
        self.canvas = tk.Canvas(
            self.window,
            bg="green4",
            width=self.window_width_pixels,
            height=self.window_height_pixels,
        )

        # draw lines to indicate the units
        # individual units
        long_edge_length = max(self.world.height, self.world.width)
        small_spacing = math.ceil(long_edge_length / 20.0)
        large_spacing = small_spacing * 10
        self._generateUnitLines(small_spacing, "light grey")
        # 10s of units
        # these are done seperately so that they overlay the grey lines underneath
        self._generateUnitLines(large_spacing, "orange red")

        self.canvas.pack()

    def _onKeypress(self, event):
        print(f"You pressed {event.char}")

    def _generateUnitLines(self, spacing, colour):
        # vertical
        i = spacing
        while i <= self.world.width:
            self.canvas.create_line(
                self._convertToPixels(i),
                self._convertToPixels(0),
                self._convertToPixels(i),
                self._convertToPixels(self.world.height),
                fill=colour,
            )
            i += spacing

        # horizontal
        i = spacing
        while i <= self.world.height:
            self.canvas.create_line(
                self._convertToPixels(0),
                self._convertToPixels(i),
                self._convertToPixels(self.world.width),
                self._convertToPixels(i),
                fill=colour,
            )

            i += spacing

    def update(self):
        self.window.update()

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


class CircleObject:
    def __init__(
        self, visualiser: Display, colour_HEX="#888888", position=[0.0, 0.0], radius=1.0
    ):
        self.display = visualiser
        self.colourHEX = colour_HEX
        self.position = position
        self.radius = radius
        self.canvasCircleObject = self._createCircle()

    def _createCircle(self):
        """
        Creates a circle with the centre in the x and y position and a radius
        returns the circle object.
        """
        # point 1
        UL_x = self.display._convertToPixels(self.position[0] - self.radius) + 1
        UL_y = self.display._convertToPixels(self.position[1] - self.radius) + 1
        # point 2
        LR_x = self.display._convertToPixels(self.position[0] + self.radius)
        LR_y = self.display._convertToPixels(self.position[1] + self.radius)

        return self.display.canvas.create_oval(
            UL_x, UL_y, LR_x, LR_y, fill=self.colourHEX
        )

    def move(self):
        """
        Moves the circle object from the position given,
        radius is subtracted because the display works from
        the top left corner
        """
        self.display.canvas.moveto(
            self.canvasCircleObject,
            self.display._convertToPixels(self.position[0] - self.radius),
            self.display._convertToPixels(self.position[1] - self.radius),
        )

    def changeColour(self):
        self.display.canvas.itemconfig(self.canvasCircleObject, fill=self.colourHEX)

    def delete(self):
        """
        removes the object from the view space
        """
        self.display.canvas.delete(self.canvasCircleObject)


def RGBtoHEX(RGB: list[float]) -> str:
    return "#%02x%02x%02x" % (int(RGB[0] * 255), int(RGB[1] * 255), int(RGB[2] * 255))


def HEXtoRGB(HEX: str) -> list[float]:
    RGB = []
    for i in range(1, len(HEX), 2):
        RGB.append(int(HEX[i : i + 2], 16) / 255.0)
    return RGB


def main():
    window = Display()
    circle = CircleObject(window)
    circle.position = [5.0, 5.0]
    circle.move()

    i = 0.0
    while True:
        i += 1
        circle.colourHEX = RGBtoHEX([(i / (10.0**3.0)) % 1.0, 0.5, 0.2])
        circle.changeColour()
        window.update()


if __name__ == "__main__":
    main()
