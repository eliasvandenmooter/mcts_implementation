# game_ai/mcts/mcts.py
import math
import random
from copy import deepcopy


class Node:
    __slots__ = ("state", "parent", "children", "visits", "reward")

    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []  # list of Node
        self.visits = 0
        self.reward = 0.0

    def uct(self, c=1.0):
        if self.visits == 0:
            return float("inf")
        return (self.reward / self.visits) + c * math.sqrt(math.log(self.parent.visits + 1) / self.visits)


class MonteCarloTreeSearchImplementation:
    def __init__(self, exploration=1.0, rollout_depth=20):
        self.exploration = exploration
        self.rollout_depth = rollout_depth

    def do_rollout(self, state, unit_index=0):
        """One rollout: select->expand->simulate->backprop."""
        root = Node(state)
        node = self._select(root)
        if not node.state.is_game_over():
            self._expand(node, unit_index)
            if node.children:
                node = random.choice(node.children)
        reward = self._simulate(node.state)
        self._backpropagate(node, reward)

    def choose(self, state, unit_index=0):
        """
        Run a small budget of rollouts and return the best child state for the root.
        This implementation runs a few deterministic rollouts then picks best child by visits.
        """
        root = Node(state)
        # Expand root once to populate children
        self._expand(root, unit_index)
        # limited rollouts budget
        budget = max(10, 30)  # keep small to reduce CPU load
        for _ in range(budget):
            node = self._select(root)
            if not node.state.is_game_over():
                self._expand(node, unit_index)
                if node.children:
                    node = random.choice(node.children)
            reward = self._simulate(node.state)
            self._backpropagate(node, reward)

        # choose child with highest visits, fallback to a random child
        if not root.children:
            return state
        best = max(root.children, key=lambda n: n.visits)
        return best.state

    def _select(self, node):
        # descend until leaf
        while node.children:
            node = max(node.children, key=lambda c: c.uct(self.exploration))
        return node

    def _expand(self, node, unit_index=0):
        state = node.state
        # pick units for the current turn
        armies = state.get_all_armies()
        if not armies:
            return
        # use current army from state.current_army (string)
        cur_army = state.current_army
        units = state.get_units_of_army(cur_army)
        if not units:
            return
        unit = units[unit_index % len(units)]

        # moves
        moves = state.get_legal_move_range_of_unit(unit)
        for m in moves:
            child_state = state.make_move(unit, m)
            node.children.append(Node(child_state, node))

        # attacks
        attacks = state.get_legal_attack_range_of_unit(unit)
        for t in attacks:
            child_state = state.attack(unit, t)
            node.children.append(Node(child_state, node))

    def _simulate(self, state):
        # light-weight random playout, limited depth
        cur = state.clone()
        depth = 0
        while not cur.is_game_over() and depth < self.rollout_depth:
            armies = cur.get_all_armies()
            if not armies:
                break
            # pick a random acting army (simplify: use current_army)
            acting_army = cur.current_army
            units = cur.get_units_of_army(acting_army)
            if not units:
                break
            u = random.choice(units)
            attacks = cur.get_legal_attack_range_of_unit(u)
            if attacks:
                cur = cur.attack(u, random.choice(attacks))
            else:
                moves = cur.get_legal_move_range_of_unit(u)
                if moves:
                    cur = cur.make_move(u, random.choice(moves))
                else:
                    break
            depth += 1
        return cur.reward()

    def _backpropagate(self, node, reward):
        n = node
        while n:
            n.visits += 1
            n.reward += reward
            n = n.parent
