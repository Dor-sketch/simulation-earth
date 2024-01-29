from rules import TransitionRules

class Cell:
    """
    Represents a single cell in a grid for the Cellular Automata simulation.
    Holds the current state of the cell and a dictionary of its neighbors.
    The cell's next state is determined based on its current state and the states
    of its neighbors according to defined transition rules.
    """

    def __init__(self, state, neighbors: dict = None):
        self.state = state
        self.neighbors = neighbors if neighbors is not None else {}

    def set_neighbors(self, neighbors: dict):
        self.neighbors = neighbors

    def update_state(self):
        rules = TransitionRules(self)
        with rules:
            return rules.apply_rules()

    def __str__(self):
        # A concise representation of the cell's state and the number of neighbors
        return f'Cell State: {self.state}, Neighbors: {len(self.neighbors)}'
