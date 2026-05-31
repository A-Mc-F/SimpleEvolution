import json
import math
import random
import copy as cp

MAX_NEURON_CONNECTION_RANGE_SQ = 1.5**2
MIN_NEURON_CONNECTION_RANGE_SQ = 0.5**2

# the strength of the sigmoid function (initialy 10)
SIGMOID_MULTIPLIER = 5


class Neuron:
    """
    This neuron makes calculations based on its position relative to the neurons surrounding it
    """

    def __init__(self, name="Blank Neuron", location=[0, 0], output_factor=None):
        self.name = name
        self.location = location
        self.type = "null"

        self.inputs = []
        self.weights = []
        self.stasis_point = 0.0

        # initialise the output of the neuron
        # -1.0 to 1.0; can determine if the output is beneficial or detrimental
        self.output_factor = (
            output_factor if output_factor != None else random.choice([-1, 1])
        )

        self.value = 0.0
        self.prior_values = []

    def connectToNeighbours(self, neuron_list: list["Neuron"], brain_side_length):
        """
        searches through the other neurons to find neighbours.
        assigns their outputs to this neuron's inputs.
        also calculates their weight based on their distance
        """
        if self.type == "input":
            return

        def shortest_distance(point1, point2, max_range):
            # Calculate direct distance
            direct_distance = abs(point2 - point1)

            # Calculate wrapped distance
            wrapped_distance = max_range - direct_distance

            # Return the minimum distance
            return min(direct_distance, wrapped_distance)

        # wipes the previously held inputs
        self.inputs = []
        self.weights = []
        self.stasis_point = 0.0
        for other_neuron in neuron_list:
            if other_neuron is self:
                continue

            x_dis = shortest_distance(
                self.location[0], other_neuron.location[0], brain_side_length
            )
            y_dis = shortest_distance(
                self.location[1], other_neuron.location[1], brain_side_length
            )
            distance_SQ = x_dis**2 + y_dis**2
            if (
                distance_SQ <= MAX_NEURON_CONNECTION_RANGE_SQ
                and distance_SQ >= MIN_NEURON_CONNECTION_RANGE_SQ
            ):
                distance_percent = 1.0 - (
                    distance_SQ - MIN_NEURON_CONNECTION_RANGE_SQ
                ) / (MAX_NEURON_CONNECTION_RANGE_SQ - MIN_NEURON_CONNECTION_RANGE_SQ)
                self.inputs.append(other_neuron)
                self.weights.append(distance_percent)
                self.stasis_point += distance_percent * other_neuron.output_factor

    def convertToExternalInput(self, name, input):
        self.name = name
        self.inputs = [input]
        self.weights = []
        self.type = "input"

    def convertToExternalOutput(self, name, type):
        self.name = name
        self.type = "output"
        if type == 0:
            return self.getValue
        if type == 1:
            return self.getValue2

    def calculateValue(self):
        """
        calculates the output of the neuron
        """
        if self.type == "input":
            self.value = self.inputs[0]()
        elif len(self.weights) == 0:
            return
        else:
            total = 0.0

            # adds up all the inputs
            for i, w in zip(self.inputs, self.weights):
                total += i.getOutput() * w

            # the sigmoid function
            # Input = -1 -> Output = 0.0
            # Input = 0 -> Output = 0.5
            # Input = 1 -> Output = 1.0
            self.value = 1 / (
                1 + math.e ** (-1 * (total - self.stasis_point) * SIGMOID_MULTIPLIER)
            )

    def getOutput(self):
        return self.value * self.output_factor

    def getValue(self):
        """
        0 to 1
        """
        return self.value

    def getValue2(self):
        """-1 to 1"""
        return self.value * 2 - 1

    def copy(self):
        return Neuron(
            name=self.name,
            location=cp.deepcopy(self.location),
            output_factor=cp.deepcopy(self.output_factor),
        )

    def info(self):
        return (
            json.dumps(self.name)
            + ";"
            + json.dumps(self.location)
            + ";"
            + json.dumps(self.output_factor)
        )


def fromLine(line: str):
    segments = line.split(";")
    name = json.loads(segments[0])
    location = json.loads(segments[1])
    output_factor = json.loads(segments[2])
    return Neuron(name, location, output_factor)


def main():
    pass


if __name__ == "__main__":
    main()
