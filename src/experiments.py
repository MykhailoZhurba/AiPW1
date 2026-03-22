# src/experiments.py
import time
import json
import random
import os
from game_logic import GameState, gen_string
from algorithms import Stats, best_move
from settings import DEPTH

TOTAL_GAMES = 10

def sim_game(alg, nums):
    state = GameState(nums, [0, 0], 0)
    stats = Stats()
    
    gen_total = 0
    eval_total = 0
    times = []
    
    while not state.is_terminal():
        start_time = time.perf_counter()
        move, _ = best_move(state, DEPTH, alg, stats)
        times.append(time.perf_counter() - start_time)
        
        gen_total += stats.gen
        eval_total += stats.eval
        state = state.apply(move)
        
    cpu_score = state.scores[0]
    opp_score = state.scores[1]
    
    if cpu_score > opp_score:
        winner = "cpu"
    elif opp_score > cpu_score:
        winner = "opp"
    else:
        winner = "draw"
        
    return {
        "winner": winner,
        "cpu_score": cpu_score, 
        "opp_score": opp_score,
        "nodes_gen": gen_total, 
        "nodes_eval": eval_total,
        "avg_time": round(sum(times) / len(times), 6)
    }

def run(seed=42):
    random.seed(seed)
    output = {}
    
    for alg in ("minimax", "alpha_beta"):
        games = []
        for _ in range(TOTAL_GAMES):
            random_string = gen_string(random.randint(15, 25))
            games.append(sim_game(alg, random_string))
            
        output[alg] = games
        output[f"{alg}_summary"] = {
            "cpu_wins":  sum(g["winner"] == "cpu"  for g in games),
            "opp_wins":  sum(g["winner"] == "opp"  for g in games),
            "draws":     sum(g["winner"] == "draw" for g in games),
            "avg_gen":   round(sum(g["nodes_gen"]  for g in games) / TOTAL_GAMES),
            "avg_eval":  round(sum(g["nodes_eval"] for g in games) / TOTAL_GAMES),
            "avg_time":  round(sum(g["avg_time"]   for g in games) / TOTAL_GAMES, 6),
        }
    return output

if __name__ == "__main__":
    print("Running…")
    results = run()
    
    output_path = os.path.join("..", "docs", "experiments_results.json")
    with open(output_path, "w") as file:
        json.dump(results, file, indent=2)
        
    for alg in ("minimax", "alpha_beta"):
        summary = results[f"{alg}_summary"]
        print(f"\n{alg}: wins={summary['cpu_wins']} opp={summary['opp_wins']} draws={summary['draws']} "
              f"avgGen={summary['avg_gen']} avgTime={summary['avg_time']}s")