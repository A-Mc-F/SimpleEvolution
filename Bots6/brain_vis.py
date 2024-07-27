import tkinter as tk
import brain
import bot
import math
import neuron as n


# Global Variables
Window_width_pixels = 600

# neuron size in units
Neuron_min_radius = 0.08
Neuron_max_radius = 0.2


def valueToNeuronRadius(value):
    """
    Figures out what the radius of the displayed neuron should be based on the value (0 to 1)
    based on the min an max radi set as global variables
    """
    new_radius = (Neuron_max_radius - Neuron_min_radius) * value + Neuron_min_radius
    return new_radius


class BrainDisplay:
    def __init__(self):
        # keeps a connection to the brain
        self.connected_brain: brain.Brain = None

        # work out how much space is required to show all the neurons
        # window should be a square
        self.vis_side_length = 15

        # calculate the size and layout of the window
        self.window_width_pixels = Window_width_pixels
        self.pixels_per_unit = self.window_width_pixels / self.vis_side_length
        self.window_height_pixels = self.vis_side_length * self.pixels_per_unit

        self.canvas_items = []

        # Create the main window
        self.window = tk.Tk()
        self.window.title("  Brain Visualiser")

        # Create canvas to show the environment
        self.canvas = tk.Canvas(
            self.window,
            bg="black",
            width=self.window_width_pixels,
            height=self.window_height_pixels,
        )

        self.canvas.pack()

    def drawConnections(self, neuron: n.Neuron):
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

            if idx == 0 and idy == 0:  # neither loop
                self.canvas.create_line(
                    self._convertToPixels(origin_X + 1),
                    self._convertToPixels(origin_Y + 1),
                    self._convertToPixels(destination_X + 1),
                    self._convertToPixels(destination_Y + 1),
                    width=abs(7 * weight),
                    fill="blue",
                )
                return

            m = (y_positions[idy] - origin_Y) / (x_positions[idx] - origin_X)
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
                x_loop_o = (y_loop_o - c) / m
                x_loop_d = x_loop_o
            else:  # both loop
                return

            self.canvas.create_line(
                self._convertToPixels(origin_X + 1),
                self._convertToPixels(origin_Y + 1),
                self._convertToPixels(x_loop_o + 1),
                self._convertToPixels(y_loop_o + 1),
                width=abs(7 * weight),
                fill="blue",
            )
            self.canvas.create_line(
                self._convertToPixels(x_loop_d + 1),
                self._convertToPixels(y_loop_d + 1),
                self._convertToPixels(destination_X + 1),
                self._convertToPixels(destination_Y + 1),
                width=abs(7 * weight),
                fill="blue",
            )

    def connectBrain(self, new_brain):
        # keeps a connection to the brain
        self.connected_brain: brain = new_brain

        # work out how much space is required to show all the neurons
        # window should be a square
        self.vis_side_length = self.connected_brain.side_length + 2

        # calculate the size and layout of the window
        self.window_width_pixels = Window_width_pixels
        self.pixels_per_unit = self.window_width_pixels / self.vis_side_length
        self.window_height_pixels = self.vis_side_length * self.pixels_per_unit

        self.canvas_items = []

    def _generateUnitLines(self, spacing, world_width, world_height, colour):
        # vertical
        items = []
        i = 1
        while i <= world_width:
            items.append(
                self.canvas.create_line(
                    self._convertToPixels(i),
                    self._convertToPixels(0),
                    self._convertToPixels(i),
                    self._convertToPixels(world_height),
                    fill=colour,
                )
            )
            i += spacing

        # horizontal
        i = 1
        while i <= world_height:
            items.append(
                self.canvas.create_line(
                    self._convertToPixels(0),
                    self._convertToPixels(i),
                    self._convertToPixels(world_width),
                    self._convertToPixels(i),
                    fill=colour,
                )
            )
            i += spacing

        return items

    def update(self):
        self.canvas.delete("all")

        self.canvas_items = []

        # draw lines to indicate the units
        # individual units
        self.canvas_items.extend(
            self._generateUnitLines(
                1, self.vis_side_length, self.vis_side_length, "light grey"
            )
        )
        # 10s of units
        # these are done seperately so that they overlay the grey lines underneath
        self.canvas_items.extend(
            self._generateUnitLines(
                10, self.vis_side_length, self.vis_side_length, "light blue"
            )
        )

        # draw the boundries of the brain
        self.canvas_items.append(
            self.canvas.create_rectangle(
                self._convertToPixels(1),
                self._convertToPixels(1),
                self._convertToPixels(self.vis_side_length - 1),
                self._convertToPixels(self.vis_side_length - 1),
                fill="",
                outline="red",
            )
        )

        for neuron in self.connected_brain.neurons:
            self.drawConnections(neuron)

        #  create the circles for the neurons
        for neuron in self.connected_brain.neurons:

            fillColour = "ghost white"

            if neuron.output_factor <= 0:
                outlineColour = "red2"
            else:
                outlineColour = "blue2"

            if neuron.type != "null":

                if neuron.name == "EP":
                    fillColour = "yellow"
                elif neuron.name == "DP":
                    fillColour = "gold"
                if neuron.name == "PPx":
                    fillColour = "cyan"
                elif neuron.name == "PPy":
                    fillColour = "spring green"
                elif neuron.name == "VF":
                    fillColour = "dark orange"
                elif neuron.name == "AVF":
                    fillColour = "pink"
                elif neuron.name == "EA":
                    fillColour = "lawn green"
                else:
                    for i in range(bot.EYE_RESOLUTION):
                        if neuron.name == "Eye Segment" + str(int(i)) + "R":
                            fillColour = "red"
                        elif neuron.name == "Eye Segment" + str(int(i)) + "G":
                            fillColour = "green"
                        elif neuron.name == "Eye Segment" + str(int(i)) + "B":
                            fillColour = "blue"
                        elif neuron.name == "Eye Segment" + str(int(i)) + "Dis":
                            fillColour = "purple"

            self.canvas_items.append(
                self.createNeuronCircle(neuron, fillColour, outlineColour)
            )

        self.window.update()

    def createNeuronCircle(
        self, neuron: brain.neuron.Neuron, fillColour, outlineColour
    ):
        """
        Creates a circle with the centre in the x and y position and a radius
        returns the circle object.
        """
        radius = valueToNeuronRadius(neuron.getValue())
        # point 1
        UL_x = self._convertToPixels(neuron.location[0] - radius + 1)
        UL_y = self._convertToPixels(neuron.location[1] - radius + 1)
        # point 2
        LR_x = self._convertToPixels(neuron.location[0] + radius + 1)
        LR_y = self._convertToPixels(neuron.location[1] + radius + 1)

        return self.canvas.create_oval(
            UL_x, UL_y, LR_x, LR_y, fill=fillColour, outline=outlineColour
        )

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


def main():
    testbrain = brain.Brain(file_name=r"Bots6\brains\#eb403fstarter_brain.txt")
    window1 = BrainDisplay()
    testbrain.configureNeurons()

    class box:
        def __init__(self) -> None:
            self.val = 0.0

        def getVal(self):
            self.val = ((self.val + 1) / 100) % 1
            return self.val

    thing = box()

    testbrain.neurons[0].convertToExternalInput("test", thing.getVal)
    window1.connectBrain(testbrain)
    window1.window.title("test brain")
    while True:
        testbrain.think()
        window1.update()


if __name__ == "__main__":
    main()
