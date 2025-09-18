import random

from game_ai.mcts.mcts import MonteCarloTreeSearchImplementation


class AIWrapperMCTS:
    def __init__(self, rollouts, rollout_depth):
        self.mcts = MonteCarloTreeSearchImplementation(rollout_depth=rollout_depth)
        self.rollouts = rollouts

    def think(self, state):
        units = [u for u in state.get_units_of_army(state.current_army)
                 if u.health > 0 and not u.has_moved and not u.already_attacked]
        if not units:
            return state, None, {}, []

        unit = random.choice(units)
        moves = state.get_legal_move_range_of_unit(unit)
        attacks = state.get_legal_attack_range_of_unit(unit)
        candidates = [("move", m) for m in moves] + [("attack", t) for t in attacks]

        heatmap = {}
        stats = []

        for kind, target in candidates:
            next_state = state.make_move(unit, target) if kind == "move" else state.attack(unit, target)
            total_score = 0.0
            for _ in range(self.rollouts):
                total_score += self.mcts._simulate(next_state)
            avg_score = total_score / self.rollouts
            heatmap[(target.x, target.y)] = avg_score
            stats.append((kind, unit, target, avg_score))

        # choose best move
        # choose best move, bias toward attacks if scores are equal
        max_score = max(s[3] for s in stats)
        best_moves = [s for s in stats if abs(s[3] - max_score) < 1e-6]

        # prefer attacks to moves
        best_moves.sort(key=lambda s: (s[3], 1 if s[0] == "attack" else 0), reverse=True)
        kind, unit, target, score = best_moves[0]

        new_state = state.make_move(unit, target) if kind == "move" else state.attack(unit, target)
        cloned_unit = next(u for u in new_state.get_units_of_army(unit.army) if u.id == unit.id)
        if kind == "move":
            cloned_unit.has_moved = True
        else:
            cloned_unit.already_attacked = True

        return new_state, target, heatmap, stats