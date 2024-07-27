import random
import math
import visualiser
import simulator


RADIUS = 1.0  # units
COLOUR_RGB = [0.9, 0, 0]
BORDER_WIDTH = 2  # units
MAX_SLICES = 10


class Reward:
    def __init__(self, simulator: simulator.Simulator):
        self.simulator = simulator

        import bot

        self.attributes = bot.Attributes(self, "reward", 0, 0, COLOUR_RGB, 0, RADIUS)

        self.position = [
            self.simulator.world.width / 2.0,
            self.simulator.world.height / 2.0,
        ]
        self.radius = RADIUS
        self.slices = MAX_SLICES

        self.x_max = simulator.world.width - (BORDER_WIDTH + self.radius)
        self.y_max = simulator.world.height - (BORDER_WIDTH + self.radius)

        self.x_min = BORDER_WIDTH + self.radius
        self.y_min = self.x_min

        self.attributes.colourRGB = COLOUR_RGB
        self.attributes.assignRGBtoHEX()

        self.energy_level = 1

        self.circleObject = visualiser.CircleObject(
            self.simulator.worldWindow,
            self.attributes.colourHEX,
            self.position,
            self.attributes.radius,
        )

        self.dead = False

        self.move()

    def simulate(self):
        pass

    def move(self):
        """
        moves the reward to a new random location
        """
        # print("the reward moved")
        self.position[0] = random.random() * (self.x_max - self.x_min) + self.x_min
        self.position[1] = random.random() * (self.y_max - self.y_min) + self.y_min
        self.circleObject.position = self.position
        self.circleObject.move()

    def isNear(self, obj):
        """
        checks if the reward is near another object
        """
        is_close = False

        x_distance = abs(self.position[0] - obj.position[0])
        y_distance = abs(self.position[1] - obj.position[1])

        distance = math.sqrt(pow(x_distance, 2) + pow(y_distance, 2))

        if distance < RADIUS:
            is_close = True

        return is_close

    def consumed(self):
        """
        removes a slice from the reward.
        if there are no more slices the reward will move and the slices reset
        """
        self.slices -= 1
        # print(str(self.slices) + " slices left")
        if self.slices <= 0:
            self.move()
            self.slices = MAX_SLICES


def main():
    sim = simulator.Simulator()
    fruit = Reward(sim)
    sim.sim_objects.append(fruit)
    sim.run()


if __name__ == "__main__":
    main()
