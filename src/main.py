# src/main.py
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import json
import os

from settings import *
from game_logic import GameState, gen_string
from algorithms import Stats, best_move

def rule_text(val_a, val_b):
    total = val_a + val_b
    if total > 7:   
        return f"{val_a}+{val_b}={total} > 7  →  becomes 1  ✚ +1 to YOU"
    elif total < 7: 
        return f"{val_a}+{val_b}={total} < 7  →  becomes 3  ✖ -1 to CPU"
    else:       
        return f"{val_a}+{val_b}={total} = 7  →  becomes 2  ✖ -1 to YOU"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Number String Game")
        self.configure(bg=BG)
        self.minsize(860, 540)

        self.state: GameState = None
        self.sel: int = None   
        self.alg: str = "minimax"
        self.active: bool = False
        self.stats = Stats()

        self._build()
        self._setup_screen()

    # ... [Keep your _build, _mk_label, _dropdown, _score_box layout methods exactly as they were, they are fine] ...
    
    def _do_human(self, pair):
        val_a = self.state.nums[pair]
        val_b = self.state.nums[pair + 1]
        
        self.state = self.state.apply(pair)
        self.sel = None
        
        human_score = self.state.scores[1]
        cpu_score = self.state.scores[0]
        
        self._log(f"YOU: {rule_text(val_a, val_b)}  |  scores: YOU {human_score}  CPU {cpu_score}", "human")
        self._refresh()
        
        if self.state.is_terminal():
            self._end()
        else:
            self.lbl_status.config(text="CPU is thinking…", fg=NEON_B)
            self.after(300, self._cpu_move)

    def _apply_cpu(self, move, elapsed):
        val_a = self.state.nums[move]
        val_b = self.state.nums[move + 1]
        
        self.state = self.state.apply(move)
        
        self.v_stats.set(
            f"Nodes generated: {self.stats.gen}\n"
            f"Nodes evaluated: {self.stats.eval}\n"
            f"Time: {elapsed:.4f}s"
        )
        
        human_score = self.state.scores[1]
        cpu_score = self.state.scores[0]
        self._log(f"CPU: {rule_text(val_a, val_b)}  |  scores: YOU {human_score}  CPU {cpu_score}", "cpu")
        self._refresh()
        
        if self.state.is_terminal():
            self._end()
        else:
            self.lbl_status.config(text="Your turn — click the LEFT cell of any pair!", fg=NEON_G)

    def _end(self):
        self.active = False
        cpu_score = self.state.scores[0]
        human_score = self.state.scores[1]
        
        if human_score > cpu_score:
            msg = f"🎉  YOU WIN!  {human_score} vs {cpu_score}"
            col = NEON_G
        elif cpu_score > human_score:
            msg = f"🤖  CPU WINS!  {cpu_score} vs {human_score}"
            col = NEON_R
        else:
            msg = f"🤝  DRAW!  {cpu_score} vs {human_score}"
            col = NEON_Y
            
        self.lbl_status.config(text=msg, fg=col)
        self.lbl_turn.config(text="END", fg=DIM)
        self._log(msg, "win")

    def _run_exp(self):
        from experiments import run
        results = run()
        
        # Save to the docs folder instead of root
        output_path = os.path.join("..", "docs", "experiments_results.json")
        with open(output_path, "w") as file:
            json.dump(results, file, indent=2)
            
        lines = []
        for alg in ("minimax", "alpha_beta"):
            summary = results[f"{alg}_summary"]
            lines.append(f"{alg}:\n  wins {summary['cpu_wins']} | avg_gen {summary['avg_gen']} | {summary['avg_time']}s/mv")
            
        self.after(0, lambda: self._exp_done("\n".join(lines)))

if __name__ == "__main__":
    App().mainloop()