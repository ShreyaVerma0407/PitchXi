import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "cricket.db")

# player, scored, faced, fours, sixes, bowled, maiden, given, wkts,
# catches, stumping, ro, value, matches, runs, 100s, 50s, ctg
PLAYER_DATA = [
    ("Kohli",         102, 98, 8, 2,  0,  0,  0,  0, 0, 0, 1, 120, 189, 8257, 28, 43, "BAT"),
    ("Yuvraj",         12, 20, 1, 0, 48,  0, 36,  1, 0, 0, 0, 100,  86, 3589, 10, 21, "BAT"),
    ("Rahane",         49, 75, 3, 0,  0,  0,  0,  1, 0, 0, 0, 100, 158, 5435, 11, 31, "BAT"),
    ("Dhawan",         32, 35, 4, 0,  0,  0,  0,  0, 0, 0, 0,  85,  25,  565,  2,  1, "BAT"),
    ("Dhoni",          56, 45, 3, 1,  0,  0,  0,  0, 3, 2, 0,  75,  78, 2573,  3, 19, "WK"),
    ("Axar",            8,  4, 2, 0, 48,  2, 35,  1, 0, 0, 0, 100,  67,  208,  0,  0, "BWL"),
    ("Pandya",         42, 36, 3, 3, 30,  0, 25,  0, 1, 0, 0,  75,  70,   77,  0,  0, "BWL"),
    ("Jadeja",         18, 10, 1, 1, 60,  3, 50,  2, 1, 0, 1,  85,  16,    1,  0,  1, "BWL"),
    ("Kedar",          65, 60, 7, 0, 24,  0, 24,  0, 0, 0, 0,  90, 111,  675,  0,  1, "BWL"),
    ("Ashwin",         23, 42, 3, 0, 60,  2, 45,  6, 0, 0, 0, 100, 136, 1914,  0, 10, "AR"),
    ("Umesh",           0,  0, 0, 0, 54,  0, 50,  4, 1, 0, 0, 110, 296, 9496, 10, 64, "AR"),
    ("Bumrah",          0,  0, 0, 0, 60,  2, 49,  1, 0, 0, 0,  60,  73, 1365,  0,  8, "WK"),
    ("Bhuvaneshwar",   15, 12, 2, 0, 60,  1, 46,  2, 0, 0, 0,  75,  17,  289,  0,  2, "AR"),
    ("Rohit",          46, 65, 5, 0,  0,  0,  0,  0, 1, 0, 0,  85, 304, 8701, 14, 52, "BAT"),
    ("Kartick",        29, 42, 3, 0,  0,  0,  0,  0, 2, 0, 1,  75,  11,  111,  0,  0, "AR"),
]


def create_tables(conn):
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS stats")
    cur.execute("""
        CREATE TABLE stats (
            player   TEXT PRIMARY KEY,
            matches  INTEGER NOT NULL,
            runs     INTEGER NOT NULL,
            hundreds INTEGER NOT NULL,
            fifties  INTEGER NOT NULL,
            value    INTEGER NOT NULL,
            ctg      TEXT NOT NULL CHECK (ctg IN ('BAT','BWL','AR','WK'))
        )
    """)

    cur.execute("DROP TABLE IF EXISTS match")
    cur.execute("""
        CREATE TABLE match (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            match_no TEXT NOT NULL,
            player   TEXT NOT NULL,
            scored   INTEGER NOT NULL,
            faced    INTEGER NOT NULL,
            fours    INTEGER NOT NULL,
            sixes    INTEGER NOT NULL,
            bowled   REAL    NOT NULL,   -- overs bowled
            maiden   INTEGER NOT NULL,
            given    INTEGER NOT NULL,   -- runs conceded
            wkts     INTEGER NOT NULL,
            catches  INTEGER NOT NULL,
            stumping INTEGER NOT NULL,
            ro       INTEGER NOT NULL,   -- run outs
            FOREIGN KEY (player) REFERENCES stats(player)
        )
    """)

    cur.execute("DROP TABLE IF EXISTS teams")
    cur.execute("""
        CREATE TABLE teams (
            name  TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("DROP TABLE IF EXISTS team_players")
    cur.execute("""
        CREATE TABLE team_players (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            player TEXT NOT NULL,
            ctg    TEXT NOT NULL,
            FOREIGN KEY (team_name) REFERENCES teams(name),
            FOREIGN KEY (player) REFERENCES stats(player)
        )
    """)

    conn.commit()


def seed_stats(conn):
    cur = conn.cursor()
    rows = [(p[0], p[13], p[14], p[15], p[16], p[12], p[17]) for p in PLAYER_DATA]
    cur.executemany(
        "INSERT INTO stats (player, matches, runs, hundreds, fifties, value, ctg) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_match_data(conn, num_matches=6):
    """
    The mock-up screens show a 'Select Match' dropdown with Match1..Match6.
    The problem statement only gives one row of aggregate data per player,
    so we generate 6 plausible per-match rows per player using that row as
    a baseline (with a bit of random variation) so the Evaluate Score
    feature has real data to work with.
    """
    random.seed(42)
    cur = conn.cursor()
    rows = []
    for p in PLAYER_DATA:
        (player, scored, faced, fours, sixes, bowled, maiden, given, wkts,
         catches, stumping, ro, *_rest) = p
        for m in range(1, num_matches + 1):
            match_no = f"Match{m}"

            def jitter(base, spread=0.35):
                return max(0, round(base * random.uniform(1 - spread, 1 + spread)))

            rows.append((
                match_no, player,
                jitter(scored), jitter(faced) if faced else 0,
                jitter(fours), jitter(sixes),
                round(jitter(bowled), 1) if bowled else 0,
                jitter(maiden) if maiden else 0,
                jitter(given) if given else 0,
                jitter(wkts) if wkts else 0,
                jitter(catches) if catches else 0,
                jitter(stumping) if stumping else 0,
                jitter(ro) if ro else 0,
            ))

    cur.executemany(
        """INSERT INTO match
           (match_no, player, scored, faced, fours, sixes, bowled, maiden,
            given, wkts, catches, stumping, ro)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def build_database():
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_stats(conn)
    seed_match_data(conn)
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    build_database()
