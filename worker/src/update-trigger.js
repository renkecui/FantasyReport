/**
 * Starts the "Update league data" GitHub workflow at 7 AM and 3 PM New York time.
 *
 * GitHub's own schedule often starts runs hours late or skips them, while Cloudflare's cron
 * triggers run on time. The crons in wrangler.toml fire an hour apart around each update (cron is in
 * UTC, and New York is UTC-4 in summer and UTC-5 in winter); only the one in the right New York hour
 * starts the workflow. Needs the GITHUB_TOKEN secret (docs/SETUP.md step 6); without it, nothing happens.
 */
export class UpdateTrigger {
  static HOURS = [7, 15];          // New York time
  static WORKFLOW = "update.yml";
  static ZONE = "America/New_York";

  // The default calls the global fetch directly: on Cloudflare, calling it as a method of another
  // object (this.fetch(...)) throws "Illegal invocation".
  constructor(env, fetchFn = (url, init) => fetch(url, init)) {
    this.token = env.GITHUB_TOKEN || "";
    this.repo = env.GITHUB_REPO || "";
    this.fetchFn = fetchFn;
  }

  /** The hour (0-23) in New York at `date`. */
  static nyHour(date) {
    return Number(new Intl.DateTimeFormat("en-US", { timeZone: UpdateTrigger.ZONE, hour: "numeric", hourCycle: "h23" })
      .format(date));
  }

  static isDue(date) { return UpdateTrigger.HOURS.includes(UpdateTrigger.nyHour(date)); }

  /** "started", "not due" or "no token"; throws if GitHub refuses (the Worker's logs show it). */
  async run(date = new Date()) {
    if (!UpdateTrigger.isDue(date)) return "not due";
    if (!this.token || !this.repo) {
      console.warn("GITHUB_TOKEN or GITHUB_REPO isn't set, so the league update wasn't started (docs/SETUP.md step 6).");
      return "no token";
    }
    const url = `https://api.github.com/repos/${this.repo}/actions/workflows/${UpdateTrigger.WORKFLOW}/dispatches`;
    const fetchFn = this.fetchFn;
    const res = await fetchFn(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "nbafantasy-api",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    });
    if (res.status !== 204) {
      throw new Error(`GitHub refused to start the league update (HTTP ${res.status}): ${await res.text()}`);
    }
    return "started";
  }
}
