# ╔══════════════════════════════════════════════════════════════╗
# ║         RKX SMM ZONE — Full Telegram Bot (Final)            ║
# ║  Permanent Colored Buttons | Real Services | Admin Panel    ║
# ║  Panel: rxsmm.top | AutoPay: rxpay.top                      ║
# ╚══════════════════════════════════════════════════════════════╝

import logging, os, requests, json, sqlite3, asyncio
from datetime import datetime, time as dtime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ══════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════
BOT_TOKEN     = os.environ.get("BOT_TOKEN",     "8331448370:AAGEdB0uDT0NnvN3DjFtuyGMRO2W8zuINYg")
ADMIN_ID      = int(os.environ.get("ADMIN_ID",  "8387741218"))
SMM_PANEL_URL = "https://rxsmm.top/api/v2"
SMM_PANEL_KEY = os.environ.get("SMM_PANEL_KEY", "835b3643be911926e000093d583fb4e5")

AUTOPAY_API_KEY    = os.environ.get("AUTOPAY_API_KEY",    "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_SECRET_KEY = os.environ.get("AUTOPAY_SECRET_KEY", "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_BRAND_KEY  = os.environ.get("AUTOPAY_BRAND_KEY",  "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV")
AUTOPAY_DEVICE_KEY = os.environ.get("AUTOPAY_DEVICE_KEY", "Dl6Vzy8T33bbGiUybEDYffaZqp2ZxtJ0cP0Ss1HB")
AUTOPAY_URL        = "https://pay.rxpay.top/api/payment/create"

LOG_CHANNEL       = "@RKXSMMZONE"
REQUIRED_CHANNELS = ["@RKXPremiumZone", "@RKXSMMZONE"]
BOT_USERNAME      = "@RKXSMMbot"
SUPPORT_USERNAME  = "@rkx_rakib"
BOT_NAME          = "RKX SMM ZONE"
DB_PATH           = "rkx_bot.db"

# Daily broadcast time (UTC) — সকাল ৬টা BD = UTC 00:00
DAILY_HOUR   = 0
DAILY_MINUTE = 0

# ══════════════════════════════════════════════════════════════
#  COLORED BUTTON HELPERS
#  ReplyKeyboard: "primary"=নীল | "success"=সবুজ | "danger"=লাল
#  InlineKeyboard: style via api_kwargs
# ══════════════════════════════════════════════════════════════
def _kb(text: str, style: str = "primary") -> KeyboardButton:
    """Colored ReplyKeyboardButton — Telegram Bot API 9.4+
    পুরনো client এ style ignore হবে, crash হবে না।
    """
    try:
        return KeyboardButton(text, api_kwargs={"style": style})
    except Exception:
        return KeyboardButton(text)

def _ib(text: str, cb: str, style: str = None) -> InlineKeyboardButton:
    """InlineKeyboardButton — style optional"""
    try:
        if style:
            return InlineKeyboardButton(text, callback_data=cb,
                                        api_kwargs={"style": style})
        return InlineKeyboardButton(text, callback_data=cb)
    except Exception:
        return InlineKeyboardButton(text, callback_data=cb)

# ══════════════════════════════════════════════════════════════
#  PERMANENT REPLY KEYBOARD (স্ক্রিনশটের মতো)
#  — এটা সবসময় নিচে থাকবে, কখনো যাবে না
# ══════════════════════════════════════════════════════════════
MAIN_KB = ReplyKeyboardMarkup(
    [
        [_kb("🛒 Order",          "primary")],           # নীল — পুরো রো
        [_kb("💳 Deposit",        "success"),
         _kb("💰 Balance",        "success")],            # সবুজ
        [_kb("🆘 Support",        "danger"),
         _kb("📦 Order Status",   "primary")],            # লাল + নীল
        [_kb("📋 Price & Info",   "primary")],            # নীল — পুরো রো
        [_kb("👥 Refer",          "success"),
         _kb("🎁 Free Service",   "success")],            # সবুজ
    ],
    resize_keyboard=True,
    is_persistent=True,   # Telegram 7.3+ — keyboard সবসময় দেখাবে
)

CANCEL_KB = ReplyKeyboardMarkup(
    [[_kb("❌ Cancel", "danger")]],
    resize_keyboard=True,
    is_persistent=True,
)

def order_cat_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [_kb("🎵 TikTok",    "primary"),  _kb("✈️ Telegram", "primary")],
            [_kb("🎬 YouTube",   "danger"),   _kb("📘 Facebook",  "primary")],
            [_kb("📸 Instagram", "success")],
            [_kb("🎁 Free Service", "success"), _kb("🔙 Main Menu", "danger")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def svc_kb(items: dict) -> ReplyKeyboardMarkup:
    rows = [[_kb(s["name"], "primary")] for s in items.values()]
    rows.append([_kb("🔙 Back", "danger")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)

# ══════════════════════════════════════════════════════════════
#  INLINE KEYBOARDS
# ══════════════════════════════════════════════════════════════
def join_kb():
    return InlineKeyboardMarkup([[
        _ib("✅ Join করেছি — চেক করো", "check_join")
    ]])

def confirm_kb():
    return InlineKeyboardMarkup([[
        _ib("✅ কনফার্ম করো", "confirm_order"),
        _ib("❌ বাতিল", "cancel_order", "destructive"),
    ]])

def deposit_btn_kb(url: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("💳  Pay Now  💳", web_app=WebAppInfo(url=url))
    ]])

def balance_kb():
    return InlineKeyboardMarkup([[
        _ib("💳 Deposit করো", "goto_deposit")
    ]])

def admin_inline_kb():
    return InlineKeyboardMarkup([
        [_ib("👥 All Users",      "adm_users"),
         _ib("📊 Full Stats",     "adm_stats")],
        [_ib("💳 Add Balance",    "adm_addbal"),
         _ib("💸 Sub Balance",    "adm_subbal")],
        [_ib("🚫 Ban User",       "adm_ban",    "destructive"),
         _ib("✅ Unban User",     "adm_unban")],
        [_ib("📢 Broadcast",      "adm_bc"),
         _ib("💼 Panel Balance",  "adm_panelbal")],
        [_ib("📦 All Orders",     "adm_orders"),
         _ib("🔧 Settings",       "adm_settings")],
        [_ib("✅ Bot ON",         "adm_boton"),
         _ib("❌ Bot OFF",        "adm_botoff",  "destructive")],
    ])

# ══════════════════════════════════════════════════════════════
#  SERVICES — rxsmm.top real IDs
# ══════════════════════════════════════════════════════════════
SERVICES = {
    "tiktok": {
        "name": "🎵 TikTok",
        "items": {
            "tt_v1":  {"name":"👁 TikTok Views [Fast]",        "sid":"4233","price":0.92, "cost":0.61,"min":100,  "max":10000000,   "desc":"1M-10M/Day | INSTANT | No Refill"},
            "tt_v2":  {"name":"👁 TikTok Views [Ultra]",       "sid":"4234","price":1.53, "cost":1.02,"min":100,  "max":2147483647, "desc":"10M/Day | INSTANT | No Refill"},
            "tt_v3":  {"name":"👁 TikTok Views [Unlimited]",   "sid":"4235","price":2.70, "cost":1.80,"min":100,  "max":2147483647, "desc":"Unlimited | 5M-10M/Day"},
            "tt_l1":  {"name":"❤️ TikTok Likes [No Refill]",  "sid":"4256","price":4.37, "cost":2.91,"min":10,   "max":5000000,    "desc":"50K-100K/Day | INSTANT"},
            "tt_l2":  {"name":"❤️ TikTok Likes [R30]",        "sid":"4257","price":4.74, "cost":3.16,"min":10,   "max":5000000,    "desc":"30 Days Refill | INSTANT"},
            "tt_l3":  {"name":"❤️ TikTok Likes [R60]",        "sid":"4258","price":5.30, "cost":3.53,"min":10,   "max":5000000,    "desc":"60 Days Refill"},
            "tt_l4":  {"name":"❤️ TikTok Likes [Lifetime]",   "sid":"4261","price":6.45, "cost":4.30,"min":10,   "max":5000000,    "desc":"Lifetime Refill"},
            "tt_f1":  {"name":"👥 TikTok Followers [Real]",   "sid":"4323","price":1.50, "cost":1.00,"min":50,   "max":160000,     "desc":"Real Stable | INSTANT | R15"},
            "tt_f2":  {"name":"👥 TikTok Followers [R30]",    "sid":"4325","price":1.50, "cost":1.00,"min":50,   "max":160000,     "desc":"30 Days Refill | 500/Day"},
            "tt_f3":  {"name":"👥 TikTok Followers [HQ]",     "sid":"4324","price":1.50, "cost":1.00,"min":10,   "max":10000,      "desc":"Real | No Bots | Instant"},
            "tt_c1":  {"name":"💬 TikTok Comments [Custom]",  "sid":"4271","price":37.50,"cost":25.0,"min":10,   "max":5000,       "desc":"Custom Comments | Fast"},
            "tt_s1":  {"name":"♻️ TikTok Shares",             "sid":"4275","price":7.50, "cost":5.00,"min":100,  "max":100000,     "desc":"Fast Shares"},
        }
    },
    "facebook": {
        "name": "📘 Facebook",
        "items": {
            "fb_rl":  {"name":"👍 Facebook Like Reaction",     "sid":"3701","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min | 20K-50K/Day"},
            "fb_rv":  {"name":"❤️ Facebook Love Reaction",    "sid":"3702","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_rc":  {"name":"🤗 Facebook Care Reaction",    "sid":"3703","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_rh":  {"name":"😂 Facebook HaHa Reaction",   "sid":"3704","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_rw":  {"name":"😲 Facebook Wow Reaction",     "sid":"3705","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_rs":  {"name":"😢 Facebook Sad Reaction",     "sid":"3706","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_ra":  {"name":"😡 Facebook Angry Reaction",   "sid":"3707","price":30.45,"cost":20.30,"min":10,  "max":500000,"desc":"WorldWide | 0-30 Min"},
            "fb_fo":  {"name":"👥 Facebook Followers",        "sid":"1846","price":35.23,"cost":23.49,"min":100, "max":5000,  "desc":"Profile/Page | Fast | HQ"},
            "fb_pl":  {"name":"👍 Facebook Page Likes",       "sid":"3729","price":33.52,"cost":22.35,"min":10,  "max":500000,"desc":"WorldWide | Fast"},
            "fb_vv":  {"name":"👁 Facebook Video Views",      "sid":"3733","price":7.50, "cost":5.00, "min":1000,"max":1000000,"desc":"Fast Video Views"},
        }
    },
    "telegram": {
        "name": "✈️ Telegram",
        "items": {
            "tg_m1":  {"name":"👥 TG Members [Cheapest]",     "sid":"4817","price":2.52, "cost":1.68,"min":10,   "max":25000,  "desc":"No Refill | ~46hr"},
            "tg_m2":  {"name":"👥 TG Members [HQ Premium]",   "sid":"4486","price":1.50, "cost":1.00,"min":10,   "max":20000,  "desc":"Premium+Online | High Quality"},
            "tg_m3":  {"name":"👥 TG Members [R7]",           "sid":"4820","price":9.42, "cost":6.28,"min":1,    "max":100000, "desc":"7 Days Refill"},
            "tg_m4":  {"name":"👥 TG Members [R30]",          "sid":"4822","price":12.50,"cost":8.33,"min":1,    "max":100000, "desc":"30 Days Refill"},
            "tg_m5":  {"name":"👥 TG Members [R60]",          "sid":"4823","price":13.62,"cost":9.08,"min":1,    "max":100000, "desc":"60 Days Refill"},
            "tg_m6":  {"name":"👥 TG Members [R90]",          "sid":"4824","price":14.37,"cost":9.58,"min":100,  "max":1000000,"desc":"90 Days Refill"},
            "tg_m7":  {"name":"👥 TG Members [Non-Drop]",     "sid":"4829","price":30.21,"cost":20.14,"min":10,  "max":100000, "desc":"No Refill | Non-Drop"},
            "tg_v1":  {"name":"👁 TG Views [1 Post]",         "sid":"4525","price":0.34, "cost":0.23,"min":50,   "max":20000,  "desc":"INSTANT | MAX 1M | From URL"},
            "tg_v2":  {"name":"👁 TG Views [Groups]",         "sid":"4531","price":0.41, "cost":0.27,"min":10,   "max":500000, "desc":"From Groups | 0-30 Min"},
            "tg_v3":  {"name":"👁 TG Views [Last 5 Posts]",   "sid":"4555","price":9.45, "cost":6.30,"min":1000, "max":40000,  "desc":"Last 5 Posts | INSTANT"},
            "tg_v4":  {"name":"👁 TG Views [Last 10 Posts]",  "sid":"4556","price":18.89,"cost":12.59,"min":1000,"max":40000,  "desc":"Last 10 Posts | INSTANT"},
            "tg_v5":  {"name":"👁 TG Views [Last 20 Posts]",  "sid":"4557","price":37.75,"cost":25.17,"min":1000,"max":40000,  "desc":"Last 20 Posts | INSTANT"},
            "tg_v6":  {"name":"👁 TG Views [Last 30 Posts]",  "sid":"4558","price":61.54,"cost":41.03,"min":1000,"max":40000,  "desc":"Last 30 Posts | INSTANT"},
            "tg_r1":  {"name":"💎 TG Mix Reactions (+)",      "sid":"4744","price":31.47,"cost":20.98,"min":10,  "max":1000000,"desc":"Mix Positive Reactions"},
            "tg_r2":  {"name":"👍 TG Reaction Like",          "sid":"4748","price":31.47,"cost":20.98,"min":10,  "max":1000000,"desc":"Like Reactions"},
            "tg_r3":  {"name":"🔥 TG Reaction Fire",          "sid":"4752","price":31.47,"cost":20.98,"min":10,  "max":1000000,"desc":"Fire Reactions"},
            "tg_r4":  {"name":"❤️ TG Reaction Heart",        "sid":"4750","price":31.47,"cost":20.98,"min":10,  "max":1000000,"desc":"Heart Reactions"},
            "tg_st":  {"name":"⭐ TG Stars [Post]",           "sid":"4509","price":6.00, "cost":4.00,"min":1,    "max":10000,  "desc":"Telegram Stars for Post"},
        }
    },
    "youtube": {
        "name": "🎬 YouTube",
        "items": {
            "yt_v1":  {"name":"👁 YT Views [India Adword]",   "sid":"1908","price":1.50, "cost":1.00,"min":1000,"max":1000000,"desc":"Adword Display | 0-72hr Start"},
            "yt_v2":  {"name":"👁 YT Views [Malaysia]",       "sid":"1909","price":1.50, "cost":1.00,"min":1000,"max":1000000,"desc":"Skippable Ads | 2K-20K/Day"},
            "yt_v3":  {"name":"👁 YT Views [Netherlands]",    "sid":"1910","price":1.50, "cost":1.00,"min":1000,"max":1000000,"desc":"Skippable Ads | 2K-20K/Day"},
            "yt_v4":  {"name":"👁 YT Views [HQ Real]",        "sid":"1916","price":7.50, "cost":5.00,"min":500, "max":100000, "desc":"High Quality | Retention"},
            "yt_l1":  {"name":"👍 YT Likes [Real]",           "sid":"1877","price":37.50,"cost":25.0,"min":20,  "max":5000,   "desc":"Real Accounts | Fast"},
            "yt_l2":  {"name":"👍 YT Likes [HQ]",             "sid":"1878","price":45.0, "cost":30.0,"min":10,  "max":10000,  "desc":"High Quality | No Drop"},
            "yt_s1":  {"name":"🔔 YT Subscribers [Real]",     "sid":"1914","price":75.0, "cost":50.0,"min":10,  "max":1000,   "desc":"Real | Gradual | HQ"},
            "yt_s2":  {"name":"🔔 YT Subscribers [Fast]",     "sid":"1915","price":150.0,"cost":100.0,"min":10, "max":5000,   "desc":"Fast Delivery | HQ"},
            "yt_c1":  {"name":"💬 YT Comments [Custom]",      "sid":"1895","price":60.0, "cost":40.0,"min":5,   "max":1000,   "desc":"Custom Comments | Fast"},
        }
    },
    "instagram": {
        "name": "📸 Instagram",
        "items": {
            "ig_v1":  {"name":"👁 IG Views [All Links]",      "sid":"2015","price":0.20, "cost":0.14,"min":100, "max":100000000, "desc":"0-5 Min | 100K-1M/Day"},
            "ig_v2":  {"name":"👁 IG Views [1M/Day]",         "sid":"2016","price":0.27, "cost":0.18,"min":100, "max":3000000,   "desc":"0-5 Min | 1M/Day"},
            "ig_v3":  {"name":"👁 IG Reel Views [10M/Day]",   "sid":"2017","price":0.27, "cost":0.18,"min":100, "max":2147483647,"desc":"0-5 Min | 10M/Day"},
            "ig_sv":  {"name":"📖 IG Story Views",            "sid":"2018","price":0.75, "cost":0.50,"min":100, "max":100000,    "desc":"INSTANT | Story Views"},
            "ig_l1":  {"name":"❤️ IG Likes [HQ]",            "sid":"2034","price":24.34,"cost":16.23,"min":100,"max":1000000,   "desc":"HQ | 0-30 Min | 10K/Day"},
            "ig_l2":  {"name":"❤️ IG Likes [Real Accounts]", "sid":"1836","price":28.87,"cost":19.25,"min":10, "max":1000000,   "desc":"Real | INSTANT | 50K/Day"},
            "ig_l3":  {"name":"❤️ IG Likes [R30]",           "sid":"1837","price":29.16,"cost":19.44,"min":10, "max":1000000,   "desc":"30 Days Refill"},
            "ig_f1":  {"name":"👥 IG Followers [Real]",       "sid":"2135","price":1.50, "cost":1.00,"min":10,  "max":1000,      "desc":"100% Real | 0-15 Min"},
            "ig_f2":  {"name":"👥 IG Followers [Male]",       "sid":"2136","price":1.50, "cost":1.00,"min":10,  "max":5000,      "desc":"Real Male | Fast"},
            "ig_f3":  {"name":"👥 IG Followers [HQ]",         "sid":"2137","price":1.50, "cost":1.00,"min":30,  "max":5000,      "desc":"Very Good Quality | Fast"},
            "ig_c1":  {"name":"💬 IG Comments [Emoji]",       "sid":"2157","price":1.50, "cost":1.00,"min":10,  "max":100,       "desc":"MQ | Emojis | Fast | Cheap"},
            "ig_c2":  {"name":"💬 IG Comments [Mix Real]",    "sid":"2159","price":1.50, "cost":1.00,"min":1,   "max":100,       "desc":"Real+MQ Mixed | Random Emoji"},
            "ig_sh":  {"name":"♻️ IG Shares",                 "sid":"2152","price":3.04, "cost":2.03,"min":100, "max":100000000, "desc":"250K/Day | No Drop"},
        }
    },
}

# Auto-build name→key map
SVC_MAP: dict = {}
for _c in SERVICES.values():
    for _k, _s in _c["items"].items():
        SVC_MAP[_s["name"]] = _k

def find_svc(key: str):
    for cat in SERVICES.values():
        if key in cat["items"]: return cat["items"][key]
    return None

# ══════════════════════════════════════════════════════════════
#  MESSAGES
# ══════════════════════════════════════════════════════════════
WELCOME = (
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🏡 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 মার্কেটের সবচেয়ে কম দামে সার্ভিস\n"
    "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
    "⚡ ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট\n"
    "🛡 গ্যারান্টি সহ সাপোর্ট ও সার্ভিস\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👇 নিচের মেনু থেকে শুরু করুন"
)

DAILY_MSG = (
    "🌅 সুপ্রভাত!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "🏡 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 আজকেও সেরা দামে SMM সার্ভিস নিন!\n\n"
    "🎵 TikTok | 📘 Facebook\n"
    "✈️ Telegram | 🎬 YouTube | 📸 Instagram\n\n"
    "💳 ডিপোজিট করুন এবং এখনই অর্ডার করুন!\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"🤖 @RKXSMMbot"
)

FREE_OFFER = (
    "🎁 *ফ্রী সার্ভিস অফার*\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 *রেফার অফার (সবসময় চালু)*\n"
    "👥 ১ জনকে রেফার করলে → *১০০ Telegram Members ফ্রী!*\n\n"
    "📌 রেফার লিংক: /refer\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 আরো অফার আসলে এখানে দেখাবে।"
)

# ══════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════
def _c(): return sqlite3.connect(DB_PATH)

def init_db():
    with _c() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT    DEFAULT '',
            first_name    TEXT    DEFAULT '',
            balance       REAL    DEFAULT 0.0,
            total_orders  INTEGER DEFAULT 0,
            total_spent   REAL    DEFAULT 0.0,
            total_deposit REAL    DEFAULT 0.0,
            refer_count   INTEGER DEFAULT 0,
            refer_by      INTEGER DEFAULT 0,
            is_banned     INTEGER DEFAULT 0,
            joined_at     TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
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
        );
        CREATE TABLE IF NOT EXISTS deposits (
            dep_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            amount     REAL,
            phone      TEXT,
            txn_ref    TEXT,
            status     TEXT DEFAULT 'Pending',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_logs (
            log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id   INTEGER,
            action     TEXT,
            target_id  INTEGER,
            detail     TEXT,
            created_at TEXT
        );
        """)
        for k, v in [("bot_active","1"),("free_offer",FREE_OFFER),("refer_qty","100")]:
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))

def gs(key, fb=""): # get setting
    with _c() as c: r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else fb

def ss(key, val): # set setting
    with _c() as c: c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key,val))

def db_upsert(uid, uname, fname):
    with _c() as c:
        c.execute("INSERT OR IGNORE INTO users(user_id,username,first_name,balance,total_orders,"
                  "total_spent,total_deposit,refer_count,refer_by,is_banned,joined_at) VALUES(?,?,?,0,0,0,0,0,0,0,?)",
                  (uid, uname or "", fname or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        c.execute("UPDATE users SET username=?,first_name=? WHERE user_id=?", (uname or "", fname or "", uid))

def db_user(uid):
    with _c() as c: return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def db_bal(uid) -> float:
    with _c() as c: r = c.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    return round(r[0], 2) if r else 0.0

def db_add_bal(uid, amt):
    with _c() as c: c.execute("UPDATE users SET balance=ROUND(balance+?,2) WHERE user_id=?", (amt, uid))

def db_banned(uid) -> bool:
    with _c() as c: r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
    return bool(r[0]) if r else False

def db_ban(uid, v=True):
    with _c() as c: c.execute("UPDATE users SET is_banned=? WHERE user_id=?", (1 if v else 0, uid))

def db_save_order(uid, svc_key, svc_name, link, qty, amount, cost, panel_id) -> int:
    profit = round(amount - cost, 2)
    with _c() as c:
        cur = c.execute(
            "INSERT INTO orders(user_id,service_key,service_name,link,quantity,amount,cost,profit,"
            "panel_order_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,'Processing',?)",
            (uid, svc_key, svc_name, link, qty, amount, cost, profit, str(panel_id),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        oid = cur.lastrowid
        c.execute("UPDATE users SET total_orders=total_orders+1,total_spent=ROUND(total_spent+?,2)"
                  " WHERE user_id=?", (amount, uid))
    return oid

def db_orders(uid, n=5):
    with _c() as c:
        return c.execute("SELECT order_id,service_name,quantity,amount,status,created_at"
                         " FROM orders WHERE user_id=? ORDER BY order_id DESC LIMIT ?",
                         (uid, n)).fetchall()

def db_save_deposit(uid, amt, phone, txn_ref):
    with _c() as c:
        c.execute("INSERT INTO deposits(user_id,amount,phone,txn_ref,status,created_at)"
                  " VALUES(?,?,?,?,'Pending',?)",
                  (uid, amt, phone, txn_ref, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def db_stats():
    with _c() as c:
        u  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        o  = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        op = c.execute("SELECT COUNT(*) FROM orders WHERE status='Processing'").fetchone()[0]
        oc = c.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
        rv = c.execute("SELECT COALESCE(SUM(amount),0) FROM orders").fetchone()[0]
        pr = c.execute("SELECT COALESCE(SUM(profit),0) FROM orders").fetchone()[0]
        dp = c.execute("SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='Completed'").fetchone()[0]
        bn = c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    return u, o, op, oc, rv, pr, dp, bn

def db_all_users(limit=30, offset=0):
    with _c() as c:
        return c.execute("SELECT user_id,username,first_name,balance,total_orders,"
                         "total_spent,total_deposit,is_banned,joined_at"
                         " FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?",
                         (limit, offset)).fetchall()

def db_all_ids():
    with _c() as c:
        return [r[0] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]

def db_all_orders_adm(n=20):
    with _c() as c:
        return c.execute("SELECT o.order_id,u.username,u.first_name,o.service_name,o.quantity,"
                         "o.amount,o.profit,o.status,o.created_at FROM orders o"
                         " JOIN users u ON o.user_id=u.user_id ORDER BY o.order_id DESC LIMIT ?",
                         (n,)).fetchall()

def db_search(q):
    p = f"%{q}%"
    with _c() as c:
        return c.execute("SELECT user_id,username,first_name,balance,total_orders,is_banned"
                         " FROM users WHERE username LIKE ? OR first_name LIKE ?"
                         " OR CAST(user_id AS TEXT) LIKE ?", (p,p,p)).fetchall()

def db_log(adm_id, action, tid, detail):
    with _c() as c:
        c.execute("INSERT INTO admin_logs(admin_id,action,target_id,detail,created_at)"
                  " VALUES(?,?,?,?,?)",
                  (adm_id, action, tid, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def db_handle_refer(new_uid, ref_uid) -> bool:
    with _c() as c:
        r = c.execute("SELECT refer_by FROM users WHERE user_id=?", (new_uid,)).fetchone()
        if r and r[0] != 0: return False
        c.execute("UPDATE users SET refer_by=? WHERE user_id=?", (ref_uid, new_uid))
        c.execute("UPDATE users SET refer_count=refer_count+1 WHERE user_id=?", (ref_uid,))
    return True

# ══════════════════════════════════════════════════════════════
#  SMM PANEL API
# ══════════════════════════════════════════════════════════════
def smm_order(sid, link, qty):
    try:
        r = requests.post(SMM_PANEL_URL, timeout=20,
                          data={"key":SMM_PANEL_KEY,"action":"add",
                                "service":sid,"link":link,"quantity":qty})
        j = r.json(); return j.get("order"), j.get("error")
    except Exception as e: return None, str(e)

def smm_balance():
    try:
        r = requests.post(SMM_PANEL_URL, timeout=15,
                          data={"key":SMM_PANEL_KEY,"action":"balance"})
        j = r.json(); return j.get("balance","N/A"), j.get("currency","BDT")
    except: return "N/A", "N/A"

# ══════════════════════════════════════════════════════════════
#  PAYMENT GATEWAY
# ══════════════════════════════════════════════════════════════
def make_payment(uid, amt, phone):
    import random
    txn = f"RKX{uid}{random.randint(10000,99999)}"
    payload = json.dumps({
        "success_url": f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "cancel_url":  f"https://t.me/{BOT_USERNAME.lstrip('@')}",
        "metadata":    {"phone": phone, "user_id": str(uid), "txn": txn},
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
            resp = requests.post(AUTOPAY_URL, headers=hdrs, data=payload, timeout=35)
            j    = resp.json()
            url  = j.get("payment_url") or j.get("url") or (j.get("data") or {}).get("payment_url")
            return (url, txn, j) if url else (None, txn, j)
        except requests.exceptions.Timeout:
            if attempt == 2: return None, txn, "পেমেন্ট সার্ভার সাড়া দিচ্ছে না।"
        except Exception as e: return None, txn, str(e)
    return None, txn, "সর্বোচ্চ চেষ্টা শেষ।"

# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
async def is_member(bot, uid):
    for ch in REQUIRED_CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ("left","kicked","banned"): return False
        except: return False
    return True

async def typ(bot, cid, delay=0.0):
    """Send typing action — delay শুধু দরকার হলে দাও, default 0"""
    try:
        await bot.send_chat_action(cid, ChatAction.TYPING)
        if delay > 0:
            await asyncio.sleep(delay)
    except:
        pass

def se(s): return "✅" if s=="Completed" else "⏳" if s=="Processing" else "❌"
def u2s(un, fn): return f"@{un}" if un else (fn or "Unknown")
def fname(u): return u.first_name or u.username or str(u.id)

# ══════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db_upsert(u.id, u.username, u.first_name)

    # referral deep link
    refer_by = 0
    if ctx.args and ctx.args[0].startswith("ref_"):
        try: refer_by = int(ctx.args[0][4:])
        except: pass
    if refer_by and refer_by != u.id:
        if db_handle_refer(u.id, refer_by):
            rqty = gs("refer_qty","100")
            try:
                await ctx.bot.send_message(refer_by,
                    f"🎉 *রেফার সফল!*\n"
                    f"👤 *{fname(u)}* আপনার লিংক দিয়ে জয়েন করেছে!\n"
                    f"🎁 পুরস্কার: *{rqty} Telegram Members*\n"
                    f"📩 ক্লেম: /refer_claim", parse_mode="Markdown")
            except: pass

    ctx.user_data.clear()
    await typ(ctx.bot, update.effective_chat.id)

    if gs("bot_active","1") != "1" and u.id != ADMIN_ID:
        await update.message.reply_text("⚠️ বট সাময়িকভাবে বন্ধ।"); return

    if db_banned(u.id):
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    if not await is_member(ctx.bot, u.id):
        await update.message.reply_text(
            "⛔ *বট ব্যবহারের আগে আমাদের চ্যানেলে জয়েন করুন* ⬇️\n\n"
            "➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE\n\n"
            "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
            reply_markup=join_kb(), parse_mode="Markdown"); return

    await update.message.reply_text(
        f"{WELCOME}\n\nস্বাগতম, *{fname(u)}!* 👋",
        reply_markup=MAIN_KB, parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
#  /refer  /refer_claim
# ══════════════════════════════════════════════════════════════
async def cmd_refer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u    = update.effective_user
    link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start=ref_{u.id}"
    row  = db_user(u.id)
    rc   = row[7] if row else 0
    rqty = gs("refer_qty","100")
    await update.message.reply_text(
        f"👥 *রেফার প্রোগ্রাম*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 প্রতি রেফারে: *{rqty} Telegram Members ফ্রী!*\n\n"
        f"🔗 আপনার লিংক:\n`{link}`\n\n"
        f"📊 মোট রেফার: *{rc} জন*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 লিংক শেয়ার করুন, পুরস্কার পাবেন!",
        parse_mode="Markdown")

async def cmd_refer_claim(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📩 রেফার ক্লেম করতে সাপোর্টে যোগাযোগ করুন:\n👉 {SUPPORT_USERNAME}")

# ══════════════════════════════════════════════════════════════
#  DAILY BROADCAST JOB
# ══════════════════════════════════════════════════════════════
async def daily_job(ctx: ContextTypes.DEFAULT_TYPE):
    uids = db_all_ids()
    sent = fail = 0
    logging.info(f"📢 Daily broadcast → {len(uids)} users")
    for uid in uids:
        try:
            await ctx.bot.send_message(uid, DAILY_MSG, reply_markup=MAIN_KB)
            sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    logging.info(f"📢 Done: ✅{sent} ❌{fail}")
    try: await ctx.bot.send_message(ADMIN_ID, f"📢 Daily broadcast!\n✅ Sent: {sent} | ❌ Fail: {fail}")
    except: pass

# ══════════════════════════════════════════════════════════════
#  /admin
# ══════════════════════════════════════════════════════════════
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!"); return
    ctx.user_data.clear()
    await typ(ctx.bot, update.effective_chat.id)
    u2, o, op, oc, rv, pr, dp, bn = db_stats()
    bal, cur = smm_balance()
    await update.message.reply_text(
        f"🔐 *{BOT_NAME} — Admin Panel*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 ইউজার: {u2} | 🚫 Banned: {bn}\n"
        f"📦 অর্ডার: {o} | ⏳{op} ✅{oc}\n"
        f"💰 Revenue: {rv:.2f}৳\n"
        f"📈 Profit: {pr:.2f}৳\n"
        f"💳 Deposits: {dp:.2f}৳\n"
        f"🖥️ Panel: {bal} {cur}\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        reply_markup=admin_inline_kb(), parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
#  ADMIN SHORTCUT COMMANDS
# ══════════════════════════════════════════════════════════════
async def cmd_addbalance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); amt = float(ctx.args[1])
        db_add_bal(tid, amt); nb = db_bal(tid)
        db_log(ADMIN_ID, "addbalance", tid, f"+{amt}")
        await update.message.reply_text(f"✅ {tid} → +{amt}৳ | নতুন: {nb:.2f}৳")
        try: await ctx.bot.send_message(tid,
            f"✅ *ব্যালেন্স যোগ!*\n💰 +{amt} টাকা\n💵 নতুন: {nb:.2f}৳", parse_mode="Markdown")
        except: pass
    except Exception as e: await update.message.reply_text(f"Usage: /addbalance <uid> <amt>\n{e}")

async def cmd_ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban(tid, True)
        db_log(ADMIN_ID, "ban", tid, "")
        await update.message.reply_text(f"🚫 {tid} banned.")
    except Exception as e: await update.message.reply_text(f"Usage: /ban <uid>\n{e}")

async def cmd_unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        tid = int(ctx.args[0]); db_ban(tid, False)
        db_log(ADMIN_ID, "unban", tid, "")
        await update.message.reply_text(f"✅ {tid} unbanned.")
    except Exception as e: await update.message.reply_text(f"Usage: /unban <uid>\n{e}")

async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /broadcast <msg>"); return
    msg = " ".join(ctx.args); uids = db_all_ids()
    sent = fail = 0
    await update.message.reply_text(f"📢 Sending to {len(uids)}...")
    for uid in uids:
        try: await ctx.bot.send_message(uid, f"📢 *{BOT_NAME}*\n━━━━━━━━━━━━\n{msg}", parse_mode="Markdown"); sent += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Done! ✅{sent} ❌{fail}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    u2,o,op,oc,rv,pr,dp,bn = db_stats(); bal,cur = smm_balance()
    await update.message.reply_text(
        f"📊 *Stats*\n━━━━━━━━━━━━\n"
        f"👥 {u2} | 🚫 {bn}\n📦 {o} | ⏳{op} ✅{oc}\n"
        f"💰 {rv:.2f}৳ | 📈 {pr:.2f}৳\n💳 {dp:.2f}৳\n🖥️ {bal} {cur}",
        parse_mode="Markdown")

async def cmd_myorders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db_orders(update.effective_user.id, 10)
    if not rows: await update.message.reply_text("📦 কোনো অর্ডার নেই।"); return
    msg = "📦 *আপনার সর্বশেষ অর্ডার*\n━━━━━━━━━━━━━━━\n"
    for r in rows:
        msg += f"{se(r[4])} `#{r[0]}` — {r[1]}\n   🔢{r[2]:,} | 💸{r[3]:.2f}৳\n   📅{r[5][:16]}\n─────────\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_setprice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        key = ctx.args[0]; price = float(ctx.args[1])
        svc = find_svc(key)
        if not svc: await update.message.reply_text("❌ Key পাওয়া যায়নি।"); return
        svc["price"] = price
        await update.message.reply_text(f"✅ {svc['name']} → {price}৳/১০০০")
    except Exception as e: await update.message.reply_text(f"Usage: /setprice <key> <price>\n{e}")

# ══════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════
async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    d = q.data; u = q.from_user; cid = q.message.chat.id

    # ── Join check ────────────────────────────────────────────
    if d == "check_join":
        await typ(ctx.bot, cid)
        if not await is_member(ctx.bot, u.id):
            await q.answer("❌ দুটো চ্যানেলেই জয়েন করো!", show_alert=True); return
        db_upsert(u.id, u.username, u.first_name)
        await q.message.delete()
        await ctx.bot.send_message(u.id,
            f"{WELCOME}\n\nস্বাগতম, *{fname(u)}!* 👋",
            reply_markup=MAIN_KB, parse_mode="Markdown"); return

    # ── Deposit from balance screen ───────────────────────────
    if d == "goto_deposit":
        ctx.user_data.clear(); ctx.user_data["dstep"] = "amt"
        await q.edit_message_text(
            "💳 *ডিপোজিট*\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও? (সর্বনিম্ন ১০৳)\n\n🔢 সংখ্যা লিখো:",
            parse_mode="Markdown"); return

    # ── Order confirm/cancel ──────────────────────────────────
    if d == "confirm_order":
        await _do_confirm(q, ctx); return

    if d == "cancel_order":
        ctx.user_data.clear()
        await q.edit_message_text("❌ অর্ডার বাতিল।"); return

    # ── ADMIN callbacks ───────────────────────────────────────
    if u.id != ADMIN_ID: return

    bk = [[_ib("🔙 Back", "adm_back")]]

    if d == "adm_stats":
        u2,o,op,oc,rv,pr,dp,bn = db_stats(); bal,cur = smm_balance()
        await q.edit_message_text(
            f"📊 *Full Stats*\n━━━━━━━━━━━━\n"
            f"👥 {u2} | 🚫 {bn}\n📦 {o} | ⏳{op} ✅{oc}\n"
            f"💰 {rv:.2f}৳ | 📈 {pr:.2f}৳\n💳 {dp:.2f}৳\n🖥️ {bal} {cur}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(bk))

    elif d == "adm_users":
        rows = db_all_users(20)
        msg = "👥 *Users (Last 20)*\n━━━━━━━━━━━━\n"
        kb2 = []
        for row in rows:
            uid2,un2,fn2,b2,o2,_,_,ban2,_ = row
            bm = "🚫" if ban2 else "✅"
            u2n = u2s(un2, fn2)
            msg += f"{bm} {u2n} | `{uid2}` | {b2:.0f}৳ | {o2} ord\n"
            kb2.append([InlineKeyboardButton(f"{bm} {u2n} ({uid2})", callback_data=f"au_{uid2}")])
        kb2.extend(bk)
        await q.edit_message_text(msg[:4000], parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(kb2))

    elif d == "adm_addbal":
        ctx.user_data["adm_step"] = "addbal_uid"
        await q.edit_message_text("💰 *Balance যোগ*\nইউজার ID দাও:", parse_mode="Markdown")

    elif d == "adm_subbal":
        ctx.user_data["adm_step"] = "subbal_uid"
        await q.edit_message_text("💸 *Balance কমাও*\nইউজার ID দাও:", parse_mode="Markdown")

    elif d == "adm_ban":
        ctx.user_data["adm_step"] = "ban_uid"
        await q.edit_message_text("🚫 Ban করার User ID:")

    elif d == "adm_unban":
        ctx.user_data["adm_step"] = "unban_uid"
        await q.edit_message_text("✅ Unban করার User ID:")

    elif d == "adm_bc":
        ctx.user_data["adm_step"] = "broadcast_msg"
        await q.edit_message_text("📢 সব ইউজারকে কী মেসেজ পাঠাবে?")

    elif d == "adm_panelbal":
        bal, cur = smm_balance()
        await q.edit_message_text(
            f"💼 *Panel Balance*\n━━━━━━━━━━━━\n💰 {bal} {cur}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(bk))

    elif d == "adm_orders":
        rows = db_all_orders_adm()
        msg = "📦 *Last 20 Orders*\n━━━━━━━━━━━━\n"
        for r in rows:
            u2n = u2s(r[1],r[2])
            msg += f"{se(r[7])} `#{r[0]}` {u2n}\n  {r[3][:25]} | {r[4]:,} | {r[5]:.2f}৳\n"
        await q.edit_message_text(msg[:4000], parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(bk))

    elif d == "adm_settings":
        await q.edit_message_text(
            f"🔧 *Settings*\n━━━━━━━━━━━━\n"
            f"Commands:\n"
            f"`/setprice <key> <price>`\n"
            f"`/addbalance <uid> <amt>`\n"
            f"`/ban <uid>` | `/unban <uid>`\n"
            f"`/broadcast <msg>`\n"
            f"`/setreferqty <qty>`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(bk))

    elif d == "adm_boton":
        ss("bot_active","1"); await q.answer("✅ Bot চালু!", show_alert=True)
    elif d == "adm_botoff":
        ss("bot_active","0"); await q.answer("❌ Bot বন্ধ!", show_alert=True)

    elif d == "adm_back":
        u2,o,op,oc,rv,pr,dp,bn = db_stats(); bal,cur = smm_balance()
        await q.edit_message_text(
            f"🔐 *{BOT_NAME} — Admin Panel*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 {u2} | 🚫 {bn}\n📦 {o} | ⏳{op} ✅{oc}\n"
            f"💰 {rv:.2f}৳ | 📈 {pr:.2f}৳\n💳 {dp:.2f}৳\n🖥️ {bal} {cur}",
            reply_markup=admin_inline_kb(), parse_mode="Markdown")

    # user detail from admin panel
    elif d.startswith("au_"):
        tid = int(d[3:]); row = db_user(tid)
        if not row: await q.answer("Not found!", show_alert=True); return
        uid2,un2,fn2,b2,o2,s2,d2,rc2,_,ban2,jn2 = row
        bm = "🚫" if ban2 else "✅"
        u2n = u2s(un2,fn2)
        o_rows = db_orders(tid, 3)
        o_txt = "".join([f"  {se(r[4])} `#{r[0]}` {r[1][:20]} | {r[3]:.2f}৳\n" for r in o_rows]) or "  নেই"
        kb2 = [
            [_ib("💰 Add Balance", f"aab_{tid}"), _ib("💸 Sub Balance", f"asb_{tid}")],
            [_ib("🚫 Ban", f"abn_{tid}", "destructive"), _ib("✅ Unban", f"aub_{tid}")],
            [_ib("🔙 Back", "adm_users")],
        ]
        await q.edit_message_text(
            f"👤 {bm} {u2n}\n🆔 `{tid}`\n"
            f"💰 {b2:.2f}৳ | 📦 {o2} | 💸 {s2:.2f}৳\n"
            f"💳 Dep: {d2:.2f}৳ | 👥 Refer: {rc2}\n"
            f"📅 {(jn2 or '')[:10]}\n\n📦 Recent:\n{o_txt}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb2))

    elif d.startswith("aab_"):
        tid = int(d[4:]); ctx.user_data["adm_target"]=tid; ctx.user_data["adm_step"]="addbal_amt"
        await q.edit_message_text(f"💰 User `{tid}` কত টাকা যোগ করবে?", parse_mode="Markdown")

    elif d.startswith("asb_"):
        tid = int(d[4:]); ctx.user_data["adm_target"]=tid; ctx.user_data["adm_step"]="subbal_amt"
        await q.edit_message_text(f"💸 User `{tid}` কত টাকা কমাবে?", parse_mode="Markdown")

    elif d.startswith("abn_"):
        tid = int(d[4:]); db_ban(tid, True); db_log(u.id,"ban",tid,"panel")
        await q.answer(f"🚫 {tid} banned!", show_alert=True)

    elif d.startswith("aub_"):
        tid = int(d[4:]); db_ban(tid, False); db_log(u.id,"unban",tid,"panel")
        await q.answer(f"✅ {tid} unbanned!", show_alert=True)

# ══════════════════════════════════════════════════════════════
#  CONFIRM ORDER (from callback)
# ══════════════════════════════════════════════════════════════
async def _do_confirm(q, ctx):
    u    = q.from_user
    svc  = find_svc(ctx.user_data.get("sel",""))
    link = ctx.user_data.get("link")
    qty  = ctx.user_data.get("qty")
    amt  = ctx.user_data.get("amt")
    cost = ctx.user_data.get("cost", 0)

    if not all([svc, link, qty, amt]):
        await q.edit_message_text("❌ কিছু ভুল হয়েছে। আবার /start দাও।")
        ctx.user_data.clear(); return

    bal = db_bal(u.id)
    if bal < amt:
        await q.edit_message_text(
            f"❌ *ব্যালেন্স কম!*\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_ib("💳 Deposit করো","goto_deposit")]]))
        ctx.user_data.clear(); return

    await q.edit_message_text("⏳ অর্ডার প্রসেস হচ্ছে...")
    await ctx.bot.send_chat_action(q.message.chat.id, ChatAction.TYPING)
    pid, err = smm_order(svc["sid"], link, qty)
    if err and not pid:
        await q.edit_message_text(f"❌ অর্ডার ব্যর্থ!\nকারণ: {err}\n\n🆘 {SUPPORT_USERNAME}"); return

    db_add_bal(u.id, -amt)
    oid = db_save_order(u.id, ctx.user_data.get("sel"), svc["name"],
                        link, qty, amt, cost, str(pid or "N/A"))
    nb = db_bal(u.id)

    await q.edit_message_text(
        f"✅ *অর্ডার সফল!*\n"
        f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
        f"👤 নাম: {fname(u)}\n"
        f"🆔 Order ID: `{oid}`\n"
        f"🛒 {svc['name']}\n"
        f"🔢 {qty:,} | 💸 {amt:.2f}৳\n"
        f"💰 বাকি: {nb:.2f}৳\n"
        f"📊 Status: ⏳ Processing\n"
        f"━━━━━━━━━━━•❈•━━━━━━━━━━━",
        parse_mode="Markdown")

    try:
        await ctx.bot.send_message(LOG_CHANNEL,
            f"📌 *{BOT_NAME} — New Order*\n"
            f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
            f"🆔 `{oid}` | 👤 {u2s(u.username,u.first_name)} ({u.id})\n"
            f"🛒 {svc['name']}\n"
            f"🔢 {qty:,} | 💸 {amt:.2f}৳ | 📈 {round(amt-cost,2):.2f}৳ profit",
            parse_mode="Markdown")
    except: pass
    ctx.user_data.clear()

# ══════════════════════════════════════════════════════════════
#  MAIN TEXT HANDLER
# ══════════════════════════════════════════════════════════════
async def txt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u    = update.effective_user
    t    = (update.message.text or "").strip()
    step = ctx.user_data.get("step")
    ds   = ctx.user_data.get("dstep")
    adm  = ctx.user_data.get("adm_step")
    fn   = fname(u)

    await typ(ctx.bot, update.effective_chat.id)

    if gs("bot_active","1") != "1" and u.id != ADMIN_ID:
        await update.message.reply_text("⚠️ বট সাময়িকভাবে বন্ধ।"); return

    if db_banned(u.id) and u.id != ADMIN_ID:
        await update.message.reply_text("🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    # ══ ADMIN STEP FLOWS ══════════════════════════════════════
    if adm and u.id == ADMIN_ID:

        if adm == "addbal_uid":
            if not t.isdigit(): await update.message.reply_text("❌ সঠিক ID!"); return
            ctx.user_data["adm_target"]=int(t); ctx.user_data["adm_step"]="addbal_amt"
            await update.message.reply_text(f"💰 User {t} কত টাকা?"); return

        if adm == "addbal_amt":
            try:
                amt=float(t); tid=ctx.user_data.get("adm_target")
                db_add_bal(tid,amt); nb=db_bal(tid); db_log(ADMIN_ID,"addbalance",tid,f"+{amt}")
                await update.message.reply_text(f"✅ {tid} → +{amt}৳ | নতুন: {nb:.2f}৳")
                try: await ctx.bot.send_message(tid,
                    f"✅ *ব্যালেন্স যোগ!*\n💰 +{amt} টাকা\n💵 নতুন: {nb:.2f}৳", parse_mode="Markdown")
                except: pass
            except: await update.message.reply_text("❌ সঠিক পরিমাণ!")
            ctx.user_data.pop("adm_step",None); ctx.user_data.pop("adm_target",None); return

        if adm == "subbal_uid":
            if not t.isdigit(): await update.message.reply_text("❌ সঠিক ID!"); return
            ctx.user_data["adm_target"]=int(t); ctx.user_data["adm_step"]="subbal_amt"
            await update.message.reply_text(f"💸 User {t} কত টাকা কমাবে?"); return

        if adm == "subbal_amt":
            try:
                amt=float(t); tid=ctx.user_data.get("adm_target")
                db_add_bal(tid,-amt); nb=db_bal(tid); db_log(ADMIN_ID,"subbalance",tid,f"-{amt}")
                await update.message.reply_text(f"✅ {tid} → -{amt}৳ | নতুন: {nb:.2f}৳")
            except: await update.message.reply_text("❌ সঠিক পরিমাণ!")
            ctx.user_data.pop("adm_step",None); ctx.user_data.pop("adm_target",None); return

        if adm == "ban_uid":
            if not t.isdigit(): await update.message.reply_text("❌ সঠিক ID!"); return
            tid=int(t); db_ban(tid,True); db_log(ADMIN_ID,"ban",tid,"")
            await update.message.reply_text(f"🚫 {tid} banned.")
            ctx.user_data.pop("adm_step",None); return

        if adm == "unban_uid":
            if not t.isdigit(): await update.message.reply_text("❌ সঠিক ID!"); return
            tid=int(t); db_ban(tid,False); db_log(ADMIN_ID,"unban",tid,"")
            await update.message.reply_text(f"✅ {tid} unbanned.")
            ctx.user_data.pop("adm_step",None); return

        if adm == "broadcast_msg":
            uids=db_all_ids(); sent=fail=0
            await update.message.reply_text(f"📢 Sending to {len(uids)}...")
            for uid5 in uids:
                try: await ctx.bot.send_message(uid5,f"📢 *{BOT_NAME}*\n━━━━━━━━━━━━\n{t}",parse_mode="Markdown"); sent+=1
                except: fail+=1
                await asyncio.sleep(0.05)
            await update.message.reply_text(f"✅ Done! ✅{sent} ❌{fail}")
            ctx.user_data.pop("adm_step",None); return

        if adm == "search_user":
            rows = db_search(t)
            if not rows: await update.message.reply_text("❌ কেউ পাওয়া যায়নি।"); return
            msg="🔍 Results:\n"; kb=[]
            for r in rows:
                uid2,un2,fn2,b2,o2,ban2 = r
                bm="🚫" if ban2 else "✅"; u2n=u2s(un2,fn2)
                msg+=f"{bm} {u2n} | {uid2} | {b2:.0f}৳\n"
                kb.append([InlineKeyboardButton(f"{bm} {u2n} ({uid2})",callback_data=f"au_{uid2}")])
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            ctx.user_data.pop("adm_step",None); return

    # ══ PERMANENT MAIN MENU BUTTONS ════════════════════════════
    if t == "🛒 Order":
        if not await is_member(ctx.bot, u.id):
            await update.message.reply_text(
                "⛔ আগে চ্যানেলে জয়েন করো!\n➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE",
                reply_markup=join_kb()); return
        ctx.user_data.clear(); ctx.user_data["in_order"] = True
        await update.message.reply_text(
            f"🏪 *সার্ভিস বেছে নিন* 👇\n\n💰 ব্যালেন্স: *{db_bal(u.id):.2f}৳*",
            reply_markup=order_cat_kb(), parse_mode="Markdown"); return

    if t == "🔙 Main Menu":
        ctx.user_data.clear()
        await update.message.reply_text(WELCOME, reply_markup=MAIN_KB, parse_mode="Markdown"); return

    # ── Category buttons ──────────────────────────────────────
    CAT_MAP = {
        "🎵 TikTok":    "tiktok",
        "📘 Facebook":  "facebook",
        "✈️ Telegram":  "telegram",
        "🎬 YouTube":   "youtube",
        "📸 Instagram": "instagram",
    }
    if t in CAT_MAP and ctx.user_data.get("in_order"):
        cat_key = CAT_MAP[t]
        ctx.user_data["cat"] = cat_key
        cat = SERVICES[cat_key]
        await update.message.reply_text(
            f"{cat['name']} Services 👇\n\n💰 ব্যালেন্স: *{db_bal(u.id):.2f}৳*",
            reply_markup=svc_kb(cat["items"]), parse_mode="Markdown"); return

    if t == "🔙 Back" and ctx.user_data.get("in_order"):
        ctx.user_data.pop("cat",None); ctx.user_data.pop("step",None)
        await update.message.reply_text(
            f"🏪 *সার্ভিস বেছে নিন* 👇\n\n💰 ব্যালেন্স: *{db_bal(u.id):.2f}৳*",
            reply_markup=order_cat_kb(), parse_mode="Markdown"); return

    # ── Service selected ──────────────────────────────────────
    if t in SVC_MAP and ctx.user_data.get("in_order"):
        svc_key = SVC_MAP[t]; svc = find_svc(svc_key)
        ctx.user_data["sel"]  = svc_key
        ctx.user_data["step"] = "link"
        await update.message.reply_text(
            f"✅ *{svc['name']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ {svc.get('desc','')}\n\n"
            f"💰 ব্যালেন্স: *{db_bal(u.id):.2f}৳*\n"
            f"📊 মূল্য: *{svc['price']}৳ / ১০০০*\n"
            f"📉 Min: {svc['min']:,}  |  📈 Max: {svc['max']:,}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔗 পোস্ট/প্রোফাইল লিংক দাও:",
            reply_markup=CANCEL_KB, parse_mode="Markdown"); return

    if t == "❌ Cancel":
        ctx.user_data.clear()
        await update.message.reply_text("❌ বাতিল।", reply_markup=MAIN_KB); return

    # ── Order: link ───────────────────────────────────────────
    if step == "link":
        if not (t.startswith("http://") or t.startswith("https://")):
            await update.message.reply_text(
                "❌ সঠিক লিংক দাও! http/https দিয়ে শুরু হতে হবে।",
                reply_markup=CANCEL_KB); return
        ctx.user_data["link"] = t
        ctx.user_data["step"] = "qty"
        svc = find_svc(ctx.user_data.get("sel",""))
        await update.message.reply_text(
            f"✅ লিংক পেয়েছি!\n\n"
            f"💰 ব্যালেন্স: *{db_bal(u.id):.2f}৳*\n"
            f"📊 *{svc['price']}৳ / ১০০০*\n"
            f"📉 Min: {svc['min']:,}  |  📈 Max: {svc['max']:,}\n\n"
            f"🔢 পরিমাণ লিখো:",
            reply_markup=CANCEL_KB, parse_mode="Markdown"); return

    # ── Order: quantity ───────────────────────────────────────
    if step == "qty":
        if not t.isdigit():
            await update.message.reply_text("❌ শুধু সংখ্যা লিখো!", reply_markup=CANCEL_KB); return
        qty = int(t); svc = find_svc(ctx.user_data.get("sel",""))
        if qty < svc["min"] or qty > svc["max"]:
            await update.message.reply_text(
                f"❌ *{svc['min']:,}* – *{svc['max']:,}* এর মধ্যে হতে হবে!",
                reply_markup=CANCEL_KB, parse_mode="Markdown"); return
        amt  = round((qty/1000)*svc["price"], 2)
        cost = round((qty/1000)*svc["cost"],  2)
        bal  = db_bal(u.id)
        if bal < amt:
            await update.message.reply_text(
                f"❌ *ব্যালেন্স কম!*\n💰 আছে: {bal:.2f}৳  |  দরকার: {amt:.2f}৳\n\n💳 ডিপোজিট করুন।",
                reply_markup=MAIN_KB, parse_mode="Markdown")
            ctx.user_data.clear(); return
        ctx.user_data.update({"qty":qty,"amt":amt,"cost":cost,"step":"confirm"})
        await update.message.reply_text(
            f"📋 *অর্ডার সারসংক্ষেপ*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 নাম: {fn}\n"
            f"🛒 {svc['name']}\n"
            f"🔗 {ctx.user_data['link']}\n"
            f"🔢 {qty:,}\n"
            f"💸 মোট: *{amt:.2f}৳*\n"
            f"💰 অর্ডারের পরে: {bal-amt:.2f}৳\n"
            f"━━━━━━━━━━━━━━━━━━\n✅ কনফার্ম করবেন?",
            reply_markup=confirm_kb(), parse_mode="Markdown"); return

    # ── Balance ───────────────────────────────────────────────
    if t == "💰 Balance":
        row  = db_user(u.id)
        bal  = row[3] if row else 0.0
        tot  = row[4] if row else 0
        sp   = row[5] if row else 0.0
        dep  = row[6] if row else 0.0
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💳 *অ্যাকাউন্ট ব্যালেন্স*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 নাম : {fn}\n"
            f"🆔 User ID : `{u.id}`\n"
            f"💰 ব্যালেন্স : *{bal:.2f} টাকা*\n"
            f"📦 Total Orders : {tot}\n"
            f"💵 Total Spent : {sp:.2f} টাকা\n"
            f"💳 Total Deposit : {dep:.2f} টাকা\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=balance_kb(), parse_mode="Markdown"); return

    # ── Deposit ───────────────────────────────────────────────
    if t == "💳 Deposit":
        ctx.user_data.clear(); ctx.user_data["dstep"] = "amt"
        await update.message.reply_text(
            "💳 *ডিপোজিট*\n━━━━━━━━━━━━━\n"
            "কত টাকা ডিপোজিট করতে চাও?\n(সর্বনিম্ন ১০ টাকা)\n\n🔢 শুধু সংখ্যা লিখো:",
            reply_markup=CANCEL_KB, parse_mode="Markdown"); return

    # ── Order Status ──────────────────────────────────────────
    if t == "📦 Order Status":
        rows = db_orders(u.id)
        if not rows: await update.message.reply_text("📦 এখনো কোনো অর্ডার নেই।"); return
        msg = "📦 *সর্বশেষ ৫টি অর্ডার:*\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            msg += (f"{se(r[4])} `#{r[0]}` | {r[1]}\n"
                    f"   🔢{r[2]:,} | 💸{r[3]:.2f}৳\n"
                    f"   📅{r[5][:16]}\n─────────\n")
        await update.message.reply_text(msg, parse_mode="Markdown"); return

    # ── Support ───────────────────────────────────────────────
    if t == "🆘 Support":
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━\n"
            "🔒 𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 𝗦𝗨𝗣𝗣𝗢𝗥𝗧\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📌 বট থেকে অর্ডার করার নিয়ম:\n"
            "🔗 https://t.me/RKXPremiumZone/84\n\n"
            "📌 বটে টাকা অ্যাড করার নিয়ম:\n"
            "🔗 https://t.me/RKXPremiumZone/86\n\n"
            "‼️ ভুল বা প্রাইভেট লিংক অর্ডার করবেন না।\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🕒 ২৪/৭ সাপোর্টের জন্য",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📩 Contact Support",
                                     url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")
            ]])); return

    # ── Price & Info ──────────────────────────────────────────
    if t == "📋 Price & Info":
        msg = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📲 *RKX SMM ZONE – SERVICE LIST*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for cat in SERVICES.values():
            msg += f"\n{cat['name']}\n"
            for s in cat["items"].values():
                msg += f"  • {s['name']}: *{s['price']}৳*/১০০০ (Min:{s['min']:,})\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ ৩০ মিনিটে অর্ডার কমপ্লিট\n🛡 গ্যারান্টি সহ সার্ভিস"
        # Split if too long
        for chunk in [msg[i:i+4000] for i in range(0,len(msg),4000)]:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        return

    # ── Refer ─────────────────────────────────────────────────
    if t == "👥 Refer":
        await cmd_refer(update, ctx); return

    # ── Free Service ──────────────────────────────────────────
    if t == "🎁 Free Service":
        offer = gs("free_offer", FREE_OFFER)
        await update.message.reply_text(offer, parse_mode="Markdown"); return

    # ══ DEPOSIT FLOW ══════════════════════════════════════════
    if ds == "amt":
        if not t.isdigit() or int(t) < 10:
            await update.message.reply_text(
                "❌ সর্বনিম্ন *১০ টাকা!*", parse_mode="Markdown"); return
        ctx.user_data["damt"]  = int(t)
        ctx.user_data["dstep"] = "phone"
        await update.message.reply_text(
            "📱 ফোন নম্বর দাও\n(যেটা দিয়ে পেমেন্ট করবে)\n\nযেমন: 01712345678",
            reply_markup=CANCEL_KB); return

    if ds == "phone":
        amt5   = ctx.user_data.get("damt"); phone = t
        await update.message.reply_text("⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        await typ(ctx.bot, update.effective_chat.id)

        import random as _r
        txn = f"RKX{u.id}{_r.randint(10000,99999)}"
        pay_url, txn_ref, raw = make_payment(u.id, amt5, phone)
        ctx.user_data.clear()

        if pay_url:
            db_save_deposit(u.id, amt5, phone, txn_ref)
            # update deposit total
            with _c() as conn: conn.execute(
                "UPDATE users SET total_deposit=ROUND(total_deposit+?,2) WHERE user_id=?",
                (amt5, u.id))
            oid = _r.randint(100000000, 999999999)
            await update.message.reply_text(
                f"✅ *পেমেন্ট লিংক তৈরি হয়েছে*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"👤 নাম: {fn}\n"
                f"💰 পরিমাণ: *{amt5:.2f}৳*\n"
                f"➕ মোট যোগ হবে: *{amt5:.2f}৳*\n"
                f"🧾 অর্ডার আইডি: `{oid}`\n\n"
                f"👉 নিচের *Pay Now* বাটনে পেমেন্ট করুন।\n"
                f"━━━━━━━━━━━━━━",
                reply_markup=deposit_btn_kb(pay_url),
                parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"❌ *পেমেন্ট লিংক তৈরি হয়নি।*\n"
                f"কারণ: {raw}\n\n🆘 {SUPPORT_USERNAME}",
                reply_markup=MAIN_KB, parse_mode="Markdown")
        return

    # ══ UNKNOWN / GARBAGE TEXT → show main menu ════════════════
    if not step and not ds and not adm and not ctx.user_data.get("in_order"):
        ctx.user_data.clear()
        await update.message.reply_text(WELCOME, reply_markup=MAIN_KB, parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
#  ADMIN EXTRA COMMANDS
# ══════════════════════════════════════════════════════════════
async def cmd_setreferqty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        qty = int(ctx.args[0]); ss("refer_qty", str(qty))
        await update.message.reply_text(f"✅ রেফার রিওয়ার্ড: {qty}")
    except Exception as e: await update.message.reply_text(f"Usage: /setreferqty <qty>\n{e}")

async def cmd_setoffer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /setoffer <text>"); return
    ss("free_offer", " ".join(ctx.args))
    await update.message.reply_text("✅ অফার আপডেট।")

async def cmd_userinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        row = db_user(int(ctx.args[0]))
        if not row: await update.message.reply_text("❌ পাওয়া যায়নি।"); return
        uid2,un2,fn2,b2,o2,s2,d2,rc2,_,ban2,jn2 = row
        await update.message.reply_text(
            f"👤 *User Info*\n━━━━━━━━━━━━\n"
            f"🆔 `{uid2}`\n📛 {fn2}\n🔗 @{un2 or 'N/A'}\n"
            f"💰 {b2:.2f}৳ | 📦 {o2} | 💸 {s2:.2f}৳\n"
            f"💳 Dep: {d2:.2f}৳ | 👥 Refer: {rc2}\n"
            f"🚫 Banned: {'Yes' if ban2 else 'No'}\n📅 {(jn2 or '')[:10]}",
            parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"Usage: /userinfo <uid>\n{e}")

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not ctx.args: await update.message.reply_text("Usage: /search <query>"); return
    rows = db_search(" ".join(ctx.args))
    if not rows: await update.message.reply_text("❌ কেউ পাওয়া যায়নি।"); return
    msg = "🔍 Results:\n"; kb = []
    for r in rows:
        uid2,un2,fn2,b2,o2,ban2 = r; bm = "🚫" if ban2 else "✅"; u2n = u2s(un2,fn2)
        msg += f"{bm} {u2n} | {uid2} | {b2:.0f}৳\n"
        kb.append([InlineKeyboardButton(f"{bm} {u2n} ({uid2})", callback_data=f"au_{uid2}")])
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    logging.basicConfig(
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        level=logging.INFO
    )
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    for cmd, fn in [
        ("start",        cmd_start),
        ("admin",        cmd_admin),
        ("addbalance",   cmd_addbalance),
        ("ban",          cmd_ban),
        ("unban",        cmd_unban),
        ("broadcast",    cmd_broadcast),
        ("stats",        cmd_stats),
        ("myorders",     cmd_myorders),
        ("setprice",     cmd_setprice),
        ("userinfo",     cmd_userinfo),
        ("search",       cmd_search),
        ("setreferqty",  cmd_setreferqty),
        ("setoffer",     cmd_setoffer),
        ("refer",        cmd_refer),
        ("refer_claim",  cmd_refer_claim),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, txt))

    # Daily morning broadcast — UTC 00:00 = BD সকাল ৬টা
    app.job_queue.run_daily(
        daily_job,
        time=dtime(hour=DAILY_HOUR, minute=DAILY_MINUTE, second=0),
        name="daily_broadcast"
    )

    logging.info(f"✅ {BOT_NAME} চালু! Daily at UTC {DAILY_HOUR}:{DAILY_MINUTE:02d}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
