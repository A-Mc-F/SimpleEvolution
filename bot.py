from __future__ import annotations
import math
import random
import brain as brain
import copy
import func_lib as fl
from reward import EnergyStore, Reward
from sim_obj import SimObj, Position, Pose
import display
import inspect
import pygame

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # from simulator import Simulator
    pass

# bot simulation constants
# breeding
MIN_ENERGY_PERCENT_TO_BREED = (
    0.4  # below this energy level the bot is too tired to breed
)
MIN_BREED_DELAY = 10  # seconds between "sessions"

# apperance
RADIUS = 0.5  # unit (size of the bot)

# eating
EAT_DELAY = 10.0  # seconds between meals
EATING_EFFICIENCY = 0.9  # percentage of energy converted to energy store
EAT_RANGE_SQ = (RADIUS + 3) ** 2
EAT_DAMAGE = 12
NUTRITIONAL_PERCENT = 0.6


# energy
MOVEMENT_ENERGY_LOSS_RATE = 0.1  # units per unit moved
ROTATION_ENERGY_LOSS_RATE = 0.1  # units per degree rotated
BASE_ENERGY_LOSS_RATE = 0.1  # units per second
MAX_ENERGY_RESERVE = 100

BOUNDRY_DAMAGE = 8

# sight
MAX_VIEW_DISTANCE = 15.0
VIEW_RANGE_SQ = MAX_VIEW_DISTANCE**2
FOV_ANGLE_RAD = 2 * math.pi * (30 / 360)  # radians
# the number of segments of vision (note this will require adapatble number of neurons. Min 1)
EYE_RESOLUTION = 2

# Mobility
MAX_TURN_SPEED = math.pi / 1.5  # radians per second
MAX_SPEED = 3.0  # units per second


class Bot(SimObj):
    """Defines a Bot with all its attributes"""

    def __init__(
        self,
        simulator,
        name="exampleBot",
        max_speed=MAX_SPEED,
        FOV_Angle=FOV_ANGLE_RAD,
        max_energy=MAX_ENERGY_RESERVE,
        colour_RGB=None,
    ):
        super().__init__(simulator)
        # simulator
        self.simulator = simulator

        if colour_RGB == None:
            colour_RGB = [random.random(), random.random(), random.random()]
        # bot attributes
        self.attributes = Attributes(
            self, name, max_speed, MAX_TURN_SPEED, colour_RGB, RADIUS
        )

        self.dead = False

        # bot internal variables
        self.energy = EnergyStore(max_energy)
        self.total_rewards_collected = 0
        self.time_since_last_child = 0.0
        self.time_since_last_meal = 0.0

        # world variables
        self.birth_time = copy.copy(self.simulator.simulated_duration)
        self.age = 0.0

        # bot enviromental variables
        self.pose = Pose(
            self.simulator.world.width / 2.0
            + self.simulator.world.width * 0.2 * (random.random() * 2 - 1),
            self.simulator.world.height / 2.0
            + self.simulator.world.height * 0.2 * (random.random() * 2 - 1),
            2 * math.pi * random.random(),
        )  # x,y

        # eye
        self.resolution_of_eye = EYE_RESOLUTION
        self.FOV_angle = FOV_Angle
        self.max_view_distance_sq = VIEW_RANGE_SQ
        self.eye = Eye(self)

        self.brain: brain.Brain = None
        self.visual: BotVisual = BotVisual(self)

    def connect_to_brain(self):
        """
        configures the brain, connects inputs, outputs, and interneurons"""
        self.brain.num_of_inputs = 0
        self.brain.num_of_outputs = 0
        self.assign_brain_inputs()
        self.assign_brain_outputs()
        self.brain.configureNeurons()

    def assign_brain_inputs(self):

        self.brain.num_of_inputs = 0

        self.brain.setInput("EP", self.energy.get_percent)
        self.brain.setInput("DP", self.get_direction_percent)
        self.brain.setInput("PPx", self.get_position_x_percent)
        self.brain.setInput("PPy", self.get_position_y_percent)

        for segment in self.eye.segments:
            self.brain.setInput(segment.name + "Dis", segment.getDisPercent)
            self.brain.setInput(segment.name + "R", segment.getRed)
            self.brain.setInput(segment.name + "G", segment.getGreen)
            self.brain.setInput(segment.name + "B", segment.getBlue)

    def assign_brain_outputs(self):
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
        self.time_step()
        if self.dead:
            return
        # consider objects
        nearby_objects = [
            obj
            for obj in self.simulator.grid.query_radius(self, MAX_VIEW_DISTANCE)
            if obj is not self
        ]
        self.observe(nearby_objects)
        if self.dead:
            return
        # run calculations through the brain
        self.think()
        if self.dead:
            return
        # move bot accoringly
        self.act(nearby_objects)

    def observe(self, nearby):
        self.eye.reset()
        for object in nearby:
            self.eye.see(object)

    def time_step(self):
        # how long the bot has been alive
        self.age += self.simulator.simulated_time_step

        # updates internal clocks accordingly
        self.time_since_last_child += self.simulator.simulated_time_step
        self.time_since_last_meal += self.simulator.simulated_time_step

        self.take_energy(BASE_ENERGY_LOSS_RATE * self.simulator.simulated_time_step)

        # makes the bot "age" and have less vitality
        self.energy.degrade_store(0.05 * self.simulator.simulated_time_step)

    def eat(self, target: SimObj):
        """
        Bot will attempt to eat from the object. Will only succeed if close enough
        updates the bot's energy level
        Returns True if successfull, otherwise False.
        """
        # will eat if;
        # - within range
        # - hasn't eaten recently
        # - wants to (neuron)
        if (
            self.time_since_last_meal >= EAT_DELAY
            and self.eat_action() <= 0.75
            and self.distance_sq(target) < EAT_RANGE_SQ
            and isinstance(target, Reward)
        ):

            # adds an energy boost to the energy level upto the maximum energy level
            took = target.consumed(EAT_DAMAGE)
            gained = took * EATING_EFFICIENCY
            self.energy.add(gained)

            # the rewards for getting a reward
            if isinstance(target, Reward):
                self.total_rewards_collected += 1
            self.time_since_last_meal = 0.0

            print(
                f"{self.attributes.getAnsiName()} gained {gained:.2f} from {target.attributes.getAnsiName()}"
            )

            # eating will consume a bit of energy, decentivising the bots from attempting to eat continuously
            self.take_energy(0.05)

    def consumed(self, amount):
        """
        The bot was nibbled on
        """
        return self.take_energy(amount) * NUTRITIONAL_PERCENT

    @property
    def willingToBreed(self) -> bool:
        # check if this bot is willing to breed
        return (
            self.energy.level >= MIN_ENERGY_PERCENT_TO_BREED * self.energy.maximum
            and self.time_since_last_child >= MIN_BREED_DELAY
        )

    def same_species(self, other: Bot) -> bool:
        # check if the bots are of the same species
        return self.attributes.species == other.attributes.species

    def breed(self, other_bot: Bot):
        """
        the assigned bot will attempt to breed with the given bot providing they are both eligable
        returns the child bot of the two parents.
        """

        # check if simulator can accept more bots
        # check not self
        # check if this bot is still willing (might not if mated with previous bot)
        # check if other bot is still willing (might not if mated with a previous bot)
        if (
            not isinstance(other_bot, Bot)
            or not self.simulator.can_add_object
            or not self.willingToBreed
            or not other_bot.willingToBreed
            or not self.same_species(other_bot)
            or self is other_bot
        ):
            return

        child_name = f"bot_{self.simulator.object_counter}"

        energy_contribution = 0.0
        for bot in [self, other_bot]:
            bot: Bot
            bot.time_since_last_child = 0.0  # reset breeding timers
            energy_contribution += bot.take_energy(bot.energy.level * 0.3)

        # determine whos traits will dominate
        domBot, recBot = (
            (other_bot, self)
            if self.total_rewards_collected < other_bot.total_rewards_collected
            else (self, other_bot)
        )

        # make love (generate the child bot)
        childBot = Bot(
            self.simulator,
            child_name,
        )
        childBot.pose = Pose(
            copy.copy(domBot.pose.x) + random.random() * 5 - 2.5,
            copy.copy(domBot.pose.y) + random.random() * 5 - 2.5,
            random.random() * 2 * math.pi,
        )
        childBot.attributes.__dict__.update(domBot.attributes.__dict__.copy())
        childBot.attributes.name = child_name
        childBot.attributes.generation += 1
        childBot.attributes.familyHistory = domBot.attributes.ownFamilyHistory()

        childBot.attributes.maxSpeed = fl.combine_unrestrained(
            domBot.attributes.maxSpeed, recBot.attributes.maxSpeed, 0.25
        )
        childBot.attributes.maxTurnSpeed = fl.combine_unrestrained(
            domBot.attributes.maxTurnSpeed, recBot.attributes.maxTurnSpeed, 0.25
        )
        childBot.energy.level = energy_contribution
        childBot.total_rewards_collected = 0

        # give child bot colour
        result_colour_RGB = []
        for i in range(3):
            result_colour_RGB.append(
                fl.Combine1(
                    domBot.attributes.colourRGB[i],
                    recBot.attributes.colourRGB[i],
                    0,
                    1,
                    0.25,
                )
            )
        childBot.attributes.colourRGB = result_colour_RGB

        childBot.brain = domBot.brain.copy()
        for my_neuron, their_neuron in zip(
            childBot.brain.neurons, recBot.brain.neurons
        ):
            my_neuron.location[0] = fl.combine_wrap(
                my_neuron.location[0],
                their_neuron.location[0],
                0,
                childBot.brain.side_length,
                0.25,
            )
            my_neuron.location[1] = fl.combine_wrap(
                my_neuron.location[1],
                their_neuron.location[1],
                0,
                childBot.brain.side_length,
                0.25,
            )
            my_neuron.output_factor = fl.Combine1(
                my_neuron.output_factor, their_neuron.output_factor, -1, 1, 0.2
            )

        childBot.connect_to_brain()

        self.simulator.add_object(childBot)

        print(
            f"{self.attributes.getAnsiName()} mated with {other_bot.attributes.getAnsiName()} to create {childBot.attributes.getAnsiName()}"
        )

    def move(self):
        # find out the direction which the bot is facing (added onto the current direction)
        rotation = (
            self.angular_velocity_factor()
            * self.attributes.maxTurnSpeed
            * self.simulator.simulated_time_step
        )

        self.pose.rotation += rotation
        self.take_energy(abs(rotation) * ROTATION_ENERGY_LOSS_RATE)

        # find out how far the bot has traveled
        displacement = (
            self.velocity_factor()
            * self.attributes.maxSpeed
            * self.simulator.simulated_time_step
        )
        # find the displacement along the axis
        old_pos = copy.copy(self.pose.position)
        # update the position
        self.pose.x += math.cos(self.pose.rotation) * displacement
        self.pose.y -= math.sin(self.pose.rotation) * displacement

        self.simulator.grid.move(self, old_pos)

        self.take_energy(abs(displacement) * MOVEMENT_ENERGY_LOSS_RATE)

    def check_boundries(self):
        # check if the bot has reached the boundry
        # Right boundry
        if self.pose.x + self.attributes.radius > self.simulator.world.width:
            self.take_energy(BOUNDRY_DAMAGE)
            self.pose.x = self.simulator.world.width - self.attributes.radius * 2
        # Bottom boundry
        if self.pose.y + self.attributes.radius > self.simulator.world.height:
            self.take_energy(BOUNDRY_DAMAGE)
            self.pose.y = self.simulator.world.height - self.attributes.radius * 2

        # Left boundry
        if self.pose.x < self.attributes.radius:
            self.take_energy(BOUNDRY_DAMAGE)
            self.pose.x = self.attributes.radius * 2
        # Top boundry
        if self.pose.y < self.attributes.radius:
            self.take_energy(BOUNDRY_DAMAGE)
            self.pose.y = self.attributes.radius * 2

    def act(self, nearby):
        for obj in nearby:
            self.eat(obj)

        for obj in self.simulator.sim_objects:
            self.breed(obj)

        self.move()
        self.check_boundries()

    def get_position_x_percent(self):
        return self.pose.x / self.simulator.world.width

    def get_position_y_percent(self):
        return self.pose.y / self.simulator.world.height

    def think(self):
        self.brain.think()

    def get_direction_percent(self):
        """
        Continuous value with 100% being at 0rad and 0% being at pi rad
        Strength of pointing 'North'
        """
        return abs(self.pose.rotation.angle_to(0) / math.pi)

    def take_energy(self, amount):
        taken = self.energy.take(amount)
        if self.energy.level <= 0:
            self.dead = True
            print(
                f"{self.attributes.getAnsiName()} died from {inspect.currentframe().f_back.f_code.co_name}"
            )
        return taken

    def save_brain(self, file_location=None):
        if file_location == None:
            file_location = "brains/" + self.attributes.name + "_brain.txt"

        self.brain.save(file_location)

    def copy(self):
        copy_bot = Bot(
            self.simulator,
            copy.deepcopy(self.attributes.name),
            copy.deepcopy(self.attributes.maxSpeed),
            copy.deepcopy(self.FOV_angle),
            copy.deepcopy(self.energy.maximum),
            copy.deepcopy(self.attributes.colourRGB),
        )
        if self.brain != None:
            copy_bot.brain = self.brain.copy()
        return copy_bot

    def mutate(self):
        self.attributes.mutate()
        self.brain.mutate()


class BotVisual(display.Visual):
    def __init__(self, bot: Bot):
        self.bot = bot

    def draw(self, disp):
        """Moves the circle object from the position given"""

        display.circle_w_outline(
            disp,
            self.bot.pose.x,
            self.bot.pose.y,
            self.bot.attributes.radius,
            display.HEXtoRGB_pygame(self.bot.attributes.colourHEX),
        )

        eye_pos = (
            self.bot.pose.x
            + ((self.bot.attributes.radius / 2) * math.cos(self.bot.pose.rotation)),
            self.bot.pose.y
            - ((self.bot.attributes.radius / 2) * math.sin(self.bot.pose.rotation)),
        )

        display.circle_w_outline(
            disp,
            eye_pos[0],
            eye_pos[1],
            self.bot.attributes.radius / 2,
            "#ffffff",
        )

    def contains_point(self, disp, pos):
        """Return True when the screen point lies within the bot's drawn circle."""
        point_x, point_y = pos
        bot_x = disp._convert_to_pixels(self.bot.pose.x)
        bot_y = disp._convert_to_pixels(self.bot.pose.y)
        bot_radius = max(1, disp._convert_to_pixels(self.bot.attributes.radius))
        return math.hypot(bot_x - point_x, bot_y - point_y) <= bot_radius


class Attributes:
    """
    Defines and handles all a bots internal and external attributes.
    """

    def __init__(self, bot: Bot, name, max_speed, max_turn_speed, colourRGB, radius):
        self.bot = bot

        self.name = name
        self.generation = 0
        self.familyHistory = ""
        self.maxSpeed = max_speed
        self.maxTurnSpeed = max_turn_speed
        self.colourRGB = colourRGB
        self.radius = radius

    @property
    def species(self):
        return ",".join([str(int(val * 5)) for val in self.colourRGB])

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
        self.maxSpeed = fl.combine_unrestrained(self.maxSpeed, self.maxSpeed, 0.75)
        self.maxTurnSpeed = fl.combine_unrestrained(
            self.maxTurnSpeed, self.maxTurnSpeed, 0.75
        )

        self.colourRGB = [
            fl.combine_wrap(colour, colour, 0, 1, 0.5) for colour in self.colourRGB
        ]

    @property
    def colourRGB(self):
        return self._rgb

    @colourRGB.setter
    def colourRGB(self, value):
        self._rgb = value
        self._hex = display.RGBtoHEX(value)

    @property
    def colourHEX(self):
        return self._hex

    @colourHEX.setter
    def colourHEX(self, value):
        self._hex = value
        self._rgb = display.HEXtoRGB(value)

    def _wrapAnsi(self, value):
        r = max(0, min(255, int(self.colourRGB[0] * 255)))
        g = max(0, min(255, int(self.colourRGB[1] * 255)))
        b = max(0, min(255, int(self.colourRGB[2] * 255)))
        return f"\033[38;2;{r};{g};{b}m{value}\033[0m"

    def getAnsiName(self):
        return self._wrapAnsi(self.name)

    def getAnsiSpecies(self):
        return self._wrapAnsi(self.species)


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
        x_displacement = object.pose.x - self.bot.pose.x
        y_displacement = self.bot.pose.y - object.pose.y
        # check if too far away, if so, skip
        distance_to_object_sq = x_displacement**2 + y_displacement**2

        if distance_to_object_sq > self.bot.max_view_distance_sq:
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
                distance_percent = 1.0 - (
                    distance_to_object_sq / self.bot.max_view_distance_sq
                )
                if segment.disPercent <= distance_percent:
                    segment.disPercent = distance_percent
                    segment.RGB = object.attributes.colourRGB

    def reset(self):
        # resets all the view segments
        for segment in self.segments:
            segment.reset()

        # determine the global angle of the left view
        self.angle_of_left_view_g = float(self.bot.pose.rotation) + (
            self.bot.FOV_angle / 2
        )
