
import logging
import os
import re
import sqlite3
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# Telegram Movie Search Bot
# For content you own or are authorized to distribute.
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # e.g. -1001234567890
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
DATABASE = os.getenv("DATABASE", "movies.db")
RESULTS_PER_PAGE = 8

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                title TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_normalized_title
            ON movies(normalized_title)
        """)
        conn.commit()


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\.(mkv|mp4|avi|mov|webm)$", "", text, flags=re.I)
    text = re.sub(r"[\[\]()._\-]+", " ", text)
    text = re.sub(r"\b(480p|720p|1080p|2160p|4k|8k|web[- ]?dl|bluray|blu[- ]?ray|x264|x265|hevc)\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(
        r"[\[\]()]?\b(480p|720p|1080p|2160p|4k|8k|web[- ]?dl|bluray|blu[- ]?ray|x264|x265|hevc)\b[\[\]()]?",
        "",
        name,
        flags=re.I,
    )
    name = re.sub(r"[._]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -_")
    return name


def save_movie(message_id: int, file_id: str, title: str, file_name: str = ""):
    with db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO movies
            (message_id, file_id, title, normalized_title, file_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            message_id,
            file_id,
            title,
            normalize(title),
            file_name,
        ))
        conn.commit()


def search_movies(query: str, limit: int = 50):
    q = normalize(query)
    if not q:
        return []

    words = q.split()
    with db() as conn:
        # First: exact/substring matches.
        rows = conn.execute("""
            SELECT * FROM movies
            WHERE normalized_title LIKE ?
            ORDER BY title COLLATE NOCASE
            LIMIT ?
        """, (f"%{q}%", limit)).fetchall()

        if rows:
            return rows

        # Second: all search words must occur somewhere in the title.
        clauses = " AND ".join(["normalized_title LIKE ?"] * len(words))
        params = [f"%{word}%" for word in words] + [limit]
        rows = conn.execute(
            f"""
            SELECT * FROM movies
            WHERE {clauses}
            ORDER BY title COLLATE NOCASE
            LIMIT ?
            """,
            params,
        ).fetchall()

    return rows


def count_movies():
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]


def get_movie(movie_id: int):
    with db() as conn:
        return conn.execute(
            "SELECT * FROM movies WHERE id = ?", (movie_id,)
        ).fetchone()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to the Movie Search Bot!\n\n"
        "Send me the title of a movie and I'll search the indexed channel content.\n\n"
        "Example:\n"
        "Avatar\n"
        "The Batman\n"
        "Avengers Endgame\n\n"
        "Use /help for more commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Movie Search Bot\n\n"
        "Simply send a movie title to search.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - Show the number of indexed movies\n\n"
        "Admins:\n"
        "/reindex - Rebuild the index from channel history\n\n"
        "The bot only distributes content that you are authorized to distribute."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎬 Indexed movies: {count_movies()}"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    rows = search_movies(query)

    if not rows:
        await update.message.reply_text(
            f"❌ No movie found for: {query}\n\n"
            "Try another spelling or a shorter title."
        )
        return

    buttons = []
    for row in rows[:RESULTS_PER_PAGE]:
        buttons.append([
            InlineKeyboardButton(
                f"🎬 {row['title'][:55]}",
                callback_data=f"movie:{row['id']}"
            )
        ])

    await update.message.reply_text(
        f"🔎 Results for: {query}\n\n"
        f"Found {len(rows)} matching result(s).",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def movie_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        movie_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Invalid movie selection.")
        return

    movie = get_movie(movie_id)
    if not movie:
        await query.message.reply_text("❌ Movie is no longer indexed.")
        return

    await query.message.reply_text(
        f"🎬 {movie['title']}\n\n"
        "📤 Sending your file..."
    )

    try:
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=movie["file_id"],
            caption=f"🎬 {movie['title']}",
        )
    except Exception as exc:
        logger.exception("Could not send file: %s", exc)
        await query.message.reply_text(
            "❌ I couldn't send the file here. "
            "Please start a private chat with the bot first using /start."
        )


async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically index new authorized channel media."""
    message = update.channel_post

    if not message or not message.document:
        return

    if CHANNEL_ID and str(message.chat_id) != str(CHANNEL_ID):
        return

    document = message.document
    filename = document.file_name or "Untitled Movie"
    title = clean_title(filename)

    save_movie(
        message_id=message.message_id,
        file_id=document.file_id,
        title=title,
        file_name=filename,
    )

    logger.info("Indexed: %s", title)


async def reindex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Telegram's Bot API does not provide a general "download all old
    # channel history" method. This command explains the limitation.
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only.")
        return

    await update.message.reply_text(
        "ℹ️ Automatic indexing works for new channel posts received "
        "after the bot is added as an administrator.\n\n"
        "Telegram's Bot API does not provide a general method for a bot "
        "to fetch the entire historical channel archive. For older posts, "
        "you can import their file IDs/message IDs into the database."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set.")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reindex", reindex))
    app.add_handler(CallbackQueryHandler(movie_callback, pattern=r"^movie:\d+$"))

    # New channel posts.
    app.add_handler(
        MessageHandler(
            filters.ChatType.CHANNEL & filters.Document.ALL,
            channel_post,
        )
    )

    # User text searches.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            search,
        )
    )

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
