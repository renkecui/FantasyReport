#!/bin/bash
# Preview the website on this Mac, with login: ./scripts/preview.sh
#
# Starts the site (web/, at http://localhost:8765) and a local copy of the login server
# (worker/, at http://localhost:8787), then opens the site in your browser. Edit anything in web/
# and reload the page to see it; Ctrl+C stops both servers.
#
# Log in with your team name and the password in worker/.dev.vars (created the first time with
# the password "local"). Local logins and theme picks never touch the live league.
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"   # project folder (this script lives in scripts/)
cd "$DIR"

SITE_PORT=8765   # must match ALLOWED_ORIGINS and LEAGUE_JSON_URL in worker/.dev.vars
API_PORT=8787    # the site uses this port on localhost (web/js/state/api-client.js)
SITE_URL="http://localhost:$SITE_PORT"
LOG_DIR="$DIR/data/preview"

command -v python3 >/dev/null || { echo "python3 not found. Install Python 3 first."; exit 1; }
command -v npm >/dev/null || { echo "npm not found. Install Node.js first (https://nodejs.org)."; exit 1; }

for port in $SITE_PORT $API_PORT; do
  if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is already in use, probably by an earlier preview. Stop it first:"
    echo "  kill \$(lsof -tiTCP:$port -sTCP:LISTEN)"
    exit 1
  fi
done

if [ ! -d worker/node_modules ]; then
  echo "Installing the login server's packages (first time only)..."
  npm --prefix worker ci --silent
fi

if [ ! -f worker/.dev.vars ]; then
  (umask 077 && cat > worker/.dev.vars <<EOF
# Local only (git-ignored). Log in on $SITE_URL with your team name and this password.
LEAGUE_PASSWORD=local
TOKEN_SECRET=$(openssl rand -hex 32)
LEAGUE_JSON_URL=$SITE_URL/league.json
ALLOWED_ORIGINS=$SITE_URL,http://127.0.0.1:$SITE_PORT
EOF
  )
  echo "Created worker/.dev.vars (local password: local)."
fi

mkdir -p "$LOG_DIR"
PIDS=()
stop() {
  trap - INT TERM EXIT
  echo
  echo "Stopping the preview..."
  kill "${PIDS[@]}" 2>/dev/null || true
  # npm starts wrangler, which starts workerd: stop whatever still holds the ports too.
  for port in $SITE_PORT $API_PORT; do
    kill $(lsof -tiTCP:$port -sTCP:LISTEN 2>/dev/null) 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap stop INT TERM EXIT

# A plain file server for web/ that tells the browser not to cache, so a reload always shows your edits.
python3 -c '
import functools, http.server, sys
class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
handler = functools.partial(NoCache, directory=sys.argv[2])
http.server.ThreadingHTTPServer(("localhost", int(sys.argv[1])), handler).serve_forever()
' $SITE_PORT web >"$LOG_DIR/site.log" 2>&1 &
PIDS+=($!)
npm --prefix worker run dev >"$LOG_DIR/login-server.log" 2>&1 &
PIDS+=($!)

# Wait until both answer (the login server takes a few seconds to start).
for _ in $(seq 1 60); do
  if curl -s -o /dev/null "$SITE_URL/" && curl -s -o /dev/null "http://localhost:$API_PORT/themes"; then
    READY=1
    break
  fi
  sleep 0.5
done
if [ -z "$READY" ]; then
  echo "The preview didn't start. See the logs in data/preview/."
  exit 1
fi

PASSWORD="$(grep '^LEAGUE_PASSWORD=' worker/.dev.vars | cut -d= -f2-)"
echo
echo "  Preview running at $SITE_URL"
echo "  Log in with your team name and the password: $PASSWORD"
echo "  Edit files in web/ and reload the page to see changes."
echo "  Press Ctrl+C to stop."
echo
open "$SITE_URL" 2>/dev/null || true
wait
