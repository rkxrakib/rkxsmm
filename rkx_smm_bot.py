import logging
import os
import asyncio
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
# ✅ CONFIG — Railway/Render এ Environment Variables থেকে নেবে
#    অথবা নিচে সরাসরি লিখে দাও
# ============================================================
BOT_TOKEN   = os.environ.get("BOT_TOKEN",   "8331448370:AAGEdB0uDT0NnvN3DjFtuyGMRO2W8zuINYg")
ADMIN_ID    = int(os.environ.get("ADMIN_ID", "8387741218"))
SMM_PANEL_KEY = os.environ.get("SMM_PANEL_KEY", "YOUR_SMM_PANEL_API_KEY")

LOG_CHANNEL        = "@RKXSMMZONE"
REQUIRED_CHANNELS  = ["@RKXPremiumZone", "@RKXSMMZONE"]
BOT_USERNAME       = "@RKXSMMbot"
SMM_PANEL_URL      = "https://your-smm-panel.com/api/v2"   # তোমার প্যানেল URL

# AutoPay Config (তোমার key গুলো সরাসরি আছে)
AUTOPAY_API_KEY    = "EEBStiWfMC0sEVm0QyZPihVekfEF7JLIpLuwLcNGK5OPS5XsQA"
AUTOPAY_SECRET_KEY = "EEBStiWfMC0sEVm0QyZPihVekfEF7JLIpLuwLcNGK5OPS5XsQA"
AUTOPAY_BRAND_KEY  = "bDDu1ET75JxV3wlAQ8bmufxBU2lIqEfvNroIprvR"
AUTOPAY_URL        = "https://pay.rxpay.top/api/payment/create"

# ============================================================
# সার্ভিস লিস্ট — service_id তোমার SMM প্যানেল অনুযায়ী পরিবর্তন করো
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
# Database
# ============================================================
def init_db():
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0.0,
        total_orders INTEGER DEFAULT 0,
        joined_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        service_key TEXT,
        service_name TEXT,
        link TEXT,
        quantity INTEGER,
        amount REAL,
        panel_order_id TEXT,
        status TEXT DEFAULT 'Processing',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        payment_ref TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(user_id, username):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id,username,balance,total_orders,joined_at) VALUES (?,?,0,0,?)",
              (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0.0

def update_balance(user_id, amount):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def save_order(user_id, service_key, service_name, link, quantity, amount, panel_order_id):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""INSERT INTO orders
        (user_id,service_key,service_name,link,quantity,amount,panel_order_id,status,created_at)
        VALUES (?,?,?,?,?,?,?,'Processing',?)""",
        (user_id, service_key, service_name, link, quantity, amount,
         str(panel_order_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    order_id = c.lastrowid
    c.execute("UPDATE users SET total_orders = total_orders + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return order_id

def get_recent_orders(user_id, limit=5):
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("""SELECT order_id,service_name,quantity,amount,status,created_at
                 FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT ?""",
              (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

# ============================================================
# SMM Panel API
# ============================================================
def place_smm_order(service_id, link, quantity):
    try:
        data = {
            "key": SMM_PANEL_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        response = requests.post(SMM_PANEL_URL, data=data, timeout=15)
        result = response.json()
        return result.get("order"), result.get("error")
    except Exception as e:
        return None, str(e)

# ============================================================
# AutoPay
# ============================================================
def create_payment(user_id, amount, phone=""):
    try:
        payload = json.dumps({
            "success_url": f"https://t.me/{BOT_USERNAME.replace('@','')}",
            "cancel_url":  f"https://t.me/{BOT_USERNAME.replace('@','')}",
            "metadata": {"phone": phone, "user_id": str(user_id)},
            "amount": str(amount)
        })
        headers = {
            "API-KEY":     AUTOPAY_API_KEY,
            "Content-Type":"application/json",
            "SECRET-KEY":  AUTOPAY_SECRET_KEY,
            "BRAND-KEY":   AUTOPAY_BRAND_KEY
        }
        response = requests.post(AUTOPAY_URL, headers=headers, data=payload, timeout=15)
        result = response.json()
        pay_url = result.get("payment_url") or result.get("url") or result.get("data", {}).get("payment_url")
        return pay_url, result
    except Exception as e:
        return None, str(e)

# ============================================================
# Channel Membership Check
# ============================================================
async def check_membership(bot, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked", "banned"]:
                return False
        except:
            return False
    return True

# ============================================================
# Helper: find service info by key
# ============================================================
def find_service(svc_key):
    for cat in SERVICES.values():
        if svc_key in cat["items"]:
            return cat["items"][svc_key]
    return None

# ============================================================
# /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username or user.first_name)
    context.user_data.clear()

    if not await check_membership(context.bot, user.id):
        text = (
            "⛔ বট ব্যবহারের আগে আমাদের চ্যানেল গুলোতে জয়েন করুন ⬇️\n\n"
            "➡️ @RKXPremiumZone\n"
            "➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন"
        )
        kb = [[InlineKeyboardButton("✅ Joined — চেক করো", callback_data="check_join")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    await send_main_menu(update.message, update.effective_user.first_name)

async def send_main_menu(msg_obj, first_name=""):
    text = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🏡 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 মার্কেটের সবচেয়ে কম দাম\n"
        "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
        "💥 ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛒 Order"),        KeyboardButton("💰 Balance")],
            [KeyboardButton("💳 Deposit"),       KeyboardButton("📦 Order Status")],
            [KeyboardButton("🆘 Support"),       KeyboardButton("📋 Price & Info")],
        ],
        resize_keyboard=True
    )
    await msg_obj.reply_text(text, reply_markup=kb)

# ============================================================
# Callbacks
# ============================================================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    # ── Join check ──────────────────────────────────────────
    if data == "check_join":
        if not await check_membership(context.bot, user.id):
            await query.answer("❌ এখনো জয়েন করোনি! দুটো চ্যানেলেই জয়েন করো।", show_alert=True)
            return
        await query.message.delete()
        await send_main_menu(query.message, user.first_name)
        return

    # ── Back to main service menu ────────────────────────────
    if data == "back_to_cats":
        await query.edit_message_text("🏪 Select your service 👇", reply_markup=_service_keyboard())
        return

    # ── Category selected ────────────────────────────────────
    if data.startswith("cat_"):
        cat_key = data[4:]
        cat = SERVICES.get(cat_key)
        if not cat:
            return
        kb = [[InlineKeyboardButton(s["name"], callback_data=f"svc_{k}")]
              for k, s in cat["items"].items()]
        kb.append([InlineKeyboardButton("🔙 Return", callback_data="back_to_cats")])
        await query.edit_message_text(
            f"✅ {cat['name']} Services 👇\nসার্ভিস বেছে নিন:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ── Service selected → ask for link ─────────────────────
    if data.startswith("svc_"):
        svc_key = data[4:]
        svc = find_service(svc_key)
        if not svc:
            return
        balance = get_balance(user.id)
        context.user_data["selected_service"] = svc_key
        context.user_data["order_step"] = "waiting_link"
        text = (
            f"✅ {svc['name']}\n\n"
            f"💰 আপনার ব্যালেন্স: {balance:.2f} টাকা\n"
            f"📊 মূল্য: {svc['price_per_1k']} টাকা / ১০০০\n"
            f"📉 সর্বনিম্ন: {svc['min']:,}\n"
            f"📈 সর্বোচ্চ: {svc['max']:,}\n\n"
            f"🔗 পোস্ট / প্রোফাইল লিংক দাও:"
        )
        kb = [[InlineKeyboardButton("❌ বাতিল", callback_data="cancel_order")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ── Confirm order ────────────────────────────────────────
    if data == "confirm_order":
        svc_key  = context.user_data.get("selected_service")
        link     = context.user_data.get("order_link")
        quantity = context.user_data.get("order_quantity")
        amount   = context.user_data.get("order_amount")
        svc      = find_service(svc_key)

        if not all([svc_key, link, quantity, amount, svc]):
            await query.edit_message_text("❌ কিছু একটা ভুল হয়েছে। আবার চেষ্টা করো।")
            context.user_data.clear()
            return

        balance = get_balance(user.id)
        if balance < amount:
            await query.edit_message_text("❌ ব্যালেন্স কম! আগে ডিপোজিট করো।")
            context.user_data.clear()
            return

        await query.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে... একটু অপেক্ষা করো।")

        panel_order_id, error = place_smm_order(svc["service_id"], link, quantity)
        if error and not panel_order_id:
            await query.edit_message_text(f"❌ অর্ডার ব্যর্থ!\nকারণ: {error}")
            return

        update_balance(user.id, -amount)
        order_id    = save_order(user.id, svc_key, svc["name"], link, quantity, amount, str(panel_order_id or "N/A"))
        new_balance = get_balance(user.id)

        success_msg = (
            f"✅ অর্ডার সফল!\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"└➤ Order ID: {order_id}\n"
            f"└➤ User ID: {user.id}\n"
            f"└➤ Status: Success ✅\n"
            f"└➤ Ordered: {quantity:,}\n"
            f"└➤ Order Link: Private\n"
            f"└➤ খরচ: {amount:.2f} টাকা\n"
            f"└➤ বাকি ব্যালেন্স: {new_balance:.2f} টাকা\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"🤖 Bot: {BOT_USERNAME}"
        )
        await query.edit_message_text(success_msg)

        # Log channel notification
        try:
            log_msg = (
                f"📌 RKX SMM ZONE Notification\n"
                f"🎯 New {svc['name']} Order Submitted\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
                f"└➤ Order ID: {order_id}\n"
                f"└➤ User ID: {user.id}\n"
                f"└➤ Status: Success ✅\n"
                f"└➤ Ordered: {quantity:,}\n"
                f"└➤ Order Link: Private\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
                f"🤖 Bot: {BOT_USERNAME}"
            )
            await context.bot.send_message(LOG_CHANNEL, log_msg)
        except Exception:
            pass

        context.user_data.clear()
        return

    # ── Cancel order ─────────────────────────────────────────
    if data == "cancel_order":
        context.user_data.clear()
        await query.edit_message_text("❌ অর্ডার বাতিল করা হয়েছে।")
        return

# ============================================================
# Text / Message Handler
# ============================================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    txt    = update.message.text.strip()
    step   = context.user_data.get("order_step")
    d_step = context.user_data.get("deposit_step")

    # ── Menu buttons ─────────────────────────────────────────
    if txt == "🛒 Order":
        if not await check_membership(context.bot, user.id):
            await start(update, context); return
        await update.message.reply_text("🏪 Select your service 👇",
                                        reply_markup=InlineKeyboardMarkup(_service_keyboard_list()))
        return

    if txt == "💰 Balance":
        balance = get_balance(user.id)
        conn = sqlite3.connect("rkx_bot.db")
        c = conn.cursor()
        c.execute("SELECT total_orders FROM users WHERE user_id=?", (user.id,))
        row = c.fetchone()
        conn.close()
        total = row[0] if row else 0
        await update.message.reply_text(
            f"💰 আপনার অ্যাকাউন্ট\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {user.id}\n"
            f"💵 ব্যালেন্স: {balance:.2f} টাকা\n"
            f"📦 মোট অর্ডার: {total}\n"
            f"━━━━━━━━━━━━━━━"
        )
        return

    if txt == "💳 Deposit":
        context.user_data.clear()
        context.user_data["deposit_step"] = "waiting_amount"
        await update.message.reply_text(
            "💳 ডিপোজিট\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\nশুধু সংখ্যা লিখো, যেমন: 100"
        )
        return

    if txt == "📦 Order Status":
        rows = get_recent_orders(user.id)
        if not rows:
            await update.message.reply_text("📦 এখনো কোনো অর্ডার নেই।")
            return
        msg = "📦 সর্বশেষ ৫টি অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            msg += (f"🆔 Order #{r[0]}\n🛒 {r[1]}\n"
                    f"🔢 {r[2]:,} | 💸 {r[3]:.2f}৳\n"
                    f"📊 {r[4]} | 📅 {r[5]}\n─────────────\n")
        await update.message.reply_text(msg)
        return

    if txt == "🆘 Support":
        await update.message.reply_text(
            "🆘 সাপোর্ট\n━━━━━━━━━━━━━━━\n"
            "📩 Telegram: @RKXPremiumZone\n"
            "📢 Channel: @RKXSMMZONE\n\n"
            "⏰ সাপোর্ট সময়: সকাল ৯টা – রাত ১১টা"
        )
        return

    if txt == "📋 Price & Info":
        msg = "📋 সার্ভিস মূল্য তালিকা\n━━━━━━━━━━━━━━━\n"
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for s in cat["items"].values():
                msg += f"  • {s['name']}: {s['price_per_1k']}৳/১০০০\n"
        msg += "\n━━━━━━━━━━━━━━━\n⚡ সকল অর্ডার ৩০ মিনিটে কমপ্লিট"
        await update.message.reply_text(msg)
        return

    # ── Order flow: waiting for link ─────────────────────────
    if step == "waiting_link":
        if not txt.startswith("http"):
            await update.message.reply_text("❌ সঠিক লিংক দাও! লিংক http দিয়ে শুরু হতে হবে।")
            return
        svc = find_service(context.user_data.get("selected_service"))
        context.user_data["order_link"] = txt
        context.user_data["order_step"] = "waiting_quantity"
        balance = get_balance(user.id)
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n"
            f"💰 ব্যালেন্স: {balance:.2f} টাকা\n"
            f"📊 মূল্য: {svc['price_per_1k']} টাকা/১০০০\n"
            f"📉 Min: {svc['min']:,} | 📈 Max: {svc['max']:,}\n\n"
            f"🔢 এখন পরিমাণ লিখো (যেমন: 1000):"
        )
        return

    # ── Order flow: waiting for quantity ─────────────────────
    if step == "waiting_quantity":
        if not txt.isdigit():
            await update.message.reply_text("❌ শুধু সংখ্যা লিখো!")
            return
        quantity = int(txt)
        svc_key  = context.user_data.get("selected_service")
        link     = context.user_data.get("order_link")
        svc      = find_service(svc_key)

        if quantity < svc["min"] or quantity > svc["max"]:
            await update.message.reply_text(
                f"❌ পরিমাণ {svc['min']:,} থেকে {svc['max']:,} এর মধ্যে হতে হবে!")
            return

        amount  = round((quantity / 1000) * svc["price_per_1k"], 2)
        balance = get_balance(user.id)

        if balance < amount:
            await update.message.reply_text(
                f"❌ ব্যালেন্স কম!\n\n"
                f"💰 আপনার ব্যালেন্স: {balance:.2f} টাকা\n"
                f"💸 প্রয়োজন: {amount:.2f} টাকা\n\n"
                f"💳 ডিপোজিট করুন।"
            )
            context.user_data.clear()
            return

        context.user_data["order_quantity"] = quantity
        context.user_data["order_amount"]   = amount
        context.user_data["order_step"]     = "confirm"

        kb = [[
            InlineKeyboardButton("✅ কনফার্ম", callback_data="confirm_order"),
            InlineKeyboardButton("❌ বাতিল",   callback_data="cancel_order")
        ]]
        await update.message.reply_text(
            f"📋 অর্ডার সারসংক্ষেপ\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛒 সার্ভিস: {svc['name']}\n"
            f"🔗 লিংক: {link}\n"
            f"🔢 পরিমাণ: {quantity:,}\n"
            f"💸 মূল্য: {amount:.2f} টাকা\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ কনফার্ম করবে?",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ── Deposit flow: waiting amount ─────────────────────────
    if d_step == "waiting_amount":
        if not txt.isdigit() or int(txt) < 10:
            await update.message.reply_text("❌ সর্বনিম্ন ১০ টাকা!")
            return
        context.user_data["deposit_amount"] = int(txt)
        context.user_data["deposit_step"]   = "waiting_phone"
        await update.message.reply_text("📱 ফোন নম্বর দাও (যেটা দিয়ে পেমেন্ট করবে):")
        return

    # ── Deposit flow: waiting phone ──────────────────────────
    if d_step == "waiting_phone":
        amount = context.user_data.get("deposit_amount")
        phone  = txt
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")

        pay_url, raw = create_payment(user.id, amount, phone)
        context.user_data.clear()

        if pay_url:
            kb = [[InlineKeyboardButton("💳 এখানে পেমেন্ট করো", url=pay_url)]]
            await update.message.reply_text(
                f"✅ পেমেন্ট লিংক তৈরি!\n\n"
                f"💰 পরিমাণ: {amount} টাকা\n"
                f"📱 ফোন: {phone}\n\n"
                f"⬇️ নিচের বাটনে পেমেন্ট করো:\n"
                f"পেমেন্ট সফল হলে ব্যালেন্স অটো যোগ হবে।",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        else:
            await update.message.reply_text(
                f"❌ পেমেন্ট লিংক তৈরি হয়নি। সাপোর্টে যোগাযোগ করুন।\nDebug: {raw}"
            )
        return

# ============================================================
# Helper keyboards
# ============================================================
def _service_keyboard():
    return InlineKeyboardMarkup(_service_keyboard_list())

def _service_keyboard_list():
    return [
        [InlineKeyboardButton("🎵 TikTok Services",    callback_data="cat_tiktok"),
         InlineKeyboardButton("✈️ TeleGram Services",  callback_data="cat_telegram")],
        [InlineKeyboardButton("🎬 YouTube Services",   callback_data="cat_youtube"),
         InlineKeyboardButton("📘 FaceBook Services",  callback_data="cat_facebook")],
        [InlineKeyboardButton("📸 InstaGram Services", callback_data="cat_instagram")],
        [InlineKeyboardButton("🔙 Return",             callback_data="back_to_cats")],
    ]

# ============================================================
# Admin commands
# ============================================================
async def cmd_addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin!")
        return
    try:
        target = int(context.args[0])
        amount = float(context.args[1])
        update_balance(target, amount)
        new_bal = get_balance(target)
        await update.message.reply_text(f"✅ {target} এর ব্যালেন্সে {amount}৳ যোগ হয়েছে। নতুন: {new_bal:.2f}৳")
        await context.bot.send_message(
            target,
            f"✅ আপনার অ্যাকাউন্টে {amount} টাকা যোগ হয়েছে!\n💰 নতুন ব্যালেন্স: {new_bal:.2f} টাকা"
        )
    except Exception as e:
        await update.message.reply_text(f"Usage: /addbalance <user_id> <amount>\nError: {e}")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("rkx_bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders")
    orders = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM orders")
    revenue = c.fetchone()[0] or 0
    conn.close()
    await update.message.reply_text(
        f"📊 Bot Stats\n━━━━━━━━━━━━\n"
        f"👥 মোট ইউজার: {users}\n"
        f"📦 মোট অর্ডার: {orders}\n"
        f"💰 মোট রেভিনিউ: {revenue:.2f}৳"
    )

# ============================================================
# Main
# ============================================================
def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("addbalance", cmd_addbalance))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logging.info("✅ RKX SMM Bot চালু হয়েছে!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
