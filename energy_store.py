class EnergyStore:
    def __init__(self, level, maximum=None):
        self.maximum = maximum
        if maximum == None:
            self.maximum = level
        self._limit = self.maximum
        self.level = min(level, self._limit)

    def degrade_store(self, degredation):
        self._limit = max(0, self._limit - degredation)

    def take(self, amount: float):
        taken = min(amount, self.level)
        self.level = max(0, self.level - amount)
        return taken

    def add(self, val):
        added = min(val, self._limit - self.level)
        self.level = min(self._limit, self.level + val)
        return added

    def get_percent(self):
        return self.level / self.maximum
