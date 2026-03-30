import logging
import os
import requests
import json
import sqlite3
import random
import string
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ============================================================
# ✅ CONFIG
# ============================================================
BOT_TOKEN     = os.environ.get("BOT_TOKEN",     "8331448370:AAGEdB0uDT0NnvN3DjFtuyGMRO2W8zuINYg")
ADMIN_ID      = int(os.environ.get("ADMIN_ID",  "8387741218"))
SMM_PANEL_KEY = os.environ.get("SMM_PANEL_KEY", "YOUR_SMM_PANEL_API_KEY")

LOG_CHANNEL       = "@RKXSMMZONE"
REQUIRED_CHANNELS = ["@RKXPremiumZone", "@RKXSMMZONE"]
BOT_USERNAME      = "@RKXSMMbot"
SUPPORT_USERNAME  = "@rkx_rakib"
SMM_PANEL_URL     = "https://your-smm-panel.com/api/v2"

AUTOPAY_API_KEY    = os.environ.get("AUTOPAY_API_KEY",    "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_SECRET_KEY = os.environ.get("AUTOPAY_SECRET_KEY", "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_BRAND_KEY  = os.environ.get("AUTOPAY_BRAND_KEY",  "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_DEVICE_KEY = os.environ.get("AUTOPAY_DEVICE_KEY", "Dl6Vzy8T33bbGiUybEDYffaZqp2ZxtJ0cP0Ss1HB")
AUTOPAY_URL        = "https://pay.rxpay.top/api/payment/create"

REFER_REWARD_SERVICE = "tg_members"
REFER_REWARD_QTY     = 100
FREE_OFFER_TEXT      = (
    "🎁 **ফ্রী সার্ভিস অফার**\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 **রেফার অফার (সবসময় চালু)**\n"
    "👥 ১ জনকে রেফার করলে → **১০০ Telegram Members ফ্রী!**\n\n"
    "📌 রেফার লিংক পেতে: /refer\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 আরো অফার আসলে এখানে দেখাবে।"
)

# ============================================================
# সার্ভিস লিস্ট (আপডেট করা প্রাইস)
# ============================================================
SERVICES = {
    "tiktok": {
        "name": "⚫ TikTok",
        "emoji": "⚫",
        "items": {
            "tiktok_views":     {"name": "👁️ TikTok Views",      "service_id": "1001", "price_per_1k": 2,   "min": 1000,  "max": 1000000, "note": "No Life Time"},
            "tiktok_likes":     {"name": "👍 TikTok Likes",       "service_id": "1002", "price_per_1k": 4,   "min": 100,   "max": 500000,  "note": "Drop 0-10%"},
            "tiktok_followers": {"name": "⭐ TikTok Followers",   "service_id": "1003", "price_per_1k": 99,  "min": 100,   "max": 100000,  "note": "Drop 10%"},
        }
    },
    "facebook": {
        "name": "🔷 Facebook",
        "emoji": "🔷",
        "items": {
            "fb_video_views":  {"name": "🎥 Facebook Video Views", "service_id": "2001", "price_per_1k": 5,  "min": 1000, "max": 1000000, "note": "Life Time"},
            "fb_followers":    {"name": "👤 Facebook Followers",   "service_id": "2002", "price_per_1k": 20, "min": 100,  "max": 100000,  "note": "Drop 0-5%"},
            "fb_reactions":    {"name": "😍 Facebook Reactions",   "service_id": "2003", "price_per_1k": 20, "min": 100,  "max": 100000,  "note": "Life Time"},
        }
    },
    "telegram": {
        "name": "🔵 Telegram",
        "emoji": "🔵",
        "items": {
            "tg_views":     {"name": "👁️ Telegram Views",    "service_id": "3001", "price_per_1k": 1,  "min": 100,  "max": 500000, "note": "Life Time"},
            "tg_reactions": {"name": "❤️ Telegram Reacts",   "service_id": "3002", "price_per_1k": 3,  "min": 100,  "max": 10000,  "note": "Life Time"},
            "tg_members":   {"name": "👥 Telegram Members",  "service_id": "3003", "price_per_1k": 9,  "min": 100,  "max": 50000,  "note": "High-Drop"},
        }
    },
    "youtube": {
        "name": "🔴 YouTube",
        "emoji": "🔴",
        "items": {
            "yt_likes":       {"name": "👍 YouTube Likes",       "service_id": "4001", "price_per_1k": 20, "min": 100,  "max": 100000,  "note": "very low Drop"},
            "yt_subscribers": {"name": "🔔 YouTube Subscribers", "service_id": "4002", "price_per_1k": 25, "min": 100,  "max": 50000,   "note": "Drop 60%"},
            "yt_views":       {"name": "▶️ YouTube Views",       "service_id": "4003", "price_per_1k": 30, "min": 1000, "max": 1000000, "note": "Drop 10%"},
        }
    },
    "instagram": {
        "name": "🟣 Instagram",
        "emoji": "🟣",
        "items": {
            "ig_views":     {"name": "👁️ Instagram Views",     "service_id": "5001", "price_per_1k": 1,  "min": 1000, "max": 1000000, "note": "Life Time"},
            "ig_likes":     {"name": "❤️ Instagram Likes",     "service_id": "5002", "price_per_1k": 20, "min": 100,  "max": 100000,  "note": "Drop 5%"},
            "ig_followers": {"name": "⭐ Instagram Followers", "service_id": "5003", "price_per_1k": 60, "min": 100,  "max": 100000,  "note": "Drop 20%"},
        }
    },
}

# Service display name → key mapping
SERVICE_NAME_MAP = {}
for cat_data in SERVICES.values():
    for key, svc in cat_data["items"].items():
        SERVICE_NAME_MAP[svc["name"]] = key

# ============================================================
# Keyboards
# ============================================================
MAIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 অর্ডার করুন"),  KeyboardButton("💰 ব্যালেন্স")],
        [KeyboardButton("💳 ডিপোজিট"),      KeyboardButton("📦 অর্ডার স্ট্যাটাস")],
        [KeyboardButton("🆘 সাপোর্ট"),      KeyboardButton("📋 প্রাইস লিস্ট")],
        [KeyboardButton("👥 রেফার করুন"),   KeyboardButton("🎁 ফ্রী সার্ভিস")],
    ],
    resize_keyboard=True
)

def order_cat_kb():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("⚫ TikTok"),    KeyboardButton("🔵 Telegram")],
            [KeyboardButton("🔴 YouTube"),   KeyboardButton("🔷 Facebook")],
            [KeyboardButton("🟣 Instagram")],
            [KeyboardButton("🎁 ফ্রী সার্ভিস"), KeyboardButton("🔙 মেইন মেনু")],
        ],
        resize_keyboard=True
    )

def _svc_kb(items: dict, back_label="🔙 Back"):
    btns = [[KeyboardButton(s["name"])] for s in items.values()]
    btns.append([KeyboardButton(back_label)])
    return ReplyKeyboardMarkup(btns, resize_keyboard=True)

def tiktok_kb():
    return _svc_kb(SERVICES["tiktok"]["items"])

def facebook_kb():
    return _svc_kb(SERVICES["facebook"]["items"])

def telegram_kb():
    return _svc_kb(SERVICES["telegram"]["items"])

def youtube_kb():
    return _svc_kb(SERVICES["youtube"]["items"])

def instagram_kb():
    return _svc_kb(SERVICES["instagram"]["items"])

CANCEL_KB = ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল করুন")]], resize_keyboard=True)

WELCOME = (
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🏡 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 মার্কেটের সবচেয়ে কম দামে সার্ভিস\n"
    "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
    "⚡ ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট\n"
    "🛡️ গ্যারান্টি সহ সাপোর্ট ও সার্ভিস\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👇 নিচের মেনু থেকে শুরু করুন"
)

# ============================================================
# Helpers
# ============================================================
def random_order_id():
    return random.randint(100000000, 999999999)

def find_svc(key):
    for cat in SERVICES.values():
        if key in cat["items"]:
            return cat["items"][key]
    return None

def get_user_name(user):
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip() or user.username or str(user.id)

# ============================================================
# Database
# ============================================================
def init_db():
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        full_name   TEXT,
        balance     REAL    DEFAULT 0.0,
        total_orders INTEGER DEFAULT 0,
        total_spent  REAL    DEFAULT 0.0,
        refer_by    INTEGER DEFAULT 0,
        refer_count INTEGER DEFAULT 0,
        joined_at   TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER,
        service_key     TEXT,
        service_name    TEXT,
        link            TEXT,
        quantity        INTEGER,
        amount          REAL,
        panel_order_id  TEXT,
        status          TEXT DEFAULT 'Processing',
        created_at      TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deposits (
        dep_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        amount      REAL,
        phone       TEXT,
        txn_ref     TEXT,
        status      TEXT DEFAULT 'Pending',
        created_at  TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    )""")
    # default settings
    defaults = [
        ("free_offer_text", FREE_OFFER_TEXT),
        ("refer_reward_qty", str(REFER_REWARD_QTY)),
        ("bot_active", "1"),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    conn.commit()
    conn.close()

def get_setting(key, fallback=""):
    conn = sqlite3.connect("rkx_bot.db")
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return r[0] if r else fallback

def set_setting(key, value):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def create_user(uid, uname, fname, refer_by=0):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id,username,full_name,balance,total_orders,total_spent,refer_by,refer_count,joined_at)"
        " VALUES(?,?,?,0,0,0,?,0,?)",
        (uid, uname, fname, refer_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect("rkx_bot.db")
    r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r  # (user_id, username, full_name, balance, total_orders, total_spent, refer_by, refer_count, joined_at)

def get_balance(uid):
    u = get_user(uid)
    return u[3] if u else 0.0

def update_balance(uid, amt):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit()
    conn.close()

def save_order(uid, svc_key, svc_name, link, qty, amt, panel_id):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders(user_id,service_key,service_name,link,quantity,amount,panel_order_id,status,created_at)"
        " VALUES(?,?,?,?,?,?,?,'Processing',?)",
        (uid, svc_key, svc_name, link, qty, amt, str(panel_id),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    oid = c.lastrowid
    conn.execute(
        "UPDATE users SET total_orders=total_orders+1, total_spent=total_spent+? WHERE user_id=?",
        (amt, uid)
    )
    conn.commit()
    conn.close()
    return oid

def get_recent_orders(uid, limit=5):
    conn = sqlite3.connect("rkx_bot.db")
    rows = conn.execute(
        "SELECT order_id,service_name,quantity,amount,status,created_at"
        " FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT ?",
        (uid, limit)
    ).fetchall()
    conn.close()
    return rows

def get_all_users():
    conn = sqlite3.connect("rkx_bot.db")
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_all_users_detail():
    conn = sqlite3.connect("rkx_bot.db")
    rows = conn.execute(
        "SELECT user_id,full_name,username,balance,total_orders,total_spent FROM users ORDER BY balance DESC"
    ).fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect("rkx_bot.db")
    u = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    o = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    r = conn.execute("SELECT SUM(amount) FROM orders").fetchone()[0] or 0
    d = conn.execute("SELECT SUM(amount) FROM deposits WHERE status='Completed'").fetchone()[0] or 0
    conn.close()
    return u, o, r, d

def save_deposit(uid, amt, phone, txn_ref):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute(
        "INSERT INTO deposits(user_id,amount,phone,txn_ref,status,created_at) VALUES(?,?,?,?,'Pending',?)",
        (uid, amt, phone, txn_ref, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def mark_deposit_done(txn_ref):
    conn = sqlite3.connect("rkx_bot.db")
    row = conn.execute("SELECT user_id,amount FROM deposits WHERE txn_ref=?", (txn_ref,)).fetchone()
    if row:
        conn.execute("UPDATE deposits SET status='Completed' WHERE txn_ref=?", (txn_ref,))
        conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (row[1], row[0]))
        conn.commit()
    conn.close()
    return row

def handle_refer(new_uid, referrer_uid):
    """Give referrer 100 Telegram members (stored as balance credit for now)"""
    conn = sqlite3.connect("rkx_bot.db")
    already = conn.execute(
        "SELECT refer_by FROM users WHERE user_id=?", (new_uid,)
    ).fetchone()
    if already and already[0] != 0:
        conn.close()
        return False  # already referred
    conn.execute("UPDATE users SET refer_by=? WHERE user_id=?", (referrer_uid, new_uid))
    conn.execute("UPDATE users SET refer_count=refer_count+1 WHERE user_id=?", (referrer_uid,))
    conn.commit()
    conn.close()
    return True

# ============================================================
# SMM Panel
# ============================================================
def place_smm_order(sid, link, qty):
    try:
        r = requests.post(
            SMM_PANEL_URL,
            data={"key": SMM_PANEL_KEY, "action": "add",
                  "service": sid, "link": link, "quantity": qty},
            timeout=20
        )
        j = r.json()
        return j.get("order"), j.get("error")
    except Exception as e:
        return None, str(e)

# ============================================================
# Payment
# ============================================================
def make_payment(uid, amt, phone):
    txn_ref = f"RKX{uid}{random.randint(10000,99999)}"
    payload = json.dumps({
        "success_url": f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "cancel_url":  f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "metadata":    {"phone": phone, "user_id": str(uid), "txn_ref": txn_ref},
        "amount":      str(amt)
    })
    hdrs = {
        "API-KEY":      AUTOPAY_API_KEY,
        "Content-Type": "application/json",
        "SECRET-KEY":   AUTOPAY_SECRET_KEY,
        "BRAND-KEY":    AUTOPAY_BRAND_KEY,
        "DEVICE-KEY":   AUTOPAY_DEVICE_KEY,
    }
    for attempt in range(3):
        try:
            r = requests.post(AUTOPAY_URL, headers=hdrs, data=payload, timeout=30).json()
            url = (
                r.get("payment_url") or
                r.get("url") or
                (r.get("data") or {}).get("payment_url")
            )
            if url:
                return url, txn_ref, r
            return None, txn_ref, r
        except requests.exceptions.Timeout:
            if attempt < 2:
                continue
            return None, txn_ref, "পেমেন্ট সার্ভার সাড়া দিচ্ছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।"
        except Exception as e:
            return None, txn_ref, str(e)
    return None, txn_ref, "সর্বোচ্চ চেষ্টা শেষ। সাপোর্টে যোগাযোগ করুন।"

# ============================================================
# Channel check
# ============================================================
async def is_member(bot, uid):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ["left", "kicked", "banned"]:
                return False
        except:
            return False
    return True

# ============================================================
# /start
# ============================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    fname = get_user_name(u)

    # referral from deep link
    refer_by = 0
    args = ctx.args
    if args and args[0].startswith("ref_"):
        try:
            refer_by = int(args[0][4:])
        except:
            pass

    create_user(u.id, u.username or "", fname, refer_by)

    # process referral reward
    if refer_by and refer_by != u.id:
        rewarded = handle_refer(u.id, refer_by)
        if rewarded:
            reward_qty = int(get_setting("refer_reward_qty", "100"))
            try:
                await ctx.bot.send_message(
                    refer_by,
                    f"🎉 **রেফার সফল!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **{fname}** আপনার লিংক দিয়ে জয়েন করেছে!\n"
                    f"🎁 পুরস্কার: **{reward_qty} Telegram Members**\n\n"
                    f"📩 অর্ডার পেতে: /refer_claim",
                    parse_mode="Markdown"
                )
            except:
                pass

    ctx.user_data.clear()
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    if get_setting("bot_active", "1") != "1" and u.id != ADMIN_ID:
        await update.message.reply_text(
            "⚠️ বট সাময়িকভাবে বন্ধ আছে। পরে আবার চেষ্টা করুন।"
        )
        return

    if not await is_member(ctx.bot, u.id):
        kb = [[InlineKeyboardButton("✅ Join করেছি — চেক করো", callback_data="check_join")]]
        await update.message.reply_text(
            "⛔ **বট ব্যবহারের আগে আমাদের চ্যানেলে জয়েন করুন** ⬇️\n\n"
            "➡️ @RKXPremiumZone\n"
            "➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(WELCOME, reply_markup=MAIN_KB)

# ============================================================
# /refer  &  /refer_claim
# ============================================================
async def cmd_refer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    bot_uname = BOT_USERNAME.lstrip("@")
    link = f"https://t.me/{bot_uname}?start=ref_{u.id}"
    user_row = get_user(u.id)
    ref_count = user_row[7] if user_row else 0
    reward_qty = get_setting("refer_reward_qty", "100")
    await update.message.reply_text(
        f"👥 **রেফার প্রোগ্রাম**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 প্রতি রেফারে: **{reward_qty} Telegram Members ফ্রী!**\n\n"
        f"🔗 আপনার রেফার লিংক:\n`{link}`\n\n"
        f"📊 মোট রেফার: **{ref_count} জন**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 লিংক শেয়ার করুন, প্রতি নতুন ইউজারে পুরস্কার পাবেন!",
        parse_mode="Markdown"
    )

async def cmd_refer_claim(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 রেফার ক্লেম করতে সাপোর্টে যোগাযোগ করুন:\n"
        f"👉 {SUPPORT_USERNAME}"
    )

# ============================================================
# /admin panel
# ============================================================
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    kb = [
        [InlineKeyboardButton("👥 সব ইউজার",         callback_data="adm_users"),
         InlineKeyboardButton("📊 স্ট্যাটস",          callback_data="adm_stats")],
        [InlineKeyboardButton("💰 ব্যালেন্স যোগ",    callback_data="adm_addbal"),
         InlineKeyboardButton("💸 ব্যালেন্স কমাও",   callback_data="adm_subbal")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট",         callback_data="adm_broadcast"),
         InlineKeyboardButton("🔧 সেটিংস",            callback_data="adm_settings")],
        [InlineKeyboardButton("📋 সার্ভিস প্রাইস",   callback_data="adm_prices"),
         InlineKeyboardButton("🔍 ইউজার সার্চ",       callback_data="adm_search")],
        [InlineKeyboardButton("✅ বট চালু",           callback_data="adm_boton"),
         InlineKeyboardButton("❌ বট বন্ধ",           callback_data="adm_botoff")],
    ]
    u, o, rev, dep = get_stats()
    await update.message.reply_text(
        f"🔐 **RKX SMM ZONE — Admin Panel**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 ইউজার: {u}  |  📦 অর্ডার: {o}\n"
        f"💰 রেভিনিউ: {rev:.2f}৳  |  💳 ডিপোজিট: {dep:.2f}৳\n"
        f"━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# shortcut commands
async def cmd_addbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        update_balance(tid, amt)
        nb = get_balance(tid)
        await update.message.reply_text(f"✅ {tid} → +{amt}৳ | নতুন: {nb:.2f}৳")
        try:
            await ctx.bot.send_message(
                tid,
                f"✅ **ব্যালেন্স যোগ হয়েছে!**\n"
                f"💰 +{amt} টাকা\n"
                f"💵 নতুন ব্যালেন্স: {nb:.2f} টাকা",
                parse_mode="Markdown"
            )
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Usage: /addbalance <uid> <amount>\n{e}")

async def cmd_subbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        update_balance(tid, -amt)
        nb = get_balance(tid)
        await update.message.reply_text(f"✅ {tid} → -{amt}৳ | নতুন: {nb:.2f}৳")
    except Exception as e:
        await update.message.reply_text(f"Usage: /subbalance <uid> <amount>\n{e}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    u, o, r, d = get_stats()
    await update.message.reply_text(
        f"📊 **Bot Stats**\n━━━━━━━━━━━━\n"
        f"👥 মোট ইউজার: {u}\n"
        f"📦 মোট অর্ডার: {o}\n"
        f"💰 মোট রেভিনিউ: {r:.2f}৳\n"
        f"💳 মোট ডিপোজিট: {d:.2f}৳",
        parse_mode="Markdown"
    )

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(ctx.args)
    uids = get_all_users()
    sent = 0
    for uid in uids:
        try:
            await ctx.bot.send_message(uid, f"📢 **Admin Message**\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ পাঠানো হয়েছে: {sent}/{len(uids)}")

async def cmd_setprice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Usage: /setprice tiktok_views 5"""
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        key = ctx.args[0]; price = float(ctx.args[1])
        svc = find_svc(key)
        if not svc:
            await update.message.reply_text("❌ Service key পাওয়া যায়নি।")
            return
        svc["price_per_1k"] = price
        await update.message.reply_text(f"✅ {svc['name']} → {price}৳/১০০০")
    except Exception as e:
        await update.message.reply_text(f"Usage: /setprice <service_key> <price>\n{e}")

async def cmd_userinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        tid = int(ctx.args[0])
        u = get_user(tid)
        if not u:
            await update.message.reply_text("❌ ইউজার পাওয়া যায়নি।")
            return
        await update.message.reply_text(
            f"👤 **User Info**\n━━━━━━━━━━━━\n"
            f"🆔 ID: {u[0]}\n"
            f"📛 নাম: {u[2]}\n"
            f"🔗 Username: @{u[1] or 'N/A'}\n"
            f"💰 ব্যালেন্স: {u[3]:.2f}৳\n"
            f"📦 অর্ডার: {u[4]}\n"
            f"💸 মোট খরচ: {u[5]:.2f}৳\n"
            f"👥 রেফার: {u[7]}\n"
            f"📅 জয়েন: {u[8]}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Usage: /userinfo <uid>\n{e}")

# ============================================================
# Callbacks
# ============================================================
async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u = q.from_user
    d = q.data

    # --- Join check ---
    if d == "check_join":
        await ctx.bot.send_chat_action(q.message.chat.id, "typing")
        if not await is_member(ctx.bot, u.id):
            await q.answer("❌ দুটো চ্যানেলেই জয়েন করো!", show_alert=True)
            return
        await q.message.delete()
        await ctx.bot.send_message(u.id, WELCOME, reply_markup=MAIN_KB)
        return

    # --- Order confirm/cancel ---
    if d == "confirm_order":
        await _do_confirm_order(q, ctx)
        return

    if d == "cancel_order":
        ctx.user_data.clear()
        await q.edit_message_text("❌ অর্ডার বাতিল করা হয়েছে।")
        return

    # --- Admin callbacks ---
    if u.id != ADMIN_ID:
        return

    if d == "adm_stats":
        us, o, r, dep = get_stats()
        await q.edit_message_text(
            f"📊 **Bot Stats**\n━━━━━━━━━━━━\n"
            f"👥 ইউজার: {us}\n📦 অর্ডার: {o}\n"
            f"💰 রেভিনিউ: {r:.2f}৳\n💳 ডিপোজিট: {dep:.2f}৳",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]])
        )

    elif d == "adm_users":
        rows = get_all_users_detail()[:15]
        msg = "👥 **Top 15 Users**\n━━━━━━━━━━━━\n"
        for r in rows:
            msg += f"🆔 {r[0]} | {r[2] or r[1]} | 💰{r[3]:.1f}৳ | 📦{r[4]}\n"
        await q.edit_message_text(
            msg, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]])
        )

    elif d == "adm_addbal":
        ctx.user_data["adm_step"] = "addbal_uid"
        await q.edit_message_text(
            "💰 **ব্যালেন্স যোগ**\nইউজার ID দাও:",
            parse_mode="Markdown"
        )

    elif d == "adm_subbal":
        ctx.user_data["adm_step"] = "subbal_uid"
        await q.edit_message_text(
            "💸 **ব্যালেন্স কমাও**\nইউজার ID দাও:",
            parse_mode="Markdown"
        )

    elif d == "adm_broadcast":
        ctx.user_data["adm_step"] = "broadcast_msg"
        await q.edit_message_text("📢 **ব্রডকাস্ট**\nমেসেজ লিখো:", parse_mode="Markdown")

    elif d == "adm_settings":
        offer = get_setting("free_offer_text", "")[:60]
        rqty  = get_setting("refer_reward_qty", "100")
        await q.edit_message_text(
            f"🔧 **Settings**\n━━━━━━━━━━━━\n"
            f"🎁 রেফার রিওয়ার্ড: {rqty} members\n"
            f"📝 Offer text: {offer}...\n\n"
            f"Commands:\n`/setprice <key> <price>`\n`/setreferqty <qty>`\n`/setoffer <text>`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]])
        )

    elif d == "adm_prices":
        msg = "📋 **Service Prices**\n━━━━━━━━━━━━\n"
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for key, s in cat["items"].items():
                msg += f"  `{key}` → {s['price_per_1k']}৳/১০০০\n"
        await q.edit_message_text(
            msg, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]])
        )

    elif d == "adm_search":
        ctx.user_data["adm_step"] = "search_uid"
        await q.edit_message_text("🔍 ইউজার ID লিখো:", parse_mode="Markdown")

    elif d == "adm_boton":
        set_setting("bot_active", "1")
        await q.answer("✅ বট চালু!", show_alert=True)

    elif d == "adm_botoff":
        set_setting("bot_active", "0")
        await q.answer("❌ বট বন্ধ!", show_alert=True)

    elif d == "adm_back":
        kb = [
            [InlineKeyboardButton("👥 সব ইউজার", callback_data="adm_users"),
             InlineKeyboardButton("📊 স্ট্যাটস",  callback_data="adm_stats")],
            [InlineKeyboardButton("💰 ব্যালেন্স যোগ", callback_data="adm_addbal"),
             InlineKeyboardButton("💸 ব্যালেন্স কমাও", callback_data="adm_subbal")],
            [InlineKeyboardButton("📢 ব্রডকাস্ট",      callback_data="adm_broadcast"),
             InlineKeyboardButton("🔧 সেটিংস",          callback_data="adm_settings")],
            [InlineKeyboardButton("📋 সার্ভিস প্রাইস", callback_data="adm_prices"),
             InlineKeyboardButton("🔍 ইউজার সার্চ",    callback_data="adm_search")],
            [InlineKeyboardButton("✅ বট চালু",        callback_data="adm_boton"),
             InlineKeyboardButton("❌ বট বন্ধ",        callback_data="adm_botoff")],
        ]
        us, o, r, dep = get_stats()
        await q.edit_message_text(
            f"🔐 **RKX SMM ZONE — Admin Panel**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 ইউজার: {us}  |  📦 অর্ডার: {o}\n"
            f"💰 রেভিনিউ: {r:.2f}৳  |  💳 ডিপোজিট: {dep:.2f}৳\n"
            f"━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )

# ============================================================
# Confirm Order
# ============================================================
async def _do_confirm_order(q, ctx):
    u = q.from_user
    svc = find_svc(ctx.user_data.get("sel", ""))
    link = ctx.user_data.get("link")
    qty  = ctx.user_data.get("qty")
    amt  = ctx.user_data.get("amt")
    fname = get_user_name(u)

    if not all([svc, link, qty, amt]):
        await q.edit_message_text("❌ কিছু ভুল হয়েছে। আবার চেষ্টা করো।")
        ctx.user_data.clear()
        return

    if get_balance(u.id) < amt:
        await q.edit_message_text("❌ ব্যালেন্স কম! আগে ডিপোজিট করো।")
        ctx.user_data.clear()
        return

    await q.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে...")
    await ctx.bot.send_chat_action(q.message.chat.id, "typing")

    pid, err = place_smm_order(svc["service_id"], link, qty)
    if err and not pid:
        await q.edit_message_text(f"❌ অর্ডার ব্যর্থ!\nকারণ: {err}")
        return

    update_balance(u.id, -amt)
    oid = save_order(u.id, ctx.user_data.get("sel"), svc["name"], link, qty, amt, str(pid or "N/A"))
    nb  = get_balance(u.id)

    await q.edit_message_text(
        f"✅ **অর্ডার সফল!**\n"
        f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
        f"👤 নাম: {fname}\n"
        f"🆔 Order ID: `{oid}`\n"
        f"🛒 সার্ভিস: {svc['name']}\n"
        f"🔢 পরিমাণ: {qty:,}\n"
        f"💸 খরচ: {amt:.2f}৳\n"
        f"💰 বাকি ব্যালেন্স: {nb:.2f}৳\n"
        f"📊 Status: ⏳ Processing\n"
        f"━━━━━━━━━━━•❈•━━━━━━━━━━━",
        parse_mode="Markdown"
    )

    try:
        await ctx.bot.send_message(
            LOG_CHANNEL,
            f"📌 **RKX SMM ZONE — New Order**\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"🆔 Order ID: {oid}\n"
            f"👤 User: {fname} ({u.id})\n"
            f"🛒 Service: {svc['name']}\n"
            f"🔢 Qty: {qty:,}\n"
            f"💸 Amount: {amt:.2f}৳\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except:
        pass
    ctx.user_data.clear()

# ============================================================
# Main Text Handler
# ============================================================
async def txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u    = update.effective_user
    t    = update.message.text.strip()
    step = ctx.user_data.get("step")
    ds   = ctx.user_data.get("dstep")
    adm  = ctx.user_data.get("adm_step")
    fname = get_user_name(u)

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    # Bot active check
    if get_setting("bot_active", "1") != "1" and u.id != ADMIN_ID:
        await update.message.reply_text("⚠️ বট সাময়িকভাবে বন্ধ।")
        return

    # ── Admin steps ──────────────────────────────────────────
    if adm and u.id == ADMIN_ID:
        if adm == "addbal_uid":
            try:
                ctx.user_data["adm_target"] = int(t)
                ctx.user_data["adm_step"]   = "addbal_amt"
                await update.message.reply_text("💰 কত টাকা যোগ করবে?")
            except:
                await update.message.reply_text("❌ সঠিক User ID দাও।")
            return

        if adm == "addbal_amt":
            try:
                amt = float(t)
                tid = ctx.user_data["adm_target"]
                update_balance(tid, amt)
                nb = get_balance(tid)
                await update.message.reply_text(f"✅ {tid} → +{amt}৳ | নতুন: {nb:.2f}৳")
                try:
                    await ctx.bot.send_message(
                        tid,
                        f"✅ **ব্যালেন্স যোগ হয়েছে!**\n💰 +{amt} টাকা\n💵 নতুন: {nb:.2f} টাকা",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                ctx.user_data.clear()
            except:
                await update.message.reply_text("❌ সঠিক পরিমাণ দাও।")
            return

        if adm == "subbal_uid":
            try:
                ctx.user_data["adm_target"] = int(t)
                ctx.user_data["adm_step"]   = "subbal_amt"
                await update.message.reply_text("💸 কত টাকা কমাবে?")
            except:
                await update.message.reply_text("❌ সঠিক User ID দাও।")
            return

        if adm == "subbal_amt":
            try:
                amt = float(t)
                tid = ctx.user_data["adm_target"]
                update_balance(tid, -amt)
                nb = get_balance(tid)
                await update.message.reply_text(f"✅ {tid} → -{amt}৳ | নতুন: {nb:.2f}৳")
                ctx.user_data.clear()
            except:
                await update.message.reply_text("❌ সঠিক পরিমাণ দাও।")
            return

        if adm == "broadcast_msg":
            uids = get_all_users()
            sent = 0
            for uid in uids:
                try:
                    await ctx.bot.send_message(uid, f"📢 **RKX SMM ZONE**\n\n{t}", parse_mode="Markdown")
                    sent += 1
                except:
                    pass
            await update.message.reply_text(f"✅ ব্রডকাস্ট সম্পন্ন: {sent}/{len(uids)}")
            ctx.user_data.clear()
            return

        if adm == "search_uid":
            try:
                tid = int(t)
                uu = get_user(tid)
                if not uu:
                    await update.message.reply_text("❌ পাওয়া যায়নি।")
                else:
                    await update.message.reply_text(
                        f"👤 {uu[2]} | @{uu[1] or 'N/A'}\n"
                        f"💰 {uu[3]:.2f}৳ | 📦 {uu[4]} orders | 💸 {uu[5]:.2f}৳ spent"
                    )
                ctx.user_data.clear()
            except:
                await update.message.reply_text("❌ সঠিক ID দাও।")
            return

    # ── Main menu buttons ────────────────────────────────────

    if t == "🛒 অর্ডার করুন":
        if not await is_member(ctx.bot, u.id):
            await cmd_start(update, ctx)
            return
        ctx.user_data.clear()
        ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 **সার্ভিস সিলেক্ট করুন** 👇", reply_markup=order_cat_kb(), parse_mode="Markdown")
        return

    if t == "🔙 মেইন মেনু":
        ctx.user_data.clear()
        await update.message.reply_text(WELCOME, reply_markup=MAIN_KB)
        return

    # ── Categories ───────────────────────────────────────────
    cat_map = {
        "⚫ TikTok":    ("tiktok",    tiktok_kb,    "⚫ TikTok Services"),
        "🔷 Facebook":  ("facebook",  facebook_kb,  "🔷 Facebook Services"),
        "🔵 Telegram":  ("telegram",  telegram_kb,  "🔵 Telegram Services"),
        "🔴 YouTube":   ("youtube",   youtube_kb,   "🔴 YouTube Services"),
        "🟣 Instagram": ("instagram", instagram_kb, "🟣 Instagram Services"),
    }
    if t in cat_map and ctx.user_data.get("in_order"):
        cat_key, kb_fn, title = cat_map[t]
        ctx.user_data["cat"] = cat_key
        await update.message.reply_text(
            f"{title} 👇\n\n💰 ব্যালেন্স: **{get_balance(u.id):.2f}৳**",
            reply_markup=kb_fn(),
            parse_mode="Markdown"
        )
        return

    if t == "🔙 Back":
        ctx.user_data.pop("cat", None)
        ctx.user_data.pop("step", None)
        ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 **সার্ভিস সিলেক্ট করুন** 👇", reply_markup=order_cat_kb(), parse_mode="Markdown")
        return

    # ── Service selected ─────────────────────────────────────
    if t in SERVICE_NAME_MAP and ctx.user_data.get("in_order"):
        svc_key = SERVICE_NAME_MAP[t]
        svc = find_svc(svc_key)
        bal = get_balance(u.id)
        ctx.user_data["sel"]  = svc_key
        ctx.user_data["step"] = "link"
        await update.message.reply_text(
            f"✅ **{svc['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 আপনার ব্যালেন্স: **{bal:.2f}৳**\n"
            f"📊 মূল্য: **{svc['price_per_1k']}৳ / ১০০০**\n"
            f"📉 Min: {svc['min']:,}  |  📈 Max: {svc['max']:,}\n"
            f"ℹ️ {svc.get('note','')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔗 পোস্ট/প্রোফাইল লিংক দাও:",
            reply_markup=CANCEL_KB,
            parse_mode="Markdown"
        )
        return

    if t == "❌ বাতিল করুন":
        ctx.user_data.clear()
        await update.message.reply_text("❌ বাতিল।", reply_markup=MAIN_KB)
        return

    # ── Order: link ──────────────────────────────────────────
    if step == "link":
        if not (t.startswith("http://") or t.startswith("https://")):
            await update.message.reply_text("❌ সঠিক লিংক দাও! http/https দিয়ে শুরু হতে হবে।")
            return
        svc = find_svc(ctx.user_data.get("sel", ""))
        ctx.user_data["link"] = t
        ctx.user_data["step"] = "qty"
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n"
            f"💰 ব্যালেন্স: **{get_balance(u.id):.2f}৳**\n"
            f"📊 মূল্য: **{svc['price_per_1k']}৳ / ১০০০**\n"
            f"📉 Min: {svc['min']:,}  |  📈 Max: {svc['max']:,}\n\n"
            f"🔢 পরিমাণ লিখো (যেমন: 1000):",
            reply_markup=CANCEL_KB,
            parse_mode="Markdown"
        )
        return

    # ── Order: quantity ──────────────────────────────────────
    if step == "qty":
        if not t.isdigit():
            await update.message.reply_text("❌ শুধু সংখ্যা লিখো!")
            return
        qty = int(t)
        svc = find_svc(ctx.user_data.get("sel", ""))
        if qty < svc["min"] or qty > svc["max"]:
            await update.message.reply_text(
                f"❌ পরিমাণ **{svc['min']:,}** – **{svc['max']:,}** এর মধ্যে হতে হবে!",
                parse_mode="Markdown"
            )
            return
        amt = round((qty / 1000) * svc["price_per_1k"], 2)
        bal = get_balance(u.id)
        if bal < amt:
            await update.message.reply_text(
                f"❌ **ব্যালেন্স কম!**\n"
                f"💰 আছে: {bal:.2f}৳  |  দরকার: {amt:.2f}৳\n\n"
                f"💳 ডিপোজিট করুন।",
                reply_markup=MAIN_KB,
                parse_mode="Markdown"
            )
            ctx.user_data.clear()
            return
        ctx.user_data["qty"]  = qty
        ctx.user_data["amt"]  = amt
        ctx.user_data["step"] = "confirm"
        kb = [[
            InlineKeyboardButton("✅ কনফার্ম করুন", callback_data="confirm_order"),
            InlineKeyboardButton("❌ বাতিল",         callback_data="cancel_order"),
        ]]
        await update.message.reply_text(
            f"📋 **অর্ডার সারসংক্ষেপ**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 নাম: {fname}\n"
            f"🛒 {svc['name']}\n"
            f"🔗 {ctx.user_data['link']}\n"
            f"🔢 {qty:,}\n"
            f"💸 মোট: **{amt:.2f}৳**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ কনফার্ম করবেন?",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

    # ── Balance ──────────────────────────────────────────────
    if t == "💰 ব্যালেন্স":
        uu = get_user(u.id)
        bal  = uu[3] if uu else 0.0
        tot  = uu[4] if uu else 0
        spent = uu[5] if uu else 0.0
        kb = [[InlineKeyboardButton("💳 ডিপোজিট করুন", callback_data="goto_deposit")]]
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💳 **অ্যাকাউন্ট ব্যালেন্স**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 নাম : {fname}\n"
            f"💰 বর্তমান ব্যালেন্স : **{bal:.2f} টাকা**\n"
            f"📦 Total Orders : {tot}\n"
            f"💵 Total Spent : {spent:.2f} টাকা\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

    # ── Deposit ──────────────────────────────────────────────
    if t == "💳 ডিপোজিট":
        ctx.user_data.clear()
        ctx.user_data["dstep"] = "amt"
        await update.message.reply_text(
            "💳 **ডিপোজিট**\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\n🔢 শুধু সংখ্যা লিখো:",
            reply_markup=CANCEL_KB,
            parse_mode="Markdown"
        )
        return

    # ── Order Status ─────────────────────────────────────────
    if t == "📦 অর্ডার স্ট্যাটাস":
        rows = get_recent_orders(u.id)
        if not rows:
            await update.message.reply_text("📦 এখনো কোনো অর্ডার নেই।")
            return
        msg = "📦 **সর্বশেষ ৫টি অর্ডার:**\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            status_emoji = "✅" if r[4] == "Completed" else "⏳" if r[4] == "Processing" else "❌"
            msg += (
                f"🆔 `#{r[0]}` | 🛒 {r[1]}\n"
                f"🔢 {r[2]:,} | 💸 {r[3]:.2f}৳ | {status_emoji} {r[4]}\n"
                f"📅 {r[5]}\n─────────────\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # ── Support ──────────────────────────────────────────────
    if t == "🆘 সাপোর্ট":
        kb = [[InlineKeyboardButton("📩 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")]]
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━\n"
            "🔒 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 𝗦𝗨𝗣𝗣𝗢𝗥𝗧\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📌 বট থেকে অর্ডার করার সম্পূর্ণ নিয়ম:\n"
            "🔗 https://t.me/RKXPremiumZone/84\n\n"
            "📌 বটে টাকা অ্যাড করার সম্পূর্ণ নিয়ম:\n"
            "🔗 https://t.me/RKXPremiumZone/86\n\n"
            "‼️ ভুল বা প্রাইভেট লিংক অর্ডার করবেন না।\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🕒 ২৪/৭ সাপোর্টের জন্য\n"
            "━━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ── Price List ───────────────────────────────────────────
    if t == "📋 প্রাইস লিস্ট":
        msg = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📲 **RX SMM ZONE – SERVICE LIST**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔵 𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠\n\n"
            "👁️ 1K Views — 1 Taka  (Life Time)\n"
            "❤️ 1K Reacts — 3 Taka  (Life Time)\n"
            "👥 1K Members — 9 Taka [High-Drop]\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔷 𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞\n\n"
            "🎥 1K Video Views — 5 Tk (Life Time)\n"
            "👤 1K Followers — 20 Taka (Drop 0-5%)\n"
            "😍 1K Reactions — 20 TK (Life Time)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🟣 𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠\n\n"
            "👁️ 1K Views — 1 Taka (Life Time)\n"
            "❤️ 1K Likes — 20 Taka (Drop 5%)\n"
            "⭐ 1K Followers — 60 Taka (Drop 20%)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚫ 𝗧𝗜𝗞𝗧𝗢𝗞\n\n"
            "👁️ 1K Views — 2 Taka  (No life Time)\n"
            "👍 1K Likes — 4 Taka (Drop 0-10%)\n"
            "⭐ 1K Followers — 99 Tk (Drop 10%)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔴 𝗬𝗢𝗨𝗧𝗨𝗕𝗘\n\n"
            "👍 1K Likes — 20 Taka (very low Drop)\n"
            "🔔 1K Subscribers — 25 Tk (Drop 60%)\n"
            "▶️ 1K Views — 30 Taka (Drop 10%)\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💥 তাড়াতাড়ি অর্ডার কমপ্লিট\n"
            "⏱ ৩০ মিনিট এর মধ্যে অর্ডার কমপ্লিট হবে\n"
            "🛡️ গ্যারান্টি সহ সাপোর্ট এবং সার্ভিস\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # ── Refer ────────────────────────────────────────────────
    if t == "👥 রেফার করুন":
        await cmd_refer(update, ctx)
        return

    # ── Free Service ─────────────────────────────────────────
    if t == "🎁 ফ্রী সার্ভিস":
        offer = get_setting("free_offer_text", FREE_OFFER_TEXT)
        await update.message.reply_text(offer, parse_mode="Markdown")
        return

    # ── Deposit: amount ──────────────────────────────────────
    if ds == "amt":
        if not t.isdigit() or int(t) < 10:
            await update.message.reply_text("❌ সর্বনিম্ন **১০ টাকা** দিতে হবে!", parse_mode="Markdown")
            return
        ctx.user_data["damt"]  = int(t)
        ctx.user_data["dstep"] = "phone"
        await update.message.reply_text(
            "📱 ফোন নম্বর দাও\n(যেটা দিয়ে পেমেন্ট করবে):",
            reply_markup=CANCEL_KB
        )
        return

    # ── Deposit: phone ───────────────────────────────────────
    if ds == "phone":
        amt   = ctx.user_data.get("damt")
        phone = t
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

        pay_url, txn_ref, raw = make_payment(u.id, amt, phone)
        ctx.user_data.clear()

        if pay_url:
            order_id = random_order_id()
            save_deposit(u.id, amt, phone, txn_ref)
            kb = [[InlineKeyboardButton(
                "💳 𝗣𝗮𝘆 𝗡𝗼𝘄",
                web_app=WebAppInfo(url=pay_url)
            )]]
            await update.message.reply_text(
                f"✅ **পেমেন্ট লিংক তৈরি হয়েছে**\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"👤 নাম: {fname}\n"
                f"💰 পরিমাণ: **{amt:.2f}৳**\n"
                f"➕ মোট যোগ হবে: **{amt:.2f}৳**\n"
                f"🧾 অর্ডার আইডি: `{order_id}`\n\n"
                f"👉 পেমেন্ট করতে নিচের **𝗣𝗮𝘆 𝗡𝗼𝘄** বাটনে ক্লিক করুন।\n"
                f"━━━━━━━━━━━━━━",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ **পেমেন্ট লিংক তৈরি হয়নি।**\n"
                f"কারণ: {raw}\n\n"
                f"🆘 সাপোর্টে যোগাযোগ করুন: {SUPPORT_USERNAME}",
                reply_markup=MAIN_KB,
                parse_mode="Markdown"
            )
        return

    # ── Unknown / garbage text → restart ────────────────────
    # Only if not in any active flow
    if not step and not ds and not adm and not ctx.user_data.get("in_order"):
        await update.message.reply_text(WELCOME, reply_markup=MAIN_KB)

# ============================================================
# Admin extra commands
# ============================================================
async def cmd_setreferqty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        qty = int(ctx.args[0])
        set_setting("refer_reward_qty", str(qty))
        await update.message.reply_text(f"✅ রেফার রিওয়ার্ড আপডেট: {qty} members")
    except Exception as e:
        await update.message.reply_text(f"Usage: /setreferqty <qty>\n{e}")

async def cmd_setoffer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /setoffer <text>")
        return
    text = " ".join(ctx.args)
    set_setting("free_offer_text", text)
    await update.message.reply_text("✅ অফার টেক্সট আপডেট হয়েছে।")

# ============================================================
# Main
# ============================================================
def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.INFO
    )
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("admin",        cmd_admin))
    app.add_handler(CommandHandler("addbalance",   cmd_addbalance))
    app.add_handler(CommandHandler("subbalance",   cmd_subbalance))
    app.add_handler(CommandHandler("stats",        cmd_stats))
    app.add_handler(CommandHandler("broadcast",    cmd_broadcast))
    app.add_handler(CommandHandler("setprice",     cmd_setprice))
    app.add_handler(CommandHandler("userinfo",     cmd_userinfo))
    app.add_handler(CommandHandler("setreferqty",  cmd_setreferqty))
    app.add_handler(CommandHandler("setoffer",     cmd_setoffer))
    app.add_handler(CommandHandler("refer",        cmd_refer))
    app.add_handler(CommandHandler("refer_claim",  cmd_refer_claim))

    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, txt))

    logging.info("✅ RKX SMM Bot চালু!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
