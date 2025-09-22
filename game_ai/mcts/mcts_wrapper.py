import random
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from game_ai.mcts.mcts import MonteCarloTreeSearchImplementation, Node


def _simulate_batch(state, rollout_depth, n_rollouts):
    """Worker runs independent MCTS rollouts and returns total reward."""
    mcts = MonteCarloTreeSearchImplementation(rollout_depth=rollout_depth)
    root = Node(state)  # get fresh root for each worker
    mcts._expand(root)
    for _ in range(n_rollouts):
        mcts.do_rollout(root)
    # average reward estimate from root
    if not root.children:
        return 0.0
    best = max(root.children, key=lambda n: n.visits)
    return best.reward / max(1, best.visits)


class AIWrapperMCTS:
    def __init__(self, rollouts, rollout_depth):
        self.rollouts = rollouts
        self.rollout_depth = rollout_depth
        self.cpu_count = mp.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.cpu_count)

    def __del__(self):
        self.executor.shutdown(wait=True)

    def think(self, state):
        units = [u for u in state.get_units_of_army(state.current_army)
                 if u.health > 0 and not u.has_moved and not u.already_attacked]
        if not units:
            return state, None, {}, []

        unit = random.choice(units)
        candidates = state.get_legal_actions(unit)

        heatmap = {}
        stats = []
        batch_size = max(1, self.rollouts // self.cpu_count)

        for action in candidates:
            next_state = state.perform_action(unit, action)
            tasks = [self.executor.submit(_simulate_batch, next_state, self.rollout_depth, batch_size)
                     for _ in range(self.cpu_count)]
            results = [f.result() for f in tasks]
            avg_score = sum(results) / len(results)

            # heatmap key by coordinates
            kind, target = action
            heatmap[(target.x, target.y)] = avg_score
            stats.append((kind, unit, target, avg_score))

        # pick best
        max_score = max(s[3] for s in stats)
        best_moves = [s for s in stats if abs(s[3] - max_score) < 1e-6]
        best_moves.sort(key=lambda s: (s[3], 1 if s[0] == "attack" else 0), reverse=True)
        kind, unit, target, score = best_moves[0]

        new_state = state.perform_action(unit, (kind, target))
        return new_state, target, heatmap, stats
