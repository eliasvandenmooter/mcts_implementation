import math
import random

class Node:
    __slots__ = ("state", "parent", "children", "visits", "reward", "action", "unit")

    def __init__(self, state, parent=None, action=None, unit=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.reward = 0.0
        self.action = action
        self.unit = unit

    def uct(self, c):
        if self.visits == 0:
            return float("inf")
        return (self.reward / self.visits) + c * math.sqrt(math.log(self.parent.visits + 1) / self.visits)


class MonteCarloTreeSearchImplementation:
    def __init__(self, exploration=math.sqrt(2), rollout_depth=20):
        self.exploration = exploration
        self.rollout_depth = rollout_depth

    def do_rollout(self, root):
        """Run one MCTS iteration starting from root Node."""
        node = self._select(root)
        if not node.state.is_game_over():
            self._expand(node)
            if node.children:
                node = random.choice(node.children)
        reward = self._simulate(node.state)
        self._backpropagate(node, reward)

    def choose(self, state, rollouts=50):
        """Run several rollouts and return the best child of root."""
        root = Node(state)
        self._expand(root)

        for _ in range(rollouts):
            self.do_rollout(root)

        if not root.children:
            return state, None

        best = max(root.children, key=lambda n: n.visits)
        return best.state, (best.action, best.unit)

    # ---- internals ----
    def _select(self, node):
        while node.children:
            node = max(node.children, key=lambda c: c.uct(self.exploration))
        return node

    def _expand(self, node):
        state = node.state
        units = state.get_units_of_army(state.current_army)
        if not units:
            return
        for u in units:
            if u.health <= 0:
                continue
            for action in state.get_legal_actions(u):
                child_state = state.perform_action(u, action)
                child = Node(child_state, parent=node, action=action, unit=u)
                node.children.append(child)

    def _simulate(self, state):
        cur = state.clone()
        depth = 0
        while not cur.is_game_over() and depth < self.rollout_depth:
            units = cur.get_units_of_army(cur.current_army)
            if not units:
                break
            u = random.choice(units)
            actions = cur.get_legal_actions(u)
            if not actions:
                break
            action = random.choice(actions)
            cur = cur.perform_action(u, action)
            depth += 1
        return cur.reward()

    def _backpropagate(self, node, reward):
        n = node
        while n:
            n.visits += 1
            n.reward += reward
            n = n.parent
