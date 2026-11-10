# Preview the website locally

Try website changes on your Mac before you push them.

## Start

From the project folder:

```bash
./scripts/preview.sh
```

The site opens at http://localhost:8765. Log in with your **team name** and the password
**`local`** (from `worker/.dev.vars`).

## Make changes

1. Edit files in `web/` (HTML, CSS, JavaScript). There's no build step.
2. Reload the page to see them.
3. Press **Ctrl+C** in the terminal to stop.

- The site shows the data in `web/league.json`. Run `git pull` first for today's numbers.
- Local logins and theme picks never touch the live league.

## Before you push

```bash
python3 -m unittest discover -s tests -t .
npm --prefix worker test
```

Pushing to `main` publishes the site, so work on a branch until you're happy with it.

## If something goes wrong

| Problem | Fix |
|---|---|
| "Couldn't reach the server" when logging in | Your browser has old files cached. Use a private (incognito) window, or hard reload once (Chrome: Cmd+Shift+R, Safari: Option+Cmd+R). |
| "Port … is already in use" | An earlier preview is still running. Run the `kill` command the script prints. |
| The preview doesn't start | Check the logs in `data/preview/`. |

## How it works

- `web/` is served at `localhost:8765`, with caching turned off.
- A local copy of the login server (`worker/`) runs at `localhost:8787`. On localhost the site uses it
  instead of the live one.
- The first run installs the login server's packages and creates `worker/.dev.vars`.
