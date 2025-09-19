import random
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

from game_ai.mcts.mcts import MonteCarloTreeSearchImplementation


def _simulate_batch(state, rollout_depth, n_rollouts):
    """
    Run N rollouts in one worker process to reduce IPC overhead.
    Each worker creates its own MCTS instance (not shared).
    """
    mcts = MonteCarloTreeSearchImplementation(rollout_depth=rollout_depth)
    total = 0.0
    for _ in range(n_rollouts):
        # clone so rollouts don't interfere with each other
        total += mcts._simulate(state.clone())
    return total


class AIWrapperMCTS:
    def __init__(self, rollouts, rollout_depth):
        self.rollouts = rollouts
        self.rollout_depth = rollout_depth
        self.cpu_count = mp.cpu_count()

        # Create pool once and reuse it
        self.executor = ProcessPoolExecutor(max_workers=self.cpu_count)

    def __del__(self):
        # Make sure processes are cleaned up when object is destroyed
        self.executor.shutdown(wait=True)

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

        # Split rollouts evenly among workers
        batch_size = max(1, self.rollouts // self.cpu_count)

        for kind, target in candidates:
            next_state = state.make_move(unit, target) if kind == "move" else state.attack(unit, target)

            tasks = [self.executor.submit(_simulate_batch, next_state, self.rollout_depth, batch_size)
                     for _ in range(self.cpu_count)]
            results = [f.result() for f in tasks]
            total_score = sum(results)

            avg_score = total_score / (batch_size * self.cpu_count)
            heatmap[(target.x, target.y)] = avg_score
            stats.append((kind, unit, target, avg_score))

        # --- choose best move ---
        max_score = max(s[3] for s in stats)
        best_moves = [s for s in stats if abs(s[3] - max_score) < 1e-6]

        # prefer attacks if tied
        best_moves.sort(key=lambda s: (s[3], 1 if s[0] == "attack" else 0), reverse=True)
        kind, unit, target, score = best_moves[0]

        new_state = state.make_move(unit, target) if kind == "move" else state.attack(unit, target)
        cloned_unit = next(u for u in new_state.get_units_of_army(unit.army) if u.id == unit.id)
        if kind == "move":
            cloned_unit.has_moved = True
        else:
            cloned_unit.already_attacked = True

        return new_state, target, heatmap, stats