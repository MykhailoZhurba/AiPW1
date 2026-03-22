# src/algorithms.py
import math
from game_logic import GameState, GameTreeNode

class Stats:
    def __init__(self):
        self.gen = 0
        self.eval = 0
        
    def reset(self):
        self.gen = 0
        self.eval = 0

def minimax(node, depth, stats):
    if depth == 0 or node.state.is_terminal():
        stats.eval += 1
        if node.state.is_terminal():
            node.value = node.state.scores[0] - node.state.scores[1]
        else:
            node.value = node.state.heuristic()
        return node.value
        
    values = []
    for move_index in node.state.moves():
        child = GameTreeNode(node.state.apply(move_index), move_index)
        stats.gen += 1
        node.add_child(child)
        values.append(minimax(child, depth - 1, stats))
        
    node.value = max(values) if node.is_max else min(values)
    return node.value

def alpha_beta(node, depth, alpha, beta, stats):
    if depth == 0 or node.state.is_terminal():
        stats.eval += 1
        if node.state.is_terminal():
            node.value = node.state.scores[0] - node.state.scores[1]
        else:
            node.value = node.state.heuristic()
        return node.value
        
    if node.is_max:
        best_value = -math.inf
        for move_index in node.state.moves():
            child = GameTreeNode(node.state.apply(move_index), move_index)
            stats.gen += 1
            node.add_child(child)
            
            best_value = max(best_value, alpha_beta(child, depth - 1, alpha, beta, stats))
            alpha = max(alpha, best_value)
            if alpha >= beta:
                break
        node.value = best_value
    else:
        best_value = math.inf
        for move_index in node.state.moves():
            child = GameTreeNode(node.state.apply(move_index), move_index)
            stats.gen += 1
            node.add_child(child)
            
            best_value = min(best_value, alpha_beta(child, depth - 1, alpha, beta, stats))
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        node.value = best_value
        
    return node.value

def best_move(state, depth, alg, stats):
    stats.reset()
    root = GameTreeNode(state)
    stats.gen += 1
    
    if alg == "minimax":
        minimax(root, depth, stats)
    else:
        alpha_beta(root, depth, -math.inf, math.inf, stats)
        
    best = max(root.children, key=lambda c: c.value, default=None)
    return (best.move if best else 0), root