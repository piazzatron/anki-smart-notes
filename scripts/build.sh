#!/bin/bash

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
  cp .env dist/
  cp manifest.json dist/
  cp config.json dist/
  cp -r src dist/
  cp license dist/
  cp changelog.md dist/
  echo "environment = \"PROD\"" > dist/env.py

  # Nuke any pycache
  rm -rf dist/__pycache__

  # Copy deps
  cp -r env/lib/python3.11/site-packages/aiohttp dist/vendor/
  cp -r env/lib/python3.11/site-packages/aiosignal dist/vendor/
  cp -r env/lib/python3.11/site-packages/async_timeout dist/vendor/
  cp -r env/lib/python3.11/site-packages/frozenlist dist/vendor/
  cp -r env/lib/python3.11/site-packages/attrs dist/vendor/
  cp -r env/lib/python3.11/site-packages/multidict dist/vendor/
  cp -r env/lib/python3.11/site-packages/yarl dist/vendor/
  cp -r env/lib/python3.11/site-packages/idna dist/vendor/
  ## Sentry
  cp -r env/lib/python3.11/site-packages/sentry_sdk dist/vendor/
  cp -r env/lib/python3.11/site-packages/certifi dist/vendor/
  cp -r env/lib/python3.11/site-packages/urllib3 dist/vendor/
  # Dotenv
  cp -r env/lib/python3.11/site-packages/dotenv dist/vendor/


  # Zip it
  cd dist
  zip -r smart-notes.ankiaddon *
  cd ..
}

clean () {
  echo "Cleaning..."
  rm -rf dist
  unlink ~/Library/Application\ Support/Anki2/addons21/smart-notes
}

link-dev () {
  ln -s $(pwd) ~/Library/Application\ Support/Anki2/addons21/smart-notes
}

# Tests a production build by symlinking dist folder
link-dist () {
  ln -s $(pwd)/dist ~/Library/Application\ Support/Anki2/addons21/smart-notes
}

anki () {
   /Applications/Anki.app/Contents/MacOS/anki
}

test-dev () {
  clean
  link-dev
  anki
}

test-build () {
  clean
  build
  link-dist
  anki
}

sentry-release () {
  # Write some jq
  version=$(jq '.human_version' manifest.json)
  echo $version
  # sentry-cli releases --org michael-piazza new --finalize ${version}
}

if [ "$1" == "build" ]; then
  build
elif [ "$1" == "clean" ]; then
  clean
elif [ "$1" == "test-dev" ]; then
  test-dev
elif [ "$1" == "test-build" ]; then
  test-build
elif [ "$1" == "sentry-release" ]; then
  sentry-release
else
  echo "Invalid argument: $1"
fi

echo "Done"
