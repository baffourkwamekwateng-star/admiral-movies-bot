# Telegram Movie Search Bot

A Telegram bot that indexes authorized movie/document files posted to a Telegram
channel and lets users search for them by title.

> Use this bot only for movies/files you own or are authorized to distribute.

## Features

- Automatically indexes new document/movie posts in your channel.
- Users can search by movie title.
- Supports simple fuzzy-style matching by title words.
- Inline buttons for search results.
- Sends the indexed Telegram file to the user.
- SQLite database.
- `/start`, `/help`, `/stats`.
- Admin-only `/reindex` explanation.

## 1. Create the bot

Open Telegram and talk to **@BotFather**.

Use:

```text
/newbot
```

Follow the instructions and copy the bot token.

## 2. Get your channel ID

Add the bot to your channel as an administrator.

The channel ID normally looks like:

```text
-1001234567890
```

You can use a Telegram ID tool/bot to determine it, or inspect updates while
testing.

## 3. Install Python

Python 3.10+ is recommended.

Then install dependencies:

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy `.env.example` and set:

```text
BOT_TOKEN=your_bot_token
CHANNEL_ID=-1001234567890
ADMIN_IDS=your_telegram_user_id
```

Do NOT publish your bot token.

### Windows PowerShell

```powershell
$env:BOT_TOKEN="YOUR_TOKEN"
$env:CHANNEL_ID="-1001234567890"
$env:ADMIN_IDS="123456789"
python bot.py
```

### Linux/macOS

```bash
export BOT_TOKEN="YOUR_TOKEN"
export CHANNEL_ID="-1001234567890"
export ADMIN_IDS="123456789"
python bot.py
```

## 5. Add the bot to your channel

Add the bot as an administrator.

It needs to receive channel posts. Keep the permissions as limited as
practical for your use case.

## 6. Test it

Start the bot:

```bash
python bot.py
```

Then:

1. Open the bot privately.
2. Send `/start`.
3. Post an authorized movie/document to your channel.
4. Send the movie title to the bot.
5. Select the result.
6. The bot sends the file.

## Important Telegram limitation

The Telegram Bot API does not provide a general method for a bot to fetch the
entire historical message archive of a channel.

Therefore this version automatically indexes **new channel posts after the
bot is installed and receiving updates**.

If your channel already contains hundreds/thousands of files, use an authorized
export/import process to populate the SQLite database, or provide the data
through a separate import script.

## Database

The SQLite database contains:

- Telegram message ID
- Telegram file ID
- Movie title
- Normalized title
- Original filename
- Creation timestamp

The bot sends the Telegram `file_id`, so it does not need to download and
re-upload every movie.

## Security

Keep these secret:

- Bot token
- Database if it contains sensitive metadata
- Any admin credentials

Never commit secrets to GitHub.

## Running 24/7

You can run this on:

- A VPS
- Railway
- Render
- PythonAnywhere
- Another Python-compatible server

For production, consider PostgreSQL instead of SQLite if you expect heavy
usage.

## Copyright / authorization

This project is intended for content you own or have permission to distribute.
Do not use it to facilitate unauthorized distribution of copyrighted movies.
