#!/bin/bash
set -e

# Copyright (C) 2024 Michael Piazza
#
# This file is part of Smart Notes.
#
# Smart Notes is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Smart Notes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.



build () {
  echo "Building..."
  rm -rf dist
  mkdir -p dist/vendor

  cp *.py dist/
  cp manifest.json dist/
  cp config.json dist/
  cp -r src dist/
  cp license dist/
  cp changelog.md dist/
  echo "environment = \"PROD\"" > dist/src/env.py

  # Nuke any pycache
  rm -rf dist/__pycache__

  # Copy deps
  vendored=(
    "aiohttp"
    "aiosignal"
    "async_timeout"
    "frozenlist"
    "attrs"
    "multidict"
    "yarl"
    "idna"
    "sentry_sdk"
    "certifi"
    "urllib3"
    "dotenv"
    "dacite"
  )

  # copy them in a loop
  for dep in "${vendored[@]}"; do
    cp -r ".venv/lib/python3.11/site-packages/$dep" dist/vendor/
  done

  # Voices
  cp -r eleven_voices.json dist/
  cp -r google_voices.json dist/
  cp -r azure_voices.json dist/
  cp -r voicevox_voices.json dist/

  # Zip it
  cd dist
  zip -9 -r smart-notes.ankiaddon .
  cd ..
}

clean-links () {
  echo "Cleaning links..."
  rm -rf dist
  rm -rf ~/Library/Application\ Support/Anki2/addons21/smart-notes
  rm -rf ~/development/anki-storage/addons21/smart-notes
  rm -rf ~/development/win_shared/smart-notes
}

clean () {
  clean-links
  rm -rf meta.json
}

link-dev () {
  mkdir -p ~/development/anki-storage/addons21
  # Link for Mac Local Dev
  ln -s "$(pwd)" ~/Library/Application\ Support/Anki2/addons21/smart-notes
  ln -s "$(pwd)" ~/development/anki-storage/addons21/smart-notes
}

win-dist () {
  clean
  build
  rm -rf ~/development/win_shared/smart-notes
  mkdir -p ~/development/win_shared/smart-notes
  # Link for Windows dev thru shared folder
  cp -r "$(pwd)/dist/"* ~/development/win_shared/smart-notes
}

# Symlink the built dist/ into both the main Anki profile and the sandbox
# profile addon folders, so either profile can run the zipped prod build.
link-dist () {
  mkdir -p ~/development/anki-storage/addons21
  ln -s "$(pwd)/dist" ~/Library/Application\ Support/Anki2/addons21/smart-notes
  ln -s "$(pwd)/dist" ~/development/anki-storage/addons21/smart-notes
}

# Helper: launch the user's main Anki install against the default profile dir.
launch-anki-main () {
   /Applications/Anki.app/Contents/MacOS/launcher
}

# Helper: launch Anki against the isolated sandbox profile at
# ~/development/anki-storage, injecting the auth token named by $1 from
# .env.local into meta.json once Anki creates it.
launch-anki-sandbox () {
  local TOKEN_VAR="${1:-LOCAL_AUTH_TOKEN}"
  local META_JSON=~/development/anki-storage/addons21/smart-notes/meta.json
  local ENV_LOCAL="$(cd "$(dirname "$0")/.." && pwd)/.env.local"

  # Launch Anki in background (stdout/stderr still print to terminal)
  /Applications/Anki.app/Contents/MacOS/launcher -b ~/development/anki-storage &
  local ANKI_PID=$!

  # Ensure Anki is killed on Ctrl+C
  trap "kill $ANKI_PID 2>/dev/null; exit" INT TERM

  # Wait for meta.json to appear (Anki creates it on load)
  echo "Waiting for Anki to create meta.json..."
  while [ ! -f "$META_JSON" ]; do
    sleep 1
  done

  # Inject auth token
  if [ -f "$ENV_LOCAL" ]; then
    local AUTH_TOKEN=$(grep "^${TOKEN_VAR}=" "$ENV_LOCAL" | cut -d= -f2-)
    if [ -n "$AUTH_TOKEN" ]; then
      jq --arg token "$AUTH_TOKEN" '.config.auth_token = $token' "$META_JSON" > /tmp/meta_tmp.json && \
        cat /tmp/meta_tmp.json > "$META_JSON"
      echo "Auth token injected into meta.json ($TOKEN_VAR)"
    else
      echo "Warning: $TOKEN_VAR not found in .env.local — skipping auth injection"
    fi
  fi

  # Block until Anki exits — Ctrl+C propagates naturally
  wait $ANKI_PID
}

# Main profile, live-linked dev source, local backend.
anki-local () {
  clean-links
  link-dev
  launch-anki-main
}

# Main profile, built prod zip, prod backend.
anki-prod () {
  clean
  build
  rm -rf dist/meta.json
  link-dist
  launch-anki-main
}

# Sandbox profile, live-linked dev source, local backend.
# Injects LOCAL_AUTH_TOKEN from .env.local.
sandbox-local () {
  clean-links
  link-dev
  launch-anki-sandbox LOCAL_AUTH_TOKEN
}

# Sandbox profile, built prod zip, prod backend.
# Injects PROD_AUTH_TOKEN from .env.local so the sandbox profile's auth
# doesn't get clobbered by a local token when flipping between backends.
sandbox-prod () {
  clean
  build
  rm -rf dist/meta.json
  link-dist
  launch-anki-sandbox PROD_AUTH_TOKEN
}

sentry-release () {
  # Write some jq
  version=$(jq '.human_version' manifest.json)
  echo $version
  # sentry-cli releases --org michael-piazza new --finalize ${version}
}

format () {
  echo "Formatting code..."
  python3 -m ruff format .
}

lint () {
  echo "Linting code..."
  python3 -m ruff check .
}

typecheck () {
  echo "Type checking..."
  python3 -m pyright .
}

check () {
  echo "Running all checks..."
  python3 -m ruff format . --check && python3 -m ruff check . && python3 -m pyright .
}

fix () {
  echo "Fixing code issues..."
  python3 -m ruff format . && python3 -m ruff check . --fix
}

version () {
  if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    exit 1
  fi

  VERSION=$1

  jq --arg version "$VERSION" '.human_version = $version' manifest.json > manifest.tmp && mv manifest.tmp manifest.json

  # Commit the changes
  git add manifest.json
  git add changelog.md
  git commit -m "v$VERSION"

  # Create a tag
  git tag "v$VERSION"

  # Push the commit and the tag
  git push
  git push origin "v$VERSION"
}


if [ "$1" == "build" ]; then
  clean
  build
elif [ "$1" == "clean" ]; then
  clean
elif [ "$1" == "win" ]; then
  win-dist
elif [ "$1" == "anki-local" ]; then
  anki-local
elif [ "$1" == "anki-prod" ]; then
  anki-prod
elif [ "$1" == "sandbox-local" ]; then
  sandbox-local
elif [ "$1" == "sandbox-prod" ]; then
  sandbox-prod
elif [ "$1" == "sentry-release" ]; then
  sentry-release
elif [ "$1" == "version" ]; then
  version $2
elif [ "$1" == "format" ]; then
  format
elif [ "$1" == "lint" ]; then
  lint
elif [ "$1" == "typecheck" ]; then
  typecheck
elif [ "$1" == "check" ]; then
  check
elif [ "$1" == "fix" ]; then
  fix
else
  echo "Invalid argument: $1"
  echo "Available commands: build, clean, win, anki-local, anki-prod, sandbox-local, sandbox-prod, sentry-release, version, format, lint, typecheck, check, fix"
  exit 1
fi

# Check if the last command succeeded
if [ $? -eq 0 ]; then
  echo "Done"
fi
