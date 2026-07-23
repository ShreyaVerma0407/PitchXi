# 🏏 PitchXI

**Build your dream cricket XI, score it against real match performances.**

PitchXI is a desktop fantasy cricket manager built with PyQt5 and SQLite. Pick players within a points budget, respect squad composition rules, save multiple squads, and evaluate how your team would've scored in a given match — all through a native desktop GUI.

---

## ✨ What is this?

Fantasy cricket, but self-contained and offline. PitchXI lets you:

- Draft a squad of 11 from a priced player pool, filtered by role (Batsman / Bowler / All-rounder / Wicket-keeper)
- Stay within a fixed points budget while the app enforces squad rules in real time (e.g. only one wicket-keeper)
- Save and reload multiple squads under different team names
- Run an **Evaluate** pass that pulls real per-match stats and computes a fantasy score using batting, bowling, and fielding scoring rules

It's a small, complete example of a stateful desktop app backed by a relational database — useful as a learning project or a template for similar picker/roster tools.

---

## 🏗️ Architecture

```
PitchXI/
├── database/
│   ├── create_database.py     # Schema definition + seed data
│   └── cricket.db             # SQLite database (generated)
├── ui/
│   └── main_window.ui         # Qt Designer layout (edit visually, no code changes needed)
├── main.py                    # Application logic & scoring engine
├── requirements.txt
└── README.md
```

**Data layer — SQLite, 4 tables:**

| Table | Purpose |
|---|---|
| `stats` | Master player list: season aggregates, price (`value`), role (`ctg`) |
| `match` | Per-match, per-player performance data used purely for score evaluation |
| `teams` | Saved squads: name + total points spent |
| `team_players` | Junction table linking squads to their players (normalized — no comma-separated blobs) |

**Application layer:**

- `main.py` loads `ui/main_window.ui` at runtime via `uic.loadUi`, so the interface can be redesigned in Qt Designer without touching any Python.
- Database access, validation, and scoring are each isolated into small single-purpose functions (`fetch_players_by_category`, `validate_selection`, `calculate_batting_points`, etc.), making the scoring rules easy to unit test or tune independently of the UI.
- `EvaluateTeamDialog` is a self-contained `QDialog` that queries a saved team + selected match and renders per-player and total fantasy points.

**Scoring engine:**

| Discipline | Rule |
|---|---|
| Batting | 1 pt / 2 runs · +5 (50) / +15 (100) · strike-rate bonus (+2 for 80–100 SR, +6 for 100+) · +1/four, +2/six |
| Bowling | 10 pts/wicket · +5 (3–4 wkts) / +10 (5+ wkts) · economy bonus (+10 <2, +7 2–3.5, +4 3.5–4.5) |
| Fielding | 10 pts each for a catch, stumping, or run-out |

---

## 🛠️ Tech Stack

- **Language:** Python 3
- **GUI:** PyQt5 (Qt Designer `.ui` files, loaded dynamically)
- **Database:** SQLite3 (built-in, no external DB server needed)
- **Design pattern:** Separation of data access, business logic (scoring/validation), and presentation

---

## 🚀 How to Run

**1. Clone and install dependencies**

```bash
git clone https://github.com/<your-username>/pitchxi.git
cd pitchxi
pip install -r requirements.txt
```

**2. Build the database** (one-time, generates `database/cricket.db`)

```bash
python database/create_database.py
```

**3. Launch the app**

```bash
python main.py
```

---

## 🔮 Possible Extensions

- Swap the synthetic per-match data generator for a real cricket stats API/feed
- Add live leaderboards across saved squads
- Package as a standalone executable with PyInstaller
- Port the UI to PyQt6/PySide6

---

## 📄 License

MIT — free to use, modify, and build on.

---

<p align="center">Made with ❤️ by <b>Shreya Verma</b></p>
