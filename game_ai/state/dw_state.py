from domain.position import Position
from domain.unit import Unit
import random
import math
import copy


class DucklingWarsState:
    """
    Efficient game state for Duckling Wars:
    Compatible with MCTS pipeline:
    - clone() for safe rollouts
    - unified get_legal_actions / perform_action
    - reward() for backpropagation
    """

    def __init__(self, current_army, board, army_turn=0, unit_turn=0):
        self.current_army = str(current_army)
        self.board = list(board)
        self.army_turn = army_turn
        self.unit_turn = unit_turn
        self.size = int(math.sqrt(len(board)))

    # ---------------- helpers ----------------
    def get_position(self, x, y):
        return next((p for p in self.board if p.x == x and p.y == y), None)

    def get_position_by_id(self, pos_id):
        return next((p for p in self.board if p.id == str(pos_id)), None)

    def get_units_of_army(self, army_id):
        return [p.unit for p in self.board if p.unit and str(p.unit.army) == str(army_id)]

    def get_all_armies(self):
        return list({p.unit.army for p in self.board if p.unit})

    def copy(self):
        return copy.deepcopy(self)

    # ---------------- clone ----------------
    def clone(self):
        new_board = []
        for p in self.board:
            if p.unit:
                new_unit = p.unit.copy_shallow()
                new_pos = Position(p.id, p.x, p.y, p.surface, new_unit)
                new_unit.position_id = new_pos.id
            else:
                new_pos = Position(p.id, p.x, p.y, p.surface, None)
            new_board.append(new_pos)
        return DucklingWarsState(self.current_army, new_board, self.army_turn, self.unit_turn)

    # ---------------- movement ----------------
    def get_legal_move_range_of_unit(self, unit):
        if not unit:
            return []
        pos = self.get_position_by_id(unit.position_id)
        if not pos:
            return []
        max_range = 3 if unit.unit_category == "archer" else 2
        moves = []
        for dx in range(-max_range, max_range+1):
            for dy in range(-max_range, max_range+1):
                if abs(dx) + abs(dy) <= max_range:
                    nx, ny = pos.x + dx, pos.y + dy
                    t = self.get_position(nx, ny)
                    if t and t.unit is None and t.surface != "ROCKS":
                        moves.append(t)
        return moves

    def make_move(self, unit, target_pos):
        new_state = self.clone()
        cloned_unit = next((u for u in new_state.get_units_of_army(unit.army) if u.id == unit.id), None)
        if not cloned_unit:
            return new_state
        old_pos = new_state.get_position_by_id(cloned_unit.position_id)
        old_pos.unit = None
        t = new_state.get_position_by_id(target_pos.id)
        t.unit = cloned_unit
        cloned_unit.position_id = t.id
        cloned_unit.has_moved = True
        return new_state

    # ---------------- attacks ----------------
    def get_legal_attack_range_of_unit(self, unit):
        if not unit:
            return []
        pos = self.get_position_by_id(unit.position_id)
        if not pos:
            return []
        attack_range = 4 if unit.unit_category == "archer" else 3
        targets = []
        for dx in range(-attack_range, attack_range+1):
            for dy in range(-attack_range, attack_range+1):
                if abs(dx) + abs(dy) <= attack_range:
                    nx, ny = pos.x + dx, pos.y + dy
                    t = self.get_position(nx, ny)
                    if t and t.unit and t.unit.army != unit.army:
                        targets.append(t)
        return targets

    def attack(self, unit, target_pos):
        new_state = self.clone()
        attacker = next((u for u in new_state.get_units_of_army(unit.army) if u.id == unit.id), None)
        target = new_state.get_position_by_id(target_pos.id)
        if not attacker or not target or not target.unit:
            return new_state
        damage = 2 if attacker.unit_category == "archer" else 3
        target.unit.health -= damage
        attacker.already_attacked = True
        if target.unit.health <= 0:
            target.unit = None
        return new_state

    # ---------------- unified actions ----------------
    def get_legal_actions(self, unit):
        """Return unified actions: ('move', Position) or ('attack', Position)."""
        if not unit:
            return []
        actions = []
        for m in self.get_legal_move_range_of_unit(unit):
            actions.append(("move", m))
        for a in self.get_legal_attack_range_of_unit(unit):
            actions.append(("attack", a))
        return actions

    def perform_action(self, unit, action):
        """Apply ('move', pos) or ('attack', pos). Returns new state."""
        kind, target = action
        if kind == "move":
            return self.make_move(unit, target)
        elif kind == "attack":
            return self.attack(unit, target)
        return self.clone()

    # ---------------- end / reward ----------------
    def is_game_over(self):
        armies = {u.army for p in self.board if (u := p.unit) and u.health > 0}
        return len(armies) <= 1

    def reward(self):
        curr_army_health = sum(u.health for p in self.board if (u := p.unit) and u.army == self.current_army)
        opp_health = sum(u.health for p in self.board if (u := p.unit) and u.army != self.current_army)
        return curr_army_health - opp_health

    def is_terminal(self):
        armies = self.get_all_armies()
        for army in armies:
            if all(u.health <= 0 for u in self.get_units_of_army(army)):
                return True
        return False

    def get_winner(self):
        armies = self.get_all_armies()
        alive = {a: [u for u in self.get_units_of_army(a) if u.health > 0] for a in armies}
        still_alive = [a for a, units in alive.items() if len(units) > 0]

        if len(still_alive) == 1:
            return still_alive[0]
        elif len(still_alive) == 0:
            return "Draw"
        return None

    # ---------------- sample generator ----------------
    @staticmethod
    def generate_sample_game_state(board_size=5, armies=("AI", "Opponent")):
        board = []
        pid = 0
        for y in range(board_size):
            for x in range(board_size):
                board.append(Position(str(pid), x, y))
                pid += 1

        for army in armies:
            for unit_type in ["soldier", "archer"]:
                empty_positions = [p for p in board if p.unit is None]
                chosen_pos = random.choice(empty_positions)
                u = Unit(army=army, unit_category=unit_type, health=5, position_id=chosen_pos.id)
                chosen_pos.unit = u

        return DucklingWarsState(current_army=armies[0], board=board)
