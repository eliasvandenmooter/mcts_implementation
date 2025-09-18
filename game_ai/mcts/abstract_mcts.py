from abc import ABC, abstractmethod


class MonteCarloTreeSearch(ABC):
    """
    An abstract method interface representation of the MCTS algorithm
    """
    @abstractmethod
    def choose(self, node):
        pass

    @abstractmethod
    def do_rollout(self, node, unit: int):
        pass

    @abstractmethod
    def _select(self, node):
        pass

    @abstractmethod
    def _expand(self, node, unit: int):
        pass

    @abstractmethod
    def _simulate(self, node):
        pass

    @abstractmethod
    def _back_propagate(self, path, reward):
        pass

    @abstractmethod
    def _uct_select(self, node):
        pass
