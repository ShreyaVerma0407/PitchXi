
import os
import sys
import sqlite3

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QMessageBox, QInputDialog,
    QListWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QPushButton, QWidget
)
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cricket.db")
UI_PATH = os.path.join(BASE_DIR, "ui", "main_window.ui")

STYLESHEET = """
QMainWindow, QDialog {
    background-color: #10141c;
}
QLabel {
    color: #d7dce5;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QLabel#lblAppTitle {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
    padding-top: 2px;
}
QLabel#lblAppSubtitle {
    color: #8a93a6;
    font-size: 13px;
    padding-bottom: 4px;
}
QFrame#statsBar {
    background-color: #171c27;
    border: 1px solid #262d3d;
    border-radius: 10px;
}
QFrame#statsBar QLabel {
    color: #7d869a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QLabel#lblBatCount, QLabel#lblBowCount, QLabel#lblArCount, QLabel#lblWkCount {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}
QLabel#lblPointsAvailable {
    color: #4ade80;
    font-size: 18px;
    font-weight: 700;
}
QLabel#lblPointsUsed {
    color: #f59e0b;
    font-size: 18px;
    font-weight: 700;
}
QLabel#lblTeamName {
    color: #60a5fa;
    font-size: 15px;
    font-weight: 700;
}
QGroupBox {
    background-color: #171c27;
    border: 1px solid #262d3d;
    border-radius: 10px;
    margin-top: 14px;
    color: #d7dce5;
    font-weight: 600;
    padding-top: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #ffffff;
}
QListWidget {
    background-color: #0d1117;
    border: 1px solid #262d3d;
    border-radius: 8px;
    color: #e5e9f0;
    padding: 6px;
    font-size: 13px;
    outline: none;
}
QListWidget::item {
    padding: 7px 8px;
    border-radius: 5px;
}
QListWidget::item:hover {
    background-color: #1c2433;
}
QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QListWidget::alternate {
    background-color: #10141c;
}
QRadioButton {
    color: #d7dce5;
    font-size: 13px;
    padding: 4px 2px;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}
QMenuBar {
    background-color: #0d1117;
    color: #d7dce5;
    border-bottom: 1px solid #262d3d;
}
QMenuBar::item:selected {
    background-color: #1c2433;
}
QMenu {
    background-color: #171c27;
    color: #d7dce5;
    border: 1px solid #262d3d;
}
QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QStatusBar {
    background-color: #0d1117;
    color: #7d869a;
    border-top: 1px solid #262d3d;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QComboBox {
    background-color: #0d1117;
    color: #e5e9f0;
    border: 1px solid #262d3d;
    border-radius: 6px;
    padding: 6px 10px;
}
QComboBox QAbstractItemView {
    background-color: #171c27;
    color: #e5e9f0;
    selection-background-color: #2563eb;
}
QLineEdit, QInputDialog QLineEdit {
    background-color: #0d1117;
    color: #e5e9f0;
    border: 1px solid #262d3d;
    border-radius: 6px;
    padding: 6px;
}
"""

STARTING_POINTS = 1000
SQUAD_SIZE = 11
CATEGORY_LIMITS = {"BAT": 6, "BOW": 6, "AR": 6, "WK": 1}
# NOTE: stats table stores bowlers/allrounders as 'BWL'/'AR'; the UI groups
# BWL under the "BOW" radio button label used in the mock-up.
CATEGORY_TO_DB_CTG = {"BAT": "BAT", "BOW": "BWL", "AR": "AR", "WK": "WK"}


# --------------------------------------------------------------------------
# Database helper functions (kept small and single-purpose -> modularity)
# --------------------------------------------------------------------------

def get_connection():
    """Open a connection to the cricket database, raising a clear error
    if the database file is missing."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run database/create_database.py first."
        )
    return sqlite3.connect(DB_PATH)


def fetch_players_by_category(ctg_label):
    """Return list of (player, value, ctg) for a UI category label (BAT/BOW/AR/WK)."""
    db_ctg = CATEGORY_TO_DB_CTG[ctg_label]
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT player, value, ctg FROM stats WHERE ctg = ? ORDER BY player", (db_ctg,))
        return cur.fetchall()
    finally:
        conn.close()


def fetch_player_value_and_ctg(player_name):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value, ctg FROM stats WHERE player = ?", (player_name,))
        row = cur.fetchone()
        return row  # (value, ctg) or None
    finally:
        conn.close()


def fetch_all_team_names():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM teams ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_all_match_numbers():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT match_no FROM match ORDER BY match_no")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def save_team_to_db(team_name, selected_players, total_value):
    """Persist a team: overwrite if it already exists."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM team_players WHERE team_name = ?", (team_name,))
        cur.execute("DELETE FROM teams WHERE name = ?", (team_name,))
        cur.execute("INSERT INTO teams (name, value) VALUES (?, ?)", (team_name, total_value))
        for player_name, ctg in selected_players:
            cur.execute(
                "INSERT INTO team_players (team_name, player, ctg) VALUES (?, ?, ?)",
                (team_name, player_name, ctg),
            )
        conn.commit()
    except sqlite3.Error as db_error:
        conn.rollback()
        raise RuntimeError(f"Could not save team: {db_error}")
    finally:
        conn.close()


def load_team_from_db(team_name):
    """Return (total_value, list of (player, ctg))."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM teams WHERE name = ?", (team_name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Team '{team_name}' does not exist")
        total_value = row[0]
        cur.execute("SELECT player, ctg FROM team_players WHERE team_name = ?", (team_name,))
        players = cur.fetchall()
        return total_value, players
    finally:
        conn.close()


def fetch_match_row(player_name, match_no):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT scored, faced, fours, sixes, bowled, maiden, given,
                      wkts, catches, stumping, ro
               FROM match WHERE player = ? AND match_no = ?""",
            (player_name, match_no),
        )
        return cur.fetchone()
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Scoring rules (each piece of scoring logic is its own function)
# --------------------------------------------------------------------------

def calculate_batting_points(scored, faced, fours, sixes):
    points = scored // 2  # 1 point per 2 runs

    if scored >= 100:
        points += 15  # additional 5 (fifty) + additional 10 (century)
    elif scored >= 50:
        points += 5

    if faced > 0:
        strike_rate = (scored / faced) * 100
        if strike_rate > 100:
            points += 6  # 2 (base) + 4 (additional)
        elif strike_rate >= 80:
            points += 2

    points += fours * 1
    points += sixes * 2
    return points


def calculate_bowling_points(bowled_overs, given, wkts):
    points = wkts * 10

    if wkts >= 5:
        points += 10
    elif wkts == 3 or wkts == 4:
        points += 5

    if bowled_overs and bowled_overs > 0:
        economy = given / bowled_overs
        if economy < 2:
            points += 10
        elif economy <= 3.5:
            points += 7
        elif economy <= 4.5:
            points += 4
    return points


def calculate_fielding_points(catches, stumping, ro):
    return (catches + stumping + ro) * 10


def calculate_total_points(match_row):
    (scored, faced, fours, sixes, bowled, maiden, given, wkts,
     catches, stumping, ro) = match_row
    batting = calculate_batting_points(scored, faced, fours, sixes)
    bowling = calculate_bowling_points(bowled, given, wkts)
    fielding = calculate_fielding_points(catches, stumping, ro)
    return batting + bowling + fielding


# --------------------------------------------------------------------------
# Evaluate Team dialog
# --------------------------------------------------------------------------

class EvaluateTeamDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Evaluate the Performance of your Fantasy Team")
        self.resize(420, 420)

        self.team_combo = QComboBox()
        self.match_combo = QComboBox()
        self.players_list = QListWidget()
        self.points_list = QListWidget()
        self.total_label = QLabel("Points: 0")
        self.calculate_btn = QPushButton("Calculate Score")

        top_row = QHBoxLayout()
        top_row.addWidget(self.team_combo)
        top_row.addWidget(self.match_combo)

        lists_row = QHBoxLayout()
        lists_row.addWidget(self.players_list)
        lists_row.addWidget(self.points_list)

        layout = QVBoxLayout()
        layout.addLayout(top_row)
        layout.addLayout(lists_row)
        layout.addWidget(self.total_label)
        layout.addWidget(self.calculate_btn)
        self.setLayout(layout)

        self.team_combo.addItems(fetch_all_team_names())
        self.match_combo.addItems(fetch_all_match_numbers())
        self.calculate_btn.clicked.connect(self.calculate_score)

    def calculate_score(self):
        team_name = self.team_combo.currentText()
        match_no = self.match_combo.currentText()
        if not team_name or not match_no:
            QMessageBox.warning(self, "Missing selection", "Please select both a team and a match.")
            return

        try:
            _, players = load_team_from_db(team_name)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.players_list.clear()
        self.points_list.clear()
        total = 0
        for player_name, _ctg in players:
            match_row = fetch_match_row(player_name, match_no)
            if match_row is None:
                points = 0
            else:
                points = calculate_total_points(match_row)
            total += points
            self.players_list.addItem(QListWidgetItem(player_name))
            self.points_list.addItem(QListWidgetItem(str(points)))

        self.total_label.setText(f"Points: {total}")


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_PATH, self)

        self.resize(980, 640)
        self.setMinimumSize(900, 600)

        self.current_team_name = None
        self.points_available = STARTING_POINTS
        self.points_used = 0
        # selected_players: dict player_name -> (value, ctg)
        self.selected_players = {}

        self._set_selection_enabled(False)
        self.listAvailablePlayers.addItem(
            QListWidgetItem("Go to Manage Teams → New Team to start drafting")
        )
        self.statusbar.showMessage("Create a new team from the Manage Teams menu to begin.")

        self.actionNewTeam.triggered.connect(self.new_team)
        self.actionOpenTeam.triggered.connect(self.open_team)
        self.actionSaveTeam.triggered.connect(self.save_team)
        self.actionEvaluateTeam.triggered.connect(self.evaluate_team)

        self.radioBat.toggled.connect(lambda checked: checked and self.populate_available_list("BAT"))
        self.radioBow.toggled.connect(lambda checked: checked and self.populate_available_list("BOW"))
        self.radioAr.toggled.connect(lambda checked: checked and self.populate_available_list("AR"))
        self.radioWk.toggled.connect(lambda checked: checked and self.populate_available_list("WK"))

        self.listAvailablePlayers.itemDoubleClicked.connect(self.add_selected_player)
        self.listSelectedPlayers.itemDoubleClicked.connect(self.remove_selected_player)

    # ---------------- UI state helpers ----------------

    def _set_selection_enabled(self, enabled):
        for widget in (self.radioBat, self.radioBow, self.radioAr, self.radioWk,
                       self.listAvailablePlayers, self.listSelectedPlayers):
            widget.setEnabled(enabled)

    def _refresh_summary_labels(self):
        counts = {"BAT": 0, "BWL": 0, "AR": 0, "WK": 0}
        for _player, (_value, ctg) in self.selected_players.items():
            counts[ctg] += 1

        self.lblBatCount.setText(str(counts["BAT"]))
        self.lblBowCount.setText(str(counts["BWL"]))
        self.lblArCount.setText(str(counts["AR"]))
        self.lblWkCount.setText(str(counts["WK"]))
        self.lblPointsAvailable.setText(str(self.points_available))
        self.lblPointsUsed.setText(str(self.points_used))
        self.lblTeamName.setText(self.current_team_name or "--")

    # ---------------- Manage Teams menu actions ----------------

    def new_team(self):
        team_name, ok = QInputDialog.getText(self, "New Team", "Enter team name:")
        if not ok or not team_name.strip():
            return
        self.current_team_name = team_name.strip()
        self.points_available = STARTING_POINTS
        self.points_used = 0
        self.selected_players = {}
        self.listSelectedPlayers.clear()
        self._set_selection_enabled(True)
        self.radioBat.setChecked(True)
        self.populate_available_list("BAT")
        self._refresh_summary_labels()
        self.statusbar.showMessage(f"Team '{self.current_team_name}' created. Start drafting!", 5000)

    def open_team(self):
        team_names = fetch_all_team_names()
        if not team_names:
            QMessageBox.information(self, "No teams", "No saved teams found yet.")
            return
        team_name, ok = QInputDialog.getItem(self, "Open Team", "Select a team:", team_names, 0, False)
        if not ok:
            return
        try:
            total_value, players = load_team_from_db(team_name)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.current_team_name = team_name
        self.points_used = total_value
        self.points_available = STARTING_POINTS - total_value
        self.selected_players = {}
        self.listSelectedPlayers.clear()

        for player_name, ctg in players:
            row = fetch_player_value_and_ctg(player_name)
            value = row[0] if row else 0
            self.selected_players[player_name] = (value, ctg)
            self.listSelectedPlayers.addItem(QListWidgetItem(player_name))

        self._set_selection_enabled(True)
        self.radioBat.setChecked(True)
        self.populate_available_list("BAT")
        self._refresh_summary_labels()

    def save_team(self):
        if not self.current_team_name:
            QMessageBox.warning(self, "No team", "Create a new team first (Manage Teams > NEW Team).")
            return
        if len(self.selected_players) == 0:
            QMessageBox.warning(self, "Empty team", "Select at least one player before saving.")
            return
        try:
            players_for_db = [(name, ctg) for name, (_v, ctg) in self.selected_players.items()]
            save_team_to_db(self.current_team_name, players_for_db, self.points_used)
        except RuntimeError as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return
        QMessageBox.information(self, "Saved", f"Team '{self.current_team_name}' saved successfully.")
        self.statusbar.showMessage(f"Team '{self.current_team_name}' saved.", 4000)

    def evaluate_team(self):
        dialog = EvaluateTeamDialog(self)
        dialog.exec_()

    # ---------------- List population & selection logic ----------------

    def populate_available_list(self, ctg_label):
        self.listAvailablePlayers.clear()
        try:
            players = fetch_players_by_category(ctg_label)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Database error", str(e))
            return

        for player_name, _value, _ctg in players:
            if player_name not in self.selected_players:
                self.listAvailablePlayers.addItem(QListWidgetItem(player_name))

    def _current_category_label(self):
        if self.radioBat.isChecked():
            return "BAT"
        if self.radioBow.isChecked():
            return "BOW"
        if self.radioAr.isChecked():
            return "AR"
        if self.radioWk.isChecked():
            return "WK"
        return "BAT"

    def validate_selection(self, player_name, value, ctg):
        """Returns (is_valid, error_message)."""
        if len(self.selected_players) >= SQUAD_SIZE:
            return False, f"You can't select more than {SQUAD_SIZE} players."

        if value > self.points_available:
            return False, "Not enough points available to select this player."

        category_count = sum(1 for _p, (_v, c) in self.selected_players.items() if c == ctg)
        limit = CATEGORY_LIMITS.get("WK" if ctg == "WK" else ctg, 99)
        if ctg == "WK" and category_count >= 1:
            return False, "You can't select more than one wicket-keeper."
        if category_count >= limit:
            return False, f"You can't select more than {limit} players in this category."

        return True, ""

    def add_selected_player(self, item):
        player_name = item.text()
        row = fetch_player_value_and_ctg(player_name)
        if row is None:
            QMessageBox.critical(self, "Error", f"Player '{player_name}' not found in database.")
            return
        value, ctg = row

        is_valid, error_message = self.validate_selection(player_name, value, ctg)
        if not is_valid:
            QMessageBox.warning(self, "Selection not allowed", error_message)
            return

        self.selected_players[player_name] = (value, ctg)
        self.points_used += value
        self.points_available -= value
        self.listSelectedPlayers.addItem(QListWidgetItem(player_name))

        current_row = self.listAvailablePlayers.row(item)
        self.listAvailablePlayers.takeItem(current_row)

        self._refresh_summary_labels()
        self.statusbar.showMessage(f"Added {player_name} to your squad ({value} pts).", 4000)

    def remove_selected_player(self, item):
        player_name = item.text()
        if player_name not in self.selected_players:
            return
        value, ctg = self.selected_players.pop(player_name)
        self.points_used -= value
        self.points_available += value

        current_row = self.listSelectedPlayers.row(item)
        self.listSelectedPlayers.takeItem(current_row)

        if CATEGORY_TO_DB_CTG[self._current_category_label()] == ctg:
            self.listAvailablePlayers.addItem(QListWidgetItem(player_name))

        self._refresh_summary_labels()
        self.statusbar.showMessage(f"Removed {player_name} from your squad.", 4000)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
