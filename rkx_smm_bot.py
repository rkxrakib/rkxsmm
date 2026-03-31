"""
╔══════════════════════════════════════════╗
║   𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 — Telegram Bot          ║
║   Full Featured SMM Bot                  ║
║   Panel: rxsmm.top | Pay: rxpay.top      ║
╚══════════════════════════════════════════╝
"""
import logging, os, requests, json, sqlite3, asyncio
from datetime import datetime, time as dtime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
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
DAILY_MSG_HOUR    = 6   # সকাল ৬টা (UTC — বাংলাদেশ UTC+6 হলে 0 দাও)

# ═══════════════════════════════════════════════════════════
# ALL SERVICES — rxsmm.top real IDs + 50% markup
# ═══════════════════════════════════════════════════════════
SERVICES = {
    "tiktok": {
        "name": "🎵 TikTok", "emoji": "🎵",
        "items": {
            "tt_views1":   {"name":"👁️ TikTok Views [Fast]",      "service_id":"4233","cost":0.6145,"price":0.92, "min":100,  "max":10000000,"desc":"⚡ 1M-10M/Day | INSTANT"},
            "tt_views2":   {"name":"👁️ TikTok Views [Ultra]",     "service_id":"4234","cost":1.02,  "price":1.53, "min":100,  "max":2147483647,"desc":"⚡ 10M/Day | INSTANT"},
            "tt_likes1":   {"name":"❤️ TikTok Likes [NoRefill]",  "service_id":"4256","cost":2.91,  "price":4.37, "min":10,   "max":5000000,"desc":"⚡ 50K-100K/Day | INSTANT"},
            "tt_likes2":   {"name":"❤️ TikTok Likes [R30] ♻️",   "service_id":"4257","cost":3.16,  "price":4.74, "min":10,   "max":5000000,"desc":"♻️ 30 Days Refill"},
            "tt_likes3":   {"name":"❤️ TikTok Likes [Lifetime]♻️","service_id":"4261","cost":4.30,  "price":6.45, "min":10,   "max":5000000,"desc":"♻️ Lifetime Refill"},
            "tt_follow1":  {"name":"👥 TikTok Followers [Real]",  "service_id":"4323","cost":1.0,   "price":1.50, "min":50,   "max":160000,"desc":"✅ Real Stable | R15"},
            "tt_follow2":  {"name":"👥 TikTok Followers [R30]♻️", "service_id":"4325","cost":1.0,   "price":1.50, "min":50,   "max":160000,"desc":"♻️ 30 Days Refill"},
            "tt_comment":  {"name":"💬 TikTok Comments",          "service_id":"4271","cost":25.0,  "price":37.50,"min":10,   "max":5000,"desc":"Custom Comments"},
            "tt_shares":   {"name":"🔁 TikTok Shares",            "service_id":"4275","cost":5.0,   "price":7.50, "min":100,  "max":100000,"desc":"⚡ Fast Shares"},
        }
    },
    "facebook": {
        "name": "📘 Facebook", "emoji": "📘",
        "items": {
            "fb_like":     {"name":"👍 FB Post Like",     "service_id":"3701","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_love":     {"name":"❤️ FB Post Love",    "service_id":"3702","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_care":     {"name":"🤗 FB Post Care",    "service_id":"3703","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_haha":     {"name":"😂 FB Post HaHa",   "service_id":"3704","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_wow":      {"name":"😲 FB Post Wow",     "service_id":"3705","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_sad":      {"name":"😢 FB Post Sad",     "service_id":"3706","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_angry":    {"name":"😡 FB Post Angry",   "service_id":"3707","cost":20.30,"price":30.45,"min":10,  "max":500000,"desc":"🌍 WorldWide | 20K-50K/Day"},
            "fb_follow":   {"name":"👥 FB Followers",   "service_id":"1846","cost":23.49,"price":35.23,"min":100, "max":5000,"desc":"Profile/Page | Fast"},
        }
    },
    "telegram": {
        "name": "✈️ Telegram", "emoji": "✈️",
        "items": {
            "tg_mem1":    {"name":"👥 TG Members [Cheap]",     "service_id":"4817","cost":1.68, "price":2.52, "min":10,   "max":25000,"desc":"সস্তা | ~46hr"},
            "tg_mem2":    {"name":"👥 TG Members [HQ]",        "service_id":"4486","cost":1.0,  "price":1.50, "min":10,   "max":20000,"desc":"Premium+Online | HQ"},
            "tg_mem3":    {"name":"👥 TG Members [R7] ♻️",    "service_id":"4820","cost":6.28, "price":9.42, "min":1,    "max":100000,"desc":"♻️ 7 Days Refill"},
            "tg_mem4":    {"name":"👥 TG Members [R30] ♻️",   "service_id":"4822","cost":8.33, "price":12.50,"min":1,    "max":100000,"desc":"♻️ 30 Days Refill"},
            "tg_mem5":    {"name":"👥 TG Members [R90] ♻️",   "service_id":"4824","cost":9.58, "price":14.37,"min":100,  "max":1000000,"desc":"♻️ 90 Days Refill"},
            "tg_view1":   {"name":"👁️ TG Views [1 Post]",      "service_id":"4525","cost":0.23, "price":0.34, "min":50,   "max":20000,"desc":"⚡ INSTANT | MAX 1M"},
            "tg_view2":   {"name":"👁️ TG Views [Last 5]",      "service_id":"4555","cost":6.30, "price":9.45, "min":1000, "max":40000,"desc":"Last 5 Posts"},
            "tg_view3":   {"name":"👁️ TG Views [Last 10]",     "service_id":"4556","cost":12.59,"price":18.89,"min":1000, "max":40000,"desc":"Last 10 Posts"},
            "tg_view4":   {"name":"👁️ TG Views [Last 20]",     "service_id":"4557","cost":25.17,"price":37.75,"min":1000, "max":40000,"desc":"Last 20 Posts"},
            "tg_react1":  {"name":"💎 TG Mix React (+)",       "service_id":"4744","cost":20.98,"price":31.47,"min":10,   "max":1000000,"desc":"👍🤩🎉🔥❤️🥰 Mix Positive"},
            "tg_react2":  {"name":"👍 TG React Like",          "service_id":"4748","cost":20.98,"price":31.47,"min":10,   "max":1000000,"desc":"👍 Like Reactions"},
            "tg_react3":  {"name":"🔥 TG React Fire",          "service_id":"4752","cost":20.98,"price":31.47,"min":10,   "max":1000000,"desc":"🔥 Fire Reactions"},
            "tg_stars":   {"name":"⭐ TG Stars [Post]",        "service_id":"4509","cost":4.0,  "price":6.0,  "min":1,    "max":10000,"desc":"Telegram Stars"},
        }
    },
    "youtube": {
        "name": "🎬 YouTube", "emoji": "🎬",
        "items": {
            "yt_view1":   {"name":"👁️ YT Views [India]",         "service_id":"1908","cost":1.0,  "price":1.50, "min":1000, "max":1000000,"desc":"Adword | Display | 0-72hr"},
            "yt_view2":   {"name":"👁️ YT Views [Malaysia]",      "service_id":"1909","cost":1.0,  "price":1.50, "min":1000, "max":1000000,"desc":"Adword Skippable"},
            "yt_view3":   {"name":"👁️ YT Views [HQ]",            "service_id":"1916","cost":5.0,  "price":7.50, "min":500,  "max":100000,"desc":"High Quality Views"},
            "yt_like1":   {"name":"👍 YT Likes [HQ]",            "service_id":"1877","cost":25.0, "price":37.50,"min":20,   "max":5000,"desc":"Real | Fast"},
            "yt_sub1":    {"name":"🔔 YT Subscribers [Real]",    "service_id":"1914","cost":50.0, "price":75.0, "min":10,   "max":1000,"desc":"Real | Gradual | HQ"},
            "yt_sub2":    {"name":"🔔 YT Subscribers [Fast]",    "service_id":"1915","cost":100.0,"price":150.0,"min":10,   "max":5000,"desc":"Fast Delivery"},
            "yt_comment": {"name":"💬 YT Comments [Custom]",     "service_id":"1895","cost":40.0, "price":60.0, "min":5,    "max":1000,"desc":"Custom Comments"},
        }
    },
    "instagram": {
        "name": "📸 Instagram", "emoji": "📸",
        "items": {
            "ig_view1":   {"name":"👁️ IG Views [Fast]",           "service_id":"2015","cost":0.14, "price":0.20, "min":100,  "max":100000000,"desc":"⚡ 0-5 Min | 100K-1M/Day"},
            "ig_view2":   {"name":"👁️ IG Reel Views",             "service_id":"2017","cost":0.18, "price":0.27, "min":100,  "max":2147483647,"desc":"⚡ 0-5 Min | 10M/Day"},
            "ig_story":   {"name":"📖 IG Story Views",            "service_id":"2018","cost":0.50, "price":0.75, "min":100,  "max":100000,"desc":"⚡ INSTANT | Fast"},
            "ig_like1":   {"name":"❤️ IG Likes [HQ]",            "service_id":"2034","cost":16.23,"price":24.34,"min":100,  "max":1000000,"desc":"HQ | 0-30 Min | 10K/Day"},
            "ig_like2":   {"name":"❤️ IG Likes [Real]",          "service_id":"1836","cost":19.25,"price":28.87,"min":10,   "max":1000000,"desc":"Real Accounts | INSTANT"},
            "ig_follow1": {"name":"👥 IG Followers [Real]",       "service_id":"2135","cost":1.0,  "price":1.50, "min":10,   "max":1000,"desc":"100% Real | 0-15 Min"},
            "ig_follow2": {"name":"👥 IG Followers [Male]",       "service_id":"2136","cost":1.0,  "price":1.50, "min":10,   "max":5000,"desc":"Real Male | Fast"},
            "ig_follow3": {"name":"👥 IG Followers [HQ]",         "service_id":"2137","cost":1.0,  "price":1.50, "min":30,   "max":5000,"desc":"Very Good Quality"},
            "ig_comment": {"name":"💬 IG Comments [Emoji]",      "service_id":"2157","cost":1.0,  "price":1.50, "min":10,   "max":100,"desc":"MQ | Emojis | Fast"},
            "ig_share":   {"name":"🔁 IG Shares",                "service_id":"2152","cost":2.03, "price":3.04, "min":100,  "max":100000000,"desc":"⚡ 250K/Day | Fast"},
        }
    },
}

# Name → key map (auto-build)
SERVICE_NAME_MAP = {}
for _cat in SERVICES.values():
    for _k, _s in _cat["items"].items():
        SERVICE_NAME_MAP[_s["name"]] = _k

def find_svc(key):
    for cat in SERVICES.values():
        if key in cat["items"]: return cat["items"][key]
    return None

# ═══════════════════════════════════════════════════════════
# KEYBOARDS  — Telegram supports button colors via
#   InlineKeyboardButton only. ReplyKeyboard has no color.
#   We use InlineKeyboard for menus to get color effect.
# ═══════════════════════════════════════════════════════════
WELCOME_MSG = (
    "━━━━━━━━━━━━━━━━━━\n"
    "🏡 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 মার্কেটের সবচেয়ে কম দাম\n"
    "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
    "💥 ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট\n"
    "━━━━━━━━━━━━━━━━━━"
)

DAILY_MORNING_MSG = (
    "🌅 সুপ্রভাত! Good Morning!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"🏡 {BOT_NAME}\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 আজকেও সেরা দামে SMM সার্ভিস নিন!\n"
    "🛒 অর্ডার করতে /start দিন\n\n"
    "💡 আমাদের সার্ভিস:\n"
    "🎵 TikTok | 📘 Facebook\n"
    "✈️ Telegram | 🎬 YouTube | 📸 Instagram\n\n"
    "💳 ডিপোজিট করুন এবং এখনই অর্ডার করুন!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"🤖 Bot: @RKXSMMbot"
)

# Main menu — Inline buttons (colored look)
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Order",        callback_data="menu_order"),
         InlineKeyboardButton("💰 Balance",      callback_data="menu_balance")],
        [InlineKeyboardButton("💳 Deposit",      callback_data="menu_deposit"),
         InlineKeyboardButton("📦 Order Status", callback_data="menu_orders")],
        [InlineKeyboardButton("🆘 Support",      callback_data="menu_support"),
         InlineKeyboardButton("📋 Price & Info", callback_data="menu_price")],
    ])

# Category menu
def cat_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 TikTok",    callback_data="cat_tiktok"),
         InlineKeyboardButton("✈️ Telegram",  callback_data="cat_telegram")],
        [InlineKeyboardButton("🎬 YouTube",   callback_data="cat_youtube"),
         InlineKeyboardButton("📘 Facebook",  callback_data="cat_facebook")],
        [InlineKeyboardButton("📸 Instagram", callback_data="cat_instagram")],
        [InlineKeyboardButton("🔙 Back",      callback_data="back_main")],
    ])

def service_list_kb(cat_key):
    rows = []
    for k, s in SERVICES[cat_key]["items"].items():
        rows.append([InlineKeyboardButton(s["name"], callback_data=f"svc_{k}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="back_cats")])
    return InlineKeyboardMarkup(rows)

def confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ কনফার্ম করো", callback_data="confirm_order"),
         InlineKeyboardButton("❌ বাতিল",        callback_data="cancel_order")]
    ])

def cancel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ বাতিল", callback_data="cancel_order")]
    ])

def join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Joined — চেক করো", callback_data="check_join")]
    ])

# Admin keyboard (Reply for speed)
ADMIN_KB = ReplyKeyboardMarkup([
    [KeyboardButton("👥 All Users"),     KeyboardButton("🔍 Search User")],
    [KeyboardButton("📊 Full Stats"),    KeyboardButton("📦 All Orders")],
    [KeyboardButton("💳 Add Balance"),   KeyboardButton("🚫 Ban User")],
    [KeyboardButton("✅ Unban User"),     KeyboardButton("📢 Broadcast")],
    [KeyboardButton("💼 Panel Balance"), KeyboardButton("🔙 Admin Exit")],
], resize_keyboard=True)

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
def get_conn(): return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
        first_name TEXT DEFAULT '', balance REAL DEFAULT 0.0,
        total_orders INTEGER DEFAULT 0, total_spent REAL DEFAULT 0.0,
        total_deposit REAL DEFAULT 0.0, is_banned INTEGER DEFAULT 0,
        joined_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, service_key TEXT, service_name TEXT,
        link TEXT, quantity INTEGER, amount REAL, cost REAL, profit REAL,
        panel_order_id TEXT, status TEXT DEFAULT 'Processing', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS deposits (
        dep_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        amount REAL, phone TEXT, status TEXT DEFAULT 'Pending', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER,
        action TEXT, target_id INTEGER, detail TEXT, created_at TEXT)""")
    conn.commit(); conn.close()
    logging.info("✅ DB ready")

def db_upsert_user(uid, uname, fname):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO users(user_id,username,first_name,balance,total_orders,total_spent,total_deposit,is_banned,joined_at) VALUES(?,?,?,0,0,0,0,0,?)",
                 (uid, uname or "", fname or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("UPDATE users SET username=?,first_name=? WHERE user_id=?", (uname or "", fname or "", uid))
    conn.commit(); conn.close()

def db_get_user(uid):
    conn = get_conn(); r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone(); conn.close(); return r

def db_balance(uid):
    conn = get_conn(); r = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone(); conn.close()
    return round(r[0], 2) if r else 0.0

def db_add_balance(uid, amt):
    conn = get_conn(); conn.execute("UPDATE users SET balance=ROUND(balance+?,2) WHERE user_id=?", (amt, uid)); conn.commit(); conn.close()

def db_banned(uid):
    conn = get_conn(); r = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone(); conn.close()
    return bool(r[0]) if r else False

def db_save_order(uid, svc_key, svc_name, link, qty, amount, cost, panel_id):
    profit = round(amount - cost, 2)
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO orders(user_id,service_key,service_name,link,quantity,amount,cost,profit,panel_order_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,'Processing',?)",
              (uid, svc_key, svc_name, link, qty, amount, cost, profit, str(panel_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    oid = c.lastrowid
    conn.execute("UPDATE users SET total_orders=total_orders+1,total_spent=ROUND(total_spent+?,2) WHERE user_id=?", (amount, uid))
    conn.commit(); conn.close(); return oid

def db_orders(uid, n=5):
    conn = get_conn()
    r = conn.execute("SELECT order_id,service_name,quantity,amount,status,created_at FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT ?", (uid, n)).fetchall()
    conn.close(); return r

def db_save_deposit(uid, amt, phone):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO deposits(user_id,amount,phone,status,created_at) VALUES(?,?,?,'Pending',?)",
              (uid, amt, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    did = c.lastrowid; conn.commit(); conn.close(); return did

def db_stats():
    conn = get_conn()
    u  = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    o  = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    op = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Processing'").fetchone()[0]
    oc = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
    rv = conn.execute("SELECT COALESCE(SUM(amount),0) FROM orders").fetchone()[0]
    pr = conn.execute("SELECT COALESCE(SUM(profit),0) FROM orders").fetchone()[0]
    dp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='Completed'").fetchone()[0]
    bn = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    conn.close(); return u, o, op, oc, rv, pr, dp, bn

def db_all_users(limit=30, offset=0):
    conn = get_conn()
    r = conn.execute("SELECT user_id,username,first_name,balance,total_orders,total_spent,total_deposit,is_banned,joined_at FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    conn.close(); return r

def db_count_users():
    conn = get_conn(); r = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]; conn.close(); return r

def db_ban(uid, v=True):
    conn = get_conn(); conn.execute("UPDATE users SET is_banned=? WHERE user_id=?", (1 if v else 0, uid)); conn.commit(); conn.close()

def db_log(admin_id, action, tid, detail):
    conn = get_conn(); conn.execute("INSERT INTO admin_logs(admin_id,action,target_id,detail,created_at) VALUES(?,?,?,?,?)",
              (admin_id, action, tid, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close()

def db_search(q):
    conn = get_conn(); p = f"%{q}%"
    r = conn.execute("SELECT user_id,username,first_name,balance,total_orders,is_banned FROM users WHERE username LIKE ? OR first_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?", (p,p,p)).fetchall()
    conn.close(); return r

def db_all_user_ids():
    conn = get_conn(); r = [x[0] for x in conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]; conn.close(); return r

# ═══════════════════════════════════════════════════════════
# SMM PANEL
# ═══════════════════════════════════════════════════════════
def smm_order(service_id, link, qty):
    try:
        r = requests.post(SMM_PANEL_URL, data={"key":SMM_PANEL_KEY,"action":"add","service":service_id,"link":link,"quantity":qty}, timeout=20)
        j = r.json(); return j.get("order"), j.get("error")
    except Exception as e: return None, str(e)

def smm_balance():
    try:
        r = requests.post(SMM_PANEL_URL, data={"key":SMM_PANEL_KEY,"action":"balance"}, timeout=15)
        j = r.json(); return j.get("balance","N/A"), j.get("currency","BDT")
    except: return "N/A","N/A"

# ═══════════════════════════════════════════════════════════
# AUTOPAY
# ═══════════════════════════════════════════════════════════
def make_payment(uid, amt, phone):
    payload = json.dumps({"success_url":f"https://t.me/{BOT_USERNAME.lstrip('@')}","cancel_url":f"https://t.me/{BOT_USERNAME.lstrip('@')}","metadata":{"phone":phone,"user_id":str(uid)},"amount":str(amt)})
    hdrs = {"API-KEY":AUTOPAY_API_KEY,"Content-Type":"application/json","SECRET-KEY":AUTOPAY_SECRET_KEY,"BRAND-KEY":AUTOPAY_BRAND_KEY,"DEVICE-KEY":AUTOPAY_DEVICE_KEY}
    for attempt in range(3):
        try:
            r = requests.post(AUTOPAY_URL, headers=hdrs, data=payload, timeout=35).json()
            url = r.get("payment_url") or r.get("url") or (r.get("data") or {}).get("payment_url")
            if url: return url, r
            if attempt == 2: return None, r
        except requests.exceptions.Timeout:
            if attempt == 2: return None, "Payment server সাড়া দিচ্ছে না।"
        except Exception as e: return None, str(e)
    return None, "Failed"

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
async def is_member(bot, uid):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked","banned"]: return False
        except: return False
    return True

async def typing(bot, cid):
    try: await bot.send_chat_action(cid, "typing")
    except: pass

def status_emoji(s):
    return "✅" if s=="Completed" else "⏳" if s=="Processing" else "❌"

def user_str(uname, fname):
    return f"@{uname}" if uname else (fname or "Unknown")

# ═══════════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db_upsert_user(u.id, u.username, u.first_name)
    ctx.user_data.clear()
    await typing(ctx.bot, update.effective_chat.id)

    if db_banned(u.id):
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    if not await is_member(ctx.bot, u.id):
        await update.message.reply_text(
            "⛔ বট ব্যবহারের আগে আমাদের চ্যানেল গুলোতে জয়েন করুন ⬇️\n\n"
            "➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
            reply_markup=join_kb()); return

    await update.message.reply_text(
        f"{WELCOME_MSG}\n\nস্বাগতম, {u.first_name}! 👋\nনিচের বাটন থেকে সার্ভিস নিন:",
        reply_markup=main_menu_kb())

# ═══════════════════════════════════════════════════════════
# DAILY MORNING BROADCAST
# ═══════════════════════════════════════════════════════════
async def daily_morning_job(ctx: ContextTypes.DEFAULT_TYPE):
    uids = db_all_user_ids()
    sent = fail = 0
    logging.info(f"📢 Daily morning broadcast → {len(uids)} users")
    for uid in uids:
        try:
            await ctx.bot.send_message(uid, DAILY_MORNING_MSG, reply_markup=main_menu_kb())
            sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    logging.info(f"📢 Done: sent={sent} fail={fail}")
    try:
        await ctx.bot.send_message(ADMIN_ID, f"📢 Daily broadcast done!\n✅ Sent: {sent} | ❌ Fail: {fail}")
    except: pass

# ═══════════════════════════════════════════════════════════
# /admin
# ═══════════════════════════════════════════════════════════
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u.id != ADMIN_ID: await update.message.reply_text("❌ শুধুমাত্র Admin!"); return
    await typing(ctx.bot, update.effective_chat.id)
    us, o, op, oc, rv, pr, dp, bn = db_stats()
    bal, cur = smm_balance()
    ctx.user_data.clear(); ctx.user_data["admin_mode"] = True
    await update.message.reply_text(
        f"🔐 Admin Panel — {BOT_NAME}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 মোট ইউজার: {us} | 🚫 Banned: {bn}\n"
        f"📦 মোট অর্ডার: {o}\n"
        f"⏳ Processing: {op} | ✅ Completed: {oc}\n"
        f"💰 Revenue: {rv:.2f}৳\n"
        f"📈 Profit: {pr:.2f}৳\n"
        f"💳 Deposits: {dp:.2f}৳\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥️ Panel: {bal} {cur}",
        reply_markup=ADMIN_KB)

# ═══════════════════════════════════════════════════════════
# ADMIN COMMANDS
# ═══════════════════════════════════════════════════════════
async def cmd_addbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        db_add_balance(tid, amt); nb = db_balance(tid)
        db_log(update.effective_user.id, "addbalance", tid, f"+{amt}")
        await update.message.reply_text(f"✅ {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
        try: await ctx.bot.send_message(tid, f"✅ আপনার অ্যাকাউন্টে {amt} টাকা যোগ হয়েছে!\n💰 নতুন ব্যালেন্স: {nb:.2f} টাকা")
        except: pass
    except Exception as e: await update.message.reply_text(f"Usage: /addbalance <uid> <amount>\nErr: {e}")

async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban(tid, True); db_log(update.effective_user.id, "ban", tid, "")
        await update.message.reply_text(f"🚫 {tid} banned.")
    except Exception as e: await update.message.reply_text(f"Usage: /ban <uid>\nErr: {e}")

async def cmd_unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban(tid, False); db_log(update.effective_user.id, "unban", tid, "")
        await update.message.reply_text(f"✅ {tid} unbanned.")
    except Exception as e: await update.message.reply_text(f"Usage: /unban <uid>\nErr: {e}")

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /broadcast <msg>"); return
    msg = " ".join(ctx.args); uids = db_all_user_ids()
    sent = fail = 0; await update.message.reply_text(f"📢 Sending to {len(uids)}...")
    for uid in uids:
        try: await ctx.bot.send_message(uid, f"📢 {BOT_NAME}\n━━━━━━━━━━━━\n{msg}"); sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Done! ✅{sent} ❌{fail}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    us, o, op, oc, rv, pr, dp, bn = db_stats(); bal, cur = smm_balance()
    await update.message.reply_text(
        f"📊 {BOT_NAME}\n━━━━━━━━━━━━\n"
        f"👥 {us} users | 🚫 {bn} banned\n📦 {o} orders | ⏳{op} ✅{oc}\n"
        f"💰 {rv:.2f}৳ | 📈 {pr:.2f}৳ profit\n💳 {dp:.2f}৳ dep\n🖥️ {bal} {cur}")

async def cmd_myorders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user; rows = db_orders(u.id, 10)
    if not rows: await update.message.reply_text("📦 কোনো অর্ডার নেই।"); return
    msg = "📦 আপনার সর্বশেষ অর্ডার\n━━━━━━━━━━━━━━━\n"
    for r in rows:
        msg += f"{status_emoji(r[4])} #{r[0]} — {r[1]}\n   🔢{r[2]:,} | 💸{r[3]:.2f}৳ | {r[5][:16]}\n─────────\n"
    await update.message.reply_text(msg)

# ═══════════════════════════════════════════════════════════
# CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════
async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    d = q.data; u = q.from_user
    cid = q.message.chat.id

    # ── Join check ───────────────────────────────────────────
    if d == "check_join":
        await typing(ctx.bot, cid)
        if not await is_member(ctx.bot, u.id):
            await q.answer("❌ দুটো চ্যানেলেই জয়েন করো!", show_alert=True); return
        db_upsert_user(u.id, u.username, u.first_name)
        await q.edit_message_text(
            f"{WELCOME_MSG}\n\nস্বাগতম, {u.first_name}! 👋\nনিচের বাটন থেকে সার্ভিস নিন:",
            reply_markup=main_menu_kb()); return

    # ── Main menu items ──────────────────────────────────────
    if d == "menu_order":
        await typing(ctx.bot, cid)
        if not await is_member(ctx.bot, u.id):
            await q.edit_message_text("⛔ আগে চ্যানেলে জয়েন করো!", reply_markup=join_kb()); return
        ctx.user_data.clear(); ctx.user_data["in_order"] = True
        await q.edit_message_text("🏪 সার্ভিস বেছে নিন 👇", reply_markup=cat_menu_kb()); return

    if d == "menu_balance":
        await typing(ctx.bot, cid)
        row = db_get_user(u.id)
        bal2 = row[3] if row else 0.0; tot2 = row[4] if row else 0; sp2 = row[5] if row else 0.0; dep2 = row[6] if row else 0.0
        await q.edit_message_text(
            f"💰 আপনার অ্যাকাউন্ট\n━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {u.id}\n📛 Name: {u.first_name}\n"
            f"💵 ব্যালেন্স: {bal2:.2f}৳\n📦 মোট অর্ডার: {tot2}\n"
            f"💸 মোট খরচ: {sp2:.2f}৳\n💳 মোট ডিপোজিট: {dep2:.2f}৳\n━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])); return

    if d == "menu_deposit":
        ctx.user_data.clear(); ctx.user_data["dstep"] = "amt"
        await q.edit_message_text(
            "💳 ডিপোজিট\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\nসংখ্যা লিখো 👇"); return

    if d == "menu_orders":
        await typing(ctx.bot, cid)
        rows = db_orders(u.id)
        if not rows:
            await q.edit_message_text("📦 এখনো কোনো অর্ডার নেই।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])); return
        msg = "📦 সর্বশেষ ৫টি অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            msg += f"{status_emoji(r[4])} #{r[0]} | {r[1]}\n   🔢{r[2]:,} | 💸{r[3]:.2f}৳\n   📅{r[5][:16]}\n─────────\n"
        await q.edit_message_text(msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])); return

    if d == "menu_support":
        await q.edit_message_text(
            f"🆘 সাপোর্ট — {BOT_NAME}\n━━━━━━━━━━━━━━━\n"
            f"📩 Telegram: @RKXPremiumZone\n📢 Channel: @RKXSMMZONE\n\n"
            f"⏰ সকাল ৯টা – রাত ১১টা\n🤖 {BOT_USERNAME}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])); return

    if d == "menu_price":
        await typing(ctx.bot, cid)
        msg = f"📋 {BOT_NAME} — মূল্য তালিকা\n━━━━━━━━━━━━━━━\n"
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for s in cat["items"].values():
                msg += f"  • {s['name']}: {s['price']}৳/১০০০\n"
        msg += "\n━━━━━━━━━━━━━━━\n⚡ অর্ডার ৩০ মিনিটে কমপ্লিট"
        # Split if too long
        chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
        await q.edit_message_text(chunks[0],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]))
        for chunk in chunks[1:]:
            await ctx.bot.send_message(cid, chunk)
        return

    # ── Back navigation ──────────────────────────────────────
    if d == "back_main":
        ctx.user_data.clear()
        await q.edit_message_text(
            f"{WELCOME_MSG}\n\nনিচের বাটন থেকে সার্ভিস নিন:",
            reply_markup=main_menu_kb()); return

    if d == "back_cats":
        ctx.user_data.pop("sel", None); ctx.user_data.pop("step", None)
        ctx.user_data["in_order"] = True
        await q.edit_message_text("🏪 সার্ভিস বেছে নিন 👇", reply_markup=cat_menu_kb()); return

    # ── Category selected ────────────────────────────────────
    if d.startswith("cat_"):
        cat_key = d[4:]
        if cat_key not in SERVICES: return
        ctx.user_data["cat"] = cat_key
        cat = SERVICES[cat_key]
        await q.edit_message_text(
            f"{cat['emoji']} {cat['name']} Services\nএকটি সার্ভিস বেছে নিন 👇",
            reply_markup=service_list_kb(cat_key)); return

    # ── Service selected ─────────────────────────────────────
    if d.startswith("svc_"):
        svc_key = d[4:]; svc = find_svc(svc_key)
        if not svc: return
        bal = db_balance(u.id)
        ctx.user_data["sel"] = svc_key; ctx.user_data["step"] = "link"
        await q.edit_message_text(
            f"✅ {svc['name']}\n\n"
            f"ℹ️ {svc.get('desc','')}\n\n"
            f"💰 আপনার ব্যালেন্স: {bal:.2f}৳\n"
            f"📊 মূল্য: {svc['price']}৳ / ১০০০\n"
            f"📉 সর্বনিম্ন: {svc['min']:,}\n"
            f"📈 সর্বোচ্চ: {svc['max']:,}\n\n"
            f"🔗 পোস্ট / প্রোফাইল লিংক দাও:",
            reply_markup=cancel_kb()); return

    # ── Confirm order ────────────────────────────────────────
    if d == "confirm_order":
        await typing(ctx.bot, cid)
        svc  = find_svc(ctx.user_data.get("sel",""))
        link = ctx.user_data.get("link")
        qty  = ctx.user_data.get("qty")
        amt  = ctx.user_data.get("amt")
        cost = ctx.user_data.get("cost", 0)

        if not all([svc, link, qty, amt]):
            await q.edit_message_text("❌ কিছু ভুল হয়েছে। আবার চেষ্টা করো।", reply_markup=main_menu_kb())
            ctx.user_data.clear(); return

        bal = db_balance(u.id)
        if bal < amt:
            await q.edit_message_text(
                f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳\n\n💳 ডিপোজিট করো।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Deposit", callback_data="menu_deposit")]]))
            ctx.user_data.clear(); return

        await q.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে...")
        pid, err = smm_order(svc["service_id"], link, qty)

        if err and not pid:
            await q.edit_message_text(
                f"❌ অর্ডার ব্যর্থ!\nকারণ: {err}\n\n🆘 @RKXPremiumZone",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main", callback_data="back_main")]]))
            return

        db_add_balance(u.id, -amt)
        oid = db_save_order(u.id, ctx.user_data.get("sel"), svc["name"], link, qty, amt, cost, str(pid or "N/A"))
        nb  = db_balance(u.id)

        await q.edit_message_text(
            f"✅ অর্ডার সফল!\n━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"└➤ Order ID: {oid}\n└➤ User ID: {u.id}\n"
            f"└➤ Status: Processing ⏳\n└➤ Service: {svc['name']}\n"
            f"└➤ Ordered: {qty:,}\n└➤ Link: Private\n"
            f"└➤ খরচ: {amt:.2f}৳\n└➤ বাকি: {nb:.2f}৳\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USERNAME}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]]))

        try:
            await ctx.bot.send_message(LOG_CHANNEL,
                f"📌 {BOT_NAME} Notification\n🎯 New {svc['name']} Order\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
                f"└➤ Order ID: {oid}\n└➤ User: {user_str(u.username,u.first_name)} ({u.id})\n"
                f"└➤ ✅ Qty: {qty:,} | Amount: {amt:.2f}৳\n"
                f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USERNAME}")
        except: pass
        ctx.user_data.clear(); return

    # ── Cancel ───────────────────────────────────────────────
    if d == "cancel_order":
        ctx.user_data.clear()
        await q.edit_message_text("❌ অর্ডার বাতিল।", reply_markup=main_menu_kb()); return

    # ── Admin user detail ────────────────────────────────────
    if d.startswith("au_"):
        tid = int(d[3:]); row = db_get_user(tid)
        if not row: await q.answer("Not found!", show_alert=True); return
        uid2,un2,fn2,bal2,ord2,sp2,dep2,ban2,jn2 = row
        ustr2 = user_str(un2, fn2); ban_str2 = " 🚫" if ban2 else " ✅"
        ord_rows = db_orders(tid, 3)
        ord_txt  = "".join([f"  #{r[0]} {r[1][:20]} | {r[2]:,} | {r[3]:.2f}৳ | {r[4]}\n" for r in ord_rows]) or "  নেই"
        kb2 = [
            [InlineKeyboardButton("💰 Add Balance", callback_data=f"aab_{tid}"),
             InlineKeyboardButton("🚫 Ban",         callback_data=f"abn_{tid}")],
            [InlineKeyboardButton("✅ Unban",        callback_data=f"aub_{tid}"),
             InlineKeyboardButton("🔙 Back",         callback_data="adm_back")]
        ]
        await q.edit_message_text(
            f"👤 {ustr2}{ban_str2}\n🆔 {tid}\n💰 {bal2:.2f}৳ | 📦 {ord2} orders\n"
            f"💸 Spent: {sp2:.2f}৳ | 💳 Dep: {dep2:.2f}৳\n📅 {jn2[:10] if jn2 else 'N/A'}\n\n"
            f"📦 Recent:\n{ord_txt}",
            reply_markup=InlineKeyboardMarkup(kb2)); return

    if d.startswith("aab_"):
        tid = int(d[4:]); ctx.user_data["adm_ab_tid"] = tid; ctx.user_data["admin_step"] = "addbal_amt"
        await q.edit_message_text(f"💰 User {tid} কত টাকা যোগ করবে?"); return

    if d.startswith("abn_"):
        tid = int(d[4:]); db_ban(tid, True); db_log(u.id, "ban", tid, "via panel")
        await q.answer(f"🚫 {tid} banned!", show_alert=True); return

    if d.startswith("aub_"):
        tid = int(d[4:]); db_ban(tid, False); db_log(u.id, "unban", tid, "via panel")
        await q.answer(f"✅ {tid} unbanned!", show_alert=True); return

    if d == "adm_back":
        await q.edit_message_text("ℹ️ Admin panel এ ফিরুন।"); return

# ═══════════════════════════════════════════════════════════
# TEXT HANDLER
# ═══════════════════════════════════════════════════════════
async def txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u    = update.effective_user
    t    = (update.message.text or "").strip()
    step = ctx.user_data.get("step")
    ds   = ctx.user_data.get("dstep")
    adm  = ctx.user_data.get("admin_step")

    await typing(ctx.bot, update.effective_chat.id)

    if db_banned(u.id) and u.id != ADMIN_ID:
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    # ── Admin steps ──────────────────────────────────────────
    if adm and u.id == ADMIN_ID:
        await adm_step(update, ctx, t, adm); return

    # ── Admin buttons ────────────────────────────────────────
    if ctx.user_data.get("admin_mode") and u.id == ADMIN_ID:
        if t == "🔙 Admin Exit":
            ctx.user_data.clear()
            await update.message.reply_text("✅ Admin Panel বন্ধ।", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)); return
        if await adm_btn(update, ctx, t): return

    # ── Order flow: link ─────────────────────────────────────
    if step == "link":
        if not t.startswith("http"):
            await update.message.reply_text("❌ সঠিক লিংক দাও! http দিয়ে শুরু হতে হবে।"); return
        svc = find_svc(ctx.user_data.get("sel",""))
        ctx.user_data["link"] = t; ctx.user_data["step"] = "qty"
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n💰 ব্যালেন্স: {db_balance(u.id):.2f}৳\n"
            f"📊 {svc['price']}৳/১০০০ | Min:{svc['min']:,} Max:{svc['max']:,}\n\n🔢 পরিমাণ লিখো:",
            reply_markup=cancel_kb()); return

    # ── Order flow: quantity ─────────────────────────────────
    if step == "qty":
        if not t.isdigit(): await update.message.reply_text("❌ শুধু সংখ্যা লিখো!"); return
        qty = int(t); svc = find_svc(ctx.user_data.get("sel",""))
        if qty < svc["min"] or qty > svc["max"]:
            await update.message.reply_text(f"❌ {svc['min']:,}–{svc['max']:,} এর মধ্যে হতে হবে!"); return
        amt  = round((qty/1000)*svc["price"], 2)
        cost = round((qty/1000)*svc["cost"],  2)
        bal  = db_balance(u.id)
        if bal < amt:
            await update.message.reply_text(
                f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Deposit", callback_data="menu_deposit")]]))
            ctx.user_data.clear(); return
        ctx.user_data.update({"qty":qty,"amt":amt,"cost":cost,"step":"confirm"})
        await update.message.reply_text(
            f"📋 অর্ডার সারসংক্ষেপ\n━━━━━━━━━━━━━━━\n"
            f"🛒 {svc['name']}\n🔗 {ctx.user_data['link']}\n"
            f"🔢 {qty:,} | 💸 {amt:.2f}৳\n"
            f"💰 অর্ডারের পরে: {bal-amt:.2f}৳\n━━━━━━━━━━━━━━━\n✅ কনফার্ম করবে?",
            reply_markup=confirm_kb()); return

    # ── Deposit: amount ──────────────────────────────────────
    if ds == "amt":
        if not t.isdigit() or int(t) < 10: await update.message.reply_text("❌ সর্বনিম্ন ১০ টাকা!"); return
        ctx.user_data["damt"] = int(t); ctx.user_data["dstep"] = "phone"
        await update.message.reply_text("📱 ফোন নম্বর দাও:\n(যেটা দিয়ে পেমেন্ট করবে)"); return

    # ── Deposit: phone ───────────────────────────────────────
    if ds == "phone":
        amt4 = ctx.user_data.get("damt"); phone = t
        dep_id = db_save_deposit(u.id, amt4, phone)
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        url, raw = make_payment(u.id, amt4, phone)
        ctx.user_data.clear()
        if url:
            await update.message.reply_text(
                f"✅ পেমেন্ট লিংক তৈরি!\n━━━━━━━━━━━━━━━\n"
                f"💰 {amt4} টাকা | 📱 {phone}\n🆔 Ref: #{dep_id}\n━━━━━━━━━━━━━━━\n"
                f"⬇️ নিচের নীল বাটনে পেমেন্ট করো\n✅ সফল হলে ব্যালেন্স অটো যোগ হবে।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💙 এখানে পেমেন্ট করো", url=url)]]))
        else:
            await update.message.reply_text(f"❌ লিংক তৈরি হয়নি।\n{raw}\n\n🆘 @RKXPremiumZone")
        return

    # ── Fallback ─────────────────────────────────────────────
    if not ctx.user_data.get("admin_mode"):
        await update.message.reply_text(
            f"{WELCOME_MSG}\n\nনিচের বাটন থেকে সার্ভিস নিন:",
            reply_markup=main_menu_kb())

# ═══════════════════════════════════════════════════════════
# ADMIN BUTTON HANDLER
# ═══════════════════════════════════════════════════════════
async def adm_btn(update, ctx, t):
    u = update.effective_user
    if t == "👥 All Users":
        rows = db_all_users(25); total = db_count_users()
        msg = f"👥 সকল ইউজার (মোট: {total})\n━━━━━━━━━━━━━━━━━━━━\n"
        kb  = []
        for row in rows:
            uid2,un2,fn2,bal2,ord2,sp2,dep2,ban2,jn2 = row
            ustr2 = user_str(un2, fn2); bm = "🚫" if ban2 else "✅"
            msg += f"{bm} {ustr2} | {uid2} | {bal2:.0f}৳ | {ord2} ord\n"
            kb.append([InlineKeyboardButton(f"{bm} {ustr2} ({uid2})", callback_data=f"au_{uid2}")])
        await update.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb[:20]))
        return True

    if t == "🔍 Search User":
        ctx.user_data["admin_step"] = "search_user"
        await update.message.reply_text("🔍 Username, Name বা User ID লিখো:"); return True

    if t == "📊 Full Stats":
        us,o,op,oc,rv,pr,dp,bn = db_stats(); bal,cur = smm_balance()
        await update.message.reply_text(
            f"📊 {BOT_NAME}\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 {us} users | 🚫 {bn} banned\n📦 {o} | ⏳{op} ✅{oc}\n"
            f"💰 Revenue: {rv:.2f}৳\n📈 Profit: {pr:.2f}৳\n💳 Dep: {dp:.2f}৳\n🖥️ {bal} {cur}")
        return True

    if t == "📦 All Orders":
        conn = get_conn()
        rows = conn.execute("SELECT o.order_id,u.username,u.first_name,o.service_name,o.quantity,o.amount,o.profit,o.status FROM orders o JOIN users u ON o.user_id=u.user_id ORDER BY o.order_id DESC LIMIT 20").fetchall()
        conn.close()
        if not rows: await update.message.reply_text("📦 নেই।"); return True
        msg = "📦 সর্বশেষ ২০ অর্ডার:\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            ustr3 = user_str(r[1],r[2])
            msg += f"{status_emoji(r[7])} #{r[0]} {ustr3}\n  {r[3][:25]} | {r[4]:,} | {r[5]:.2f}৳ | p:{r[6]:.2f}৳\n"
        await update.message.reply_text(msg[:4000]); return True

    if t == "💳 Add Balance":
        ctx.user_data["admin_step"] = "addbal_uid"
        await update.message.reply_text("💳 User ID দাও:"); return True

    if t == "🚫 Ban User":
        ctx.user_data["admin_step"] = "ban_uid"
        await update.message.reply_text("🚫 Ban করার User ID:"); return True

    if t == "✅ Unban User":
        ctx.user_data["admin_step"] = "unban_uid"
        await update.message.reply_text("✅ Unban করার User ID:"); return True

    if t == "📢 Broadcast":
        ctx.user_data["admin_step"] = "broadcast_msg"
        await update.message.reply_text("📢 মেসেজ লিখো:"); return True

    if t == "💼 Panel Balance":
        bal, cur = smm_balance()
        await update.message.reply_text(f"💼 Panel Balance\n━━━━━━━━━━━━\n💰 {bal} {cur}"); return True

    return False

# ═══════════════════════════════════════════════════════════
# ADMIN STEP HANDLER
# ═══════════════════════════════════════════════════════════
async def adm_step(update, ctx, t, adm):
    u = update.effective_user

    if adm == "search_user":
        rows = db_search(t)
        if not rows: await update.message.reply_text("❌ কেউ পাওয়া যায়নি।")
        else:
            msg = f"🔍 ({len(rows)}):\n"; kb = []
            for r in rows:
                uid4,un4,fn4,bal4,ord4,ban4 = r
                ustr4 = user_str(un4,fn4); bm4 = "🚫" if ban4 else "✅"
                msg += f"{bm4} {ustr4} | {uid4} | {bal4:.0f}৳\n"
                kb.append([InlineKeyboardButton(f"{bm4} {ustr4} ({uid4})", callback_data=f"au_{uid4}")])
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        ctx.user_data.pop("admin_step",None); return

    if adm == "addbal_uid":
        if not t.isdigit(): await update.message.reply_text("❌ সঠিক User ID!"); return
        ctx.user_data["adm_ab_tid"] = int(t); ctx.user_data["admin_step"] = "addbal_amt"
        await update.message.reply_text(f"💰 User {t} কত টাকা?"); return

    if adm == "addbal_amt":
        try:
            amt = float(t); tid = ctx.user_data.get("adm_ab_tid")
            db_add_balance(tid, amt); nb = db_balance(tid)
            db_log(u.id,"addbalance",tid,f"+{amt}")
            await update.message.reply_text(f"✅ {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
            try: await ctx.bot.send_message(tid, f"✅ {amt} টাকা যোগ!\n💰 নতুন: {nb:.2f}৳")
            except: pass
        except Exception as e: await update.message.reply_text(f"❌ {e}")
        ctx.user_data.pop("admin_step",None); ctx.user_data.pop("adm_ab_tid",None); return

    if adm == "ban_uid":
        if not t.isdigit(): await update.message.reply_text("❌ সঠিক User ID!"); return
        tid = int(t); db_ban(tid,True); db_log(u.id,"ban",tid,"")
        await update.message.reply_text(f"🚫 {tid} banned.")
        ctx.user_data.pop("admin_step",None); return

    if adm == "unban_uid":
        if not t.isdigit(): await update.message.reply_text("❌ সঠিক User ID!"); return
        tid = int(t); db_ban(tid,False); db_log(u.id,"unban",tid,"")
        await update.message.reply_text(f"✅ {tid} unbanned.")
        ctx.user_data.pop("admin_step",None); return

    if adm == "broadcast_msg":
        uids = db_all_user_ids(); sent = fail = 0
        await update.message.reply_text(f"📢 Sending to {len(uids)}...")
        for uid5 in uids:
            try: await ctx.bot.send_message(uid5, f"📢 {BOT_NAME}\n━━━━━━━━━━━━\n{t}"); sent += 1
            except: fail += 1
            await asyncio.sleep(0.05)
        await update.message.reply_text(f"✅ Done! ✅{sent} ❌{fail}")
        ctx.user_data.pop("admin_step",None); return

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s — %(message)s", level=logging.INFO)
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("admin",      cmd_admin))
    app.add_handler(CommandHandler("addbalance", cmd_addbalance))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("ban",        cmd_ban))
    app.add_handler(CommandHandler("unban",      cmd_unban))
    app.add_handler(CommandHandler("broadcast",  cmd_broadcast))
    app.add_handler(CommandHandler("myorders",   cmd_myorders))

    # Callbacks & messages
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, txt))

    # ✅ Daily morning job — সকাল ৬টা (UTC 0 = BD 6 AM)
    job_queue = app.job_queue
    job_queue.run_daily(
        daily_morning_job,
        time=dtime(hour=DAILY_MSG_HOUR, minute=0, second=0),
        name="daily_morning"
    )

    logging.info(f"✅ {BOT_NAME} চালু! Daily msg at {DAILY_MSG_HOUR}:00 UTC")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
