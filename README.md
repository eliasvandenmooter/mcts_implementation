# Monte Carlo Tree Search heuristic algorithm in-game implementation 

Monte Carlo Tree Search (MCTS) is a algorithm designed for problems with extremely large decision spaces, like the game Go with its $10^{170}$ 
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
