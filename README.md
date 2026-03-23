# 🎮 String Game — Cyber Edition

A two-player number-string strategy game where you compete against an AI opponent powered by Minimax or Alpha-Beta pruning. Built with Python and Pygame.



---

## How to Play

The game starts with a randomly generated string of numbers. On each turn, a player picks **any adjacent pair** of numbers. The pair is replaced by a single number according to these rules:

| Condition | Replacement | Score Effect |
|-----------|-------------|--------------|
| Sum **> 7** | → **1** | **+1** to current player |
| Sum **< 7** | → **3** | **−1** to opponent |
| Sum **= 7** | → **2** | **−1** to current player |

The game ends when only **one number remains**. The player with the higher score wins.

---

## Project Structure

```
src/
├── main.py          # Pygame UI, game loop, rendering
├── game_logic.py    # GameState, moves, apply, heuristic
├── algorithms.py    # Minimax & Alpha-Beta implementations
├── experiments.py   # Automated benchmarking runner
└── settings.py      # Depth, colours, number-colour palette
```

---

## Algorithms

Both algorithms search the game tree to depth `DEPTH` (default: **4**, set in `settings.py`).

### Minimax
Exhaustively explores all possible moves, maximising the CPU score and minimising the human score. No pruning — generates every node.

### Alpha-Beta Pruning
An optimised version of Minimax that skips branches provably unable to affect the final decision. Significantly reduces nodes generated while producing **identical results** to Minimax.

The **heuristic** used at leaf nodes considers:
- Score advantage (`scores[0] - scores[1]`)
- Potential future score changes from remaining pairs
- A small turn-order bonus

---

## Running the Game

```bash
pip install pygame
python src/main.py
```

### Options (top bar in-game)
- **LEN** — starting string length (default 11–25)
- **First** — who moves first: Human or CPU
- **ALG** — AI algorithm: Minimax or Alpha-Beta

---

## Running Experiments

Simulates 10 full games for each algorithm and outputs statistics:

```bash
python src/experiments.py
```

Results are saved to `docs/experiments_results.json`.

### Output summary fields

| Field | Description |
|-------|-------------|
| `cpu_wins` | Games won by the CPU player |
| `opp_wins` | Games won by the opponent |
| `draws` | Tied games |
| `avg_gen` | Average nodes generated per game |
| `avg_eval` | Average nodes evaluated per game |
| `avg_time` | Average time per move (seconds) |

---

## Configuration

Edit `src/settings.py` to tweak:

```python
DEPTH = 4   # Search depth — higher = stronger AI but slower
```

Colour palette and number-to-colour mappings are also defined there.

---

## Dependencies

- Python 3.8+
- `pygame`
