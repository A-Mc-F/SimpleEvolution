import neuron
import random
import math
import func_lib as fl

CHANCE_OF_MUTATION = 0.2


class Brain:
    """Handles all the neurons
    each of the neurons will be placed in a field.
    the result of each neuron will come from it's neighbours
    the weights between each neuron will be based on its proximity"""

    def __init__(self, num_of_neurons=60, file_name=None):
        self.num_of_inputs = 0
        self.num_of_outputs = 0
        self.num_of_neurons = num_of_neurons
        self.side_length = math.sqrt(num_of_neurons)

        self.neurons: list[neuron.Neuron] = []

        if file_name == None:
            # Create Neurons
            for _ in range(self.num_of_neurons):
                self.neurons.append(self._makeNewNeuron())

        else:
            # collect data about neurons
            with open(file_name, "r") as file_object:
                for line in file_object.readlines():
                    line = str(line)
                    if line != "~":
                        self.neurons.append(neuron.fromLine(line))

        # initialise neuron inputs from one another
        self.configureNeurons()

    def _makeNewNeuron(self):
        return neuron.Neuron(
            name="Neuron " + str(len(self.neurons)),
            location=[
                self.side_length * random.random(),
                self.side_length * random.random(),
            ],
        )

    def configureNeurons(self):
        """initialise all the neurons inputs
        will select from surounding Neurons"""
        self.side_length = math.sqrt(len(self.neurons))
        for N in self.neurons:
            N.connectToNeighbours(self.neurons, self.side_length)

    def think(self):
        # each neuron collects its inputs from the list on neurons
        for neuron in self.neurons:
            neuron.calculateValue()

    def setInput(self, name, input_function):
        # inputs go to first neurons
        self.neurons[self.num_of_inputs].convertToExternalInput(name, input_function)
        self.num_of_inputs += 1

    def setOutput(self, name, type):
        # gets the outputs from the end of the list of neurons
        self.num_of_outputs += 1
        return self.neurons[-self.num_of_outputs].convertToExternalOutput(name, type)

    def copy(self):
        """returns a copy of the brain
        will not have the inputs or outputs assigned"""
        new_brain = Brain()

        new_brain.neurons = [N.copy() for N in self.neurons]
        new_brain.configureNeurons()

        return new_brain

    def save(self, file_location):
        brainFile = open(file_location, "w")

        for neuron in self.neurons:
            brainFile.write(neuron.info() + "\n")

        brainFile.write("~")
        brainFile.close()

    def mutate(self):
        for neuron in self.neurons:
            for loc_axis in neuron.location:
                loc_axis = fl.combine_wrap(
                    loc_axis,
                    fl.try_mutate(loc_axis, 0, self.side_length, CHANCE_OF_MUTATION),
                    0,
                    self.side_length,
                )
