import copy
import os
import time
import visualiser as vis
import world
import brain_vis
import random
import brain
import multiprocessing as mp


def split(iter, n):
    k, m = divmod(len(iter), n)
    split_data = [
        iter[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)
    ]
    split_data_order_number = [[i, v] for i, v in enumerate(split_data)]
    return split_data_order_number


def mpSimulate(sub_list, queue):
    objects = sub_list[1]
    for object in objects:
        object.simulate()
    queue.put()


def mpSim(objects):
    sub_list = split(objects, 4)
    qout = mp.Queue()
    processes = [mp.Process(target=mpSimulate, args=(sub, qout)) for sub in sub_list]
    for p in processes:
        p.daemon = True
        p.start()
    # the computation only get triggered when we run this q.get() method
    qout.get()
    for p in processes:
        # p.join tells the process to wait until all jobs finished then exit, effectively cleaning up the pool.
        p.join()
        # p.close terminate the pool and tells the process not to accept any new job.
        p.close()


TOTAL_NUMBER_OF_SIMULATIONS = 1

HOURS = 0
MINUTES = 5
SECONDS = 0
# time frame
TIME_MULTIPLIER = 1.0

# Global Variables
# World
WORLD_WIDTH = 200
WORLD_HEIGHT = 200
# Collisions
ENABLE_COLLISIONS = False
# Number of bots
BOT_DENSITY = 5.0 / 100
MAX_NUMBER_OF_BOTS = 100
MAX_NUMBER_OF_BOTS = int(
    min(WORLD_WIDTH * WORLD_HEIGHT * BOT_DENSITY, MAX_NUMBER_OF_BOTS)
)

REWARD_DENSITY = 1.0 / 1500
NUMBER_OF_REWARDS = int(WORLD_WIDTH * WORLD_HEIGHT * REWARD_DENSITY)

STARTING_NUMBER_OF_BOTS = int(MAX_NUMBER_OF_BOTS * 0.5)

FRAME_RATE = 24.0
FRAME_INTERVAL = 1 / FRAME_RATE


class Simulator:
    def __init__(
        self, run_time_minutes=MINUTES, sim_time_factor=1.0, world=world.World()
    ):
        self.maxRunTime = run_time_minutes * 60
        self.runTime = 0.0
        self.simTime = 0.0
        self.simTimeFactor = sim_time_factor
        self.maxSimTime = self.maxRunTime * self.simTimeFactor
        self.simTimeInterval = 0.0
        self.startTime = 0.0

        self.world = world

        self.maxNumOfObjects = MAX_NUMBER_OF_BOTS
        self.minNumOfBots = 2
        self.simObjects = []
        self.totalNumOfObjects = 0
        self.allObjects = []

        self.worldWindow = vis.Display(self.world)

        self.brainWindow = brain_vis.BrainDisplay()

        self.frameInterval = 1.0 / FRAME_RATE

        self.status = False

    def addObject(self, object):
        if len(self.simObjects) >= self.maxNumOfObjects:
            print("Cant add any more objects")
            return
        self.totalNumOfObjects += 1
        self.simObjects.append(object)
        self.allObjects.append(object)

    def run(self):
        last_print_time = 0.0
        real_time_interval = 0.0
        self.startTime = now()
        last_real_time = 0.0
        self.status = True
        while self.status:
            self.simTime += self.simTimeInterval
            real_time_interval = self.runTime - last_real_time
            last_real_time = self.runTime
            self.simTimeInterval = min(real_time_interval * self.simTimeFactor, 1.0)

            for object in self.simObjects:
                object.simulate()

            if len(self.simObjects) <= 20:
                import bot

                new_species = bot.Bot(self)
                for _ in range(10):
                    new_bot = new_species.copy()
                    new_bot.attributes.name = f"bot{self.totalNumOfObjects}"
                    new_bot.net = brain.Brain()
                    new_bot.connectToBrain()
                    self.addObject(new_bot)

            if (self.runTime - last_print_time) >= self.frameInterval:
                last_print_time = self.runTime
                self.worldWindow.update()

            self.status = self.runTime < self.maxRunTime and self.status
            self.runTime = now() - self.startTime
        print("The simulation has ended")

    def endOfSimulation(self):
        from bot import Bot

        print("all bots results:")
        bestBots: list[Bot] = []
        for object in self.allObjects:
            if "bot" in object.attributes.name:
                print(
                    object.attributes.name
                    + "  Rewards collected: "
                    + str(object.total_rewards_collected)
                    + " Gen: "
                    + str(object.attributes.generation)
                )
                if object.total_rewards_collected >= 3:
                    isUnique = True
                    if len(bestBots) == 0:
                        bestBots.append(object)
                    else:
                        for bot in bestBots:
                            if object.sameSpecies(bot):
                                isUnique = False
                                print("same species")
                                if (
                                    object.total_rewards_collected
                                    >= bot.total_rewards_collected
                                ):
                                    bot = object
                                break

                        if isUnique:
                            bestBots.append(object)
        if len(bestBots) == 0:
            print("no bots passed the conditions")
            return

        # record the results of the simulation
        bestbot = bestBots[0]
        for bot in bestBots:
            if bot.total_rewards_collected > bestbot.total_rewards_collected:
                bestbot = bot

            text = f"The {bot.attributes.colourHEX} bot which colllected the most rewards was {bot.attributes.name} with {bot.total_rewards_collected}. RPM: {str(bot.total_rewards_collected / (bot.age / 60.0))} Gen: {bot.attributes.generation} Max Speed: {bot.attributes.maxSpeed}"
            print(text)
            bot.saveBrain("brains/" + bot.attributes.colourHEX + "starter_brain.txt")
            bot.attributes.save(
                "attributes/" + bot.attributes.colourHEX + "starter_attributes.txt"
            )

        with open("starting_species.txt", "w") as specs:
            for bot in bestBots:
                specs.write(f"{bot.attributes.colourHEX},")

        text = (
            "The absolute best was "
            + bestbot.attributes.colourHEX
            + " bot "
            + bestbot.attributes.name
            + " RPM: "
            + str(bestbot.total_rewards_collected / (bestbot.age / 60.0))
            + " Gen: "
            + str(bestbot.attributes.generation)
            + " with "
            + str(bestbot.total_rewards_collected)
            + " Max Speed: "
            + str(bestbot.attributes.maxSpeed)
        )
        record = open("record.txt", "a")
        record.write(text + "\n")
        record.close()
        # show results to the screen
        print(text)
        bestbot.saveBrain("brains/starter_brain.txt")
        bestbot.attributes.save("attributes/starter_attributes.txt")

        self.worldWindow.canvas.quit()
        self.worldWindow.window.quit()


def now():
    return time.time_ns() / 10.0**9


def main():
    for x in range(6):
        import bot
        import reward

        bots_per_species = 3

        plane = world.World(WORLD_WIDTH, WORLD_HEIGHT)
        simulator = Simulator(10, 1, plane)

        for _ in range(NUMBER_OF_REWARDS):
            simulator.addObject(reward.Reward(simulator))

        with open("starting_species.txt") as ss:
            starting_species = ss.read().split(",")

        for species_name in starting_species:
            for i in range(bots_per_species):
                initial_bot = bot.Bot(simulator)

                initial_bot.net = brain.Brain(
                    file_name=rf"brains\{species_name}starter_brain.txt"
                )
                initial_bot.attributes.load(
                    rf"attributes\{species_name}starter_attributes.txt"
                )

                initial_bot.attributes.name = "bot" + str(simulator.totalNumOfObjects)

                initial_bot.position[0] = plane.width / 2.0 + plane.width * 0.2 * (
                    random.random() * 2 - 1
                )
                initial_bot.position[1] = plane.height / 2.0 + plane.height * 0.2 * (
                    random.random() * 2 - 1
                )
                initial_bot.direction = 6.28 * random.random()

                if i >= bots_per_species * 0.5:
                    initial_bot.attributes.mutate()
                    for neuron in initial_bot.net.neurons:
                        neuron.location[0] = bot.Combine_Wrap(
                            neuron.location[0],
                            neuron.location[0],
                            0,
                            initial_bot.net.side_length,
                        )
                        neuron.location[1] = bot.Combine_Wrap(
                            neuron.location[1],
                            neuron.location[1],
                            0,
                            initial_bot.net.side_length,
                        )

                initial_bot.connectToBrain()
                simulator.addObject(initial_bot)

        print("Simulator starting")
        simulator.run()

        simulator.endOfSimulation()


if __name__ == "__main__":
    os.chdir("./Bots6")
    main()
