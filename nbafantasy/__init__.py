"""Fantasy Report: pull ESPN fantasy basketball league data and publish it to a Google Sheet and a website.

One class per file; each subpackage groups one part of a run:

  app/            Application (the process), SyncPipeline (the steps of a run), RunOptions (CLI flags)
  common/         Singleton, SyncError, Logger, Files, RetryPolicy, MacNotifier, RunLock
  config/         Paths (where files live), Config (config.json)
  models/         Categories and the plain data passed between steps (LeagueData, Week, ...)
  espn/           EspnClient (ESPN -> LeagueData), LeagueValidator (refuses incomplete data)
  stats/          Ranking, LeagueStats, WeeklyRow, SeasonRow: ranks and totals in Python
  workbook/       WorkbookBuilder and one SheetWriter subclass per tab -> styled .xlsx
  google_sheets/  GoogleSheetPublisher, GoogleAuth, SyncState, ... -> the shared Google Sheet
  website/        LeagueJson, SiteBuilder, SitePublisher -> league.json, data/site/, GitHub Pages

Each file is named after the class it holds, e.g. stats/league_stats.py -> LeagueStats.
"""
