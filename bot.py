"""
بات حضور و غیاب تلگرام + چت با هوش مصنوعی
- هر کسی توی گروه ایموجی ✋ بفرسته، حضور اون روزش ثبت میشه.
- هر جمعه شب ساعت ۲۱ به وقت تهران، گزارش هفتگی توی گروه فرستاده میشه.
- اگه کسی روی پیام بات ریپلای کنه، @ منشن کنه، یا /ask بزنه، بات با AI جواب میده.
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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
TZ = ZoneInfo("Asia/Tehran")

# ایموجی‌هایی که به عنوان "حضور" قبول میشن
PRESENT_EMOJIS = {"✋", "✅", "👋", "🙋", "🙋‍♂️", "🙋‍♀️", "🫡", "🌞", "☀️"}

# شخصیت بات برای چت AI
SYSTEM_PROMPT = """تو یه بات تلگرامی به اسم «حضور و غیاب» هستی که توی یه گروه دوستی ایرونی به اسم «مهاجران» فعالیت میکنی. شخصیتت یه رفیق بامزه‌ی زبون‌دراز و باحاله که خودش رو هم‌سطح بقیه می‌بینه — نه رسمی، نه ربات‌گونه، نه فرمایشی.

شخصیتت:
- بامزه و طنازی، اهل متلک رفاقتی و تکه‌اندازی نرم.
- باهوش و حاضرجواب — جواب‌هات نباید کلیشه‌ای یا «چت‌بات‌مانند» باشه.
- خلاق و غیرقابل‌پیش‌بینی — هر بار یه مدل متفاوت جواب بده، تکراری نباش.
- اهل فرهنگ ایرونی — ضرب‌المثل، تیکه‌های فارسی، اشاره به فیلم‌سریال ایرونی، شعر حافظ یا سعدی هر از گاهی بنداز.
- گاهی شعر یا تیکه‌ی موزیکال (مثل ابی، گوگوش، شجریان، یا حتی رپ فارسی) به‌جا بنداز.
- ایموجی استفاده کن ولی نه زیادی — فقط جایی که واقعاً به جا و بامزه‌ست.

سبک حرف زدن:
- کاملاً خودمونی و محاوره‌ای فارسی، نه کتابی.
- از کلمات کوچه‌بازاری و خودمونی استفاده کن: «داش»، «رفیق»، «جیگر»، «بابا»، «والا»، «جون من»، «بخدا»، «این چی بود»، «جدی؟»، «نه بابا!».
- جواب‌ها معمولاً ۲ تا ۵ جمله. اگه سوال طولانی یا جدی بود، کامل‌تر جواب بده.
- اگه طرف باهات شوخی کرد یا تیکه انداخت، حاضرجوابی کن — جواب دندون‌شکن (ولی دوستانه) بده.

قوانین:
- اگه کسی پرسید کی هستی، با شوخی بگو که بات گروهی هستی، حضور و غیابو ثبت می‌کنی و رفیق همه‌تونم.
- اگه کسی فحش داد یا شوخی سنگین کرد، با حاضرجوابی و شوخی جواب بده، خودت فحش نده.
- موضوع‌های حساس (سیاست تند، مسائل غیرقانونی، خلاف اخلاق) رو با شوخی رد کن، وارد جزئیات نشو.
- اگه از پیام «ریپلای‌شده» اطلاعاتی هست، حتماً بهش اشاره کن و توی جوابت بهش گره بزن (نه فقط جواب کلی).
- هیچ‌وقت نگو «من یه مدل زبانی هستم» یا «به عنوان یه AI» — تو رفیق گروهی، نه ربات.
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
        logger.info("✅ OpenAI متصل شد.")
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی OpenAI: {e}")
else:
    logger.warning("⚠️ OPENAI_API_KEY تنظیم نشده — قابلیت چت AI غیرفعال.")


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


# ---------- AI ----------
async def ask_ai(user_name: str, user_message: str, replied_text: str | None = None) -> str:
    """ارسال پیام به OpenAI و دریافت جواب."""
    if not openai_client:
        return "🤖 الان قابلیت چت AI فعال نیست. مدیر گروه باید OPENAI_API_KEY رو تنظیم کنه."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if replied_text:
        messages.append({
            "role": "system",
            "content": f"کاربر داره به این پیام قبلی ریپلای میزنه: «{replied_text}»",
        })

    messages.append({
        "role": "user",
        "content": f"({user_name} میگه): {user_message}",
    })

    try:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=1.1,
            max_tokens=600,
            presence_penalty=0.6,
            frequency_penalty=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"خطای OpenAI: {e}")
        return "😅 یه مشکلی پیش اومد، بعداً امتحان کن."


async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """جواب AI رو به پیام کاربر بفرست."""
    user = update.effective_user
    user_name = user.full_name or user.username or "رفیق"

    replied_text = None
    if update.message.reply_to_message and update.message.reply_to_message.text:
        replied_text = update.message.reply_to_message.text

    # نشون بده داره تایپ میکنه
    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
    except Exception:
        pass

    answer = await ask_ai(user_name, user_message, replied_text)
    await update.message.reply_text(answer)


# ---------- هندلرها ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    register_chat(chat.id, chat.title)
    msg = (
        "سلام بچه‌ها 👋\n"
        "من بات حضور و غیاب گروهم.\n\n"
        f"هر روز یکی از این ایموجی‌ها رو بفرستین تا حضورتون ثبت بشه:\n"
        f"{' '.join(sorted(PRESENT_EMOJIS))}\n\n"
        "💬 برای چت با من، یا روی پیامم ریپلای بزن، یا منشن کن، یا /ask بنویس.\n\n"
        "کامندها:\n"
        "/today — لیست حاضرین امروز\n"
        "/week — گزارش این هفته\n"
        "/me — آمار خودت\n"
        "/ask — چت با هوش مصنوعی\n"
        "/help — راهنما"
    )
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 راهنمای بات\n\n"
        f"📌 ثبت حضور:\n{' '.join(sorted(PRESENT_EMOJIS))}\n"
        "(هر روز یه بار حساب میشه)\n\n"
        "💬 چت با هوش مصنوعی:\n"
        "• /ask سوالت — مستقیم بپرس\n"
        "• ریپلای روی پیام بات بزن\n"
        "• @Hoozoor_ghiab_bot رو منشن کن\n\n"
        "📊 کامندها:\n"
        "/today — حاضرین امروز\n"
        "/week — گزارش این هفته\n"
        "/me — آمار حضور خودت\n"
        "/report — گزارش کامل ۷ روز اخیر\n\n"
        "🤖 هر جمعه ساعت ۲۱ به وقت تهران، گزارش خودکار هفته میاد."
    )
    await update.message.reply_text(msg)


async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کامند /ask — کاربر سوالش رو بعد از /ask مینویسه."""
    if not update.message:
        return

    # متن بعد از /ask
    text = update.message.text or ""
    parts = text.split(maxsplit=1)
    question = parts[1].strip() if len(parts) > 1 else ""

    # اگه روی پیامی ریپلای کرده ولی متنی ننوشته، از پیام ریپلای استفاده کن
    if not question and update.message.reply_to_message and update.message.reply_to_message.text:
        question = update.message.reply_to_message.text

    if not question:
        await update.message.reply_text(
            "💬 بعد از /ask سوالت رو بنویس. مثلاً:\n/ask امروز چه خبر؟"
        )
        return

    await handle_ai_chat(update, context, question)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های متنی: حضور، ریپلای به بات، یا منشن."""
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text

    # ثبت اعضای فعال
    user_name = user.full_name or user.username or f"user_{user.id}"
    register_member(chat.id, user.id, user_name)
    register_chat(chat.id, chat.title)

    # ۱) چک ایموجی حضور
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
        return

    # ۲) چک ریپلای به پیام بات
    bot_username = context.bot.username
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user
        and update.message.reply_to_message.from_user.id == context.bot.id
    )

    # ۳) چک منشن بات
    is_mention = f"@{bot_username}" in text if bot_username else False

    if is_reply_to_bot or is_mention:
        # متن سوال رو پاک کن از منشن
        question = text.replace(f"@{bot_username}", "").strip() if bot_username else text.strip()
        if not question and is_reply_to_bot:
            question = "چی شده؟"
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
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_daily(
        weekly_report_job,
        time=time(hour=21, minute=0, tzinfo=TZ),
        days=(4,),
        name="weekly_report",
    )

    logger.info("🤖 بات شروع به کار کرد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
