from __future__ import annotations
import random

CHANCE_OF_MUTATION = 1.0 / 25.0


def Combine1(dom_value, sub_value, min_value, max_value):
    """returns a value close to the dom value towards the sub value
    The amount of pull the sub has is dictated by the probability that
    it is on a particular side of the dom value"""

    prob_less = (dom_value - min_value) / (max_value - min_value)
    sub_pull = 0.003
    mut_pull = 0.005

    if random.random() <= CHANCE_OF_MUTATION:
        # mutation occurs
        difference = ((max_value - min_value) * random.random() + min_value) - dom_value
        new_val = dom_value + mut_pull * difference
    else:
        # combine
        difference = sub_value - dom_value
        if sub_value < dom_value:
            new_val = dom_value + sub_pull * difference * (1.1 - prob_less)
        else:
            new_val = dom_value + sub_pull * difference * (prob_less + 0.1)

    return min(max(new_val, min_value), max_value)


def Combine2(dom_value, sub_value, min_value, max_value):
    sub_pull = 0.2
    mut_pull = 0.5

    midpoint = (max_value - min_value) / 2.0

    mutation_value = (max_value - min_value) * random.random() + min_value

    if random.random() <= CHANCE_OF_MUTATION:
        # mutation occurs
        return min(max(dom_value + mut_pull * mutation_value, min_value), max_value)
    else:
        # combine
        difference = sub_value - midpoint
        return min(max(dom_value + sub_pull * difference, min_value), max_value)


def Combine3(dom_value, sub_value, min_value, max_value):
    """only tries to combine the values if they are within a
    half length of the range of each other"""

    sub_pull = 0.2
    mut_pull = 0.5

    if random.random() <= CHANCE_OF_MUTATION:
        # mutation occurs
        return min(
            max(dom_value + mut_pull * (random.random() * 2 - 1), min_value), max_value
        )
    else:
        # combine
        quater_length = (max_value - min_value) / 2.0

        lower_limit = max(dom_value - quater_length, min_value)
        upper_limit = min(dom_value + quater_length, max_value)

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

        return min(max(dom_value + movement * sub_pull, min_value), max_value)


def Combine_Wrap(dom_value, sub_value, lower_bound, upper_bound):
    dom_value = dom_value - lower_bound

    max_range = upper_bound - lower_bound
    pull_factor = 0.02

    if random.random() <= CHANCE_OF_MUTATION:
        # mutation occurs
        sub_value = max_range * random.random()
    else:
        sub_value = sub_value - lower_bound

    distance = sub_value - dom_value  # neg if dom greater than sub
    # is it quicker to wrap around
    if abs(distance) > max_range / 2:
        if distance < 0:
            # Wrap around lower bound
            distance = max_range - distance
        else:
            # Wrap around upper bound
            distance = distance - max_range

    resulting_value = dom_value + distance * pull_factor

    if resulting_value > max_range:
        resulting_value = resulting_value - upper_bound
    elif resulting_value < 0:
        resulting_value = max_range - resulting_value

    return resulting_value + lower_bound
