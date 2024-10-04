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
  vendored=(
    "aiohttp"
    "aiosignal"
    "aiofiles"
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
  )

  # copy them in a loop
  for dep in "${vendored[@]}"; do
    cp -r "env/lib/python3.11/site-packages/$dep" dist/vendor/
  done

  # Voices
  cp -r eleven_voices.json dist/
  cp -r google_voices.json dist/

  # Zip it
  cd dist
  zip -9 -r smart-notes.ankiaddon .
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
  rm -rf dist/meta.json
  link-dist
  # cp meta.json dist/
  # copy the current meta to make testing easier
  # jq '.config.auth_token = null' dist/meta.json > dist/temp.json && mv dist/temp.json dist/meta.json
  anki
}

sentry-release () {
  # Write some jq
  version=$(jq '.human_version' manifest.json)
  echo $version
  # sentry-cli releases --org michael-piazza new --finalize ${version}
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
elif [ "$1" == "test-dev" ]; then
  test-dev
elif [ "$1" == "test-build" ]; then
  test-build
elif [ "$1" == "sentry-release" ]; then
  sentry-release
elif [ "$1" == "version" ]; then
  version $2
else

  echo "Invalid argument: $1"
fi

echo "Done"
