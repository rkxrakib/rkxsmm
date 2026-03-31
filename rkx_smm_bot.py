import logging
import os
import requests
import json
import sqlite3
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ============================================================
# ✅ CONFIG
# ============================================================
BOT_TOKEN     = os.environ.get("BOT_TOKEN",     "YOUR_BOT_TOKEN_HERE")
ADMIN_ID      = int(os.environ.get("ADMIN_ID",  "123456789"))
SMM_PANEL_URL = "https://rxsmm.top/api/v2"
SMM_PANEL_KEY = os.environ.get("SMM_PANEL_KEY", "65904810a831ae1bbb8edb1d03514e47")

AUTOPAY_API_KEY    = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_SECRET_KEY = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_BRAND_KEY  = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_DEVICE_KEY = "Dl6Vzy8T33bbGiUybEDYffaZqp2ZxtJ0cP0Ss1HB"
AUTOPAY_URL        = "https://pay.rxpay.top/api/payment/create"

LOG_CHANNEL       = "@RKXSMMZONE"
REQUIRED_CHANNELS = ["@RKXPremiumZone", "@RKXSMMZONE"]
BOT_USERNAME      = "@RKXSMMbot"
BOT_NAME          = "𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘"
DB_PATH           = "rkx_bot.db"

# ============================================================
# ✅ REAL SERVICES — আসল rxsmm.top ID + তোমার দাম (+50% profit)
# cost = প্যানেলের দাম | price_per_1k = তোমার বিক্রির দাম
# ============================================================
SERVICES = {
    "tiktok": {
        "name": "🎵 TikTok",
        "emoji": "🎵",
        "items": {
            "tiktok_views": {
                "name": "👁️ TikTok Views",
                "service_id": "4233",
                "cost_per_1k": 0.6145,
                "price_per_1k": 0.92,
                "min": 100, "max": 10000000,
                "desc": "⚡ INSTANT | 1M-10M/Day | Fast Delivery"
            },
            "tiktok_likes": {
                "name": "❤️ TikTok Likes",
                "service_id": "4256",
                "cost_per_1k": 2.91,
                "price_per_1k": 4.37,
                "min": 10, "max": 5000000,
                "desc": "⚡ INSTANT | 50K-100K/Day | No Refill"
            },
            "tiktok_followers": {
                "name": "👥 TikTok Followers",
                "service_id": "4323",
                "cost_per_1k": 1.0,
                "price_per_1k": 1.50,
                "min": 50, "max": 160000,
                "desc": "✅ Real Stable | INSTANT | R15"
            },
            "tiktok_likes_r30": {
                "name": "❤️ TikTok Likes [R30]",
                "service_id": "4257",
                "cost_per_1k": 3.16,
                "price_per_1k": 4.74,
                "min": 10, "max": 5000000,
                "desc": "⚡ INSTANT | 30 Days Refill ♻️"
            },
            "tiktok_likes_lifetime": {
                "name": "❤️ TikTok Likes [Lifetime]",
                "service_id": "4261",
                "cost_per_1k": 4.30,
                "price_per_1k": 6.45,
                "min": 10, "max": 5000000,
                "desc": "⚡ INSTANT | Lifetime Refill ♻️"
            },
        }
    },
    "facebook": {
        "name": "📘 Facebook",
        "emoji": "📘",
        "items": {
            "fb_reactions_like": {
                "name": "👍 Facebook Post Like",
                "service_id": "3701",
                "cost_per_1k": 20.3,
                "price_per_1k": 30.45,
                "min": 10, "max": 500000,
                "desc": "🌍 WorldWide | 0-30 Min | 20K-50K/Day"
            },
            "fb_reactions_love": {
                "name": "❤️ Facebook Post Love",
                "service_id": "3702",
                "cost_per_1k": 20.3,
                "price_per_1k": 30.45,
                "min": 10, "max": 500000,
                "desc": "🌍 WorldWide | 0-30 Min | 20K-50K/Day"
            },
            "fb_reactions_haha": {
                "name": "😂 Facebook Post HaHa",
                "service_id": "3704",
                "cost_per_1k": 20.3,
                "price_per_1k": 30.45,
                "min": 10, "max": 500000,
                "desc": "🌍 WorldWide | 0-30 Min | 20K-50K/Day"
            },
            "fb_reactions_wow": {
                "name": "😲 Facebook Post Wow",
                "service_id": "3705",
                "cost_per_1k": 20.3,
                "price_per_1k": 30.45,
                "min": 10, "max": 500000,
                "desc": "🌍 WorldWide | 0-30 Min | 20K-50K/Day"
            },
            "fb_followers": {
                "name": "👥 Facebook Followers",
                "service_id": "1846",
                "cost_per_1k": 23.49,
                "price_per_1k": 35.23,
                "min": 100, "max": 5000,
                "desc": "Profile/Page | Fast | HQ"
            },
        }
    },
    "telegram": {
        "name": "✈️ Telegram",
        "emoji": "✈️",
        "items": {
            "tg_members_cheap": {
                "name": "👥 TG Members [Cheap]",
                "service_id": "4817",
                "cost_per_1k": 1.68,
                "price_per_1k": 2.52,
                "min": 10, "max": 25000,
                "desc": "সস্তা | No Refill | ~46hr"
            },
            "tg_members_hq": {
                "name": "👥 TG Members [HQ]",
                "service_id": "4486",
                "cost_per_1k": 1.0,
                "price_per_1k": 1.50,
                "min": 10, "max": 20000,
                "desc": "Premium + Online | High Quality"
            },
            "tg_members_r7": {
                "name": "👥 TG Members [R7]",
                "service_id": "4820",
                "cost_per_1k": 6.28,
                "price_per_1k": 9.42,
                "min": 1, "max": 100000,
                "desc": "7 Days Refill ♻️"
            },
            "tg_members_r30": {
                "name": "👥 TG Members [R30]",
                "service_id": "4822",
                "cost_per_1k": 8.33,
                "price_per_1k": 12.50,
                "min": 1, "max": 100000,
                "desc": "30 Days Refill ♻️"
            },
            "tg_post_views": {
                "name": "👁️ TG Post Views [1 Post]",
                "service_id": "4525",
                "cost_per_1k": 0.2276,
                "price_per_1k": 0.34,
                "min": 50, "max": 20000,
                "desc": "⚡ INSTANT | MAX 1M | Fast"
            },
            "tg_post_views_5": {
                "name": "👁️ TG Post Views [Last 5]",
                "service_id": "4555",
                "cost_per_1k": 6.30,
                "price_per_1k": 9.45,
                "min": 1000, "max": 40000,
                "desc": "⚡ INSTANT | Last 5 Posts"
            },
            "tg_post_views_10": {
                "name": "👁️ TG Post Views [Last 10]",
                "service_id": "4556",
                "cost_per_1k": 12.59,
                "price_per_1k": 18.89,
                "min": 1000, "max": 40000,
                "desc": "⚡ INSTANT | Last 10 Posts"
            },
            "tg_reactions": {
                "name": "💎 TG Mix Reactions",
                "service_id": "4744",
                "cost_per_1k": 20.98,
                "price_per_1k": 31.47,
                "min": 10, "max": 1000000,
                "desc": "👍🤩🎉🔥❤️🥰👏 Mix | INSTANT"
            },
        }
    },
    "youtube": {
        "name": "🎬 YouTube",
        "emoji": "🎬",
        "items": {
            "yt_views": {
                "name": "👁️ YouTube Views",
                "service_id": "1908",
                "cost_per_1k": 1.0,
                "price_per_1k": 1.50,
                "min": 1000, "max": 1000000,
                "desc": "India Adword | Display | 0-72hr"
            },
            "yt_likes": {
                "name": "👍 YouTube Likes",
                "service_id": "1877",
                "cost_per_1k": 25.0,
                "price_per_1k": 37.50,
                "min": 20, "max": 5000,
                "desc": "Real | Fast | HQ"
            },
            "yt_subscribers": {
                "name": "🔔 YouTube Subscribers",
                "service_id": "1914",
                "cost_per_1k": 50.0,
                "price_per_1k": 75.0,
                "min": 10, "max": 1000,
                "desc": "Real | Gradual | HQ"
            },
        }
    },
    "instagram": {
        "name": "📸 Instagram",
        "emoji": "📸",
        "items": {
            "ig_views": {
                "name": "👁️ IG Views",
                "service_id": "2015",
                "cost_per_1k": 0.1366,
                "price_per_1k": 0.20,
                "min": 100, "max": 100000000,
                "desc": "⚡ 0-5 Min | 100K-1M/Day | All Links"
            },
            "ig_likes": {
                "name": "❤️ IG Likes",
                "service_id": "2034",
                "cost_per_1k": 16.23,
                "price_per_1k": 24.34,
                "min": 100, "max": 1000000,
                "desc": "HQ | 0-30 Min | 10K/Day"
            },
            "ig_followers": {
                "name": "👥 IG Followers",
                "service_id": "2135",
                "cost_per_1k": 1.0,
                "price_per_1k": 1.50,
                "min": 10, "max": 1000,
                "desc": "100% Real | 0-15 Min"
            },
            "ig_comments": {
                "name": "💬 IG Comments",
                "service_id": "2157",
                "cost_per_1k": 1.0,
                "price_per_1k": 1.50,
                "min": 10, "max": 100,
                "desc": "MQ | Emojis | Fast | Cheap"
            },
            "ig_story_views": {
                "name": "📖 IG Story Views",
                "service_id": "2018",
                "cost_per_1k": 0.50,
                "price_per_1k": 0.75,
                "min": 100, "max": 100000,
                "desc": "⚡ INSTANT | Fast"
            },
            "ig_reel_views": {
                "name": "🎬 IG Reel Views",
                "service_id": "2020",
                "cost_per_1k": 0.40,
                "price_per_1k": 0.60,
                "min": 100, "max": 1000000,
                "desc": "⚡ INSTANT | Fast"
            },
        }
    },
}

# Name → key map
SERVICE_NAME_MAP = {}
for _cat in SERVICES.values():
    for _k, _s in _cat["items"].items():
        SERVICE_NAME_MAP[_s["name"]] = _k

# ============================================================
# Keyboards
# ============================================================
MAIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("🛒 Order"),    KeyboardButton("💰 Balance")],
     [KeyboardButton("💳 Deposit"),  KeyboardButton("📦 Order Status")],
     [KeyboardButton("🆘 Support"),  KeyboardButton("📋 Price & Info")]],
    resize_keyboard=True
)

def order_cat_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🎵 TikTok"),    KeyboardButton("✈️ Telegram")],
         [KeyboardButton("🎬 YouTube"),   KeyboardButton("📘 Facebook")],
         [KeyboardButton("📸 Instagram")],
         [KeyboardButton("🔙 Main Menu")]],
        resize_keyboard=True
    )

def make_service_kb(cat_key):
    items = SERVICES[cat_key]["items"]
    rows  = [[KeyboardButton(s["name"])] for s in items.values()]
    rows.append([KeyboardButton("🔙 Back")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

CAT_KEY_MAP = {
    "🎵 TikTok":    "tiktok",
    "📘 Facebook":  "facebook",
    "✈️ Telegram":  "telegram",
    "🎬 YouTube":   "youtube",
    "📸 Instagram": "instagram",
}

WELCOME_MSG = (
    "━━━━━━━━━━━━━━━━━━\n"
    "🏡 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 মার্কেটের সবচেয়ে কম দাম\n"
    "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
    "💥 ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট\n"
    "━━━━━━━━━━━━━━━━━━"
)

# ============================================================
# Database
# ============================================================
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id       INTEGER PRIMARY KEY,
        username      TEXT    DEFAULT '',
        first_name    TEXT    DEFAULT '',
        balance       REAL    DEFAULT 0.0,
        total_orders  INTEGER DEFAULT 0,
        total_spent   REAL    DEFAULT 0.0,
        total_deposit REAL    DEFAULT 0.0,
        is_banned     INTEGER DEFAULT 0,
        joined_at     TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER,
        service_key    TEXT,
        service_name   TEXT,
        link           TEXT,
        quantity       INTEGER,
        amount         REAL,
        cost           REAL,
        profit         REAL,
        panel_order_id TEXT,
        status         TEXT DEFAULT 'Processing',
        created_at     TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deposits (
        dep_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        amount     REAL,
        phone      TEXT,
        pay_ref    TEXT DEFAULT '',
        status     TEXT DEFAULT 'Pending',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
        log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id   INTEGER,
        action     TEXT,
        target_id  INTEGER,
        detail     TEXT,
        created_at TEXT
    )""")
    conn.commit(); conn.close()
    logging.info("✅ DB ready.")

def db_create_user(uid, uname, fname):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id,username,first_name,balance,total_orders,total_spent,total_deposit,is_banned,joined_at) VALUES(?,?,?,0,0,0,0,0,?)",
        (uid, uname or "", fname or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.execute("UPDATE users SET username=?,first_name=? WHERE user_id=?", (uname or "", fname or "", uid))
    conn.commit(); conn.close()

def db_get_user(uid):
    conn = get_conn()
    r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close(); return r

def db_get_balance(uid):
    conn = get_conn()
    r = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close(); return round(r[0], 2) if r else 0.0

def db_update_balance(uid, amt):
    conn = get_conn()
    conn.execute("UPDATE users SET balance=ROUND(balance+?,2) WHERE user_id=?", (amt, uid))
    conn.commit(); conn.close()

def db_is_banned(uid):
    conn = get_conn()
    r = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close(); return bool(r[0]) if r else False

def db_save_order(uid, svc_key, svc_name, link, qty, amount, cost, panel_id):
    profit = round(amount - cost, 2)
    conn = get_conn(); c = conn.cursor()
    c.execute(
        "INSERT INTO orders(user_id,service_key,service_name,link,quantity,amount,cost,profit,panel_order_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,'Processing',?)",
        (uid, svc_key, svc_name, link, qty, amount, cost, profit, str(panel_id),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    oid = c.lastrowid
    conn.execute("UPDATE users SET total_orders=total_orders+1, total_spent=ROUND(total_spent+?,2) WHERE user_id=?", (amount, uid))
    conn.commit(); conn.close(); return oid

def db_get_orders(uid, limit=5):
    conn = get_conn()
    rows = conn.execute(
        "SELECT order_id,service_name,quantity,amount,status,created_at FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT ?",
        (uid, limit)
    ).fetchall()
    conn.close(); return rows

def db_save_deposit(uid, amt, phone):
    conn = get_conn(); c = conn.cursor()
    c.execute(
        "INSERT INTO deposits(user_id,amount,phone,status,created_at) VALUES(?,?,?,'Pending',?)",
        (uid, amt, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    did = c.lastrowid; conn.commit(); conn.close(); return did

def db_all_users(limit=50, offset=0):
    conn = get_conn()
    rows = conn.execute(
        "SELECT user_id,username,first_name,balance,total_orders,total_spent,total_deposit,is_banned,joined_at FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    conn.close(); return rows

def db_count_users():
    conn = get_conn()
    r = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close(); return r

def db_stats():
    conn = get_conn()
    u   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    o   = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    op  = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Processing'").fetchone()[0]
    oc  = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
    rv  = conn.execute("SELECT SUM(amount) FROM orders").fetchone()[0] or 0
    pr  = conn.execute("SELECT SUM(profit) FROM orders").fetchone()[0] or 0
    dp  = conn.execute("SELECT SUM(amount) FROM deposits WHERE status='Completed'").fetchone()[0] or 0
    bn  = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    conn.close(); return u, o, op, oc, rv, pr, dp, bn

def db_ban_user(uid, ban=True):
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=? WHERE user_id=?", (1 if ban else 0, uid))
    conn.commit(); conn.close()

def db_admin_log(admin_id, action, target_id, detail):
    conn = get_conn()
    conn.execute(
        "INSERT INTO admin_logs(admin_id,action,target_id,detail,created_at) VALUES(?,?,?,?,?)",
        (admin_id, action, target_id, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit(); conn.close()

def db_search_user(query):
    conn = get_conn(); q = f"%{query}%"
    rows = conn.execute(
        "SELECT user_id,username,first_name,balance,total_orders,is_banned FROM users WHERE username LIKE ? OR first_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?",
        (q, q, q)
    ).fetchall()
    conn.close(); return rows

# ============================================================
# SMM Panel
# ============================================================
def smm_add_order(service_id, link, qty):
    try:
        r = requests.post(SMM_PANEL_URL, data={
            "key": SMM_PANEL_KEY, "action": "add",
            "service": service_id, "link": link, "quantity": qty
        }, timeout=20)
        j = r.json(); return j.get("order"), j.get("error")
    except Exception as e:
        return None, str(e)

def smm_order_status(order_id):
    try:
        r = requests.post(SMM_PANEL_URL, data={
            "key": SMM_PANEL_KEY, "action": "status", "order": order_id
        }, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def smm_balance():
    try:
        r = requests.post(SMM_PANEL_URL, data={"key": SMM_PANEL_KEY, "action": "balance"}, timeout=15)
        j = r.json(); return j.get("balance","N/A"), j.get("currency","BDT")
    except:
        return "N/A", "N/A"

# ============================================================
# AutoPay
# ============================================================
def make_payment(uid, amt, phone):
    payload = json.dumps({
        "success_url": f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "cancel_url":  f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "metadata":    {"phone": phone, "user_id": str(uid)},
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
            resp = requests.post(AUTOPAY_URL, headers=hdrs, data=payload, timeout=30)
            j    = resp.json()
            url  = (j.get("payment_url") or j.get("url") or
                    (j.get("data") or {}).get("payment_url"))
            if url: return url, j
            if attempt == 2: return None, j
        except requests.exceptions.Timeout:
            if attempt == 2:
                return None, "Payment server সাড়া দিচ্ছে না। কিছুক্ষণ পর চেষ্টা করুন।"
        except Exception as e:
            return None, str(e)
    return None, "সর্বোচ্চ চেষ্টা শেষ।"

# ============================================================
# Helpers
# ============================================================
def find_svc(key):
    for cat in SERVICES.values():
        if key in cat["items"]: return cat["items"][key]
    return None

async def is_member(bot, uid):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked","banned"]: return False
        except: return False
    return True

async def typing(bot, chat_id):
    try: await bot.send_chat_action(chat_id, "typing")
    except: pass

# ============================================================
# /start
# ============================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db_create_user(u.id, u.username, u.first_name)
    ctx.user_data.clear()
    await typing(ctx.bot, update.effective_chat.id)

    if db_is_banned(u.id):
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    if not await is_member(ctx.bot, u.id):
        kb = [[InlineKeyboardButton("✅ Joined — চেক করো", callback_data="check_join")]]
        await update.message.reply_text(
            "⛔ বট ব্যবহারের আগে আমাদের চ্যানেল গুলোতে জয়েন করুন ⬇️\n\n"
            "➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
            reply_markup=InlineKeyboardMarkup(kb)); return

    await update.message.reply_text(
        f"{WELCOME_MSG}\n\nস্বাগতম, {u.first_name}! 👋", reply_markup=MAIN_KB)

# ============================================================
# /admin
# ============================================================
ADMIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("👥 All Users"),    KeyboardButton("🔍 Search User")],
     [KeyboardButton("📊 Full Stats"),   KeyboardButton("📦 All Orders")],
     [KeyboardButton("💳 Add Balance"),  KeyboardButton("🚫 Ban User")],
     [KeyboardButton("✅ Unban User"),    KeyboardButton("📢 Broadcast")],
     [KeyboardButton("💼 Panel Balance"),KeyboardButton("🔙 Admin Exit")]],
    resize_keyboard=True
)

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u.id != ADMIN_ID:
        await update.message.reply_text("❌ শুধুমাত্র Admin!"); return
    await typing(ctx.bot, update.effective_chat.id)
    u2, o, op, oc, rv, pr, dp, bn = db_stats()
    bal, cur = smm_balance()
    await update.message.reply_text(
        f"🔐 Admin Panel — {BOT_NAME}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 মোট ইউজার: {u2} | 🚫 Banned: {bn}\n"
        f"📦 মোট অর্ডার: {o}\n"
        f"⏳ Processing: {op} | ✅ Completed: {oc}\n"
        f"💰 Revenue: {rv:.2f}৳\n"
        f"📈 Profit: {pr:.2f}৳\n"
        f"💳 Deposits: {dp:.2f}৳\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥️ Panel: {bal} {cur}",
        reply_markup=ADMIN_KB)
    ctx.user_data["admin_mode"] = True

# ============================================================
# /addbalance /ban /unban /broadcast /myorders /stats
# ============================================================
async def cmd_addbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin!"); return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        db_update_balance(tid, amt); nb = db_get_balance(tid)
        db_admin_log(update.effective_user.id, "addbalance", tid, f"+{amt}")
        await update.message.reply_text(f"✅ User {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
        try:
            await ctx.bot.send_message(tid,
                f"✅ আপনার অ্যাকাউন্টে {amt} টাকা যোগ হয়েছে!\n💰 নতুন ব্যালেন্স: {nb:.2f} টাকা")
        except: pass
    except Exception as e:
        await update.message.reply_text(f"Usage: /addbalance <uid> <amount>\nError: {e}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    u2, o, op, oc, rv, pr, dp, bn = db_stats()
    bal, cur = smm_balance()
    await update.message.reply_text(
        f"📊 {BOT_NAME} Stats\n━━━━━━━━━━━━\n"
        f"👥 Users: {u2} | 🚫 Banned: {bn}\n"
        f"📦 Orders: {o} | ⏳ Processing: {op}\n"
        f"💰 Revenue: {rv:.2f}৳\n"
        f"📈 Profit: {pr:.2f}৳\n"
        f"💳 Deposits: {dp:.2f}৳\n"
        f"🖥️ Panel: {bal} {cur}")

async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban_user(tid, True)
        db_admin_log(update.effective_user.id, "ban", tid, "banned")
        await update.message.reply_text(f"🚫 User {tid} banned.")
    except Exception as e:
        await update.message.reply_text(f"Usage: /ban <uid>\nError: {e}")

async def cmd_unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban_user(tid, False)
        db_admin_log(update.effective_user.id, "unban", tid, "unbanned")
        await update.message.reply_text(f"✅ User {tid} unbanned.")
    except Exception as e:
        await update.message.reply_text(f"Usage: /unban <uid>\nError: {e}")

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /broadcast <msg>"); return
    msg  = " ".join(ctx.args)
    conn = get_conn()
    uids = [r[0] for r in conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]
    conn.close()
    sent = fail = 0
    await update.message.reply_text(f"📢 Sending to {len(uids)} users...")
    for uid in uids:
        try:
            await ctx.bot.send_message(uid, f"📢 {BOT_NAME}\n━━━━━━━━━━━━\n{msg}")
            sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Done! Sent: {sent} | Failed: {fail}")

async def cmd_myorders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user; rows = db_get_orders(u.id, 10)
    if not rows: await update.message.reply_text("📦 কোনো অর্ডার নেই।"); return
    msg = f"📦 আপনার সর্বশেষ অর্ডার\n━━━━━━━━━━━━━━━\n"
    for r in rows:
        e = "✅" if r[4]=="Completed" else "⏳" if r[4]=="Processing" else "❌"
        msg += f"{e} #{r[0]} — {r[1]}\n   🔢 {r[2]:,} | 💸 {r[3]:.2f}৳\n   📅 {r[5][:16]}\n─────────\n"
    await update.message.reply_text(msg)

# ============================================================
# Callbacks
# ============================================================
async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    d = q.data; u = q.from_user

    if d == "check_join":
        await typing(ctx.bot, q.message.chat.id)
        if not await is_member(ctx.bot, u.id):
            await q.answer("❌ দুটো চ্যানেলেই জয়েন করো!", show_alert=True); return
        await q.message.delete()
        db_create_user(u.id, u.username, u.first_name)
        await q.message.reply_text(f"{WELCOME_MSG}\n\nস্বাগতম, {u.first_name}! 👋", reply_markup=MAIN_KB)
        return

    if d == "confirm_order":
        await typing(ctx.bot, q.message.chat.id)
        svc  = find_svc(ctx.user_data.get("sel",""))
        link = ctx.user_data.get("link")
        qty  = ctx.user_data.get("qty")
        amt  = ctx.user_data.get("amt")
        cost = ctx.user_data.get("cost")

        if not all([svc, link, qty, amt]):
            await q.edit_message_text("❌ কিছু ভুল হয়েছে। আবার চেষ্টা করো।")
            ctx.user_data.clear(); return

        if db_get_balance(u.id) < amt:
            await q.edit_message_text(
                f"❌ ব্যালেন্স কম!\n💰 আছে: {db_get_balance(u.id):.2f}৳\n💸 দরকার: {amt:.2f}৳\n\n💳 ডিপোজিট করো।")
            ctx.user_data.clear(); return

        await q.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে...")
        pid, err = smm_add_order(svc["service_id"], link, qty)

        if err and not pid:
            await q.edit_message_text(
                f"❌ অর্ডার ব্যর্থ!\nকারণ: {err}\n\n🆘 @RKXPremiumZone"); return

        db_update_balance(u.id, -amt)
        oid = db_save_order(u.id, ctx.user_data.get("sel"), svc["name"], link, qty, amt, cost or 0, str(pid or "N/A"))
        nb  = db_get_balance(u.id)

        await q.edit_message_text(
            f"✅ অর্ডার সফল!\n━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"└➤ Order ID: {oid}\n└➤ User ID: {u.id}\n"
            f"└➤ Status: Processing ⏳\n└➤ Service: {svc['name']}\n"
            f"└➤ Ordered: {qty:,}\n└➤ Link: Private\n"
            f"└➤ খরচ: {amt:.2f}৳\n└➤ বাকি: {nb:.2f}৳\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USERNAME}")

        try:
            ustr = f"@{u.username}" if u.username else u.first_name
            await ctx.bot.send_message(LOG_CHANNEL,
                f"📌 {BOT_NAME} Notification\n🎯 New {svc['name']} Order\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
                f"└➤ Order ID: {oid}\n└➤ User: {ustr} ({u.id})\n"
                f"└➤ Status: ✅\n└➤ Qty: {qty:,}\n└➤ Amount: {amt:.2f}৳\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USERNAME}")
        except: pass
        ctx.user_data.clear(); return

    if d == "cancel_order":
        ctx.user_data.clear()
        await q.edit_message_text("❌ অর্ডার বাতিল।"); return

    if d.startswith("admin_user_"):
        tid = int(d.replace("admin_user_",""))
        row = db_get_user(tid)
        if not row: await q.answer("User not found!", show_alert=True); return
        uid, uname, fname, bal, orders, spent, dep, banned, joined = row
        ustr = f"@{uname}" if uname else fname
        orders_rows = db_get_orders(tid, 3)
        order_txt = "".join([f"  #{r[0]} {r[1][:25]} | {r[2]:,} | {r[3]:.2f}৳ | {r[4]}\n" for r in orders_rows]) or "  নেই"
        kb = [
            [InlineKeyboardButton("💰 Add Bal", callback_data=f"adm_ab_{tid}"),
             InlineKeyboardButton("🚫 Ban",     callback_data=f"adm_bn_{tid}")],
            [InlineKeyboardButton("✅ Unban",   callback_data=f"adm_ub_{tid}"),
             InlineKeyboardButton("🔙 Back",    callback_data="adm_back")]
        ]
        ban_str = " 🚫BANNED" if banned else ""
        await q.edit_message_text(
            f"👤 {ustr}{ban_str}\n🆔 {tid}\n💰 {bal:.2f}৳ | 📦 {orders} orders\n"
            f"💸 Spent: {spent:.2f}৳ | 💳 Dep: {dep:.2f}৳\n📅 {joined[:10] if joined else 'N/A'}\n\n"
            f"📦 Recent:\n{order_txt}",
            reply_markup=InlineKeyboardMarkup(kb)); return

    if d.startswith("adm_ab_"):
        tid = int(d.replace("adm_ab_",""))
        ctx.user_data["admin_addbal_target"] = tid
        ctx.user_data["admin_step"] = "addbal_amt"
        await q.edit_message_text(f"💰 User {tid} এর জন্য কত টাকা যোগ করবে?"); return

    if d.startswith("adm_bn_"):
        tid = int(d.replace("adm_bn_",""))
        db_ban_user(tid, True)
        db_admin_log(update.effective_user.id, "ban", tid, "via panel")
        await q.answer(f"🚫 {tid} banned!", show_alert=True); return

    if d.startswith("adm_ub_"):
        tid = int(d.replace("adm_ub_",""))
        db_ban_user(tid, False)
        db_admin_log(update.effective_user.id, "unban", tid, "via panel")
        await q.answer(f"✅ {tid} unbanned!", show_alert=True); return

    if d == "adm_back":
        await q.edit_message_text("Admin panel এ ফিরুন।"); return

# ============================================================
# Admin step handler
# ============================================================
async def handle_admin_step(update, ctx, t, adm):
    u = update.effective_user

    if adm == "search_user":
        rows = db_search_user(t)
        if not rows:
            await update.message.reply_text("❌ কেউ পাওয়া যায়নি।")
            ctx.user_data.pop("admin_step", None); return
        msg = f"🔍 ফলাফল ({len(rows)}):\n━━━━━━━━━━━━\n"
        kb  = []
        for r in rows:
            uid2, uname2, fname2, bal2, orders2, banned2 = r
            ustr2 = f"@{uname2}" if uname2 else fname2
            ban2  = "🚫" if banned2 else "✅"
            msg  += f"{ban2} {ustr2} | {uid2} | {bal2:.0f}৳ | {orders2} orders\n"
            kb.append([InlineKeyboardButton(f"{ban2} {ustr2} ({uid2})", callback_data=f"admin_user_{uid2}")])
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        ctx.user_data.pop("admin_step", None); return

    if adm == "addbal_uid":
        if not t.isdigit():
            await update.message.reply_text("❌ সঠিক User ID দাও!"); return
        ctx.user_data["admin_addbal_target"] = int(t)
        ctx.user_data["admin_step"] = "addbal_amt"
        await update.message.reply_text(f"💰 User {t} কত টাকা যোগ করবে?"); return

    if adm == "addbal_amt":
        try:
            amt = float(t); tid = ctx.user_data.get("admin_addbal_target")
            db_update_balance(tid, amt); nb = db_get_balance(tid)
            db_admin_log(u.id, "addbalance", tid, f"+{amt}")
            await update.message.reply_text(f"✅ {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
            try: await ctx.bot.send_message(tid, f"✅ আপনার অ্যাকাউন্টে {amt} টাকা যোগ হয়েছে!\n💰 নতুন ব্যালেন্স: {nb:.2f} টাকা")
            except: pass
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
        ctx.user_data.pop("admin_step", None)
        ctx.user_data.pop("admin_addbal_target", None); return

    if adm == "ban_uid":
        if not t.isdigit():
            await update.message.reply_text("❌ সঠিক User ID দাও!"); return
        tid = int(t); db_ban_user(tid, True)
        db_admin_log(u.id, "ban", tid, "banned")
        await update.message.reply_text(f"🚫 User {tid} banned.")
        ctx.user_data.pop("admin_step", None); return

    if adm == "unban_uid":
        if not t.isdigit():
            await update.message.reply_text("❌ সঠিক User ID দাও!"); return
        tid = int(t); db_ban_user(tid, False)
        db_admin_log(u.id, "unban", tid, "unbanned")
        await update.message.reply_text(f"✅ User {tid} unbanned.")
        ctx.user_data.pop("admin_step", None); return

    if adm == "broadcast_msg":
        conn = get_conn()
        uids = [r[0] for r in conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]
        conn.close()
        sent = fail = 0
        await update.message.reply_text(f"📢 Sending to {len(uids)} users...")
        for uid2 in uids:
            try:
                await ctx.bot.send_message(uid2, f"📢 {BOT_NAME}\n━━━━━━━━━━━━\n{t}")
                sent += 1
            except: fail += 1
            await asyncio.sleep(0.05)
        await update.message.reply_text(f"✅ Done! Sent: {sent} | Failed: {fail}")
        ctx.user_data.pop("admin_step", None); return

# ============================================================
# Admin button handler
# ============================================================
async def handle_admin_buttons(update, ctx, t):
    u = update.effective_user

    if t == "👥 All Users":
        rows  = db_all_users(25, 0)
        total = db_count_users()
        msg   = f"👥 সকল ইউজার (মোট: {total})\n━━━━━━━━━━━━━━━━━━━━\n"
        kb    = []
        for row in rows:
            uid2, uname2, fname2, bal2, orders2, spent2, dep2, banned2, joined2 = row
            ustr2  = f"@{uname2}" if uname2 else fname2
            bmark2 = "🚫" if banned2 else "✅"
            msg   += f"{bmark2} {ustr2} | {uid2} | {bal2:.0f}৳\n"
            kb.append([InlineKeyboardButton(f"{bmark2} {ustr2} ({uid2})", callback_data=f"admin_user_{uid2}")])
        await update.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb[:20]))
        return True

    if t == "🔍 Search User":
        ctx.user_data["admin_step"] = "search_user"
        await update.message.reply_text("🔍 Username, Name বা User ID লিখো:"); return True

    if t == "📊 Full Stats":
        u2, o, op, oc, rv, pr, dp, bn = db_stats()
        bal, cur = smm_balance()
        await update.message.reply_text(
            f"📊 Full Stats — {BOT_NAME}\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Users: {u2} | 🚫 Banned: {bn}\n"
            f"📦 Orders: {o} | ⏳: {op} | ✅: {oc}\n"
            f"💰 Revenue: {rv:.2f}৳\n📈 Profit: {pr:.2f}৳\n💳 Deposits: {dp:.2f}৳\n"
            f"🖥️ Panel: {bal} {cur}")
        return True

    if t == "📦 All Orders":
        conn = get_conn()
        rows = conn.execute(
            "SELECT o.order_id,u.username,u.first_name,o.service_name,o.quantity,o.amount,o.profit,o.status "
            "FROM orders o JOIN users u ON o.user_id=u.user_id ORDER BY o.order_id DESC LIMIT 20"
        ).fetchall(); conn.close()
        if not rows: await update.message.reply_text("📦 কোনো অর্ডার নেই।"); return True
        msg = "📦 সর্বশেষ ২০ অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            ustr2 = f"@{r[1]}" if r[1] else r[2]
            e2    = "✅" if r[7]=="Completed" else "⏳"
            msg  += f"{e2} #{r[0]} | {ustr2}\n   {r[3][:25]} | {r[4]:,} | {r[5]:.2f}৳ | profit:{r[6]:.2f}৳\n"
        await update.message.reply_text(msg[:4000]); return True

    if t == "💳 Add Balance":
        ctx.user_data["admin_step"] = "addbal_uid"
        await update.message.reply_text("💳 User ID দাও:"); return True

    if t == "🚫 Ban User":
        ctx.user_data["admin_step"] = "ban_uid"
        await update.message.reply_text("🚫 Ban করার User ID দাও:"); return True

    if t == "✅ Unban User":
        ctx.user_data["admin_step"] = "unban_uid"
        await update.message.reply_text("✅ Unban করার User ID দাও:"); return True

    if t == "📢 Broadcast":
        ctx.user_data["admin_step"] = "broadcast_msg"
        await update.message.reply_text("📢 সকল ইউজারকে কী মেসেজ পাঠাবে?"); return True

    if t == "💼 Panel Balance":
        bal, cur = smm_balance()
        await update.message.reply_text(f"💼 Panel Balance\n━━━━━━━━━━━━\n💰 {bal} {cur}"); return True

    return False

# ============================================================
# Main Text Handler
# ============================================================
async def txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u    = update.effective_user
    t    = (update.message.text or "").strip()
    step = ctx.user_data.get("step")
    ds   = ctx.user_data.get("dstep")
    adm  = ctx.user_data.get("admin_step")

    await typing(ctx.bot, update.effective_chat.id)

    if db_is_banned(u.id) and u.id != ADMIN_ID:
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    # Admin steps
    if adm and u.id == ADMIN_ID:
        await handle_admin_step(update, ctx, t, adm); return

    # Admin buttons
    if ctx.user_data.get("admin_mode") and u.id == ADMIN_ID:
        if t == "🔙 Admin Exit":
            ctx.user_data.clear()
            await update.message.reply_text("✅ Admin Panel বন্ধ।", reply_markup=MAIN_KB); return
        if await handle_admin_buttons(update, ctx, t): return

    # Main menu
    if t in ("🔙 Main Menu", "🔙 Admin Exit"):
        ctx.user_data.clear()
        await update.message.reply_text(WELCOME_MSG, reply_markup=MAIN_KB); return

    # ── 🛒 ORDER ─────────────────────────────────────────────
    if t == "🛒 Order":
        if not await is_member(ctx.bot, u.id):
            await cmd_start(update, ctx); return
        ctx.user_data.clear(); ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 সার্ভিস বেছে নিন 👇", reply_markup=order_cat_kb()); return

    # Category selected
    if t in CAT_KEY_MAP and ctx.user_data.get("in_order"):
        cat_key = CAT_KEY_MAP[t]
        ctx.user_data["cat"] = cat_key
        await update.message.reply_text(
            f"{SERVICES[cat_key]['emoji']} {SERVICES[cat_key]['name']} Services 👇",
            reply_markup=make_service_kb(cat_key)); return

    if t == "🔙 Back":
        ctx.user_data.pop("cat",  None)
        ctx.user_data.pop("step", None)
        ctx.user_data.pop("sel",  None)
        ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 সার্ভিস বেছে নিন 👇", reply_markup=order_cat_kb()); return

    if t == "❌ বাতিল":
        ctx.user_data.clear()
        await update.message.reply_text("❌ বাতিল।", reply_markup=MAIN_KB); return

    # Service selected
    if t in SERVICE_NAME_MAP and ctx.user_data.get("in_order"):
        svc_key = SERVICE_NAME_MAP[t]
        svc     = find_svc(svc_key)
        bal     = db_get_balance(u.id)
        ctx.user_data["sel"]  = svc_key
        ctx.user_data["step"] = "link"
        await update.message.reply_text(
            f"✅ {svc['name']}\n\n"
            f"ℹ️ {svc.get('desc','')}\n\n"
            f"💰 আপনার ব্যালেন্স: {bal:.2f}৳\n"
            f"📊 মূল্য: {svc['price_per_1k']}৳ / ১০০০\n"
            f"📉 সর্বনিম্ন: {svc['min']:,}\n"
            f"📈 সর্বোচ্চ: {svc['max']:,}\n\n"
            f"🔗 পোস্ট / প্রোফাইল লিংক দাও:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)); return

    # Order: link
    if step == "link":
        if not t.startswith("http"):
            await update.message.reply_text("❌ সঠিক লিংক দাও! http দিয়ে শুরু হতে হবে।"); return
        ctx.user_data["link"] = t; ctx.user_data["step"] = "qty"
        svc = find_svc(ctx.user_data.get("sel",""))
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n💰 ব্যালেন্স: {db_get_balance(u.id):.2f}৳\n"
            f"📊 {svc['price_per_1k']}৳/১০০০ | Min: {svc['min']:,} | Max: {svc['max']:,}\n\n"
            f"🔢 পরিমাণ লিখো:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ বাতিল")]], resize_keyboard=True)); return

    # Order: quantity
    if step == "qty":
        if not t.isdigit(): await update.message.reply_text("❌ শুধু সংখ্যা লিখো!"); return
        qty = int(t); svc = find_svc(ctx.user_data.get("sel",""))
        if qty < svc["min"] or qty > svc["max"]:
            await update.message.reply_text(f"❌ পরিমাণ {svc['min']:,}–{svc['max']:,} এর মধ্যে হতে হবে!"); return
        amt  = round((qty / 1000) * svc["price_per_1k"], 2)
        cost = round((qty / 1000) * svc["cost_per_1k"], 2)
        bal  = db_get_balance(u.id)
        if bal < amt:
            await update.message.reply_text(
                f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳\n\n💳 ডিপোজিট করো।",
                reply_markup=MAIN_KB)
            ctx.user_data.clear(); return
        ctx.user_data.update({"qty": qty, "amt": amt, "cost": cost, "step": "confirm"})
        kb = [[InlineKeyboardButton("✅ কনফার্ম করো", callback_data="confirm_order"),
               InlineKeyboardButton("❌ বাতিল",        callback_data="cancel_order")]]
        await update.message.reply_text(
            f"📋 অর্ডার সারসংক্ষেপ\n━━━━━━━━━━━━━━━\n"
            f"🛒 {svc['name']}\n🔗 {ctx.user_data['link']}\n"
            f"🔢 {qty:,} | 💸 {amt:.2f}৳\n"
            f"💰 অর্ডারের পরে ব্যালেন্স: {bal-amt:.2f}৳\n"
            f"━━━━━━━━━━━━━━━\n✅ কনফার্ম করবে?",
            reply_markup=InlineKeyboardMarkup(kb)); return

    # ── 💰 BALANCE ────────────────────────────────────────────
    if t == "💰 Balance":
        row = db_get_user(u.id)
        bal2 = row[3] if row else 0.0; tot2 = row[4] if row else 0
        sp2  = row[5] if row else 0.0; dep2 = row[6] if row else 0.0
        await update.message.reply_text(
            f"💰 আপনার অ্যাকাউন্ট\n━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {u.id}\n📛 Name: {u.first_name}\n"
            f"💵 ব্যালেন্স: {bal2:.2f}৳\n"
            f"📦 মোট অর্ডার: {tot2}\n💸 মোট খরচ: {sp2:.2f}৳\n"
            f"💳 মোট ডিপোজিট: {dep2:.2f}৳\n━━━━━━━━━━━━━━━"); return

    # ── 💳 DEPOSIT ────────────────────────────────────────────
    if t == "💳 Deposit":
        ctx.user_data.clear(); ctx.user_data["dstep"] = "amt"
        await update.message.reply_text(
            "💳 ডিপোজিট\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\nসংখ্যা লিখো:"); return

    if t == "📦 Order Status":
        rows = db_get_orders(u.id)
        if not rows: await update.message.reply_text("📦 এখনো কোনো অর্ডার নেই।"); return
        msg = "📦 সর্বশেষ ৫টি অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            e3 = "✅" if r[4]=="Completed" else "⏳" if r[4]=="Processing" else "❌"
            msg += f"{e3} #{r[0]} | {r[1]}\n   🔢 {r[2]:,} | 💸 {r[3]:.2f}৳\n   📅 {r[5][:16]}\n─────────\n"
        await update.message.reply_text(msg); return

    if t == "🆘 Support":
        await update.message.reply_text(
            f"🆘 সাপোর্ট — {BOT_NAME}\n━━━━━━━━━━━━━━━\n"
            f"📩 Telegram: @RKXPremiumZone\n📢 Channel: @RKXSMMZONE\n\n"
            f"⏰ সকাল ৯টা – রাত ১১টা\n🤖 {BOT_USERNAME}"); return

    if t == "📋 Price & Info":
        msg = f"📋 {BOT_NAME}\n━━━━━━━━━━━━━━━\n"
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for s in cat["items"].values():
                msg += f"  • {s['name']}: {s['price_per_1k']}৳/১০০০ (Min:{s['min']:,})\n"
        msg += "\n━━━━━━━━━━━━━━━\n⚡ অর্ডার ৩০ মিনিটে কমপ্লিট"
        await update.message.reply_text(msg); return

    # ── Deposit: amount ──────────────────────────────────────
    if ds == "amt":
        if not t.isdigit() or int(t) < 10:
            await update.message.reply_text("❌ সর্বনিম্ন ১০ টাকা!"); return
        ctx.user_data["damt"] = int(t); ctx.user_data["dstep"] = "phone"
        await update.message.reply_text("📱 ফোন নম্বর দাও:\n(যেটা দিয়ে পেমেন্ট করবে)"); return

    # ── Deposit: phone ───────────────────────────────────────
    if ds == "phone":
        amt4  = ctx.user_data.get("damt"); phone = t
        dep_id = db_save_deposit(u.id, amt4, phone)
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        url, raw = make_payment(u.id, amt4, phone)
        ctx.user_data.clear()
        if url:
            kb = [[InlineKeyboardButton("💙 এখানে পেমেন্ট করো", url=url)]]
            await update.message.reply_text(
                f"✅ পেমেন্ট লিংক তৈরি!\n━━━━━━━━━━━━━━━\n"
                f"💰 পরিমাণ: {amt4} টাকা\n📱 ফোন: {phone}\n🆔 Ref: #{dep_id}\n━━━━━━━━━━━━━━━\n"
                f"⬇️ নিচের নীল বাটনে পেমেন্ট করো\n✅ সফল হলে ব্যালেন্স অটো যোগ হবে।",
                reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(
                f"❌ পেমেন্ট লিংক তৈরি হয়নি।\nকারণ: {raw}\n\n🆘 @RKXPremiumZone")
        return

# ============================================================
# Main
# ============================================================
def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        level=logging.INFO
    )
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("admin",      cmd_admin))
    app.add_handler(CommandHandler("addbalance", cmd_addbalance))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("ban",        cmd_ban))
    app.add_handler(CommandHandler("unban",      cmd_unban))
    app.add_handler(CommandHandler("broadcast",  cmd_broadcast))
    app.add_handler(CommandHandler("myorders",   cmd_myorders))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, txt))
    logging.info(f"✅ {BOT_NAME} চালু!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
