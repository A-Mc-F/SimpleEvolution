from __future__ import annotations
import random
import math

SUB_PULL_STRENGTH = 0.05
MUTATION_PULL_STRENGTH = 0.05


def combine_unrestrained(dom_val, sub_val, mutation_probability):
    """
    returns a value close to the dom value pulled towards the sub value.
    can be pulled infinitly in any direction.
    """
    diff = sub_val - dom_val
    if random.random() <= mutation_probability:
        # mutation occurs
        mutation_strength = MUTATION_PULL_STRENGTH * random.random()
        mutation_direction = random.choice((-1, 1))
        change = diff * mutation_strength * mutation_direction
    else:
        change = diff * SUB_PULL_STRENGTH
    return dom_val + change


def try_mutate(val, min_val, max_val, mutation_probability):
    """Decorator that adds a mutation_probability arg to wrapped functions."""
    if not mutation_probability or random.random() > mutation_probability:
        return val
    else:
        return min(
            max(
                (max_val - min_val) * random.random() + min_val,
                min_val,
            ),
            max_val,
        )


def Combine1(dom_value, sub_value, min_value, max_value, mutatation_probability=None):
    """returns a value close to the dom value towards the sub value
    The amount of pull the sub has is dictated by the probability that
    it is on a particular side of the dom value"""

    sub_value = try_mutate(sub_value, min_value, max_value, mutatation_probability)

    prob_less = (dom_value - min_value) / (max_value - min_value)
    difference = sub_value - dom_value

    if sub_value < dom_value:
        new_val = dom_value + SUB_PULL_STRENGTH * difference * (1.1 - prob_less)
    else:
        new_val = dom_value + SUB_PULL_STRENGTH * difference * (prob_less + 0.1)

    return min(max(new_val, min_value), max_value)


def Combine2(dom_value, sub_value, min_value, max_value, mutatation_probability=None):
    """
    pulls dom in a direction depending on if sub is higher or lower than the midpoint of the range
    """

    sub_value = try_mutate(sub_value, min_value, max_value, mutatation_probability)

    midpoint = (max_value - min_value) / 2.0

    difference = sub_value - midpoint
    return min(max(dom_value + SUB_PULL_STRENGTH * difference, min_value), max_value)


def Combine3(dom_value, sub_value, min_value, max_value, mutatation_probability=None):
    """only tries to combine the values if they are within a
    half length of the range of each other"""

    sub_value = try_mutate(sub_value, min_value, max_value, mutatation_probability)

    half_length = (max_value - min_value) / 2.0

    lower_limit = max(dom_value - half_length, min_value)
    upper_limit = min(dom_value + half_length, max_value)

    lower_length = dom_value - lower_limit
    upper_length = upper_limit - dom_value

    difference = sub_value - dom_value

    if sub_value < dom_value and sub_value >= lower_limit:
        movement = difference / lower_length
    elif sub_value > dom_value and sub_value <= upper_limit:
        movement = difference / upper_length
    else:
        """outside of bounds, no movement"""
        return dom_value

    return min(max(dom_value + movement * SUB_PULL_STRENGTH, min_value), max_value)


def combine_wrap(
    dom_value, sub_value, min_value, max_value, mutatation_probability=None
):

    sub_value = try_mutate(sub_value, min_value, max_value, mutatation_probability)

    dom_value = dom_value - min_value

    range = max_value - min_value

    difference = sub_value - dom_value  # neg if dom greater than sub
    # is it quicker to wrap around
    if abs(difference) > range / 2:
        if difference < 0:
            # Wrap around lower bound
            difference += range
        else:
            # Wrap around upper bound
            difference -= range

    resulting_value = dom_value + difference * SUB_PULL_STRENGTH

    if resulting_value > range:
        resulting_value -= range
    elif resulting_value < 0:
        resulting_value += range

    return resulting_value + min_value


def angle_diff(a, b):
    """
    returns the angle between two angles
    normalised between -pi/2 to pi/2"""
    diff = (b - a) % (2 * math.pi)
    if diff > math.pi:
        diff -= 2 * math.pi
    return diff
