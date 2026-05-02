# 🤖 بات حضور و غیاب تلگرام

یه بات ساده و باحال برای گروه دوستی. هر روز با یه ایموجی حضور می‌زنین، آخر هفته خودش گزارش می‌فرسته.

## ویژگی‌ها

- ✅ ثبت حضور با ایموجی (✋ ✅ 👋 🙋 🫡 🌞 ☀️)
- 📊 هر روز فقط یک بار حساب میشه
- 🔔 گزارش خودکار هر جمعه ساعت ۲۱ به وقت تهران
- 📅 کامندهای `/today`، `/week`، `/me`، `/report`، `/help`
- 🏆 جدول رتبه‌بندی با مدال 🥇🥈🥉 و نشون غیبت 👻

---

## مرحله ۱: ساخت بات تو تلگرام (۲ دقیقه)

1. توی تلگرام برو سراغ [@BotFather](https://t.me/BotFather)
2. بزن `/newbot`
3. یه اسم بده (مثلاً «بات حضور بچه‌ها»)
4. یه یوزرنیم بده که آخرش `bot` باشه (مثلاً `friends_attendance_bot`)
5. **توکنی که میده رو کپی کن** — این مهمه، گم نشه
6. بعد به BotFather بزن `/setprivacy` → بات‌ت رو انتخاب کن → `Disable`
   (این لازمه تا بات بتونه پیام‌های گروه رو بخونه)

---

## مرحله ۲: اضافه کردن بات به گروه

1. بات رو به گروه دوستی اضافه کن
2. بات رو **ادمین** کن (لازمه برای خوندن همه پیام‌ها)
3. توی گروه بزن `/start@یوزرنیم_باتت`

---

## مرحله ۳: اجرا کردن بات

### روش الف: اجرای محلی (برای تست)

```bash
cd telegram-attendance-bot
python -m venv venv
source venv/bin/activate     # روی ویندوز: venv\Scripts\activate
pip install -r requirements.txt
export BOT_TOKEN="توکنی_که_BotFather_داد"
python bot.py
```

تا وقتی پنجره ترمینال بازه، بات کار میکنه.

### روش ب: دیپلوی رایگان روی Railway (پیشنهادی) ⭐

Railway بهترین گزینه‌ست چون:
- رایگانه (تا ۵۰۰ ساعت در ماه)
- ۲۴/۷ آنلاین می‌مونه
- خودش کد رو از GitHub می‌گیره

**مراحل:**

1. کل پوشه `telegram-attendance-bot` رو روی [GitHub](https://github.com) به صورت یه ریپو خصوصی پوش کن.
2. برو به [railway.app](https://railway.app) و با گیت‌هاب وارد شو.
3. بزن **New Project → Deploy from GitHub repo** → ریپوت رو انتخاب کن.
4. بعد از ساخته شدن پروژه، برو به تب **Variables** و اضافه کن:
   - `BOT_TOKEN` = توکنی که BotFather داد
5. تو تب **Settings** اطمینان حاصل کن که Start Command رو `python bot.py` گذاشته (Procfile خودش این کار رو میکنه).
6. تمام. لاگ‌ها رو چک کن، باید بنویسه `🤖 بات شروع به کار کرد...`.

### روش ج: VPS شخصی با systemd

اگه VPS داری، یه فایل سرویس بساز:

```ini
# /etc/systemd/system/attendance-bot.service
[Unit]
Description=Telegram Attendance Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-attendance-bot
Environment="BOT_TOKEN=توکنت"
ExecStart=/home/ubuntu/telegram-attendance-bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable attendance-bot
sudo systemctl start attendance-bot
sudo systemctl status attendance-bot
```

---

## مرحله ۴: استفاده تو گروه

- **ثبت حضور:** هر کس یکی از این ایموجی‌ها بفرسته → ✋ ✅ 👋 🙋 🫡 🌞 ☀️
- **/today** — لیست حاضرین امروز
- **/week** — گزارش این هفته (شنبه تا جمعه)
- **/me** — آمار حضور خودت
- **/report** — مثل /week
- **/help** — راهنما

🔔 هر جمعه ساعت ۲۱:۰۰ به وقت تهران، بات خودش گزارش هفته رو تو گروه می‌فرسته.

---

## نکته فنی

دیتابیس `attendance.db` کنار `bot.py` ساخته میشه. روی Railway اگه ری‌استارت بشه ممکنه پاک شه. برای پایداری بیشتر، از Railway Volume یا یه دیتابیس Postgres استفاده کن (نسخه فعلی SQLite ساده‌ست برای سادگی).

اگه میخوای ایموجی‌های حضور رو عوض کنی، بالای `bot.py` متغیر `PRESENT_EMOJIS` رو ویرایش کن.
