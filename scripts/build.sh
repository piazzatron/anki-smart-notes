#!/bin/bash

build () {
  echo "Building..."
  rm -rf dist
  mkdir -p dist/vendor

  cp *.py dist/
  cp manifest.json dist/
  cp config.json dist/
  cp -r src dist/
  cp license dist/
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

dev () {
  ln -s $(pwd) ~/Library/Application\ Support/Anki2/addons21/smart-notes
}

if [ "$1" == "build" ]; then
  build
elif [ "$1" == "clean" ]; then
  clean
elif [ "$1" == "dev" ]; then
  dev
else
  echo "Invalid argument: $1"
fi

echo "Done"
