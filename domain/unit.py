# domain/unit/unit.py
import itertools

_id_counter = itertools.count()

class Unit:
    """
    Lightweight Unit object. Keep it small and cheap to copy.
    """
    def __init__(self, army, unit_category="soldier", health=3, position_id=None):
        self.id = f"U{next(_id_counter)}"
        self.army = str(army)
        self.unit_category = unit_category  # string like 'soldier' or 'archer'
        self.health = int(health)
        self.max_health = int(health)  # <-- added max_health
        self.position_id = str(position_id) if position_id is not None else None
        self.has_moved = False
        self.already_attacked = False

    def copy_shallow(self):
        u = Unit(self.army, self.unit_category, self.health, self.position_id)
        u.id = self.id  # <-- preserve original id!
        u.max_health = self.max_health
        u.has_moved = self.has_moved
        u.already_attacked = self.already_attacked
        return u

    def __repr__(self):
        return f"{self.id}({self.army},{self.unit_category},hp={self.health}/{self.max_health})"
