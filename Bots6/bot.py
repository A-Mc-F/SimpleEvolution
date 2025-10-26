from __future__ import annotations
import math
import random
import neural_net as neural_net
import visualiser
import simulator
import copy
import func_lib as fl


# bot simulation constants
# breeding
MIN_ENERGY_TO_BREED = 10  # below this energy level the bot is too tired to breed
MIN_BREED_DELAY = 10  # seconds between "sessions"
ENERGY_LOST_FROM_BREEDING = 2.5
CHANCE_OF_MUTATION = 1.0 / 15.0

# apperance
RADIUS = 0.5  # unit (size of the bot)

# eating
EAT_DELAY = 7  # seconds between meals

# energy
MOVEMENT_ENERGY_LOSS_RATE = 0.05  # units per unit moved
BASE_ENERGY_LOSS_RATE = 0.9  # units per second
MAX_ENERGY_RESERVE = 100

BOUNDRY_DAMAGE = 8

# sight
MAX_VIEW_DISTANCE = 40.0
FOV_ANGLE = math.pi / 2.0  # radians
# the number of segments of vision (note this will require adapatble number of neurons. Min 1)
EYE_RESOLUTION = 5

# Mobility
MAX_TURN_SPEED = math.pi / 1.5  # radians per second
MAX_SPEED = 3.0  # units per second


class Bot:
    """Defines a Bot with all its attributes"""

    def __init__(
        self,
        simulator: simulator.Simulator,
        name="exampleBot",
        max_speed=MAX_SPEED,
        FOV_Angle=FOV_ANGLE,
        max_energy=MAX_ENERGY_RESERVE,
        colour_RGB=None,
    ):
        # simulator
        self.simulator = simulator

        if colour_RGB == None:
            colour_RGB = [random.random(), random.random(), random.random()]
        # bot attributes
        self.attributes = Attributes(
            self, name, max_speed, MAX_TURN_SPEED, colour_RGB, max_energy, RADIUS
        )

        self.dead = False

        # bot internal variables
        self.energy_level = self.attributes.energy_limit
        self.breeding_points = 0
        self.total_rewards_collected = 0
        self.time_since_last_child = 0.0
        self.time_since_last_meal = 0.0

        # world variables
        self.birth_time = copy.copy(self.simulator.simulated_duration)
        self.age = 0.0

        # bot enviromental variables
        self.position = [
            self.simulator.world.width / 2.0
            + self.simulator.world.width * 0.2 * (random.random() * 2 - 1),
            self.simulator.world.height / 2.0
            + self.simulator.world.height * 0.2 * (random.random() * 2 - 1),
        ]  # x,y
        self.direction = (
            2 * math.pi * random.random()
        )  # angle from x axis, anti-clockwise, radians

        # eye
        self.resolution_of_eye = EYE_RESOLUTION
        self.FOV_angle = FOV_Angle
        self.max_view_distance = MAX_VIEW_DISTANCE
        self.eye = Eye(self)

        self.brain: neural_net.Network = None

    def connectToBrain(self):
        self.brain.num_of_inputs = 0
        self.brain.num_of_outputs = 0
        self.brain.configureNeurons()
        self.assignBrainInputs()
        self.assignBrainOutputs()

    def assignBrainInputs(self):

        self.brain.num_of_inputs = 0

        self.brain.setInput("EP", self.getEnergyPercent)
        self.brain.setInput("DP", self.getDirectionPercent)
        self.brain.setInput("PPx", self.getPPx)
        self.brain.setInput("PPy", self.getPPy)

        for segment in self.eye.segments:
            self.brain.setInput(segment.name + "Dis", segment.getDisPercent)
            self.brain.setInput(segment.name + "R", segment.getRed)
            self.brain.setInput(segment.name + "G", segment.getGreen)
            self.brain.setInput(segment.name + "B", segment.getBlue)

    def assignBrainOutputs(self):
        def neuronToFactor(neuron_output_function):
            """Returns a wrapper function which converts
            the 0 to 1 output of a neuron to -1 to 1"""

            def convertedValue():
                """Wrapper function which converts the neuron
                output to the -1 to 1 scale"""
                return neuron_output_function() * 2 - 1

            return convertedValue

        self.brain.num_of_outputs = 0

        self.angular_velocity_factor = self.brain.setOutput("AVF", 1)
        self.velocity_factor = self.brain.setOutput("VF", 1)
        self.eat_action = self.brain.setOutput("EA", 0)

    def simulate(self):
        # determine the elapsed time
        self.calculateInternalVariables()
        # consider objects
        self.loopThroughObjects()
        # run calculations through the brain
        self.think()
        # move bot accoringly
        self.move()
        # calculate energy consumption
        self.calculate_energy()
        # if died
        if self.dead:
            print(f"{self.attributes.name} [{self.attributes.colourHEX}] died")
            self.simulator.sim_objects.remove(self)

    def calculateInternalVariables(self):
        # how long the bot has been alive
        self.age += self.simulator.simulated_time_step

        # updates internal clocks accordingly
        self.time_since_last_child += self.simulator.simulated_time_step
        self.time_since_last_meal += self.simulator.simulated_time_step

    def loopThroughObjects(self):
        self.eye.reset()
        for object in self.simulator.sim_objects:
            if object.attributes.name != self.attributes.name:
                self.eye.see(object)
                self.eat(object)
                self.breed(object)

    def eat(self, object):
        """
        Bot will attempt to eat from the object. Will only succeed if close enough
        updates the bot's energy level
        Returns True if successfull, otherwise False.
        """
        import reward

        if object.__class__ != reward.Reward:
            return

        self.eat_success = False
        target_x_pos = object.position[0]
        target_y_pos = object.position[1]

        # check the distance from the object
        distance = math.sqrt(
            (self.position[0] - target_x_pos) ** 2
            + (self.position[1] - target_y_pos) ** 2
        )

        # will eat if;
        # - within range
        # - hasn't eaten recently
        # - wants to (neuron)
        if (
            (distance <= RADIUS + 1)
            and self.time_since_last_meal >= EAT_DELAY
            and self.eat_action() <= 0.8
        ):
            # print(self.attributes.name + " took a nibble")

            # adds an energy boost to the energy level upto the maximum energy level
            energy_boost = 30
            self.energy_level += energy_boost
            if self.energy_level > self.attributes.energy_limit:
                self.energy_level = self.attributes.energy_limit

            # makes the bot "age" and have less vitality
            if self.attributes.energy_limit >= 30:
                self.attributes.energy_limit -= 2

            # the rewards for getting a reward
            self.total_rewards_collected += 1
            self.breeding_points += 2
            self.time_since_last_meal = 0

            # flag for the simulator
            self.eat_success = True

            object.consumed()

        # eating will consume a bit of energy, decentivising the bots from attempting to eat continuously
        self.energy_level -= 0.001

    def willingToBreed(self) -> bool:
        # check if this bot is willing to breed
        result = (
            self.breeding_points >= 1
            and self.energy_level >= MIN_ENERGY_TO_BREED
            and self.time_since_last_child >= MIN_BREED_DELAY
        )

        return result

    def sameSpecies(self, other: Bot) -> bool:
        # check if the bots are of the same species
        colour_range = 5 / 255.0
        result = True
        for i in range(3):
            if (
                self.attributes.colourRGB[i]
                <= other.attributes.colourRGB[i] + colour_range / 2
                and self.attributes.colourRGB[i]
                >= other.attributes.colourRGB[i] - colour_range / 2
            ):
                result = result and True
            else:
                result = False

        return result

    def breed(self, other_bot: Bot):
        """
        the assigned bot will attempt to breed with the given bot providing they are both eligable
        returns the child bot of the two parents.
        """

        if "bot" in str.lower(other_bot.attributes.name):
            # check if simulator can accept more bots
            if not self.simulator.canAddObject():
                return

            # check not self
            if self == other_bot:
                print("is self")
                return

            # check if this bot is still willing (might not if mated with previous bot)
            if not self.willingToBreed():
                return

            # check if other bot is still willing (might not if mated with a previous bot)
            if not other_bot.willingToBreed():
                return

            # check if the two bots are of the same species
            if not self.sameSpecies(other_bot):
                return

            child_name = f"bot_{self.simulator.object_counter}"

            print(
                f"{self.attributes.name} {self.attributes.colourHEX} mated with {other_bot.attributes.name} {other_bot.attributes.colourHEX} to create {child_name}"
            )

            for bot in [self, other_bot]:
                bot.time_since_last_child = 0  # reset breeding timers
                bot.breeding_points -= 1  # remove a breeding point
                bot.energy_level -= ENERGY_LOST_FROM_BREEDING  # remove some energy

            # determine whos traits will dominate
            if self.total_rewards_collected > other_bot.total_rewards_collected:
                domBot = self  # dominate traits
                recBot = other_bot  # recessive traits
            else:
                recBot = self
                domBot = other_bot

            # make love (generate the child bot)
            childBot = Bot(
                self.simulator, "new_bot", colour_RGB=domBot.attributes.colourRGB
            )
            childBot.position = domBot.position.copy()
            childBot.attributes.__dict__.update(domBot.attributes.__dict__.copy())
            childBot.brain = domBot.brain.copy()
            childBot.eye = Eye(childBot)

            childBot.attributes.name = child_name
            childBot.direction = 2 * math.pi * random.random()
            childBot.attributes.generation += 1
            childBot.attributes.familyHistory = domBot.attributes.ownFamilyHistory()

            # give child bot colour
            result_colour_RGB = []
            for i in range(3):
                result_colour_RGB.append(
                    fl.Combine1(
                        domBot.attributes.colourRGB[i],
                        recBot.attributes.colourRGB[i],
                        0,
                        1,
                    )
                )
            childBot.attributes.colourRGB = result_colour_RGB
            childBot.attributes.assignRGBtoHEX()

            childBot.circleVisual.changeColour()

            i = 0
            for neuron in childBot.brain.neurons:
                neuron.location[0] = fl.Combine_Wrap(
                    neuron.location[0],
                    recBot.brain.neurons[i].location[0],
                    0,
                    childBot.brain.side_length,
                )
                neuron.location[1] = fl.Combine_Wrap(
                    neuron.location[1],
                    recBot.brain.neurons[i].location[1],
                    0,
                    childBot.brain.side_length,
                )
                neuron.output_factor = fl.Combine1(
                    neuron.output_factor, recBot.brain.neurons[i].output_factor, -1, 1
                )
                i += 1

            childBot.connectToBrain()

            childBot.attributes.maxSpeed = float(domBot.attributes.maxSpeed) + (
                random.random() * 0.1 - 0.05
            )
            childBot.attributes.maxTurnSpeed = float(domBot.attributes.maxTurnSpeed) + (
                random.random() * 0.1 - 0.05
            )
            childBot.attributes.maxEnergyReserve = float(
                domBot.attributes.maxEnergyReserve + (random.random() * 0.1 - 0.05)
            )

            childBot.energy_level = childBot.attributes.maxEnergyReserve
            childBot.total_rewards_collected = 0

            self.simulator.addObject(childBot)

    def move(self):
        # find out the direction which the bot is facing (added onto the current direction)
        self.direction += (
            self.angular_velocity_factor()
            * self.attributes.maxTurnSpeed
            * self.simulator.simulated_time_step
        )
        # limit the angle to be within 2*Pi radians or 360 degrees
        self.direction = self.direction % (2 * math.pi)
        # find out how far the bot has traveled
        displacement = (
            self.velocity_factor()
            * self.attributes.maxSpeed
            * self.simulator.simulated_time_step
        )
        # find the displacement along the axis
        x_displacement = math.cos(self.direction) * displacement
        y_displacement = -math.sin(self.direction) * displacement
        # update the position
        self.position = [
            self.position[0] + x_displacement,
            self.position[1] + y_displacement,
        ]

        # check if the bot has reached the boundry
        # Right boundry
        if self.position[0] > self.simulator.world.width - self.attributes.radius:
            self.energy_level -= BOUNDRY_DAMAGE
            self.position[0] = self.simulator.world.width - self.attributes.radius * 2
        # Bottom boundry
        if self.position[1] > self.simulator.world.height - self.attributes.radius:
            self.energy_level -= BOUNDRY_DAMAGE
            self.position[1] = self.simulator.world.height - self.attributes.radius * 2
        # Left boundry
        if self.position[0] < self.attributes.radius:
            self.energy_level -= BOUNDRY_DAMAGE
            self.position[0] = self.attributes.radius * 2
        # Top boundry
        if self.position[1] < self.attributes.radius:
            self.energy_level -= BOUNDRY_DAMAGE
            self.position[1] = self.attributes.radius * 2

    def getPPx(self):
        return self.position[0] / self.simulator.world.width

    def getPPy(self):
        return self.position[1] / self.simulator.world.height

    def think(self):
        self.brain.think()

    def getDirectionPercent(self):
        return (self.direction % math.pi) / math.pi

    def calculate_energy(self):
        # how much energy was used
        base_energy_loss = BASE_ENERGY_LOSS_RATE * self.simulator.simulated_time_step

        movement_energy_loss = (
            self.attributes.maxSpeed
            * abs(self.velocity_factor())
            * MOVEMENT_ENERGY_LOSS_RATE
            * self.simulator.simulated_time_step
        )

        # take from resoviour
        self.energy_level -= movement_energy_loss + base_energy_loss

        # limits to 0
        self.dead = self.energy_level <= 0

        # limits above (shouldnt be possible but is somehow)
        if self.energy_level > self.attributes.energy_limit:
            self.energy_level = self.attributes.energy_limit

    def getEnergyPercent(self):
        return self.energy_level / self.attributes.energy_limit

    def saveBrain(self, file_location=None):
        if file_location == None:
            file_location = "brains/" + self.attributes.name + "_brain.txt"

        self.brain.save(file_location)

    def copy(self):
        copy_bot = Bot(
            self.simulator,
            self.attributes.name,
            self.attributes.maxSpeed,
            self.FOV_angle,
            self.attributes.maxEnergyReserve,
            self.attributes.colourRGB,
        )
        if self.brain != None:
            copy_bot.brain = self.brain.copy()
        return copy_bot

    def mutate(self):
        self.attributes.mutate()
        self.brain.mutate()


class Attributes:
    """
    Defines and handles all a bots internal and external attributes.
    """

    def __init__(
        self, bot: Bot, name, max_speed, max_turn_speed, colourRGB, max_energy, radius
    ):
        self.bot = bot

        self.name = name
        self.generation = 0
        self.familyHistory = ""
        self.maxSpeed = max_speed
        self.maxTurnSpeed = max_turn_speed
        self.colourRGB = colourRGB
        self.assignRGBtoHEX()
        self.maxEnergyReserve = max_energy
        self.energy_limit = self.maxEnergyReserve
        self.radius = radius

    def save(self, file_location=None):
        if file_location == None:
            file_location = "attributes/" + self.name + "_attributes.txt"

        attributeFile = open(file_location, "w")

        attributeFile.write("Name: " + self.name + "\n")
        attributeFile.write("Generation: " + str(self.generation) + "\n")
        attributeFile.write("Family History: " + self.ownFamilyHistory() + "\n")
        attributeFile.write("Max Speed: " + str(self.maxSpeed) + "\n")
        attributeFile.write("Max Turn Speed: " + str(self.maxTurnSpeed) + "\n")
        attributeFile.write("Colour: " + self.colourHEX + "\n")
        attributeFile.write("Energy Reserve: " + str(self.maxEnergyReserve))

        attributeFile.close()

    def load(self, file_location):
        with open(file_location, "r") as attributeFile:

            name = attributeFile.readline()
            generation = attributeFile.readline()
            family_history = attributeFile.readline()
            max_speed = attributeFile.readline()
            max_turn_speed = attributeFile.readline()
            colour = attributeFile.readline()
            energy_reserve = attributeFile.readline()

            name = name.strip()
            generation = generation.strip()
            family_history = family_history.strip()
            max_speed = max_speed.strip()
            max_turn_speed = max_turn_speed.strip()
            colour = colour.strip()
            energy_reserve = energy_reserve.strip()

            name = name.lstrip("Name: ")
            generation = generation.lstrip("Generation: ")
            family_history = family_history.lstrip("Family History: ")
            max_speed = max_speed.lstrip("Max Speed: ")
            max_turn_speed = max_turn_speed.lstrip("Max Turn Speed: ")
            colour = colour.lstrip("Colour: ")
            energy_reserve = energy_reserve.lstrip("Energy Reserve: ")

            self.name = name
            self.generation = int(generation)
            self.familyHistory = family_history
            self.maxSpeed = float(max_speed)
            self.maxTurnSpeed = float(max_turn_speed)
            self.colourHEX = colour
            self.assignHEXtoRGB()

            self.maxEnergyReserve = float(energy_reserve)

            self.changeCircleColour()

    def ownFamilyHistory(self):
        return (
            self.familyHistory
            + " ~> (N:"
            + self.name
            + " G:"
            + str(self.generation)
            + ")"
        )

    def mutate(self):
        """
        Mutates the attributes for the bot
        """
        self.maxSpeed = self.maxSpeed + (random.random() - 0.5) * 0.3
        self.maxTurnSpeed = self.maxTurnSpeed + (random.random() - 0.5) * 0.3
        self.maxEnergyReserve = self.maxEnergyReserve + (random.random() - 0.5) * 0.3
        self.energy_limit = self.maxEnergyReserve

        new_colours = []
        for i in range(3):
            new_colours.append(
                max(min(self.colourRGB[i] + (random.random() - 0.5) * 0.1, 1), 0)
            )
        self.setRGB(new_colours)

    def setRGB(self, rgb_array):
        self.colourRGB = rgb_array
        self.assignRGBtoHEX()

    def assignRGBtoHEX(self):
        self.colourHEX = visualiser.RGBtoHEX(self.colourRGB)

    def assignHEXtoRGB(self):
        self.colourRGB = visualiser.HEXtoRGB(self.colourHEX)


class Eye:
    class Segment:
        def __init__(self, name, sAngle, eAngle):
            self.name = name
            self.startAngle = sAngle
            self.endAngle = eAngle
            self.disPercent = 0.0
            self.RGB = [0.0, 0.0, 0.0]

        def reset(self):
            self.disPercent = 0.0
            self.RGB = [0.0, 0.0, 0.0]

        def getDisPercent(self):
            return self.disPercent

        def getRed(self):
            return self.RGB[0]

        def getGreen(self):
            return self.RGB[1]

        def getBlue(self):
            return self.RGB[2]

    def __init__(self, bot: Bot):
        self.bot = bot
        self.angle_of_left_view_g = 0.0
        self.segment_angle = self.bot.FOV_angle / self.bot.resolution_of_eye
        self.segments: list[Eye.Segment] = []
        for i in range(self.bot.resolution_of_eye):
            self.segments.append(
                Eye.Segment(
                    "Eye Segment" + str(int(i)),
                    i * self.segment_angle,
                    (i + 1) * self.segment_angle,
                )
            )

    def see(self, object: Bot):
        # determine where the object is in comparison to self
        x_displacement = object.position[0] - self.bot.position[0]
        y_displacement = self.bot.position[1] - object.position[1]
        # check if too far away, if so, skip
        distance_to_object = math.sqrt(x_displacement**2 + y_displacement**2)

        if distance_to_object > self.bot.max_view_distance:
            return
        # determine the angle to the object from self in global coords
        angle_to_object_g = math.atan2(y_displacement, x_displacement)
        # determine the angle from the left most side of the bots view
        angle_of_object_in_view = (angle_to_object_g - self.angle_of_left_view_g) % (
            2 * math.pi
        )
        # if the object is outside the field of view skip it
        if angle_of_object_in_view > self.bot.FOV_angle:
            return

        for segment in self.segments:
            if (
                angle_of_object_in_view >= segment.startAngle
                and angle_of_object_in_view < segment.endAngle
            ):
                distance_percent = 1.0 - distance_to_object / self.bot.max_view_distance
                if segment.disPercent <= distance_percent:
                    segment.disPercent = distance_percent
                    segment.RGB = object.attributes.colourRGB

    def reset(self):
        # resets all the view segments
        for segment in self.segments:
            segment.reset()

        # determine the global angle of the left view
        self.angle_of_left_view_g = (self.bot.direction - self.bot.FOV_angle / 2) % (
            2 * math.pi
        )


def main():
    sim = simulator.Simulator()
    # create a new bot
    new_bot = Bot(
        sim,
    )


if __name__ == "__main__":
    main()
