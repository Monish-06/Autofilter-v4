#!/bin/bash
set -e

if [ -z "$UPSTREAM_REPO" ]; then
  echo "Cloning main Repository"
  git clone https://github.com/GreyMatterbots/url-auto-delete-shortener-bot temp_repo
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO"
  git clone "$UPSTREAM_REPO" temp_repo
fi

cd temp_repo
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 bot.py
