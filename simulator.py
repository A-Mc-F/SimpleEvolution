from __future__ import annotations
import os
import time
import world
import multiprocessing as mp
import brain as nn
import bot
import uniform_grid
from sim_obj import SimObj
import bot as BOT
from display import Display


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

HOURS = 1
MINUTES = 0
SECONDS = 0
MAX_RUN_TIME_S = HOURS * 3600 + MINUTES * 60 + SECONDS
# time frame
TIME_MULTIPLIER = 2.0

# Global Variables
# World
WORLD_WIDTH = 100
WORLD_HEIGHT = 100
WORLD_AREA = WORLD_WIDTH * WORLD_HEIGHT
# Collisions
ENABLE_COLLISIONS = False
# Number of bots
BOT_DENSITY = 0.02
MIN_NUM_OF_BOTS = 10
MAX_NUMBER_OF_BOTS = int(max(MIN_NUM_OF_BOTS, int(WORLD_AREA * BOT_DENSITY)))

# Number of rewards
REWARD_DENSITY = 0.0005
MIN_NUM_OF_REWARDS = 2
MAX_NUMBER_OF_REWARDS = int(max(MIN_NUM_OF_REWARDS, int(WORLD_AREA * REWARD_DENSITY)))

MAX_NUMBER_OF_OBJECTS = 200
MAX_NUMBER_OF_OBJECTS = int(
    min(MAX_NUMBER_OF_BOTS + MAX_NUMBER_OF_REWARDS, MAX_NUMBER_OF_OBJECTS)
)
MAX_NUMBER_OF_BOTS = MAX_NUMBER_OF_OBJECTS - MAX_NUMBER_OF_REWARDS

STARTING_NUMBER_OF_BOTS = int(MAX_NUMBER_OF_OBJECTS * 0.5)

FRAME_RATE = 24.0
FRAME_INTERVAL = 1.0 / FRAME_RATE

MAX_RETRIES = 5


class Simulator:
    def __init__(
        self, world=world.World(world_width=WORLD_WIDTH, world_height=WORLD_HEIGHT)
    ):
        self.simulated_duration = 0.0
        self.real_start_time = 0.0
        self.simulated_time_step = 0.0

        self.world = world
        self.time_multiplier = TIME_MULTIPLIER
        self.grid = uniform_grid.UniformGrid(bot.MAX_VIEW_DISTANCE)

        self.object_counter = 0
        self.sim_objects: list[SimObj] = []
        self.all_objects = []

        self.display = Display(self)

        self.status = False

    @property
    def can_add_object(self):
        return len(self.sim_objects) < MAX_NUMBER_OF_OBJECTS

    def add_object(self, object):
        if not self.can_add_object:
            return
        self.object_counter += 1
        self.grid.add(object)
        self.sim_objects.append(object)
        self.all_objects.append(object)

    def remove_object(self, object):
        self.grid.remove(object)
        self.sim_objects.remove(object)

    def repopulate(self, count, template=None):
        if not self.can_add_object:
            return
        if template == None:
            new_species = bot.Bot(self)
            new_species.brain = nn.Brain()
        else:
            new_species = template
        print(
            f"Repopulating {new_species.attributes.getAnsiSpecies()} with {new_species.attributes.getAnsiName()}, rewards: {new_species.total_rewards_collected}"
        )
        for _ in range(int(count)):
            new_bot = new_species.copy()
            new_bot.attributes.name = f"bot_{self.object_counter}"
            new_bot.mutate()
            new_bot.connect_to_brain()
            new_bot.energy.take(70)
            self.add_object(new_bot)
        del new_species

    def run(self):
        real_time_interval = 0.0
        last_real_time = 0.0
        self.real_start_time = now()
        self.simulated_time_step = 0.0
        self.status = True

        species_retries = {}

        while self.status:

            self.simulated_duration += self.simulated_time_step
            real_time_interval = self.real_duration - last_real_time
            last_real_time = self.real_duration
            self.simulated_time_step = min(
                real_time_interval * self.time_multiplier, 0.25
            )

            for object in self.sim_objects:
                object.simulate()

            for dead_obj in self.sim_objects:
                if getattr(dead_obj, "dead", False):
                    self.remove_object(dead_obj)

            remaining_bots = [
                bot for bot in self.sim_objects if isinstance(bot, BOT.Bot)
            ]

            if len(remaining_bots) == 0:

                best_bots_by_species = best_bot_by_species(
                    [bot for bot in self.all_objects if isinstance(bot, BOT.Bot)]
                )

                if len(best_bots_by_species) == 0:
                    self.repopulate(int(MAX_NUMBER_OF_BOTS * 0.2))
                    self.repopulate(int(MAX_NUMBER_OF_BOTS * 0.2))
                else:
                    bots_per_species = int(
                        MAX_NUMBER_OF_BOTS * 0.6 * (1 / (1 + len(best_bots_by_species)))
                    )
                    self.repopulate(bots_per_species)
                    for species_id, bestbot in best_bots_by_species.items():
                        self.repopulate(bots_per_species, bestbot)

            elif len(remaining_bots) < MIN_NUM_OF_BOTS:

                # Remove inactive species from tracking dict
                active_species = set(bot.attributes.species for bot in remaining_bots)
                species_retries = {
                    s: r for s, r in species_retries.items() if s in active_species
                }

                # Track best bot per species
                best_bots_by_species = best_bot_by_species(remaining_bots)

                # Repopulate best bots of each species
                for species_id, bestbot in best_bots_by_species.items():
                    if species_id not in species_retries:
                        species_retries[species_id] = 1

                    if species_retries[species_id] < MAX_RETRIES:
                        species_retries[species_id] += 1
                        self.repopulate(
                            int(
                                MAX_NUMBER_OF_BOTS
                                * 0.5
                                * (1 / len(best_bots_by_species))
                            ),
                            bestbot,
                        )

            self.display.update()

            self.status = self.real_duration < MAX_RUN_TIME_S and self.status
        print("The simulation has ended")

    @property
    def real_duration(self):
        return now() - self.real_start_time

    def end_simulation(self):

        print("all bots results:")
        species_dict = {}
        # key: colourHEX, value: bot with max rewards for that species
        passed_bots = [
            object
            for object in self.all_objects
            if "bot" in object.attributes.name and object.total_rewards_collected >= 3
        ]
        if len(passed_bots) > 0:
            for object in passed_bots:
                species = object.attributes.species
            if (
                species not in species_dict
                or object.total_rewards_collected
                > species_dict[species].total_rewards_collected
            ):
                species_dict[species] = object
            print(
                object.attributes.getAnsiName()
                + "  Rewards collected: "
                + str(object.total_rewards_collected)
                + " Gen: "
                + str(object.attributes.generation)
            )
        else:
            print("no bots passed the conditions")
            return

        # record the results of the simulation
        bestbot = None
        for spec, bot in species_dict.items():
            if bot.total_rewards_collected > bestbot.total_rewards_collected:
                bestbot = bot

            print(
                f"The {spec} which colllected the most rewards was {bestbot.attributes.getAnsiName()} with {bestbot.total_rewards_collected}. RPM: {str(bestbot.total_rewards_collected / (bestbot.age / 60.0))} Gen: {bestbot.attributes.generation} Max Speed: {bestbot.attributes.maxSpeed}"
            )
        # bot.saveBrain("brains/" + bot.attributes.colourHEX + "starter_brain.txt")
        # bot.attributes.save(
        #     "attributes/" + bot.attributes.colourHEX + "starter_attributes.txt"
        # )

        with open("starting_species.txt", "w") as specs:
            for bot in bestBots:
                specs.write(f"{bot.attributes.colourHEX}, ")

        text = (
            "The absolute best was "
            + bestbot.attributes.getAnsiSpecies()
            + " bot "
            + bestbot.attributes.getAnsiName()
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
        # bestbot.saveBrain("brains/starter_brain.txt")
        # bestbot.attributes.save("attributes/starter_attributes.txt")

        self.world_display.canvas.quit()
        self.world_display.window.quit()


def best_bot_by_species(bots: list[bot.Bot], min_rewards=3):

    # Track best bot per species
    best_bots_by_species = {}
    for bot in bots:
        if bot.total_rewards_collected < min_rewards:
            continue

        species_id = bot.attributes.species
        if species_id not in best_bots_by_species:
            best_bots_by_species[species_id] = bot
        elif (
            bot.total_rewards_collected
            > best_bots_by_species[species_id].total_rewards_collected
        ):
            best_bots_by_species[species_id] = bot

    return best_bots_by_species


def now():
    return time.time_ns() / 10.0**9


def main():
    import bot
    import reward
    import brain as brain
    import random

    bots_per_species = 3

    plane = world.World(WORLD_WIDTH, WORLD_HEIGHT)
    simulator = Simulator(plane)

    for _ in range(MAX_NUMBER_OF_REWARDS):
        simulator.add_object(reward.Reward(simulator, f"reward_{_}"))

    if False:
        with open("starting_species.txt") as ss:
            starting_species = ss.read().split(",")

        for species_name in starting_species:
            for i in range(bots_per_species):
                initial_bot = bot.bot_.Bot(simulator)

                initial_bot.net = brain.Brain(
                    file_name=rf"brains\{species_name}starter_brain.txt"
                )
                initial_bot.attributes.load(
                    rf"attributes\{species_name}starter_attributes.txt"
                )
                initial_bot.attributes.generation = 0

                initial_bot.attributes.name = f"bot_{simulator.object_counter}"

                initial_bot.position[0] = plane.width / 2.0 + plane.width * 0.2 * (
                    random.random() * 2 - 1
                )
                initial_bot.position[1] = plane.height / 2.0 + plane.height * 0.2 * (
                    random.random() * 2 - 1
                )
                initial_bot.direction = 6.28 * random.random()

                if i >= bots_per_species * 0.5:
                    initial_bot.mutate()

                initial_bot.connectToBrain()
                simulator.addObject(initial_bot)

    print("Simulator starting")

    try:
        simulator.run()
    except KeyboardInterrupt:
        print("program stopped by user")
    finally:
        simulator.end_simulation()


if __name__ == "__main__":
    main()
