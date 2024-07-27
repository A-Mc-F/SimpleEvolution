import json
import math
import random


class Neuron:
    """
    This neuron makes calculations based on its position relative to the neurons surrounding it
    """

    def __init__(self, name="Blank Neuron", location=[0, 0], output_factor=None):

        self.max_range_of_neuron = 1
        self.min_range_of_neuron = 0.05

        # the strength of the sigmoid function (initialy 10)
        self.sigmoid_multiplier = 5

        self.name = name
        self.location = location
        self.type = "null"

        self.inputs = []
        self.weights = []

        # initialise the output of the neuron
        # -1.0 to 1.0; can determine if the output is beneficial or detrimental
        if output_factor == None:
            if random.random() > 0.5:
                self.output_factor = 1.0
            else:
                self.output_factor = -1.0
        else:
            self.output_factor = output_factor
        self.value = 0.0

    def connectToNeighbours(self, neuron_list: list["Neuron"], brain_side_length):
        """
        searches through the other neurons to find neighbours.
        assigns their outputs to this neuron's inputs.
        also calculates their weight based on their distance
        """

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
        for other_neuron in neuron_list:
            x_dis = shortest_distance(
                self.location[0], other_neuron.location[0], brain_side_length
            )
            y_dis = shortest_distance(
                self.location[1], other_neuron.location[1], brain_side_length
            )
            distance = math.sqrt(x_dis**2 + y_dis**2)
            if (
                distance <= self.max_range_of_neuron
                and distance >= self.min_range_of_neuron
            ):
                distance_percent = 1.0 - (distance - self.min_range_of_neuron) / (
                    self.max_range_of_neuron - self.min_range_of_neuron
                )
                self.inputs.append(other_neuron)
                self.weights.append(distance_percent)

    def convertToExternalInput(self, name, input):
        self.name = name
        self.inputs = [input]
        self.weights = []
        self.type = "input"

    def convertToExternalOutput(self, name):
        self.name = name
        self.type = "output"
        return self.getValue

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
            # TF = -1 -> O = 0.0
            # TF = 0 -> O = 0.5
            # TF = 1 -> O = 1.0
            self.value = 1 / (1 + math.e ** (total * self.sigmoid_multiplier))

    def getOutput(self):
        return self.value * self.output_factor

    def getValue(self):
        return self.value

    def copy(self):
        return Neuron(
            name=self.name, location=self.location, output_factor=self.output_factor
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
