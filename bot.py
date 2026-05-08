"""
Ø¨Ø§Øª Ø­Ø¶ÙˆØ± Ùˆ ØºÛŒØ§Ø¨ ØªÙ„Ú¯Ø±Ø§Ù… + Ú†Øª Ø¨Ø§ Ù‡ÙˆØ´ Ù…ØµÙ†ÙˆØ¹ÛŒ
- Ù‡Ø± Ú©Ø³ÛŒ ØªÙˆÛŒ Ú¯Ø±ÙˆÙ‡ Ø§ÛŒÙ…ÙˆØ¬ÛŒ âœ‹ Ø¨ÙØ±Ø³ØªÙ‡ØŒ Ø­Ø¶ÙˆØ± Ø§ÙˆÙ† Ø±ÙˆØ²Ø´ Ø«Ø¨Øª Ù…ÛŒØ´Ù‡.
- Ù‡Ø± Ø¬Ù…Ø¹Ù‡ Ø´Ø¨ Ø³Ø§Ø¹Øª Û²Û± Ø¨Ù‡ ÙˆÙ‚Øª ØªÙ‡Ø±Ø§Ù†ØŒ Ú¯Ø²Ø§Ø±Ø´ Ù‡ÙØªÚ¯ÛŒ ØªÙˆÛŒ Ú¯Ø±ÙˆÙ‡ ÙØ±Ø³ØªØ§Ø¯Ù‡ Ù…ÛŒØ´Ù‡.
- Ø§Ú¯Ù‡ Ú©Ø³ÛŒ Ø±ÙˆÛŒ Ù¾ÛŒØ§Ù… Ø¨Ø§Øª Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ú©Ù†Ù‡ØŒ @ Ù…Ù†Ø´Ù† Ú©Ù†Ù‡ØŒ ÛŒØ§ /ask Ø¨Ø²Ù†Ù‡ØŒ Ø¨Ø§Øª Ø¨Ø§ AI Ø¬ÙˆØ§Ø¨ Ù…ÛŒØ¯Ù‡.
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------- ØªÙ†Ø¸ÛŒÙ…Ø§Øª ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DB_PATH = os.environ.get("DB_PATH", "attendance.db")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
TZ = ZoneInfo("Asia/Tehran")

# Ø§ÛŒÙ…ÙˆØ¬ÛŒâ€ŒÙ‡Ø§ÛŒÛŒ Ú©Ù‡ Ø¨Ù‡ Ø¹Ù†ÙˆØ§Ù† "Ø­Ø¶ÙˆØ±" Ù‚Ø¨ÙˆÙ„ Ù…ÛŒØ´Ù†
PRESENT_EMOJIS = {"âœ‹", "âœ…", "ðŸ‘‹", "ðŸ™‹", "ðŸ™‹â€â™‚ï¸", "ðŸ™‹â€â™€ï¸", "ðŸ«¡", "ðŸŒž", "â˜€ï¸"}

# Ø´Ø®ØµÛŒØª Ø¨Ø§Øª Ø¨Ø±Ø§ÛŒ Ú†Øª AI
SYSTEM_PROMPT = """ØªÙˆ ÛŒÙ‡ Ø¨Ø§Øª ØªÙ„Ú¯Ø±Ø§Ù…ÛŒ Ø¨Ù‡ Ø§Ø³Ù… Â«Ø­Ø¶ÙˆØ± Ùˆ ØºÛŒØ§Ø¨Â» Ù‡Ø³ØªÛŒ Ú©Ù‡ ØªÙˆÛŒ ÛŒÙ‡ Ú¯Ø±ÙˆÙ‡ Ø¯ÙˆØ³ØªÛŒ ÙØ¹Ø§Ù„ÛŒØª Ù…ÛŒÚ©Ù†ÛŒ.
Ø´Ø®ØµÛŒØªØª Ø¯ÙˆØ³ØªØ§Ù†Ù‡ØŒ ØµÙ…ÛŒÙ…ÛŒ Ùˆ Ø´ÙˆØ®Ù‡. Ù…Ø«Ù„ ÛŒÙ‡ Ø±ÙÛŒÙ‚ Ø¨Ø§ Ù‡Ù…Ù‡ Ø­Ø±Ù Ù…ÛŒØ²Ù†ÛŒ.
- Ù‡Ù…ÛŒØ´Ù‡ Ø¨Ù‡ ÙØ§Ø±Ø³ÛŒ Ø®ÙˆØ¯Ù…ÙˆÙ†ÛŒ Ø¬ÙˆØ§Ø¨ Ø¨Ø¯Ù‡ØŒ Ù†Ù‡ Ø±Ø³Ù…ÛŒ.
- Ø´ÙˆØ®ÛŒ Ú©Ù†ØŒ ØªÚ©Ù‡ Ø¨Ù†Ø¯Ø§Ø²ØŒ Ø¨Ø§ Ø­Ø§Ù„ Ø¨Ø§Ø´.
- Ù¾Ø§Ø³Ø®â€ŒÙ‡Ø§Øª Ú©ÙˆØªØ§Ù‡ Ø¨Ø§Ø´Ù‡ (Ù…Ø¹Ù…ÙˆÙ„Ø§Ù‹ Û±-Û³ Ø¬Ù…Ù„Ù‡)ØŒ Ù…Ú¯Ù‡ Ø§ÛŒÙ†Ú©Ù‡ Ø³ÙˆØ§Ù„ Ø·ÙˆÙ„Ø§Ù†ÛŒ Ø¨Ø§Ø´Ù‡.
- Ø§Ú¯Ù‡ Ú©Ø³ÛŒ Ù¾Ø±Ø³ÛŒØ¯ Ú©ÛŒ Ù‡Ø³ØªÛŒØŒ Ø¨Ú¯Ùˆ Ù…Ù† Ø¨Ø§Øª Ú¯Ø±ÙˆÙ‡Ù…Ù…ØŒ Ø­Ø¶ÙˆØ± Ùˆ ØºÛŒØ§Ø¨Ùˆ Ø«Ø¨Øª Ù…ÛŒÚ©Ù†Ù… Ùˆ Ø¨Ø§Ù‡Ø§ØªÙˆÙ† Ú†Øª Ù…ÛŒÚ©Ù†Ù….
- Ø§Ú¯Ù‡ ÙØ­Ø´ Ø¯Ø§Ø¯Ù† ÛŒØ§ Ø´ÙˆØ®ÛŒ Ø³Ù†Ú¯ÛŒÙ† Ú©Ø±Ø¯Ù†ØŒ Ø¨Ø§ Ø´ÙˆØ®ÛŒ Ø¬ÙˆØ§Ø¨ Ø¨Ø¯Ù‡ ÙˆÙ„ÛŒ ÙØ­Ø´ Ù†Ø¯Ù‡.
- Ù…ÙˆØ¶ÙˆØ¹â€ŒÙ‡Ø§ÛŒ Ø­Ø³Ø§Ø³ (Ø³ÛŒØ§Ø³Øª ØªÙ†Ø¯ØŒ Ù…Ø³Ø§Ø¦Ù„ ØºÛŒØ±Ù‚Ø§Ù†ÙˆÙ†ÛŒ) Ø±Ùˆ Ø¨Ø§ Ø´ÙˆØ®ÛŒ Ø±Ø¯ Ú©Ù†.
"""

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# OpenAI client
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("âœ… OpenAI Ù…ØªØµÙ„ Ø´Ø¯.")
    except Exception as e:
        logger.error(f"âŒ Ø®Ø·Ø§ Ø¯Ø± Ø±Ø§Ù‡â€ŒØ§Ù†Ø¯Ø§Ø²ÛŒ OpenAI: {e}")
else:
    logger.warning("âš ï¸ OPENAI_API_KEY ØªÙ†Ø¸ÛŒÙ… Ù†Ø´Ø¯Ù‡ â€” Ù‚Ø§Ø¨Ù„ÛŒØª Ú†Øª AI ØºÛŒØ±ÙØ¹Ø§Ù„.")


# ---------- Ø¯ÛŒØªØ§Ø¨ÛŒØ³ ----------
def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(chat_id, user_id, date)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            first_seen TEXT NOT NULL,
            PRIMARY KEY (chat_id, user_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            registered_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def register_chat(chat_id: int, title: str | None):
    conn = db_connect()
    conn.execute(
        "INSERT OR IGNORE INTO chats(chat_id, title, registered_at) VALUES (?, ?, ?)",
        (chat_id, title or "", datetime.now(TZ).isoformat()),
    )
    conn.commit()
    conn.close()


def register_member(chat_id: int, user_id: int, user_name: str):
    conn = db_connect()
    conn.execute(
        """INSERT INTO members(chat_id, user_id, user_name, first_seen)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(chat_id, user_id) DO UPDATE SET user_name=excluded.user_name""",
        (chat_id, user_id, user_name, datetime.now(TZ).isoformat()),
    )
    conn.commit()
    conn.close()


def mark_present(chat_id: int, user_id: int, user_name: str) -> bool:
    """Ø«Ø¨Øª Ø­Ø¶ÙˆØ± Ø¨Ø±Ø§ÛŒ Ø§Ù…Ø±ÙˆØ². Ø§Ú¯Ù‡ Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø¨Ø§Ø´Ù‡ False Ø¨Ø±Ù…ÛŒÚ¯Ø±Ø¯ÙˆÙ†Ù‡."""
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    now = datetime.now(TZ).isoformat()
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO attendance(chat_id, user_id, user_name, date, timestamp) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, user_name, today, now),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ---------- AI ----------
async def ask_ai(user_name: str, user_message: str, replied_text: str | None = None) -> str:
    """Ø§Ø±Ø³Ø§Ù„ Ù¾ÛŒØ§Ù… Ø¨Ù‡ OpenAI Ùˆ Ø¯Ø±ÛŒØ§ÙØª Ø¬ÙˆØ§Ø¨."""
    if not openai_client:
        return "ðŸ¤– Ø§Ù„Ø§Ù† Ù‚Ø§Ø¨Ù„ÛŒØª Ú†Øª AI ÙØ¹Ø§Ù„ Ù†ÛŒØ³Øª. Ù…Ø¯ÛŒØ± Ú¯Ø±ÙˆÙ‡ Ø¨Ø§ÛŒØ¯ OPENAI_API_KEY Ø±Ùˆ ØªÙ†Ø¸ÛŒÙ… Ú©Ù†Ù‡."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if replied_text:
        messages.append({
            "role": "system",
            "content": f"Ú©Ø§Ø±Ø¨Ø± Ø¯Ø§Ø±Ù‡ Ø¨Ù‡ Ø§ÛŒÙ† Ù¾ÛŒØ§Ù… Ù‚Ø¨Ù„ÛŒ Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ù…ÛŒØ²Ù†Ù‡: Â«{replied_text}Â»",
        })

    messages.append({
        "role": "user",
        "content": f"({user_name} Ù…ÛŒÚ¯Ù‡): {user_message}",
    })

    try:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ø®Ø·Ø§ÛŒ OpenAI: {e}")
        return "ðŸ˜… ÛŒÙ‡ Ù…Ø´Ú©Ù„ÛŒ Ù¾ÛŒØ´ Ø§ÙˆÙ…Ø¯ØŒ Ø¨Ø¹Ø¯Ø§Ù‹ Ø§Ù…ØªØ­Ø§Ù† Ú©Ù†."


async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """Ø¬ÙˆØ§Ø¨ AI Ø±Ùˆ Ø¨Ù‡ Ù¾ÛŒØ§Ù… Ú©Ø§Ø±Ø¨Ø± Ø¨ÙØ±Ø³Øª."""
    user = update.effective_user
    user_name = user.full_name or user.username or "Ø±ÙÛŒÙ‚"

    replied_text = None
    if update.message.reply_to_message and update.message.reply_to_message.text:
        replied_text = update.message.reply_to_message.text

    # Ù†Ø´ÙˆÙ† Ø¨Ø¯Ù‡ Ø¯Ø§Ø±Ù‡ ØªØ§ÛŒÙ¾ Ù…ÛŒÚ©Ù†Ù‡
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
    except Exception:
        pass

    answer = await ask_ai(user_name, user_message, replied_text)
    await update.message.reply_text(answer)


# ---------- Ù‡Ù†Ø¯Ù„Ø±Ù‡Ø§ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    register_chat(chat.id, chat.title)
    msg = (
        "Ø³Ù„Ø§Ù… Ø¨Ú†Ù‡â€ŒÙ‡Ø§ ðŸ‘‹\n"
        "Ù…Ù† Ø¨Ø§Øª Ø­Ø¶ÙˆØ± Ùˆ ØºÛŒØ§Ø¨ Ú¯Ø±ÙˆÙ‡Ù….\n\n"
        f"Ù‡Ø± Ø±ÙˆØ² ÛŒÚ©ÛŒ Ø§Ø² Ø§ÛŒÙ† Ø§ÛŒÙ…ÙˆØ¬ÛŒâ€ŒÙ‡Ø§ Ø±Ùˆ Ø¨ÙØ±Ø³ØªÛŒÙ† ØªØ§ Ø­Ø¶ÙˆØ±ØªÙˆÙ† Ø«Ø¨Øª Ø¨Ø´Ù‡:\n"
        f"{' '.join(sorted(PRESENT_EMOJIS))}\n\n"
        "ðŸ’¬ Ø¨Ø±Ø§ÛŒ Ú†Øª Ø¨Ø§ Ù…Ù†ØŒ ÛŒØ§ Ø±ÙˆÛŒ Ù¾ÛŒØ§Ù…Ù… Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ø¨Ø²Ù†ØŒ ÛŒØ§ Ù…Ù†Ø´Ù† Ú©Ù†ØŒ ÛŒØ§ /ask Ø¨Ù†ÙˆÛŒØ³.\n\n"
        "Ú©Ø§Ù…Ù†Ø¯Ù‡Ø§:\n"
        "/today â€” Ù„ÛŒØ³Øª Ø­Ø§Ø¶Ø±ÛŒÙ† Ø§Ù…Ø±ÙˆØ²\n"
        "/week â€” Ú¯Ø²Ø§Ø±Ø´ Ø§ÛŒÙ† Ù‡ÙØªÙ‡\n"
        "/me â€” Ø¢Ù…Ø§Ø± Ø®ÙˆØ¯Øª\n"
        "/ask â€” Ú†Øª Ø¨Ø§ Ù‡ÙˆØ´ Ù…ØµÙ†ÙˆØ¹ÛŒ\n"
        "/help â€” Ø±Ø§Ù‡Ù†Ù…Ø§"
    )
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "ðŸ“– Ø±Ø§Ù‡Ù†Ù…Ø§ÛŒ Ø¨Ø§Øª\n\n"
        f"ðŸ“Œ Ø«Ø¨Øª Ø­Ø¶ÙˆØ±:\n{' '.join(sorted(PRESENT_EMOJIS))}\n"
        "(Ù‡Ø± Ø±ÙˆØ² ÛŒÙ‡ Ø¨Ø§Ø± Ø­Ø³Ø§Ø¨ Ù…ÛŒØ´Ù‡)\n\n"
        "ðŸ’¬ Ú†Øª Ø¨Ø§ Ù‡ÙˆØ´ Ù…ØµÙ†ÙˆØ¹ÛŒ:\n"
        "â€¢ /ask Ø³ÙˆØ§Ù„Øª â€” Ù…Ø³ØªÙ‚ÛŒÙ… Ø¨Ù¾Ø±Ø³\n"
        "â€¢ Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ø±ÙˆÛŒ Ù¾ÛŒØ§Ù… Ø¨Ø§Øª Ø¨Ø²Ù†\n"
        "â€¢ @Hoozoor_ghiab_bot Ø±Ùˆ Ù…Ù†Ø´Ù† Ú©Ù†\n\n"
        "ðŸ“Š Ú©Ø§Ù…Ù†Ø¯Ù‡Ø§:\n"
        "/today â€” Ø­Ø§Ø¶Ø±ÛŒÙ† Ø§Ù…Ø±ÙˆØ²\n"
        "/week â€” Ú¯Ø²Ø§Ø±Ø´ Ø§ÛŒÙ† Ù‡ÙØªÙ‡\n"
        "/me â€” Ø¢Ù…Ø§Ø± Ø­Ø¶ÙˆØ± Ø®ÙˆØ¯Øª\n"
        "/report â€” Ú¯Ø²Ø§Ø±Ø´ Ú©Ø§Ù…Ù„ Û· Ø±ÙˆØ² Ø§Ø®ÛŒØ±\n\n"
        "ðŸ¤– Ù‡Ø± Ø¬Ù…Ø¹Ù‡ Ø³Ø§Ø¹Øª Û²Û± Ø¨Ù‡ ÙˆÙ‚Øª ØªÙ‡Ø±Ø§Ù†ØŒ Ú¯Ø²Ø§Ø±Ø´ Ø®ÙˆØ¯Ú©Ø§Ø± Ù‡ÙØªÙ‡ Ù…ÛŒØ§Ø¯."
    )
    await update.message.reply_text(msg)


async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ú©Ø§Ù…Ù†Ø¯ /ask â€” Ú©Ø§Ø±Ø¨Ø± Ø³ÙˆØ§Ù„Ø´ Ø±Ùˆ Ø¨Ø¹Ø¯ Ø§Ø² /ask Ù…ÛŒÙ†ÙˆÛŒØ³Ù‡."""
    if not update.message:
        return

    # Ù…ØªÙ† Ø¨Ø¹Ø¯ Ø§Ø² /ask
    text = update.message.text or ""
    parts = text.split(maxsplit=1)
    question = parts[1].strip() if len(parts) > 1 else ""

    # Ø§Ú¯Ù‡ Ø±ÙˆÛŒ Ù¾ÛŒØ§Ù…ÛŒ Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ú©Ø±Ø¯Ù‡ ÙˆÙ„ÛŒ Ù…ØªÙ†ÛŒ Ù†Ù†ÙˆØ´ØªÙ‡ØŒ Ø§Ø² Ù¾ÛŒØ§Ù… Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ø§Ø³ØªÙØ§Ø¯Ù‡ Ú©Ù†
    if not question and update.message.reply_to_message and update.message.reply_to_message.text:
        question = update.message.reply_to_message.text

    if not question:
        await update.message.reply_text(
            "ðŸ’¬ Ø¨Ø¹Ø¯ Ø§Ø² /ask Ø³ÙˆØ§Ù„Øª Ø±Ùˆ Ø¨Ù†ÙˆÛŒØ³. Ù…Ø«Ù„Ø§Ù‹:\n/ask Ø§Ù…Ø±ÙˆØ² Ú†Ù‡ Ø®Ø¨Ø±ØŸ"
        )
        return

    await handle_ai_chat(update, context, question)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ù¾Ø±Ø¯Ø§Ø²Ø´ Ù¾ÛŒØ§Ù…â€ŒÙ‡Ø§ÛŒ Ù…ØªÙ†ÛŒ: Ø­Ø¶ÙˆØ±ØŒ Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ø¨Ù‡ Ø¨Ø§ØªØŒ ÛŒØ§ Ù…Ù†Ø´Ù†."""
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text

    # Ø«Ø¨Øª Ø§Ø¹Ø¶Ø§ÛŒ ÙØ¹Ø§Ù„
    user_name = user.full_name or user.username or f"user_{user.id}"
    register_member(chat.id, user.id, user_name)
    register_chat(chat.id, chat.title)

    # Û±) Ú†Ú© Ø§ÛŒÙ…ÙˆØ¬ÛŒ Ø­Ø¶ÙˆØ±
    if any(emoji in text for emoji in PRESENT_EMOJIS):
        is_new = mark_present(chat.id, user.id, user_name)
        if is_new:
            await update.message.reply_text(
                f"âœ… {user_name} Ø­Ø¶ÙˆØ±Øª Ø¨Ø±Ø§ÛŒ Ø§Ù…Ø±ÙˆØ² Ø«Ø¨Øª Ø´Ø¯."
            )
        else:
            await update.message.reply_text(
                f"ðŸ˜„ {user_name} Ø§Ù…Ø±ÙˆØ² Ù‚Ø¨Ù„Ø§Ù‹ Ø­Ø¶ÙˆØ± Ø²Ø¯ÛŒ."
            )
        return

    # Û²) Ú†Ú© Ø±ÛŒÙ¾Ù„Ø§ÛŒ Ø¨Ù‡ Ù¾ÛŒØ§Ù… Ø¨Ø§Øª
    bot_username = context.bot.username
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user
        and update.message.reply_to_message.from_user.id == context.bot.id
    )

    # Û³) Ú†Ú© Ù…Ù†Ø´Ù† Ø¨Ø§Øª
    is_mention = f"@{bot_username}" in text if bot_username else False

    if is_reply_to_bot or is_mention:
        # Ù…ØªÙ† Ø³ÙˆØ§Ù„ Ø±Ùˆ Ù¾Ø§Ú© Ú©Ù† Ø§Ø² Ù…Ù†Ø´Ù†
        question = text.replace(f"@{bot_username}", "").strip() if bot_username else text.strip()
        if not question and is_reply_to_bot:
            question = "Ú†ÛŒ Ø´Ø¯Ù‡ØŸ"
        if not question:
            return
        await handle_ai_chat(update, context, question)


async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    conn = db_connect()
    rows = conn.execute(
        "SELECT user_name, timestamp FROM attendance WHERE chat_id=? AND date=? ORDER BY timestamp",
        (chat_id, today),
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("ðŸ¤· Ø§Ù…Ø±ÙˆØ² Ù‡Ù†ÙˆØ² Ú©Ø³ÛŒ Ø­Ø¶ÙˆØ± Ù†Ø²Ø¯Ù‡.")
        return

    lines = [f"ðŸ“… Ø­Ø§Ø¶Ø±ÛŒÙ† Ø§Ù…Ø±ÙˆØ² ({today}):\n"]
    for i, r in enumerate(rows, 1):
        t = datetime.fromisoformat(r["timestamp"]).strftime("%H:%M")
        lines.append(f"{i}. {r['user_name']} â€” Ø³Ø§Ø¹Øª {t}")
    lines.append(f"\nðŸ‘¥ Ø¬Ù…Ø¹Ø§Ù‹ {len(rows)} Ù†ÙØ±")
    await update.message.reply_text("\n".join(lines))


async def me_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    conn = db_connect()
    week_ago = (datetime.now(TZ) - timedelta(days=7)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date FROM attendance WHERE chat_id=? AND user_id=? AND date>=? ORDER BY date DESC",
        (chat_id, user.id, week_ago),
    ).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) as c FROM attendance WHERE chat_id=? AND user_id=?",
        (chat_id, user.id),
    ).fetchone()["c"]
    conn.close()

    days = [r["date"] for r in rows]
    msg = (
        f"ðŸ“Š Ø¢Ù…Ø§Ø± Ø­Ø¶ÙˆØ± ØªÙˆ ({user.full_name}):\n\n"
        f"Ø§ÛŒÙ† Ù‡ÙØªÙ‡: {len(days)} Ø±ÙˆØ² Ø§Ø² Û· Ø±ÙˆØ²\n"
        f"Ú©Ù„ Ø­Ø¶ÙˆØ±Ù‡Ø§: {total}\n"
    )
    if days:
        msg += "\nØ±ÙˆØ²Ø§ÛŒ Ø­Ø§Ø¶Ø± Ø§ÛŒÙ† Ù‡ÙØªÙ‡:\n" + "\n".join(f"â€¢ {d}" for d in days)
    await update.message.reply_text(msg)


def build_week_report(chat_id: int) -> str:
    """Ú¯Ø²Ø§Ø±Ø´ Û· Ø±ÙˆØ² Ø§Ø®ÛŒØ± Ø±Ùˆ Ù…ÛŒØ³Ø§Ø²Ù‡."""
    now = datetime.now(TZ)
    week_ago = now - timedelta(days=7)
    week_ago_str = week_ago.strftime("%Y-%m-%d")

    conn = db_connect()
    members = conn.execute(
        "SELECT user_id, user_name FROM members WHERE chat_id=?",
        (chat_id,),
    ).fetchall()

    stats = []
    for m in members:
        count = conn.execute(
            """SELECT COUNT(DISTINCT date) as c FROM attendance
               WHERE chat_id=? AND user_id=? AND date>=?""",
            (chat_id, m["user_id"], week_ago_str),
        ).fetchone()["c"]
        stats.append((m["user_name"], count))

    days_data = conn.execute(
        """SELECT date, COUNT(*) as c FROM attendance
           WHERE chat_id=? AND date>=?
           GROUP BY date ORDER BY date""",
        (chat_id, week_ago_str),
    ).fetchall()
    conn.close()

    if not stats:
        return "ðŸ“­ ØªÙˆÛŒ Ø§ÛŒÙ† Ù‡ÙØªÙ‡ Ù‡ÛŒÚ† Ú©Ø³ÛŒ ÙØ¹Ø§Ù„ÛŒØªÛŒ Ù†Ø¯Ø§Ø´ØªÙ‡."

    stats.sort(key=lambda x: -x[1])

    lines = [f"ðŸ“Š Ú¯Ø²Ø§Ø±Ø´ Ù‡ÙØªÚ¯ÛŒ ({week_ago.strftime('%Y-%m-%d')} ØªØ§ {now.strftime('%Y-%m-%d')})\n"]
    lines.append("ðŸ† Ø¬Ø¯ÙˆÙ„ Ø­Ø¶ÙˆØ±:")
    for i, (name, count) in enumerate(stats, 1):
        absent = 7 - count
        if count >= 6:
            badge = "ðŸ¥‡"
        elif count >= 4:
            badge = "ðŸ¥ˆ"
        elif count >= 2:
            badge = "ðŸ¥‰"
        elif count == 0:
            badge = "ðŸ‘»"
        else:
            badge = "ðŸ«¥"
        bar = "â–ˆ" * count + "â–‘" * absent
        lines.append(f"{badge} {name}: {bar} {count}/Û· (ØºÛŒØ¨Øª: {absent})")

    if days_data:
        lines.append("\nðŸ“… Ø­Ø§Ø¶Ø±ÛŒÙ† Ø¯Ø± Ù‡Ø± Ø±ÙˆØ²:")
        for d in days_data:
            lines.append(f"  â€¢ {d['date']}: {d['c']} Ù†ÙØ±")

    lines.append("\nðŸŽ¯ Ø´Ø§Ø¯ Ùˆ Ø³Ù„Ø§Ù…Øª Ø¨Ø§Ø´ÛŒØ¯!")
    return "\n".join(lines)


async def week_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    report = build_week_report(chat_id)
    await update.message.reply_text(report)


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await week_cmd(update, context)


# ---------- Ø¬Ø§Ø¨ Ù‡ÙØªÚ¯ÛŒ ----------
async def weekly_report_job(context: ContextTypes.DEFAULT_TYPE):
    """Ù‡Ø± Ø¬Ù…Ø¹Ù‡ Û²Û±:Û°Û° Ø¨Ù‡ ÙˆÙ‚Øª ØªÙ‡Ø±Ø§Ù† Ø§Ø¬Ø±Ø§ Ù…ÛŒØ´Ù‡."""
    conn = db_connect()
    chats = conn.execute("SELECT chat_id FROM chats").fetchall()
    conn.close()
    for c in chats:
        try:
            report = build_week_report(c["chat_id"])
            await context.bot.send_message(
                chat_id=c["chat_id"],
                text="ðŸ”” Ú¯Ø²Ø§Ø±Ø´ Ø®ÙˆØ¯Ú©Ø§Ø± Ù‡ÙØªÚ¯ÛŒ:\n\n" + report,
            )
        except Exception as e:
            logger.error(f"Ø®Ø·Ø§ Ø¯Ø± Ø§Ø±Ø³Ø§Ù„ Ú¯Ø²Ø§Ø±Ø´ Ø¨Ù‡ {c['chat_id']}: {e}")


# ---------- main ----------
def main():
    if not BOT_TOKEN:
        raise SystemExit("âŒ Ù…ØªØºÛŒØ± BOT_TOKEN ØªÙ†Ø¸ÛŒÙ… Ù†Ø´Ø¯Ù‡.")

    db_init()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("week", week_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("me", me_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_daily(
        weekly_report_job,
        time=time(hour=21, minute=0, tzinfo=TZ),
        days=(4,),
        name="weekly_report",
    )

    logger.info("ðŸ¤– Ø¨Ø§Øª Ø´Ø±ÙˆØ¹ Ø¨Ù‡ Ú©Ø§Ø± Ú©Ø±Ø¯...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
