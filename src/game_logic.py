# src/game_logic.py
import random

def apply_move(numbers, index):
    """Applies the game rules to a pair of numbers."""
    val_sum = numbers[index] + numbers[index + 1]
    result = numbers[:index] + numbers[index + 2:]
    
    if val_sum > 7:
        result.insert(index, 1)
        return result, 1, 0   # +1 to current player
    elif val_sum < 7:
        result.insert(index, 3)
        return result, 0, -1  # -1 to opponent
    else:
        result.insert(index, 2)
        return result, -1, 0  # -1 to current player

class GameState:
    """Full snapshot: number string, scores [cpu, human], whose turn (0=cpu, 1=human)."""
    def __init__(self, numbers, scores=None, turn=0):
        self.nums = numbers[:]
        self.scores = scores[:] if scores else [0, 0]
        self.turn = turn

    def is_terminal(self):
        return len(self.nums) == 1
        
    def moves(self):
        return list(range(len(self.nums) - 1))

    def apply(self, index):
        new_nums, score_current, score_opponent = apply_move(self.nums, index)
        new_scores = self.scores[:]
        
        new_scores[self.turn] += score_current
        new_scores[1 - self.turn] += score_opponent
        
        return GameState(new_nums, new_scores, 1 - self.turn)

    def heuristic(self):
        advantage = self.scores[0] - self.scores[1]
        
        # Calculate potential future score adjustments
        potential = 0
        for a, b in zip(self.nums, self.nums[1:]):
            if a + b > 7:
                potential += 0.3
            elif a + b == 7:
                potential -= 0.3
            else:
                potential += 0.2
                
        turn_bonus = 0.1 if self.turn == 0 else -0.1
        return advantage + potential + turn_bonus

class GameTreeNode:
    """Node in the game tree."""
    def __init__(self, state, move=None):
        self.state = state
        self.move = move
        self.value = None
        self.children = []
        self.is_max = (state.turn == 0)

    def add_child(self, child_node):
        self.children.append(child_node)

def gen_string(length):
    return [random.randint(1, 9) for _ in range(length)]