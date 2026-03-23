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

    # ── Layout Methods (From your original gui.py) ───────────────────────────
    def _build(self):
        top = tk.Frame(self, bg=PANEL, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="⬡ NUMBER STRING", bg=PANEL, fg=NEON_G,
                 font=("Courier New", 18, "bold")).pack(side="left", padx=18)

        ctrl = tk.Frame(top, bg=PANEL)
        ctrl.pack(side="right", padx=18)

        self._mk_label(ctrl, "Length:").pack(side="left")
        self.v_len = tk.IntVar(value=15)
        tk.Spinbox(ctrl, from_=15, to=25, width=3, textvariable=self.v_len,
                   bg=DARKER, fg=NEON_Y, font=("Courier New", 12),
                   bd=0, relief="flat", buttonbackground=DARKER,
                   insertbackground=NEON_Y).pack(side="left", padx=(2, 10))

        self._mk_label(ctrl, "First:").pack(side="left")
        self.v_first = tk.StringVar(value="Human")
        self._dropdown(ctrl, self.v_first, ["Human", "CPU"]).pack(side="left", padx=(2, 10))

        self._mk_label(ctrl, "Algorithm:").pack(side="left")
        self.v_alg = tk.StringVar(value="Minimax")
        self._dropdown(ctrl, self.v_alg, ["Minimax", "Alpha-Beta"]).pack(side="left", padx=(2, 14))

        self.btn_new = tk.Button(ctrl, text="▶  NEW GAME",
                                 bg=NEON_G, fg=BG,
                                 font=("Courier New", 11, "bold"),
                                 bd=0, padx=14, pady=5,
                                 activebackground="#00cc6a",
                                 cursor="hand2", command=self.new_game)
        self.btn_new.pack(side="left")

        scores = tk.Frame(self, bg=BG)
        scores.pack(fill="x", padx=24, pady=(14, 4))

        self.lbl_human = self._score_box(scores, "YOU",  NEON_G)
        self.lbl_human.pack(side="left")

        self.lbl_turn = tk.Label(scores, text="VS", bg=BG, fg=DIM,
                                 font=("Courier New", 13, "bold"))
        self.lbl_turn.pack(side="left", expand=True)

        self.lbl_cpu = self._score_box(scores, "CPU", NEON_B)
        self.lbl_cpu.pack(side="right")

        self.strip_frame = tk.Frame(self, bg=BG)
        self.strip_frame.pack(fill="x", padx=24, pady=6)

        self.lbl_hint = tk.Label(self, text="", bg=BG, fg=NEON_Y,
                                 font=("Courier New", 10), height=1)
        self.lbl_hint.pack()

        self.lbl_status = tk.Label(self, text="", bg=BG, fg=WHITE,
                                   font=("Courier New", 12, "bold"))
        self.lbl_status.pack(pady=(2, 0))

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="both", expand=True, padx=24, pady=(6, 14))

        self._build_log(bottom)
        self._build_stats(bottom)

    def _mk_label(self, p, t):
        return tk.Label(p, text=t, bg=PANEL, fg=DIM, font=("Courier New", 9))

    def _dropdown(self, parent, var, opts):
        m = tk.OptionMenu(parent, var, *opts)
        m.config(bg=DARKER, fg=NEON_B, font=("Courier New", 10),
                 bd=0, relief="flat", activebackground=PANEL,
                 highlightthickness=0, cursor="hand2")
        m["menu"].config(bg=DARKER, fg=NEON_B, font=("Courier New", 10),
                         bd=0, activebackground=PANEL)
        return m

    def _score_box(self, parent, label, colour):
        f = tk.Frame(parent, bg=BG)
        tk.Label(f, text=label, bg=BG, fg=colour,
                 font=("Courier New", 9, "bold")).pack()
        v = tk.StringVar(value="0")
        tk.Label(f, textvariable=v, bg=BG, fg=colour,
                 font=("Courier New", 32, "bold")).pack()
        f._var = v
        return f

    def _build_log(self, parent):
        f = tk.Frame(parent, bg=PANEL, bd=0)
        f.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(f, text="MOVE LOG", bg=PANEL, fg=DIM,
                 font=("Courier New", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        self.log = tk.Text(f, bg=PANEL, fg=WHITE, font=("Courier New", 9),
                           bd=0, relief="flat", state="disabled",
                           wrap="word", height=7)
        self.log.pack(fill="both", expand=True, padx=8, pady=4)

        self.log.tag_config("cpu",   foreground=NEON_B)
        self.log.tag_config("human", foreground=NEON_G)
        self.log.tag_config("sys",   foreground=DIM)
        self.log.tag_config("win",   foreground=NEON_Y)

    def _build_stats(self, parent):
        f = tk.Frame(parent, bg=PANEL, bd=0, width=220)
        f.pack(side="right", fill="y")
        f.pack_propagate(False)
        tk.Label(f, text="LAST MOVE STATS", bg=PANEL, fg=DIM,
                 font=("Courier New", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        self.v_stats = tk.StringVar(value="—")
        tk.Label(f, textvariable=self.v_stats, bg=PANEL, fg=NEON_B,
                 font=("Courier New", 9), justify="left",
                 wraplength=200).pack(anchor="w", padx=8)

        tk.Frame(f, bg=DIM, height=1).pack(fill="x", padx=8, pady=6)
        tk.Label(f, text="RULES CHEAT SHEET", bg=PANEL, fg=DIM,
                 font=("Courier New", 8, "bold")).pack(anchor="w", padx=8)
        rules = (
            "Sum > 7  →  pair = 1   +1 to you\n"
            "Sum < 7  →  pair = 3   -1 to CPU\n"
            "Sum = 7  →  pair = 2   -1 to you\n\n"
            "Click the LEFT cell\nof the pair you want!"
        )
        tk.Label(f, text=rules, bg=PANEL, fg=WHITE,
                 font=("Courier New", 9), justify="left").pack(anchor="w", padx=8)

        tk.Frame(f, bg=DIM, height=1).pack(fill="x", padx=8, pady=6)
        self.btn_exp = tk.Button(f, text="⚗ Run Experiments",
                                 bg=DARKER, fg=NEON_Y,
                                 font=("Courier New", 9, "bold"),
                                 bd=0, padx=8, pady=4,
                                 activebackground=PANEL,
                                 cursor="hand2",
                                 command=self._run_exp_thread)
        self.btn_exp.pack(padx=8, pady=2, fill="x")
        self.v_exp = tk.StringVar(value="")
        tk.Label(f, textvariable=self.v_exp, bg=PANEL, fg=DIM,
                 font=("Courier New", 8), justify="left",
                 wraplength=200).pack(anchor="w", padx=8)

    # ── Game Flow & Logic Methods ────────────────────────────────────────────
    def _setup_screen(self):
        self.lbl_status.config(text="Press  ▶ NEW GAME  to start!", fg=NEON_Y)

    def new_game(self):
        n = self.v_len.get()
        turn = 1 if self.v_first.get() == "Human" else 0
        self.alg = "alpha_beta" if "Alpha" in self.v_alg.get() else "minimax"
        self.state = GameState(gen_string(n), [0, 0], turn)
        self.sel = None
        self.active = True
        self._log(f"New game — length {n}, first: {self.v_first.get()}, alg: {self.alg}", "sys")
        self._refresh()
        if turn == 0:
            self.lbl_status.config(text="CPU is thinking…", fg=NEON_B)
            self.after(350, self._cpu_move)
        else:
            self.lbl_status.config(text="Your turn — click the LEFT cell of any pair!", fg=NEON_G)

    def _refresh(self):
        self.lbl_human._var.set(str(self.state.scores[1]))
        self.lbl_cpu._var.set(str(self.state.scores[0]))
        if self.active:
            self.lbl_turn.config(text="←YOU" if self.state.turn == 1 else "CPU→", fg=NEON_Y)
        self._draw_strip()

    def _draw_strip(self):
        for w in self.strip_frame.winfo_children():
            w.destroy()

        nums = self.state.nums
        human = self.active and self.state.turn == 1

        canvas = tk.Canvas(self.strip_frame, bg=BG, height=72, highlightthickness=0)
        canvas.pack(fill="x")
        inner = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        for i, n in enumerate(nums):
            sel1 = (self.sel is not None and i == self.sel)
            sel2 = (self.sel is not None and i == self.sel + 1)
            fg = NUM_COLOR.get(n, WHITE)
            bg = NEON_Y if sel1 else (NEON_O if sel2 else DARKER)
            txt_fg = BG if (sel1 or sel2) else fg

            cell = tk.Label(inner, text=str(n), width=3, height=2,
                            bg=bg, fg=txt_fg,
                            font=("Courier New", 16, "bold"),
                            relief="flat", bd=0,
                            cursor="hand2" if human else "arrow")
            cell.grid(row=0, column=i, padx=3, pady=4)

            if human:
                cell.bind("<Enter>", lambda e, c=cell, idx=i: self._hover(c, idx, True))
                cell.bind("<Leave>", lambda e, c=cell, idx=i: self._hover(c, idx, False))
                cell.bind("<Button-1>", lambda e, idx=i: self._click(idx))

        self.lbl_hint.config(text="")

    def _hover(self, cell, idx, entering):
        nums = self.state.nums
        if self.sel is None:
            if idx < len(nums) - 1:
                if entering:
                    cell.config(bg=NEON_Y, fg=BG)
                    self.lbl_hint.config(text=f"  Preview: {rule_text(nums[idx], nums[idx+1])}")
                else:
                    cell.config(bg=DARKER, fg=NUM_COLOR.get(nums[idx], WHITE))
                    self.lbl_hint.config(text="")
        elif idx in (self.sel, self.sel + 1):
            pass 

    def _click(self, idx):
        if not self.active or self.state.turn != 1:
            return
        nums = self.state.nums

        if self.sel is None:
            if idx >= len(nums) - 1:
                self.lbl_status.config(text="That's the last cell — pick any other!", fg=NEON_R)
                return
            self.sel = idx
            self.lbl_status.config(
                text=f"Picked [{nums[idx]}]. Now click [{nums[idx+1]}] (right neighbour) to confirm!",
                fg=NEON_Y)
            self._draw_strip()
        else:
            if idx == self.sel + 1 or idx == self.sel - 1:
                pair = min(self.sel, idx)
                self._do_human(pair)
            else:
                self.sel = None
                self.lbl_status.config(text="Cancelled. Click the LEFT cell of a pair!", fg=NEON_G)
                self._draw_strip()

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

    def _cpu_move(self):
        def think():
            t0 = time.perf_counter()
            mv, _ = best_move(self.state, DEPTH, self.alg, self.stats)
            elapsed = time.perf_counter() - t0
            self.after(0, lambda: self._apply_cpu(mv, elapsed))
        threading.Thread(target=think, daemon=True).start()

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

    def _log(self, msg, tag="sys"):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _run_exp_thread(self):
        self.btn_exp.config(state="disabled", text="Running…")
        self.v_exp.set("Please wait…")
        threading.Thread(target=self._run_exp, daemon=True).start()

    def _run_exp(self):
        from experiments import run
        results = run()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(base_dir, "docs", "experiments_results.json")
        
        with open(output_path, "w") as file:
            json.dump(results, file, indent=2)
            
        lines = []
        for alg in ("minimax", "alpha_beta"):
            summary = results[f"{alg}_summary"]
            lines.append(f"{alg}:\n  wins {summary['cpu_wins']} | avg_gen {summary['avg_gen']} | {summary['avg_time']}s/mv")
            
        self.after(0, lambda: self._exp_done("\n".join(lines)))

    def _exp_done(self, txt):
        self.btn_exp.config(state="normal", text="⚗ Run Experiments")
        self.v_exp.set(txt + "\n→ experiments_results.json")

if __name__ == "__main__":
    App().mainloop()