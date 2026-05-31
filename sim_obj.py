from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from display import Visual
    from simulator import Simulator
    from reward import EnergyStore


class SimObj:
    def __init__(self, simulator: Simulator):
        self.simulator: Simulator = simulator
        self.pose: Pose
        self.grid_cell: tuple[int, int]
        self.visual: Visual

    def simulate(self): ...

    def consumed(self): ...

    def distance_sq(self, object: SimObj):
        return (self.pose.x - object.pose.x) ** 2 + (self.pose.y - object.pose.y) ** 2


import math


class Rotation:
    def __init__(self, theta: float):
        self._value = theta % (2 * math.pi)

    def __add__(self, other):
        return Rotation((self._value + other) % (2 * math.pi))

    def __sub__(self, other):
        return Rotation((self._value - other) % (2 * math.pi))

    def __set__(self, instance, value):
        self._value = value % (2 * math.pi)

    def __get__(self, instance, owner):
        return self._value

    def __str__(self):
        return f"{self._value:.2f}"

    def __float__(self):
        return self._value

    def angle_to(self, other):
        """
        returns the angle between two angles
        normalised between -pi/2 to pi/2"""
        diff = (other - self._value) % (2 * math.pi)
        if diff > math.pi:
            diff -= 2 * math.pi
        return diff


class Position:
    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    def __str__(self):
        return f"x: {self.x:.2f}, y: {self.y:.2f}"

    @property
    def _vector(self) -> tuple[float, float]:
        return (self.x, self.y)

    def __iter__(self):
        return iter(self._vector)

    def __getitem__(self, index):
        return self._vector[index]


class Pose:
    def __init__(self, x, y, theta):
        self.position: Position = Position(x, y)
        self.rotation: Rotation = Rotation(theta)

    @property
    def x(self):
        return self.position.x

    @x.setter
    def x(self, value):
        self.position.x = value

    @property
    def y(self):
        return self.position.y

    @y.setter
    def y(self, value):
        self.position.y = value

    def __repr__(self):
        return f"{self.position}, ϴ: {self.rotation}"


if __name__ == "__main__":
    rot = Pose(3, 4, 10)
    print(rot)
    for i in range(7):
        rot -= 1
        print(rot)
