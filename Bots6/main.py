from __future__ import annotations
import os
import simulator as sim
import world
import visualiser as vis

WORLD_WIDTH = 40
WORLD_HEIGHT = 40


def main():

    plane = world.World(WORLD_WIDTH, WORLD_HEIGHT)

    simulator = sim.Simulator(plane)
    visualiser = vis.Display(simulator)

    simulator.start()
    while True:
        simulator.runSimStep()
        visualiser.updateDisplay()


if __name__ == "__main__":
    os.chdir("./Bots6")
    main()
