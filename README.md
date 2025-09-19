# Monte Carlo Tree Search heuristic algorithm in-game implementation 

## Algorithm

Monte Carlo Tree Search (MCTS) is a heuristic algorithm designed for problems with extremely large decision spaces, like the game Go with its $10^{170}$ 
possible board states. Instead of exploring all moves, MCTS incrementally builds a search tree using random simulations (rollouts) to guide its decisions. It balances exploration of new possibilities and usage of known promising paths, effectively focusing computational effort where it matters most, making it highly efficient for complex decision-making tasks.

<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/4c38dfd4-e79c-47ad-8cd8-98a344523b41" />

Selection Phase: Starting from the root node, the algorithm traverses down the tree using a selection policy. The most common approach employs the Upper Confidence Bounds applied to Trees (UCT) formula, which balances exploration and exploitation by selecting child nodes based on both their average reward and uncertainty.

Expansion Phase: When the selection phase reaches a leaf node that isn't terminal, the algorithm expands the tree by adding one or more child nodes representing possible actions from that state.

Simulation Phase: From the newly added node, a random playout is performed until reaching a terminal state. During this phase, moves are chosen randomly or using simple heuristics, making the simulation computationally inexpensive.

Backpropagation Phase: The result of the simulation is propagated back up the tree to the root, updating statistics (visit counts and win rates) for all nodes visited during the selection phase.

Mathematical Foundation: UCB1 Formula
The selection phase relies on the UCB1 (Upper Confidence Bound) formula to determine which child node to visit next:

$$
\text{UCB1} = \frac{w_i}{n_i} + c \cdot \sqrt{\frac{\ln N}{n_i}}
$$

Where:

- $\bar{X}_i$ is the average reward of node $i$  
- $c$ is the exploration parameter (typically $\sqrt{2}$)  
- $N$ is the total number of visits to the parent node  
- $n_i$ is the number of visits to node $i$

The first term encourages exploitation of nodes with high average rewards, while the second term promotes exploration of less-visited nodes. The logarithmic factor ensures that exploration decreases over time as confidence in the estimates increases.

## Duckling Wars 🦆

Duckling Wars is a small turn-based strategy game where two armies of ducklings battle it out on a grid-based board. Each unit can **move** or **attack** depending on its type (soldiers, archers, etc.), and the game ends when one side is eliminated.

### 🎮 Gameplay

- The board is a square grid.
- Each army has different unit types (soldiers, archers).
- On a unit’s turn, you can either **move** to an empty tile or **attack** an enemy in range.
- The game continues until only one army remains.

### 🧠 AI: Monte Carlo Tree Search (MCTS)

The AI opponent is powered by **Monte Carlo Tree Search (MCTS)**, a popular algorithm used in board games like Go and Chess engines.

How it works here:

1. For each possible move (move or attack), the AI **simulates many random rollouts** of the game.
2. Each rollout plays the game forward until an end state (win/loss/draw) or a depth limit.
3. The average result across rollouts gives the AI a **score** for that move.
4. The AI chooses the move with the best expected score (favoring attacks when tied).

This makes the AI **look ahead**, even without hardcoded strategies, and improve its decisions through simulation.

### ⚡ Concurrency

Running many rollouts can be slow if done in a single process. To speed this up, Duckling Wars runs the MCTS **concurrently**:

- Python’s `multiprocessing` is used to launch multiple worker processes.
- Each worker runs batches of simulations in parallel.
- The results are combined to evaluate the best move.

This means the AI uses **all CPU cores** to think faster and play stronger.
