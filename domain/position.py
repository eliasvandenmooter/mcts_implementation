# domain/position.py
class Position:
    def __init__(self, pos_id, x, y, surface="GRASS", unit=None):
        self.id = str(pos_id)
        self.x = int(x)
        self.y = int(y)
        self.surface = surface
        self.unit = unit

    def __repr__(self):
        return f"Pos({self.x},{self.y}, unit={self.unit})"
