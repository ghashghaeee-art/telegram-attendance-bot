"""
بات حضور و غیاب تلگرام
هر کسی توی گروه ایموجی ✋ بفرسته، حضور اون روزش ثبت میشه.
هر جمعه شب ساعت ۲۱ به وقت تهران، گزارش هفتگی توی گروه فرستاده میشه.
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

# ---------- تنظیمات ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DB_PATH = os.environ.get("DB_PATH", "attendance.db")
TZ = ZoneInfo("Asia/Tehran")

# ایموجی‌هایی که به عنوان "حضور" قبول میشن
PRESENT_EMOJIS = {"✋", "✅", "👋", "🙋", "🙋‍♂️", "🙋‍♀️", "🫡", "🌞", "☀️"}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------- دیتابیس ----------
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
    """ثبت حضور برای امروز. اگه قبلاً ثبت شده باشه False برمیگردونه."""
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


# ---------- هندلرها ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    register_chat(chat.id, chat.title)
    msg = (
        "سلام بچه‌ها 👋\n"
        "من بات حضور و غیاب گروهم.\n\n"
        f"هر روز یکی از این ایموجی‌ها رو بفرستین تا حضورتون ثبت بشه:\n"
        f"{' '.join(sorted(PRESENT_EMOJIS))}\n\n"
        "کامندها:\n"
        "/today — لیست حاضرین امروز\n"
        "/week — گزارش این هفته\n"
        "/me — آمار خودت\n"
        "/help — راهنما"
    )
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 راهنمای بات حضور و غیاب\n\n"
        f"برای ثبت حضور یکی از این ایموجی‌ها رو بفرست:\n{' '.join(sorted(PRESENT_EMOJIS))}\n\n"
        "هر روز فقط یک بار حساب میشه (مهم نیست چند تا بفرستی).\n\n"
        "📌 کامندها:\n"
        "/today — حاضرین امروز\n"
        "/week — گزارش این هفته (شنبه تا جمعه)\n"
        "/me — آمار حضور خودت\n"
        "/report — گزارش کامل ۷ روز اخیر\n\n"
        "🤖 هر جمعه ساعت ۲۱ به وقت تهران، گزارش خودکار هفته میاد."
    )
    await update.message.reply_text(msg)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اگه پیام شامل ایموجی حضور باشه، ثبت میکنه."""
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text

    # ثبت اعضای فعال
    user_name = user.full_name or user.username or f"user_{user.id}"
    register_member(chat.id, user.id, user_name)
    register_chat(chat.id, chat.title)

    # چک ایموجی حضور
    if any(emoji in text for emoji in PRESENT_EMOJIS):
        is_new = mark_present(chat.id, user.id, user_name)
        if is_new:
            await update.message.reply_text(
                f"✅ {user_name} حضورت برای امروز ثبت شد."
            )
        else:
            await update.message.reply_text(
                f"😄 {user_name} امروز قبلاً حضور زدی."
            )


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
        await update.message.reply_text("🤷 امروز هنوز کسی حضور نزده.")
        return

    lines = [f"📅 حاضرین امروز ({today}):\n"]
    for i, r in enumerate(rows, 1):
        t = datetime.fromisoformat(r["timestamp"]).strftime("%H:%M")
        lines.append(f"{i}. {r['user_name']} — ساعت {t}")
    lines.append(f"\n👥 جمعاً {len(rows)} نفر")
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
        f"📊 آمار حضور تو ({user.full_name}):\n\n"
        f"این هفته: {len(days)} روز از ۷ روز\n"
        f"کل حضورها: {total}\n"
    )
    if days:
        msg += "\nروزای حاضر این هفته:\n" + "\n".join(f"• {d}" for d in days)
    await update.message.reply_text(msg)


def build_week_report(chat_id: int) -> str:
    """گزارش ۷ روز اخیر رو میسازه."""
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

    # حاضرین به تفکیک روز
    days_data = conn.execute(
        """SELECT date, COUNT(*) as c FROM attendance
           WHERE chat_id=? AND date>=?
           GROUP BY date ORDER BY date""",
        (chat_id, week_ago_str),
    ).fetchall()
    conn.close()

    if not stats:
        return "📭 توی این هفته هیچ کسی فعالیتی نداشته."

    stats.sort(key=lambda x: -x[1])

    lines = [f"📊 گزارش هفتگی ({week_ago.strftime('%Y-%m-%d')} تا {now.strftime('%Y-%m-%d')})\n"]
    lines.append("🏆 جدول حضور:")
    for i, (name, count) in enumerate(stats, 1):
        absent = 7 - count
        if count >= 6:
            badge = "🥇"
        elif count >= 4:
            badge = "🥈"
        elif count >= 2:
            badge = "🥉"
        elif count == 0:
            badge = "👻"
        else:
            badge = "🫥"
        bar = "█" * count + "░" * absent
        lines.append(f"{badge} {name}: {bar} {count}/۷ (غیبت: {absent})")

    if days_data:
        lines.append("\n📅 حاضرین در هر روز:")
        for d in days_data:
            lines.append(f"  • {d['date']}: {d['c']} نفر")

    lines.append("\n🎯 شاد و سلامت باشید!")
    return "\n".join(lines)


async def week_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    report = build_week_report(chat_id)
    await update.message.reply_text(report)


async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مثل /week ولی برای دستی گرفتن گزارش."""
    await week_cmd(update, context)


# ---------- جاب هفتگی ----------
async def weekly_report_job(context: ContextTypes.DEFAULT_TYPE):
    """هر جمعه ۲۱:۰۰ به وقت تهران اجرا میشه."""
    conn = db_connect()
    chats = conn.execute("SELECT chat_id FROM chats").fetchall()
    conn.close()
    for c in chats:
        try:
            report = build_week_report(c["chat_id"])
            await context.bot.send_message(
                chat_id=c["chat_id"],
                text="🔔 گزارش خودکار هفتگی:\n\n" + report,
            )
        except Exception as e:
            logger.error(f"خطا در ارسال گزارش به {c['chat_id']}: {e}")


# ---------- main ----------
def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ متغیر BOT_TOKEN تنظیم نشده.")

    db_init()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("week", week_cmd))
    app.add_handler(CommandHandler("report", report_cmd))
    app.add_handler(CommandHandler("me", me_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # جاب هفتگی - هر جمعه ساعت ۲۱:۰۰ به وقت تهران
    # در python-telegram-bot، روز ۴ = جمعه (دوشنبه=۰)
    app.job_queue.run_daily(
        weekly_report_job,
        time=time(hour=21, minute=0, tzinfo=TZ),
        days=(4,),  # جمعه
        name="weekly_report",
    )

    logger.info("🤖 بات شروع به کار کرد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
