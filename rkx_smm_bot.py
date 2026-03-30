import logging
import os
import requests
import json
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
SMM_PANEL_URL     = "https://your-smm-panel.com/api/v2"

# ✅ আপডেট করা Payment Keys
AUTOPAY_API_KEY    = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_SECRET_KEY = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_BRAND_KEY  = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
AUTOPAY_DEVICE_KEY = "Dl6Vzy8T33bbGiUybEDYffaZqp2ZxtJ0cP0Ss1HB"
AUTOPAY_URL        = "https://pay.rxpay.top/api/payment/create"

# ============================================================
# সার্ভিস লিস্ট
# ============================================================
SERVICES = {
    "tiktok": {
        "name": "🎵 TikTok",
        "items": {
            "tiktok_views":     {"name": "👁️ TikTok Views",     "service_id": "1001", "price_per_1k": 5,  "min": 1000, "max": 1000000},
            "tiktok_likes":     {"name": "❤️ TikTok Likes",     "service_id": "1002", "price_per_1k": 10, "min": 100,  "max": 500000},
            "tiktok_followers": {"name": "👥 TikTok Followers", "service_id": "1003", "price_per_1k": 15, "min": 100,  "max": 100000},
        }
    },
    "facebook": {
        "name": "📘 Facebook",
        "items": {
            "fb_likes":     {"name": "👍 Facebook Page Likes",  "service_id": "2001", "price_per_1k": 12, "min": 100,  "max": 100000},
            "fb_followers": {"name": "👥 Facebook Followers",   "service_id": "2002", "price_per_1k": 10, "min": 100,  "max": 100000},
            "fb_views":     {"name": "👁️ Facebook Video Views", "service_id": "2003", "price_per_1k": 4,  "min": 1000, "max": 1000000},
        }
    },
    "telegram": {
        "name": "✈️ Telegram",
        "items": {
            "tg_members":   {"name": "👥 Telegram Members",    "service_id": "3001", "price_per_1k": 30, "min": 100, "max": 50000},
            "tg_views":     {"name": "👁️ Telegram Post Views", "service_id": "3002", "price_per_1k": 5,  "min": 100, "max": 500000},
            "tg_reactions": {"name": "💎 Telegram Reactions",  "service_id": "3003", "price_per_1k": 20, "min": 100, "max": 10000},
        }
    },
    "youtube": {
        "name": "🎬 YouTube",
        "items": {
            "yt_views":       {"name": "👁️ YouTube Views",       "service_id": "4001", "price_per_1k": 8,  "min": 1000, "max": 1000000},
            "yt_likes":       {"name": "👍 YouTube Likes",       "service_id": "4002", "price_per_1k": 15, "min": 100,  "max": 100000},
            "yt_subscribers": {"name": "🔔 YouTube Subscribers", "service_id": "4003", "price_per_1k": 50, "min": 100,  "max": 50000},
        }
    },
    "instagram": {
        "name": "📸 Instagram",
        "items": {
            "ig_followers": {"name": "👥 Instagram Followers", "service_id": "5001", "price_per_1k": 18, "min": 100,  "max": 100000},
            "ig_likes":     {"name": "❤️ Instagram Likes",     "service_id": "5002", "price_per_1k": 8,  "min": 100,  "max": 100000},
            "ig_views":     {"name": "👁️ Instagram Views",     "service_id": "5003", "price_per_1k": 4,  "min": 1000, "max": 1000000},
        }
    },
}

# ============================================================
# Keyboards
# ============================================================
MAIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("🛒 Order"),   KeyboardButton("💰 Balance")],
     [KeyboardButton("💳 Deposit"), KeyboardButton("📦 Order Status")],
     [KeyboardButton("🆘 Support"), KeyboardButton("📋 Price & Info")]],
    resize_keyboard=True
)

def order_cat_kb():
    """Order category — permanent keyboard"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🎵 TikTok"),     KeyboardButton("✈️ Telegram")],
         [KeyboardButton("🎬 YouTube"),    KeyboardButton("📘 Facebook")],
         [KeyboardButton("📸 Instagram")],
         [KeyboardButton("🔙 Main Menu")]],
        resize_keyboard=True
    )

def tiktok_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👁️ TikTok Views")],
         [KeyboardButton("❤️ TikTok Likes")],
         [KeyboardButton("👥 TikTok Followers")],
         [KeyboardButton("🔙 Back")]],
        resize_keyboard=True
    )

def facebook_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👍 Facebook Page Likes")],
         [KeyboardButton("👥 Facebook Followers")],
         [KeyboardButton("👁️ Facebook Video Views")],
         [KeyboardButton("🔙 Back")]],
        resize_keyboard=True
    )

def telegram_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👥 Telegram Members")],
         [KeyboardButton("👁️ Telegram Post Views")],
         [KeyboardButton("💎 Telegram Reactions")],
         [KeyboardButton("🔙 Back")]],
        resize_keyboard=True
    )

def youtube_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👁️ YouTube Views")],
         [KeyboardButton("👍 YouTube Likes")],
         [KeyboardButton("🔔 YouTube Subscribers")],
         [KeyboardButton("🔙 Back")]],
        resize_keyboard=True
    )

def instagram_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👥 Instagram Followers")],
         [KeyboardButton("❤️ Instagram Likes")],
         [KeyboardButton("👁️ Instagram Views")],
         [KeyboardButton("🔙 Back")]],
        resize_keyboard=True
    )

# Service name → key mapping
SERVICE_NAME_MAP = {
    "👁️ TikTok Views":       "tiktok_views",
    "❤️ TikTok Likes":       "tiktok_likes",
    "👥 TikTok Followers":   "tiktok_followers",
    "👍 Facebook Page Likes":"fb_likes",
    "👥 Facebook Followers": "fb_followers",
    "👁️ Facebook Video Views":"fb_views",
    "👥 Telegram Members":   "tg_members",
    "👁️ Telegram Post Views":"tg_views",
    "💎 Telegram Reactions": "tg_reactions",
    "👁️ YouTube Views":      "yt_views",
    "👍 YouTube Likes":      "yt_likes",
    "🔔 YouTube Subscribers":"yt_subscribers",
    "👥 Instagram Followers":"ig_followers",
    "❤️ Instagram Likes":    "ig_likes",
    "👁️ Instagram Views":    "ig_views",
}

WELCOME = (
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
def init_db():
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT,
        balance REAL DEFAULT 0.0, total_orders INTEGER DEFAULT 0, joined_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, service_key TEXT, service_name TEXT,
        link TEXT, quantity INTEGER, amount REAL,
        panel_order_id TEXT, status TEXT DEFAULT 'Processing', created_at TEXT)""")
    conn.commit(); conn.close()

def create_user(uid, uname):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute("INSERT OR IGNORE INTO users(user_id,username,balance,total_orders,joined_at) VALUES(?,?,0,0,?)",
                 (uid, uname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()

def get_balance(uid):
    conn = sqlite3.connect("rkx_bot.db")
    r = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close(); return r[0] if r else 0.0

def update_balance(uid, amt):
    conn = sqlite3.connect("rkx_bot.db")
    conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit(); conn.close()

def save_order(uid, svc_key, svc_name, link, qty, amt, panel_id):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""INSERT INTO orders(user_id,service_key,service_name,link,quantity,amount,panel_order_id,status,created_at)
                 VALUES(?,?,?,?,?,?,?,'Processing',?)""",
              (uid, svc_key, svc_name, link, qty, amt, str(panel_id),
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    oid = c.lastrowid
    conn.execute("UPDATE users SET total_orders=total_orders+1 WHERE user_id=?", (uid,))
    conn.commit(); conn.close(); return oid

def get_recent_orders(uid):
    conn = sqlite3.connect("rkx_bot.db")
    rows = conn.execute("""SELECT order_id,service_name,quantity,amount,status,created_at
                           FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT 5""", (uid,)).fetchall()
    conn.close(); return rows

def get_stats():
    conn = sqlite3.connect("rkx_bot.db")
    u = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    o = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    r = conn.execute("SELECT SUM(amount) FROM orders").fetchone()[0] or 0
    conn.close(); return u, o, r

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
            if m.status in ["left", "kicked", "banned"]: return False
        except: return False
    return True

def place_order(sid, link, qty):
    try:
        r = requests.post(SMM_PANEL_URL,
                          data={"key": SMM_PANEL_KEY, "action": "add",
                                "service": sid, "link": link, "quantity": qty},
                          timeout=20)
        j = r.json(); return j.get("order"), j.get("error")
    except Exception as e: return None, str(e)

# ✅ আপডেট করা Payment function — retry + device key
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
            r = requests.post(AUTOPAY_URL, headers=hdrs, data=payload, timeout=30).json()
            url = (r.get("payment_url") or
                   r.get("url") or
                   (r.get("data") or {}).get("payment_url"))
            if url: return url, r
            # যদি url না পাই কিন্তু response আসে
            return None, r
        except requests.exceptions.Timeout:
            if attempt < 2:
                continue
            return None, "Payment server সাড়া দিচ্ছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।"
        except Exception as e:
            return None, str(e)
    return None, "সর্বোচ্চ চেষ্টা শেষ। সাপোর্টে যোগাযোগ করুন।"

# ============================================================
# /start
# ============================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    create_user(u.id, u.username or u.first_name)
    ctx.user_data.clear()

    # ✅ typing effect
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    if not await is_member(ctx.bot, u.id):
        kb = [[InlineKeyboardButton("✅ Joined — চেক করো", callback_data="check_join")]]
        await update.message.reply_text(
            "⛔ বট ব্যবহারের আগে আমাদের চ্যানেল গুলোতে জয়েন করুন ⬇️\n\n"
            "➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
            reply_markup=InlineKeyboardMarkup(kb))
        return

    await update.message.reply_text(WELCOME, reply_markup=MAIN_KB)

# ============================================================
# Callbacks (শুধু join check এর জন্য)
# ============================================================
async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    u = q.from_user

    if q.data == "check_join":
        await ctx.bot.send_chat_action(q.message.chat.id, "typing")
        if not await is_member(ctx.bot, u.id):
            await q.answer("❌ দুটো চ্যানেলেই জয়েন করো!", show_alert=True)
            return
        await q.message.delete()
        await q.message.reply_text(WELCOME, reply_markup=MAIN_KB)

    elif q.data == "confirm_order":
        await handle_confirm_order(q, ctx)

    elif q.data == "cancel_order":
        ctx.user_data.clear()
        await q.edit_message_text("❌ অর্ডার বাতিল।")

# ============================================================
# Confirm Order (inline থেকে call হয়)
# ============================================================
async def handle_confirm_order(q, ctx):
    u = q.from_user
    svc = find_svc(ctx.user_data.get("sel", ""))
    link = ctx.user_data.get("link")
    qty  = ctx.user_data.get("qty")
    amt  = ctx.user_data.get("amt")

    if not all([svc, link, qty, amt]):
        await q.edit_message_text("❌ কিছু ভুল হয়েছে। আবার চেষ্টা করো।")
        ctx.user_data.clear(); return

    if get_balance(u.id) < amt:
        await q.edit_message_text("❌ ব্যালেন্স কম! আগে ডিপোজিট করো।")
        ctx.user_data.clear(); return

    await q.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে...")
    await ctx.bot.send_chat_action(q.message.chat.id, "typing")

    pid, err = place_order(svc["service_id"], link, qty)
    if err and not pid:
        await q.edit_message_text(f"❌ অর্ডার ব্যর্থ!\nকারণ: {err}"); return

    update_balance(u.id, -amt)
    oid = save_order(u.id, ctx.user_data.get("sel"), svc["name"], link, qty, amt, str(pid or "N/A"))
    nb  = get_balance(u.id)

    await q.edit_message_text(
        f"✅ অর্ডার সফল!\n━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
        f"└➤ Order ID: {oid}\n└➤ User ID: {u.id}\n"
        f"└➤ Status: Success ✅\n└➤ Ordered: {qty:,}\n"
        f"└➤ Order Link: Private\n└➤ খরচ: {amt:.2f}৳\n"
        f"└➤ বাকি ব্যালেন্স: {nb:.2f}৳\n"
        f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 Bot: {BOT_USERNAME}")

    try:
        await ctx.bot.send_message(LOG_CHANNEL,
            f"📌 RKX SMM ZONE Notification\n🎯 New {svc['name']} Order\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"└➤ Order ID: {oid}\n└➤ User ID: {u.id}\n"
            f"└➤ Status: Success ✅\n└➤ Ordered: {qty:,}\n"
            f"└➤ Order Link: Private\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 Bot: {BOT_USERNAME}")
    except: pass
    ctx.user_data.clear()

# ============================================================
# Main Text Handler
# ============================================================
async def txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u  = update.effective_user
    t  = update.message.text.strip()
    step = ctx.user_data.get("step")
    ds   = ctx.user_data.get("dstep")

    # typing effect সবসময়
    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    # ── Main Menu ────────────────────────────────────────────
    if t == "🛒 Order":
        if not await is_member(ctx.bot, u.id):
            await cmd_start(update, ctx); return
        ctx.user_data.clear()
        ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 Select your service 👇", reply_markup=order_cat_kb())
        return

    if t == "🔙 Main Menu":
        ctx.user_data.clear()
        await update.message.reply_text(WELCOME, reply_markup=MAIN_KB)
        return

    # ── Category selection ───────────────────────────────────
    if t == "🎵 TikTok" and ctx.user_data.get("in_order"):
        ctx.user_data["cat"] = "tiktok"
        await update.message.reply_text("🎵 TikTok Services 👇", reply_markup=tiktok_kb())
        return

    if t == "📘 Facebook" and ctx.user_data.get("in_order"):
        ctx.user_data["cat"] = "facebook"
        await update.message.reply_text("📘 Facebook Services 👇", reply_markup=facebook_kb())
        return

    if t == "✈️ Telegram" and ctx.user_data.get("in_order"):
        ctx.user_data["cat"] = "telegram"
        await update.message.reply_text("✈️ Telegram Services 👇", reply_markup=telegram_kb())
        return

    if t == "🎬 YouTube" and ctx.user_data.get("in_order"):
        ctx.user_data["cat"] = "youtube"
        await update.message.reply_text("🎬 YouTube Services 👇", reply_markup=youtube_kb())
        return

    if t == "📸 Instagram" and ctx.user_data.get("in_order"):
        ctx.user_data["cat"] = "instagram"
        await update.message.reply_text("📸 Instagram Services 👇", reply_markup=instagram_kb())
        return

    if t == "🔙 Back":
        ctx.user_data.pop("cat", None)
        ctx.user_data.pop("step", None)
        ctx.user_data["in_order"] = True
        await update.message.reply_text("🏪 Select your service 👇", reply_markup=order_cat_kb())
        return

    # ── Service selected ─────────────────────────────────────
    if t in SERVICE_NAME_MAP and ctx.user_data.get("in_order"):
        svc_key = SERVICE_NAME_MAP[t]
        svc = find_svc(svc_key)
        bal = get_balance(u.id)
        ctx.user_data["sel"]  = svc_key
        ctx.user_data["step"] = "link"
        await update.message.reply_text(
            f"✅ {svc['name']}\n\n"
            f"💰 আপনার ব্যালেন্স: {bal:.2f}৳\n"
            f"📊 মূল্য: {svc['price_per_1k']}৳/১০০০\n"
            f"📉 Min: {svc['min']:,} | 📈 Max: {svc['max']:,}\n\n"
            f"🔗 পোস্ট/প্রোফাইল লিংক দাও:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("❌ বাতিল")]],
                resize_keyboard=True))
        return

    if t == "❌ বাতিল":
        ctx.user_data.clear()
        await update.message.reply_text("❌ বাতিল।", reply_markup=MAIN_KB)
        return

    # ── Order: link ──────────────────────────────────────────
    if step == "link":
        if not t.startswith("http"):
            await update.message.reply_text("❌ সঠিক লিংক দাও! http দিয়ে শুরু হতে হবে।")
            return
        svc = find_svc(ctx.user_data.get("sel", ""))
        ctx.user_data["link"] = t
        ctx.user_data["step"] = "qty"
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n"
            f"💰 ব্যালেন্স: {get_balance(u.id):.2f}৳\n"
            f"📊 মূল্য: {svc['price_per_1k']}৳/১০০০\n"
            f"📉 Min: {svc['min']:,} | 📈 Max: {svc['max']:,}\n\n"
            f"🔢 পরিমাণ লিখো (যেমন: 1000):",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("❌ বাতিল")]],
                resize_keyboard=True))
        return

    # ── Order: quantity ──────────────────────────────────────
    if step == "qty":
        if not t.isdigit():
            await update.message.reply_text("❌ শুধু সংখ্যা লিখো!"); return
        qty = int(t)
        svc = find_svc(ctx.user_data.get("sel", ""))
        if qty < svc["min"] or qty > svc["max"]:
            await update.message.reply_text(
                f"❌ পরিমাণ {svc['min']:,}–{svc['max']:,} এর মধ্যে হতে হবে!"); return
        amt = round((qty / 1000) * svc["price_per_1k"], 2)
        bal = get_balance(u.id)
        if bal < amt:
            await update.message.reply_text(
                f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳\n\n💳 ডিপোজিট করো।",
                reply_markup=MAIN_KB)
            ctx.user_data.clear(); return
        ctx.user_data["qty"] = qty
        ctx.user_data["amt"] = amt
        ctx.user_data["step"] = "confirm"
        kb = [[InlineKeyboardButton("✅ কনফার্ম", callback_data="confirm_order"),
               InlineKeyboardButton("❌ বাতিল",   callback_data="cancel_order")]]
        await update.message.reply_text(
            f"📋 অর্ডার সারসংক্ষেপ\n━━━━━━━━━━━━━━━\n"
            f"🛒 {svc['name']}\n🔗 {ctx.user_data['link']}\n"
            f"🔢 {qty:,}\n💸 {amt:.2f}৳\n━━━━━━━━━━━━━━━\n✅ কনফার্ম করবে?",
            reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Balance ──────────────────────────────────────────────
    if t == "💰 Balance":
        conn = sqlite3.connect("rkx_bot.db")
        r = conn.execute("SELECT balance,total_orders FROM users WHERE user_id=?",
                         (u.id,)).fetchone()
        conn.close()
        bal, tot = (r[0], r[1]) if r else (0.0, 0)
        await update.message.reply_text(
            f"💰 আপনার অ্যাকাউন্ট\n━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {u.id}\n💵 ব্যালেন্স: {bal:.2f}৳\n"
            f"📦 মোট অর্ডার: {tot}\n━━━━━━━━━━━━━━━")
        return

    # ── Deposit ──────────────────────────────────────────────
    if t == "💳 Deposit":
        ctx.user_data.clear()
        ctx.user_data["dstep"] = "amt"
        await update.message.reply_text(
            "💳 ডিপোজিট\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\nশুধু সংখ্যা লিখো:")
        return

    if t == "📦 Order Status":
        rows = get_recent_orders(u.id)
        if not rows:
            await update.message.reply_text("📦 এখনো কোনো অর্ডার নেই।"); return
        msg = "📦 সর্বশেষ ৫টি অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            msg += (f"🆔 #{r[0]} | 🛒 {r[1]}\n"
                    f"🔢 {r[2]:,} | 💸 {r[3]:.2f}৳ | 📊 {r[4]}\n"
                    f"📅 {r[5]}\n─────────────\n")
        await update.message.reply_text(msg); return

    if t == "🆘 Support":
        await update.message.reply_text(
            "🆘 সাপোর্ট\n━━━━━━━━━━━━━━━\n"
            "📩 Telegram: @RKXPremiumZone\n📢 Channel: @RKXSMMZONE\n\n"
            "⏰ সকাল ৯টা – রাত ১১টা")
        return

    if t == "📋 Price & Info":
        msg = "📋 সার্ভিস মূল্য তালিকা\n━━━━━━━━━━━━━━━\n"
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for s in cat["items"].values():
                msg += f"  • {s['name']}: {s['price_per_1k']}৳/১০০০\n"
        msg += "\n━━━━━━━━━━━━━━━\n⚡ সকল অর্ডার ৩০ মিনিটে কমপ্লিট"
        await update.message.reply_text(msg); return

    # ── Deposit: amount ──────────────────────────────────────
    if ds == "amt":
        if not t.isdigit() or int(t) < 10:
            await update.message.reply_text("❌ সর্বনিম্ন ১০ টাকা!"); return
        ctx.user_data["damt"]  = int(t)
        ctx.user_data["dstep"] = "phone"
        await update.message.reply_text("📱 ফোন নম্বর দাও (যেটা দিয়ে পেমেন্ট করবে):")
        return

    # ── Deposit: phone ───────────────────────────────────────
    if ds == "phone":
        amt   = ctx.user_data.get("damt")
        phone = t
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
        url, raw = make_payment(u.id, amt, phone)
        ctx.user_data.clear()
        if url:
            await update.message.reply_text(
                f"✅ পেমেন্ট লিংক তৈরি!\n\n"
                f"💰 পরিমাণ: {amt} টাকা\n📱 ফোন: {phone}\n\n"
                f"⬇️ নিচের বাটনে পেমেন্ট করো:\nসফল হলে ব্যালেন্স অটো যোগ হবে।",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("💳 এখানে পেমেন্ট করো", url=url)]]))
        else:
            await update.message.reply_text(
                f"❌ পেমেন্ট লিংক তৈরি হয়নি।\n"
                f"কারণ: {raw}\n\n"
                f"🆘 সাপোর্টে যোগাযোগ করুন: @RKXPremiumZone")
        return

# ============================================================
# Admin
# ============================================================
async def cmd_addbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin!"); return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        update_balance(tid, amt); nb = get_balance(tid)
        await update.message.reply_text(f"✅ {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
        await ctx.bot.send_message(tid,
            f"✅ আপনার অ্যাকাউন্টে {amt} টাকা যোগ হয়েছে!\n💰 নতুন ব্যালেন্স: {nb:.2f} টাকা")
    except Exception as e:
        await update.message.reply_text(f"Usage: /addbalance <uid> <amount>\nError: {e}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    u, o, r = get_stats()
    await update.message.reply_text(
        f"📊 Bot Stats\n━━━━━━━━━━━━\n"
        f"👥 মোট ইউজার: {u}\n📦 মোট অর্ডার: {o}\n💰 মোট রেভিনিউ: {r:.2f}৳")

# ============================================================
# Main
# ============================================================
def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("addbalance", cmd_addbalance))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, txt))
    logging.info("✅ RKX SMM Bot চালু!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
