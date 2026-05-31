from sim_obj import Position, SimObj


class UniformGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cells = {}

    def _cell_key(self, position: Position):
        cx = int(position.x // self.cell_size)
        cy = int(position.y // self.cell_size)
        return (cx, cy)

    def add(self, obj: SimObj):
        key = self._cell_key(obj.pose.position)
        self.cells.setdefault(key, []).append(obj)
        obj._grid_cell = key

    def remove(self, obj):
        key = getattr(obj, "_grid_cell", None)
        if key and key in self.cells:
            self.cells[key].remove(obj)
            if not self.cells[key]:
                del self.cells[key]
        return None

    def move(self, obj: SimObj, old_position: Position):
        old_key = self._cell_key(old_position)
        new_key = self._cell_key(obj.pose.position)
        if old_key != new_key:
            self.remove(obj)
            self.add(obj)

    def query_radius(self, object: SimObj, radius):
        min_cx = int((object.pose.x - radius) // self.cell_size)
        max_cx = int((object.pose.x + radius) // self.cell_size)
        min_cy = int((object.pose.y - radius) // self.cell_size)
        max_cy = int((object.pose.y + radius) // self.cell_size)

        results = []
        for cx in range(min_cx, max_cx):
            for cy in range(min_cy, max_cy):
                results.extend(self.cells.get((cx, cy), []))
        return results
