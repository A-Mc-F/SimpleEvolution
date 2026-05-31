from __future__ import annotations
import random
import math
import simulator
import sim_obj
import display
from energy_store import EnergyStore
from sim_obj import Position
import copy
import pygame

RADIUS = 1.0  # units
COLOUR_RGB = [0.9, 0, 0]
BORDER_WIDTH = 2  # units
MAX_ENERGY = 200
DECAY_RATE = 2


class Reward(sim_obj.SimObj):
    def __init__(self, simulator: simulator.Simulator, name):
        super().__init__(simulator)

        self.energy = EnergyStore(MAX_ENERGY)

        from bot import Attributes

        self.attributes = Attributes(self, name, 0, 0, COLOUR_RGB, RADIUS)

        self.pose = sim_obj.Pose(
            self.simulator.world.width / 2.0, self.simulator.world.height / 2.0, 0
        )

        self.x_max = simulator.world.width - (BORDER_WIDTH + self.attributes.radius)
        self.y_max = simulator.world.height - (BORDER_WIDTH + self.attributes.radius)

        self.x_min = BORDER_WIDTH + self.attributes.radius
        self.y_min = self.x_min

        self.dead = False

        self.visual = RewardVisual(self)

        self.move()

    def simulate(self):
        self.energy.take(self.simulator.simulated_time_step * DECAY_RATE)
        if self.energy.level == 0:
            self.energy.add(1000)
            self.move()

    def move(self):
        """
        moves the reward to a new random location
        """
        old_pose = copy.copy(self.pose.position)
        self.pose.x = random.random() * (self.x_max - self.x_min) + self.x_min
        self.pose.y = random.random() * (self.y_max - self.y_min) + self.y_min
        self.simulator.grid.move(self, Position(old_pose[0], old_pose[1]))

    def consumed(self, amount):
        return self.energy.take(amount) * 2.0


class RewardVisual(display.Visual):
    def __init__(self, reward: Reward):
        self.display = reward.simulator.display.world_display
        self.reward = reward

    def draw(self, disp):
        """Moves the circle object from the position given"""
        display.circle_w_outline(
            disp,
            self.reward.pose.x,
            self.reward.pose.y,
            self.reward.attributes.radius,
            display.HEXtoRGB_pygame(self.reward.attributes.colourHEX),
        )
