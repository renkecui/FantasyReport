from datetime import datetime

from openpyxl import Workbook

from .season_totals_sheet import SeasonTotalsSheet
from .team_roster_sheet import TeamRosterSheet
from .theme import Theme
from .weekly_stats_sheet import WeeklyStatsSheet


class WorkbookBuilder:
    """Builds the whole workbook: Season Totals, Weekly Stats, then one roster tab per team
    (my team first)."""

    def __init__(self, data, now=None):
        self.data = data
        self.stamp = (now or datetime.now()).strftime("%b %d, %Y %I:%M %p")
        self.colors = {t: Theme.PALETTE[i % len(Theme.PALETTE)] for i, t in enumerate(data.teams_mine_first())}

    def build(self):
        wb = Workbook()
        default = wb.active  # a new Workbook starts with one empty sheet
        if default is not None:
            wb.remove(default)
        args = (wb, self.data, self.stamp, self.colors)
        weekly = WeeklyStatsSheet(*args)
        sheets = [SeasonTotalsSheet(*args, weekly=weekly, index=0), weekly]
        used = {SeasonTotalsSheet.TITLE.lower(), WeeklyStatsSheet.TITLE.lower()}
        for team in self.data.teams_mine_first():
            sheets.append(TeamRosterSheet(*args, team=team, title=TeamRosterSheet.tab_title(team, used)))
        for sheet in sheets:
            sheet.write()
            sheet.page_setup()
        wb.active = 0
        return wb

    def save(self, path):
        self.build().save(path)
