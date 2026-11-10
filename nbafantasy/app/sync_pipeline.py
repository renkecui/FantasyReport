import os
from typing import List

from .run_options import RunOptions
from ..common.logger import Logger
from ..common.retry_policy import RetryPolicy
from ..common.sync_error import SyncError
from ..config.config import Config
from ..config.paths import Paths
from ..espn.espn_client import EspnClient
from ..espn.league_validator import LeagueValidator
from ..google_sheets.google_auth import GoogleAuth
from ..google_sheets.google_sheet_publisher import GoogleSheetPublisher
from ..models.league_data import LeagueData
from ..website.league_json import LeagueJson
from ..website.site_builder import SiteBuilder
from ..website.site_publisher import SitePublisher
from ..workbook.workbook_builder import WorkbookBuilder


class SyncPipeline:
    """One run: ESPN -> validate -> local .xlsx -> Google Sheet, and the website.
    Google and the website are published independently: one failing doesn't stop the other."""

    def __init__(self, paths: Paths, options: RunOptions):
        self.paths = paths
        self.options = options
        self.log = Logger()
        self.retry = RetryPolicy()
        self.auth = GoogleAuth(paths)

    def run(self):
        config = Config.load(self.paths.config)
        if self.options.login and not self.options.site_only:
            self.auth.credentials(interactive=True)
            self.log.info("Google login saved.")

        data = self.fetch(config)
        report = [f"ESPN data OK: {len(data.weeks)} weeks, {len(data.rosters)} rosters."]
        failures: List[str] = []

        if self.options.build_workbook:
            self.build_workbook(data)
        site = self.build_site(config, data)
        report.append(f"Site built in {os.path.relpath(site, self.paths.root)}/.")

        if self.options.publish_sheet:
            self._attempt(failures, report, lambda: self.publish_sheet(config))
        if self.options.publish_site(config):
            self._attempt(failures, report, lambda: self.publish_site(site))

        self.log.info(" ".join(report))
        if failures:
            raise SyncError("; ".join(failures))

    # ---------------------------------------------------------------- steps
    def fetch(self, config: Config) -> LeagueData:
        data = EspnClient(config, self.retry).fetch()
        LeagueValidator(config).validate(data)
        return data

    def build_workbook(self, data: LeagueData):
        local = self.paths.local_xlsx
        tmp = local + ".tmp.xlsx"
        WorkbookBuilder(data).save(tmp)
        os.replace(tmp, local)  # local copy, always kept up to date

    def build_site(self, config: Config, data: LeagueData):
        league = LeagueJson(data, config.sheet_title, data.season_year)
        return SiteBuilder(self.paths.web, self.paths.site).build(league)

    def publish_sheet(self, config: Config):
        publisher = GoogleSheetPublisher(self.paths, self.auth, self.retry)
        result = publisher.publish(self.paths.local_xlsx, config.sheet_title, interactive=self.options.login)
        for warning in result.warnings:
            self.log.warning(warning)
        return f"{'Created' if result.created else 'Updated'} Google Sheet: {result.url}"

    def publish_site(self, site_dir):
        res = SitePublisher(self.paths.root, self.paths.site_deploy).publish(site_dir)
        return f"Website {'updated' if res.changed else 'unchanged'}: {res.url or 'pushed to main'}"

    @staticmethod
    def _attempt(failures: List[str], report: List[str], step):
        """Run one publish step; record its message, or its error without stopping the run."""
        try:
            report.append(step())
        except SyncError as e:
            failures.append(str(e))
        except Exception as e:
            failures.append(f"Unexpected error while publishing: {e}")
