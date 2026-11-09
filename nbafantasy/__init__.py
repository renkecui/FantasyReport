"""NBAFantasy26: pull ESPN fantasy basketball league data and publish it to a Google Sheet.

Module map (each step of a run lives in its own class):

  config.py       Paths, Config            where files live (app output in data/); config.json
  errors.py       SyncError                a known problem: stop without touching the sheet
  models.py       LeagueData & friends     plain data passed between the steps
  espn_client.py  EspnClient               ESPN -> LeagueData (matchups + every team's roster)
  validation.py   LeagueValidator          refuses data that looks incomplete
  workbook.py     WorkbookBuilder          LeagueData -> styled .xlsx (totals, weekly, a roster tab per team)
  google_sync.py  GoogleSheetPublisher     .xlsx -> the shared Google Sheet, with backups
  lock.py         RunLock                  stops two runs overlapping
  util.py         log, RetryPolicy, MacNotifier, file helpers
  app.py          SyncApp, main()          wires the steps together
"""
