"""
╔══════════════════════════════════════════════════════════╗
║   𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 — Telegram SMM Bot                     ║
║   Uses raw HTTP (requests) — colored buttons supported   ║
║   Panel: rxsmm.top | Pay: rxpay.top                      ║
╚══════════════════════════════════════════════════════════╝
"""
import os, json, sqlite3, asyncio, logging, requests as req
from datetime import datetime, time as dtime
from aiohttp import web

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
TOKEN    = os.environ.get("BOT_TOKEN",     "8331448370:AAGEdB0uDT0NnvN3DjFtuyGMRO2W8zuINYg")
ADMIN_ID = int(os.environ.get("ADMIN_ID",  "7761133429"))
API_URL  = f"https://api.telegram.org/bot{TOKEN}"

SMM_URL  = "https://rxsmm.top/api/v2"
SMM_KEY  = os.environ.get("SMM_PANEL_KEY", "835b3643be911926e000093d583fb4e5")

PAY_API    = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
PAY_SECRET = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
PAY_BRAND  = "jp7ZgCTGj7X1YENParBkipjJnvyZIoNFDTLlOG3Y4ayNaue8bV"
PAY_DEVICE = "Dl6Vzy8T33bbGiUybEDYffaZqp2ZxtJ0cP0Ss1HB"
PAY_URL    = "https://pay.rxpay.top/api/payment/create"

LOG_CH   = "@RKXSMMZONE"
REQ_CH   = ["@RKXPremiumZone", "@RKXSMMZONE"]
BOT_NAME = "𝗥𝗞𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘"
BOT_USER = "@RKXSMMbot"
DB       = "rkx.db"

# ═══════════════════════════════════════
# SERVICES — rxsmm.top real IDs, +50%
# ═══════════════════════════════════════
SVCS = {
    # ── TikTok ──────────────────────────
    "tt_v1": {"cat":"tiktok","sub":"views",    "sid":"4233","cost":0.6145,"price":0.92, "min":100,  "max":10000000,   "name":"👁️ TikTok Views [1M-10M/Day]"},
    "tt_v2": {"cat":"tiktok","sub":"views",    "sid":"4234","cost":1.02,  "price":1.53, "min":100,  "max":2147483647, "name":"👁️ TikTok Views [10M/Day]"},
    "tt_v3": {"cat":"tiktok","sub":"views",    "sid":"4230","cost":1.07,  "price":1.60, "min":100,  "max":1000000000, "name":"👁️ TikTok Views [Unlimited]"},
    "tt_l1": {"cat":"tiktok","sub":"likes",    "sid":"4256","cost":2.91,  "price":4.37, "min":10,   "max":5000000,    "name":"❤️ TikTok Likes [No Refill]"},
    "tt_l2": {"cat":"tiktok","sub":"likes",    "sid":"4257","cost":3.16,  "price":4.74, "min":10,   "max":5000000,    "name":"❤️ TikTok Likes [R30] ♻️"},
    "tt_l3": {"cat":"tiktok","sub":"likes",    "sid":"4263","cost":3.19,  "price":4.79, "min":10,   "max":5000000,    "name":"❤️ TikTok Likes [Hidden]"},
    "tt_f1": {"cat":"tiktok","sub":"followers","sid":"4323","cost":1.0,   "price":1.50, "min":50,   "max":160000,     "name":"👥 TikTok Followers [Real R15]"},
    "tt_f2": {"cat":"tiktok","sub":"followers","sid":"4324","cost":1.0,   "price":1.50, "min":10,   "max":10000,      "name":"👥 TikTok Followers [Engagement]"},
    "tt_f3": {"cat":"tiktok","sub":"followers","sid":"4325","cost":1.0,   "price":1.50, "min":50,   "max":160000,     "name":"👥 TikTok Followers [Real R30]"},
    # ── Instagram ───────────────────────
    "ig_v1": {"cat":"instagram","sub":"views",    "sid":"2015","cost":0.1366,"price":0.20, "min":100,  "max":2147483647, "name":"👁️ IG Views [All Links Fast]"},
    "ig_v2": {"cat":"instagram","sub":"views",    "sid":"2016","cost":0.1821,"price":0.27, "min":100,  "max":3000000,    "name":"👁️ IG Views [1M/Day]"},
    "ig_v3": {"cat":"instagram","sub":"views",    "sid":"2017","cost":0.1821,"price":0.27, "min":100,  "max":2147483647, "name":"👁️ IG Views [10M/Day]"},
    "ig_l1": {"cat":"instagram","sub":"likes",    "sid":"2034","cost":16.23, "price":24.34,"min":100,  "max":1000000,    "name":"❤️ IG Likes [HQ]"},
    "ig_l2": {"cat":"instagram","sub":"likes",    "sid":"1836","cost":19.25, "price":28.88,"min":10,   "max":1000000,    "name":"❤️ IG Likes [Real]"},
    "ig_l3": {"cat":"instagram","sub":"likes",    "sid":"1837","cost":19.44, "price":29.16,"min":10,   "max":1000000,    "name":"❤️ IG Likes [Real R30]"},
    "ig_f1": {"cat":"instagram","sub":"followers","sid":"2135","cost":1.0,   "price":1.50, "min":10,   "max":1000,       "name":"👥 IG Followers [Real Any]"},
    "ig_f2": {"cat":"instagram","sub":"followers","sid":"2136","cost":1.0,   "price":1.50, "min":10,   "max":5000,       "name":"👥 IG Followers [Male]"},
    "ig_f3": {"cat":"instagram","sub":"followers","sid":"2137","cost":1.0,   "price":1.50, "min":30,   "max":5000,       "name":"👥 IG Followers [HQ]"},
    "ig_c1": {"cat":"instagram","sub":"comments", "sid":"2157","cost":1.0,   "price":1.50, "min":10,   "max":100,        "name":"💬 IG Comments [Emoji]"},
    "ig_c2": {"cat":"instagram","sub":"comments", "sid":"2159","cost":1.0,   "price":1.50, "min":1,    "max":100,        "name":"💬 IG Comments [Mix Real]"},
    "ig_sh": {"cat":"instagram","sub":"shares",   "sid":"2152","cost":2.03,  "price":3.04, "min":100,  "max":100000000,  "name":"🔁 IG Shares [250K/Day]"},
    # ── Telegram ────────────────────────
    "tg_m1": {"cat":"telegram","sub":"members",  "sid":"4486","cost":1.0,   "price":1.50, "min":10,   "max":20000,      "name":"👥 TG Members [Premium HQ]"},
    "tg_m2": {"cat":"telegram","sub":"members",  "sid":"4817","cost":1.68,  "price":2.52, "min":10,   "max":25000,      "name":"👥 TG Members [Cheapest]"},
    "tg_m3": {"cat":"telegram","sub":"members",  "sid":"4820","cost":6.28,  "price":9.42, "min":1,    "max":100000,     "name":"👥 TG Members [R7] ♻️"},
    "tg_m4": {"cat":"telegram","sub":"members",  "sid":"4822","cost":8.33,  "price":12.50,"min":1,    "max":100000,     "name":"👥 TG Members [R30] ♻️"},
    "tg_m5": {"cat":"telegram","sub":"members",  "sid":"4824","cost":9.58,  "price":14.37,"min":100,  "max":1000000,    "name":"👥 TG Members [R90] ♻️"},
    "tg_v1": {"cat":"telegram","sub":"views",    "sid":"4525","cost":0.2276,"price":0.34, "min":50,   "max":20000,      "name":"👁️ TG Views [1 Post URL]"},
    "tg_v2": {"cat":"telegram","sub":"views",    "sid":"4531","cost":0.2731,"price":0.41, "min":10,   "max":500000,     "name":"👁️ TG Views [1 Post Groups]"},
    "tg_v3": {"cat":"telegram","sub":"views",    "sid":"4555","cost":6.30,  "price":9.45, "min":1000, "max":40000,      "name":"👁️ TG Views [Last 5 Posts]"},
    "tg_v4": {"cat":"telegram","sub":"views",    "sid":"4556","cost":12.59, "price":18.89,"min":1000, "max":40000,      "name":"👁️ TG Views [Last 10 Posts]"},
    "tg_r1": {"cat":"telegram","sub":"reactions","sid":"4744","cost":20.98, "price":31.47,"min":10,   "max":1000000,    "name":"💎 TG Mix Reactions (+)"},
    "tg_r2": {"cat":"telegram","sub":"reactions","sid":"4748","cost":20.98, "price":31.47,"min":10,   "max":1000000,    "name":"👍 TG Reaction Like"},
    "tg_r3": {"cat":"telegram","sub":"reactions","sid":"4750","cost":20.98, "price":31.47,"min":10,   "max":1000000,    "name":"❤️ TG Reaction Heart"},
    "tg_st": {"cat":"telegram","sub":"stars",    "sid":"4509","cost":4.0,   "price":6.00, "min":1,    "max":10000,      "name":"⭐ TG Stars [Post]"},
    # ── Facebook ────────────────────────
    "fb_r1": {"cat":"facebook","sub":"reactions","sid":"3701","cost":20.30,"price":30.45,"min":10,  "max":500000,     "name":"👍 FB Like Reaction"},
    "fb_r2": {"cat":"facebook","sub":"reactions","sid":"3702","cost":20.30,"price":30.45,"min":10,  "max":500000,     "name":"❤️ FB Love Reaction"},
    "fb_r3": {"cat":"facebook","sub":"reactions","sid":"3703","cost":20.30,"price":30.45,"min":10,  "max":500000,     "name":"🤗 FB Care Reaction"},
    "fb_r4": {"cat":"facebook","sub":"reactions","sid":"3704","cost":20.30,"price":30.45,"min":10,  "max":500000,     "name":"😂 FB HaHa Reaction"},
    "fb_r5": {"cat":"facebook","sub":"reactions","sid":"3705","cost":20.30,"price":30.45,"min":10,  "max":500000,     "name":"😲 FB Wow Reaction"},
    "fb_pl": {"cat":"facebook","sub":"post_likes","sid":"3692","cost":37.10,"price":55.65,"min":10, "max":1000000,    "name":"👍 FB Post Likes [HQ]"},
    "fb_fo": {"cat":"facebook","sub":"followers","sid":"1846","cost":23.49, "price":35.23,"min":100, "max":50000,     "name":"👥 FB Followers [VN]"},
    # ── YouTube ─────────────────────────
    "yt_v1": {"cat":"youtube","sub":"views",  "sid":"1908","cost":1.0,  "price":1.50, "min":1000,"max":1000000,  "name":"👁️ YT Views [India Adword]"},
    "yt_v2": {"cat":"youtube","sub":"views",  "sid":"1909","cost":1.0,  "price":1.50, "min":1000,"max":1000000,  "name":"👁️ YT Views [Malaysia]"},
    "yt_v3": {"cat":"youtube","sub":"views",  "sid":"1910","cost":1.0,  "price":1.50, "min":1000,"max":1000000,  "name":"👁️ YT Views [Netherlands]"},
}

# Category structure for menus
CATS = {
    "tiktok":    {"label":"🎵 TikTok",    "subs":["views","likes","followers"]},
    "instagram": {"label":"📸 Instagram", "subs":["views","likes","followers","comments","shares"]},
    "telegram":  {"label":"✈️ Telegram",  "subs":["members","views","reactions","stars"]},
    "facebook":  {"label":"📘 Facebook",  "subs":["reactions","post_likes","followers"]},
    "youtube":   {"label":"🎬 YouTube",   "subs":["views"]},
}

SUB_LABELS = {
    "views":"👁️ Views","likes":"❤️ Likes","followers":"👥 Followers",
    "members":"👥 Members","comments":"💬 Comments","shares":"🔁 Shares",
    "reactions":"💎 Reactions","stars":"⭐ Stars","post_likes":"👍 Post Likes",
}

def svc_list(cat, sub):
    return {k:v for k,v in SVCS.items() if v["cat"]==cat and v["sub"]==sub}

# ═══════════════════════════════════════
# TELEGRAM API — raw HTTP
# ═══════════════════════════════════════
def tg(method, **kwargs):
    try:
        r = req.post(f"{API_URL}/{method}", json=kwargs, timeout=20)
        return r.json()
    except: return {}

def send(chat_id, text, kb=None, edit_msg_id=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode":"HTML"}
    if kb: payload["reply_markup"] = kb
    if edit_msg_id:
        payload["message_id"] = edit_msg_id
        return tg("editMessageText", **payload)
    return tg("sendMessage", **payload)

def answer_cb(cb_id, text="", alert=False):
    tg("answerCallbackQuery", callback_query_id=cb_id, text=text, show_alert=alert)

def typing(chat_id):
    tg("sendChatAction", chat_id=chat_id, action="typing")

def check_member(user_id, channel):
    r = tg("getChatMember", chat_id=channel, user_id=user_id)
    status = r.get("result",{}).get("status","left")
    return status not in ["left","kicked","banned"]

def all_members_ok(user_id):
    return all(check_member(user_id, ch) for ch in REQ_CH)

# ═══════════════════════════════════════
# BUTTON BUILDERS — with color style
# Blue=default | Red="destructive" | Green="secondary" (gray/green)
# ═══════════════════════════════════════
def ibtn(text, cb, style=None):
    """Inline button dict with optional style for color"""
    b = {"text": text, "callback_data": cb}
    if style: b["style"] = style
    return b

def rbtn(text, style=None):
    """Reply keyboard button dict"""
    b = {"text": text}
    if style: b["style"] = style
    return b

def inline_kb(rows):
    return {"inline_keyboard": rows}

def reply_kb(rows, resize=True, persistent=True):
    return {"keyboard": rows, "resize_keyboard": resize, "is_persistent": persistent}

# ── Main menu keyboard (colored) ──
def main_kb():
    return inline_kb([
        [ibtn("🛒 Order","m:order"), ibtn("💰 Balance","m:balance")],
        [ibtn("💳 Deposit","m:deposit"), ibtn("📦 My Orders","m:orders")],
        [ibtn("🆘 Support","m:support","secondary"), ibtn("📋 Prices","m:prices","secondary")],
    ])

def join_kb():
    return inline_kb([[ibtn("✅ Joined — Check","check_join")]])

def cat_kb():
    rows = []
    for k,v in CATS.items():
        rows.append([ibtn(v["label"], f"cat:{k}")])
    rows.append([ibtn("🔙 Back","m:back","secondary")])
    return inline_kb(rows)

def sub_kb(cat):
    rows = []
    for sub in CATS[cat]["subs"]:
        if svc_list(cat, sub):
            rows.append([ibtn(SUB_LABELS.get(sub,sub), f"sub:{cat}:{sub}")])
    rows.append([ibtn("🔙 Back","m:cat","secondary")])
    return inline_kb(rows)

def svc_kb(cat, sub):
    svcs = svc_list(cat, sub)
    rows = []
    for k,v in svcs.items():
        rows.append([ibtn(f"{v['name']} — {v['price']}৳/1K", f"svc:{k}")])
    rows.append([ibtn("🔙 Back",f"sub_back:{cat}","secondary")])
    return inline_kb(rows)

def confirm_kb():
    return inline_kb([[
        ibtn("✅ Confirm","confirm"),
        ibtn("❌ Cancel","cancel","destructive"),
    ]])

def cancel_kb():
    return inline_kb([[ibtn("❌ Cancel","cancel","destructive")]])

def back_kb():
    return inline_kb([[ibtn("🏠 Main Menu","m:back","secondary")]])

def pay_kb(url):
    return inline_kb([[{"text":"💙 Pay Now","url":url},],
                      [ibtn("🏠 Main Menu","m:back","secondary")]])

def deposit_kb():
    return inline_kb([[ibtn("💳 Deposit","m:deposit")]])

# ═══════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════
def db_conn(): return sqlite3.connect(DB)

def db_init():
    c = db_conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        uid INTEGER PRIMARY KEY, username TEXT DEFAULT '',
        fname TEXT DEFAULT '', balance REAL DEFAULT 0,
        orders INTEGER DEFAULT 0, spent REAL DEFAULT 0,
        deposited REAL DEFAULT 0, banned INTEGER DEFAULT 0,
        created TEXT);
    CREATE TABLE IF NOT EXISTS orders(
        oid INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER,
        svc_key TEXT, svc_name TEXT, link TEXT,
        qty INTEGER, amount REAL, cost REAL, profit REAL,
        panel_id TEXT, status TEXT DEFAULT 'Processing', ts TEXT);
    CREATE TABLE IF NOT EXISTS deposits(
        did INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER,
        amount REAL, phone TEXT, status TEXT DEFAULT 'Pending', ts TEXT);
    CREATE TABLE IF NOT EXISTS logs(
        lid INTEGER PRIMARY KEY AUTOINCREMENT, admin INTEGER,
        action TEXT, target INTEGER, detail TEXT, ts TEXT);
    """)
    c.commit(); c.close()

def db_upsert(uid, un, fn):
    c = db_conn()
    c.execute("INSERT OR IGNORE INTO users(uid,username,fname,balance,orders,spent,deposited,banned,created) VALUES(?,?,?,0,0,0,0,0,?)",
              (uid,un or "",fn or "",datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.execute("UPDATE users SET username=?,fname=? WHERE uid=?", (un or "",fn or "",uid))
    c.commit(); c.close()

def db_user(uid):
    c = db_conn(); r = c.execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone(); c.close(); return r

def db_bal(uid):
    c = db_conn(); r = c.execute("SELECT balance FROM users WHERE uid=?", (uid,)).fetchone(); c.close()
    return round(r[0],2) if r else 0.0

def db_add_bal(uid, amt):
    c = db_conn(); c.execute("UPDATE users SET balance=ROUND(balance+?,2) WHERE uid=?", (amt,uid)); c.commit(); c.close()

def db_banned(uid):
    c = db_conn(); r = c.execute("SELECT banned FROM users WHERE uid=?", (uid,)).fetchone(); c.close()
    return bool(r[0]) if r else False

def db_save_order(uid, skey, sname, link, qty, amt, cost, pid):
    profit = round(amt-cost, 2)
    c = db_conn(); cur = c.cursor()
    cur.execute("INSERT INTO orders(uid,svc_key,svc_name,link,qty,amount,cost,profit,panel_id,status,ts) VALUES(?,?,?,?,?,?,?,?,?,'Processing',?)",
                (uid,skey,sname,link,qty,amt,cost,profit,str(pid),datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    oid = cur.lastrowid
    c.execute("UPDATE users SET orders=orders+1,spent=ROUND(spent+?,2) WHERE uid=?", (amt,uid))
    c.commit(); c.close(); return oid

def db_orders(uid, n=5):
    c = db_conn()
    r = c.execute("SELECT oid,svc_name,qty,amount,status,ts FROM orders WHERE uid=? ORDER BY oid DESC LIMIT ?", (uid,n)).fetchall()
    c.close(); return r

def db_dep(uid, amt, phone):
    c = db_conn(); cur = c.cursor()
    cur.execute("INSERT INTO deposits(uid,amount,phone,status,ts) VALUES(?,?,?,'Pending',?)",
                (uid,amt,phone,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    did = cur.lastrowid; c.commit(); c.close(); return did

def db_stats():
    c = db_conn()
    u  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    o  = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    op = c.execute("SELECT COUNT(*) FROM orders WHERE status='Processing'").fetchone()[0]
    oc = c.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
    rv = c.execute("SELECT COALESCE(SUM(amount),0) FROM orders").fetchone()[0]
    pr = c.execute("SELECT COALESCE(SUM(profit),0) FROM orders").fetchone()[0]
    dp = c.execute("SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='Completed'").fetchone()[0]
    bn = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
    c.close(); return u,o,op,oc,rv,pr,dp,bn

def db_all_users(limit=30):
    c = db_conn()
    r = c.execute("SELECT uid,username,fname,balance,orders,spent,deposited,banned,created FROM users ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    c.close(); return r

def db_count():
    c = db_conn(); r = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; c.close(); return r

def db_ban(uid, v=True):
    c = db_conn(); c.execute("UPDATE users SET banned=? WHERE uid=?", (1 if v else 0,uid)); c.commit(); c.close()

def db_log(adm, action, tid, detail):
    c = db_conn(); c.execute("INSERT INTO logs(admin,action,target,detail,ts) VALUES(?,?,?,?,?)",
                             (adm,action,tid,detail,datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); c.commit(); c.close()

def db_search(q):
    c = db_conn(); p = f"%{q}%"
    r = c.execute("SELECT uid,username,fname,balance,orders,banned FROM users WHERE username LIKE ? OR fname LIKE ? OR CAST(uid AS TEXT) LIKE ?", (p,p,p)).fetchall()
    c.close(); return r

def db_all_ids():
    c = db_conn(); r = [x[0] for x in c.execute("SELECT uid FROM users WHERE banned=0").fetchall()]; c.close(); return r

def db_all_orders_adm(n=20):
    c = db_conn()
    r = c.execute("SELECT o.oid,u.username,u.fname,o.svc_name,o.qty,o.amount,o.profit,o.status FROM orders o JOIN users u ON o.uid=u.uid ORDER BY o.oid DESC LIMIT ?", (n,)).fetchall()
    c.close(); return r

# ═══════════════════════════════════════
# SMM PANEL
# ═══════════════════════════════════════
def smm_order(sid, link, qty):
    try:
        r = req.post(SMM_URL, data={"key":SMM_KEY,"action":"add","service":sid,"link":link,"quantity":qty}, timeout=20)
        j = r.json(); return j.get("order"), j.get("error")
    except Exception as e: return None, str(e)

def smm_bal():
    try:
        r = req.post(SMM_URL, data={"key":SMM_KEY,"action":"balance"}, timeout=15)
        j = r.json(); return j.get("balance","N/A"), j.get("currency","BDT")
    except: return "N/A","N/A"

# ═══════════════════════════════════════
# PAYMENT
# ═══════════════════════════════════════
def make_pay(uid, amt, phone):
    payload = json.dumps({"success_url":f"https://t.me/{BOT_USER.lstrip('@')}","cancel_url":f"https://t.me/{BOT_USER.lstrip('@')}","metadata":{"phone":phone,"user_id":str(uid)},"amount":str(amt)})
    hdrs = {"API-KEY":PAY_API,"Content-Type":"application/json","SECRET-KEY":PAY_SECRET,"BRAND-KEY":PAY_BRAND,"DEVICE-KEY":PAY_DEVICE}
    for i in range(3):
        try:
            r = req.post(PAY_URL, headers=hdrs, data=payload, timeout=35).json()
            url = r.get("payment_url") or r.get("url") or (r.get("data") or {}).get("payment_url")
            if url: return url, r
            if i==2: return None, r
        except req.exceptions.Timeout:
            if i==2: return None, "Payment server সাড়া দিচ্ছে না"
        except Exception as e: return None, str(e)
    return None, "Failed"

# ═══════════════════════════════════════
# USER STATE (in-memory per chat)
# ═══════════════════════════════════════
STATE = {}  # {chat_id: {step, data...}}

def st(cid): return STATE.setdefault(cid, {})
def st_clear(cid): STATE[cid] = {}
def st_set(cid, **kwargs): STATE.setdefault(cid, {}).update(kwargs)

# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════
def se(s): return "✅" if s=="Completed" else "⏳" if s=="Processing" else "❌"
def ustr(un, fn): return f"@{un}" if un else (fn or "Unknown")
def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

WELCOME = (
    "━━━━━━━━━━━━━━━━━━\n"
    f"🏡 <b>{BOT_NAME}</b>\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 মার্কেটের সবচেয়ে কম দাম\n"
    "🤖 সম্পূর্ণ অটোমেটিক সিস্টেম\n"
    "💥 ৩০ মিনিটের মধ্যেই অর্ডার কমপ্লিট"
)

MORNING = (
    "🌅 <b>সুপ্রভাত! Good Morning!</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"🏡 {BOT_NAME}\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🔥 আজকেও সেরা দামে SMM সার্ভিস নিন!\n"
    "🎵 TikTok | 📸 Instagram | ✈️ Telegram\n"
    "📘 Facebook | 🎬 YouTube\n\n"
    "💳 ডিপোজিট করুন এবং অর্ডার করুন!\n"
    f"🤖 {BOT_USER}"
)

# ═══════════════════════════════════════
# HANDLE /start
# ═══════════════════════════════════════
def handle_start(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    un  = msg["from"].get("username","")
    fn  = msg["from"].get("first_name","")
    db_upsert(uid, un, fn)
    st_clear(cid)
    typing(cid)

    if db_banned(uid):
        send(cid, "🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    if not all_members_ok(uid):
        send(cid,
             "⛔ বট ব্যবহারের আগে আমাদের চ্যানেল গুলোতে জয়েন করুন ⬇️\n\n"
             "➡️ @RKXPremiumZone\n➡️ @RKXSMMZONE\n\n"
             "✅ Join করার পর নিচের বাটনে ক্লিক করুন",
             kb=join_kb()); return

    send(cid, f"{WELCOME}\n\nস্বাগতম, <b>{fn}</b>! 👋", kb=main_kb())

# ═══════════════════════════════════════
# HANDLE /admin
# ═══════════════════════════════════════
def handle_admin(msg):
    cid = msg["chat"]["id"]; uid = msg["from"]["id"]
    if uid != ADMIN_ID: send(cid,"❌ শুধুমাত্র Admin!"); return
    typing(cid)
    u,o,op,oc,rv,pr,dp,bn = db_stats()
    bal,cur = smm_bal()
    st_clear(cid); st_set(cid, admin=True)
    kb = inline_kb([
        [ibtn("👥 All Users","adm:users"), ibtn("🔍 Search","adm:search")],
        [ibtn("📊 Stats","adm:stats"), ibtn("📦 Orders","adm:orders")],
        [ibtn("💳 Add Balance","adm:addbal"), ibtn("🚫 Ban","adm:ban","destructive")],
        [ibtn("✅ Unban","adm:unban"), ibtn("📢 Broadcast","adm:broadcast")],
        [ibtn("💼 Panel Bal","adm:panelbal","secondary"), ibtn("🚪 Exit","adm:exit","secondary")],
    ])
    send(cid,
         f"🔐 <b>Admin Panel — {BOT_NAME}</b>\n"
         f"━━━━━━━━━━━━━━━━━━━━\n"
         f"👥 ইউজার: {u} | 🚫 Banned: {bn}\n"
         f"📦 অর্ডার: {o} | ⏳{op} ✅{oc}\n"
         f"💰 Revenue: {rv:.2f}৳\n"
         f"📈 Profit: {pr:.2f}৳\n"
         f"💳 Deposits: {dp:.2f}৳\n"
         f"━━━━━━━━━━━━━━━━━━━━\n"
         f"🖥️ Panel: {bal} {cur}",
         kb=kb)

# ═══════════════════════════════════════
# HANDLE CALLBACK QUERIES
# ═══════════════════════════════════════
def handle_cb(cb):
    cid  = cb["message"]["chat"]["id"]
    mid  = cb["message"]["message_id"]
    uid  = cb["from"]["id"]
    un   = cb["from"].get("username","")
    fn   = cb["from"].get("first_name","")
    data = cb["data"]
    answer_cb(cb["id"])
    typing(cid)

    # ── Join check ────────────────────────────────────────────
    if data == "check_join":
        if not all_members_ok(uid):
            answer_cb(cb["id"],"❌ দুটো চ্যানেলেই জয়েন করো!", True); return
        db_upsert(uid, un, fn); st_clear(cid)
        send(cid, f"{WELCOME}\n\nস্বাগতম, <b>{fn}</b>! 👋", kb=main_kb(), edit_msg_id=mid); return

    # ── Main menu ─────────────────────────────────────────────
    if data == "m:back":
        st_clear(cid)
        send(cid, f"{WELCOME}\n\nনিচের বাটন থেকে শুরু করুন:", kb=main_kb(), edit_msg_id=mid); return

    if data == "m:order":
        if not all_members_ok(uid):
            send(cid,"⛔ আগে চ্যানেলে জয়েন করো!", kb=join_kb(), edit_msg_id=mid); return
        st_clear(cid); st_set(cid, step="cat")
        send(cid,"🏪 Platform বেছে নিন 👇", kb=cat_kb(), edit_msg_id=mid); return

    if data == "m:balance":
        row = db_user(uid)
        b,t,s,d = (row[3],row[4],row[5],row[6]) if row else (0,0,0,0)
        send(cid,
             f"💰 <b>আপনার অ্যাকাউন্ট</b>\n━━━━━━━━━━━━━━━\n"
             f"👤 ID: {uid}\n📛 Name: {fn}\n"
             f"💵 ব্যালেন্স: {b:.2f}৳\n"
             f"📦 মোট অর্ডার: {t}\n"
             f"💸 মোট খরচ: {s:.2f}৳\n"
             f"💳 মোট ডিপোজিট: {d:.2f}৳",
             kb=back_kb(), edit_msg_id=mid); return

    if data == "m:deposit":
        st_clear(cid); st_set(cid, step="dep_amt")
        send(cid,
             "💳 <b>ডিপোজিট</b>\n━━━━━━━━━━━━━\n"
             "কত টাকা ডিপোজিট করতে চাও?\n"
             "(সর্বনিম্ন ১০ টাকা)\n\n"
             "👇 পরিমাণ লিখো:",
             kb=back_kb(), edit_msg_id=mid); return

    if data == "m:orders":
        rows = db_orders(uid)
        if not rows:
            send(cid,"📦 এখনো কোনো অর্ডার নেই।", kb=back_kb(), edit_msg_id=mid); return
        msg = "📦 <b>সর্বশেষ ৫টি অর্ডার</b>\n━━━━━━━━━━━━━━━\n"
        for r in rows:
            msg += f"{se(r[4])} #{r[0]} | {r[1]}\n   🔢{r[2]:,} | 💸{r[3]:.2f}৳ | {r[5][:16]}\n─────────\n"
        send(cid, msg, kb=back_kb(), edit_msg_id=mid); return

    if data == "m:support":
        send(cid,
             f"🆘 <b>সাপোর্ট — {BOT_NAME}</b>\n━━━━━━━━━━━━━━━\n"
             f"📩 Telegram: @RKXPremiumZone\n"
             f"📢 Channel: @RKXSMMZONE\n\n"
             f"⏰ সকাল ৯টা – রাত ১১টা\n🤖 {BOT_USER}",
             kb=back_kb(), edit_msg_id=mid); return

    if data == "m:prices":
        msg = f"📋 <b>{BOT_NAME} — মূল্য তালিকা</b>\n━━━━━━━━━━━━━━━\n"
        for cat_k, cat_v in CATS.items():
            msg += f"\n<b>{cat_v['label']}</b>\n"
            for sub in cat_v["subs"]:
                for k,v in svc_list(cat_k,sub).items():
                    msg += f"  • {v['name']}: {v['price']}৳/1K (min:{v['min']:,})\n"
        msg += "\n━━━━━━━━━━━━━━━\n⚡ অর্ডার ৩০ মিনিটে কমপ্লিট"
        # split if too long
        chunks = [msg[i:i+3800] for i in range(0,len(msg),3800)]
        send(cid, chunks[0], kb=back_kb(), edit_msg_id=mid)
        for ch in chunks[1:]: send(cid, ch)
        return

    # ── Category ──────────────────────────────────────────────
    if data.startswith("cat:"):
        cat = data[4:]
        if cat not in CATS: return
        st_set(cid, cat=cat, step="sub")
        send(cid, f"{CATS[cat]['label']} — সার্ভিস টাইপ বেছে নিন 👇",
             kb=sub_kb(cat), edit_msg_id=mid); return

    if data == "m:cat":
        st_set(cid, step="cat")
        send(cid,"🏪 Platform বেছে নিন 👇", kb=cat_kb(), edit_msg_id=mid); return

    if data.startswith("sub:"):
        _, cat, sub = data.split(":")
        st_set(cid, cat=cat, sub=sub, step="svc")
        send(cid, f"{CATS[cat]['label']} › {SUB_LABELS.get(sub,sub)}\nসার্ভিস বেছে নিন 👇",
             kb=svc_kb(cat, sub), edit_msg_id=mid); return

    if data.startswith("sub_back:"):
        cat = data[9:]
        st_set(cid, cat=cat, step="sub")
        send(cid, f"{CATS[cat]['label']} — সার্ভিস টাইপ বেছে নিন 👇",
             kb=sub_kb(cat), edit_msg_id=mid); return

    # ── Service selected ──────────────────────────────────────
    if data.startswith("svc:"):
        skey = data[4:]
        svc  = SVCS.get(skey)
        if not svc: return
        bal = db_bal(uid)
        st_set(cid, skey=skey, step="link")
        send(cid,
             f"✅ <b>{svc['name']}</b>\n\n"
             f"💰 আপনার ব্যালেন্স: {bal:.2f}৳\n"
             f"📊 মূল্য: {svc['price']}৳ / ১০০০\n"
             f"📉 সর্বনিম্ন: {svc['min']:,}\n"
             f"📈 সর্বোচ্চ: {svc['max']:,}\n\n"
             f"🔗 পোস্ট / প্রোফাইল লিংক দাও:",
             kb=cancel_kb(), edit_msg_id=mid); return

    # ── Confirm order ─────────────────────────────────────────
    if data == "confirm":
        s = st(cid)
        svc  = SVCS.get(s.get("skey",""))
        link = s.get("link")
        qty  = s.get("qty")
        amt  = s.get("amt")
        cost = s.get("cost",0)

        if not all([svc, link, qty, amt]):
            send(cid,"❌ কিছু ভুল। /start দাও।", kb=back_kb(), edit_msg_id=mid)
            st_clear(cid); return

        bal = db_bal(uid)
        if bal < amt:
            send(cid, f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳",
                 kb=deposit_kb(), edit_msg_id=mid)
            st_clear(cid); return

        send(cid,"⏳ অর্ডার প্রসেস হচ্ছে...", edit_msg_id=mid)
        pid, err = smm_order(svc["sid"], link, qty)

        if err and not pid:
            send(cid, f"❌ অর্ডার ব্যর্থ!\n{err}\n\n🆘 @RKXPremiumZone", kb=back_kb(), edit_msg_id=mid); return

        db_add_bal(uid, -amt)
        oid = db_save_order(uid, s["skey"], svc["name"], link, qty, amt, cost, str(pid or "N/A"))
        nb  = db_bal(uid)
        pr  = round(amt-cost,2)

        send(cid,
             f"✅ <b>অর্ডার সফল!</b>\n━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
             f"└➤ Order ID: {oid}\n└➤ User ID: {uid}\n"
             f"└➤ Status: Processing ⏳\n"
             f"└➤ Service: {svc['name']}\n"
             f"└➤ Ordered: {qty:,}\n└➤ Link: Private\n"
             f"└➤ খরচ: {amt:.2f}৳\n└➤ বাকি: {nb:.2f}৳\n"
             f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USER}",
             kb=back_kb(), edit_msg_id=mid)

        try:
            tg("sendMessage", chat_id=LOG_CH,
               text=f"📌 {BOT_NAME}\n🎯 New {svc['name']} Order\n"
                    f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n"
                    f"└➤ Order ID: {oid}\n└➤ User: {ustr(un,fn)} ({uid})\n"
                    f"└➤ ✅ Qty: {qty:,} | Amount: {amt:.2f}৳ | Profit: {pr:.2f}৳\n"
                    f"━━━━━━━━━━━•❈•━━━━━━━━━━━\n🤖 {BOT_USER}",
               parse_mode="HTML")
        except: pass
        st_clear(cid); return

    if data == "cancel":
        st_clear(cid)
        send(cid,"❌ বাতিল।", kb=main_kb(), edit_msg_id=mid); return

    # ── Admin callbacks ───────────────────────────────────────
    if data.startswith("adm:"):
        if uid != ADMIN_ID: return
        action = data[4:]

        if action == "exit":
            st_clear(cid); send(cid,"✅ Admin panel বন্ধ।", kb=main_kb(), edit_msg_id=mid); return

        if action == "users":
            rows = db_all_users(25); total = db_count()
            msg  = f"👥 <b>সকল ইউজার (মোট: {total})</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            btns = []
            for row in rows:
                u2,un2,fn2,b2,o2,s2,d2,ban2,j2 = row
                us2 = ustr(un2,fn2); bm = "🚫" if ban2 else "✅"
                msg += f"{bm} {us2} | {u2} | {b2:.0f}৳ | {o2} ord\n"
                btns.append([ibtn(f"{bm} {us2} ({u2})", f"au:{u2}")])
            btns.append([ibtn("🔙 Back","adm:back","secondary")])
            send(cid, msg[:4000], kb=inline_kb(btns[:20]), edit_msg_id=mid); return

        if action == "search":
            st_set(cid, adm_step="search"); send(cid,"🔍 Username/Name/ID লিখো:", edit_msg_id=mid); return

        if action == "stats":
            u2,o2,op2,oc2,rv2,pr2,dp2,bn2 = db_stats(); bal2,cur2 = smm_bal()
            send(cid,
                 f"📊 <b>Full Stats — {BOT_NAME}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                 f"👥 {u2} users | 🚫 {bn2} banned\n"
                 f"📦 {o2} | ⏳{op2} ✅{oc2}\n"
                 f"💰 Revenue: {rv2:.2f}৳\n📈 Profit: {pr2:.2f}৳\n"
                 f"💳 Dep: {dp2:.2f}৳\n🖥️ {bal2} {cur2}",
                 kb=inline_kb([[ibtn("🔙","adm:back","secondary")]]), edit_msg_id=mid); return

        if action == "orders":
            rows = db_all_orders_adm()
            msg  = "📦 <b>সর্বশেষ ২০ অর্ডার</b>\n━━━━━━━━━━━━━━━\n"
            for r in rows:
                us2 = ustr(r[1],r[2])
                msg += f"{se(r[7])} #{r[0]} {us2}\n  {r[3][:25]} | {r[4]:,} | {r[5]:.2f}৳ | p:{r[6]:.2f}৳\n"
            send(cid, msg[:4000], kb=inline_kb([[ibtn("🔙","adm:back","secondary")]]), edit_msg_id=mid); return

        if action == "addbal":
            st_set(cid, adm_step="addbal_uid"); send(cid,"💳 User ID দাও:", edit_msg_id=mid); return
        if action == "ban":
            st_set(cid, adm_step="ban_uid"); send(cid,"🚫 Ban করার User ID:", edit_msg_id=mid); return
        if action == "unban":
            st_set(cid, adm_step="unban_uid"); send(cid,"✅ Unban করার User ID:", edit_msg_id=mid); return
        if action == "broadcast":
            st_set(cid, adm_step="broadcast"); send(cid,"📢 মেসেজ লিখো:", edit_msg_id=mid); return
        if action == "panelbal":
            bal2,cur2 = smm_bal()
            send(cid, f"💼 Panel Balance\n━━━━━━━━━━━━\n💰 {bal2} {cur2}",
                 kb=inline_kb([[ibtn("🔙","adm:back","secondary")]]), edit_msg_id=mid); return
        if action == "back":
            handle_admin_panel_msg(cid, uid); return

    # ── Admin user detail ─────────────────────────────────────
    if data.startswith("au:"):
        if uid != ADMIN_ID: return
        tid = int(data[3:]); row = db_user(tid)
        if not row: answer_cb(cb["id"],"Not found!",True); return
        tu,tun,tfn,tb,to,ts,td,tbn,tj = row
        tus = ustr(tun,tfn); ban_s = "🚫BANNED" if tbn else "✅Active"
        ord_rows = db_orders(tid,3)
        ord_txt = "".join([f"  {se(r[4])} #{r[0]} {r[1][:20]} | {r[4]}\n" for r in ord_rows]) or "  নেই"
        btns = [
            [ibtn("💰 Add Balance",f"aab:{tid}"), ibtn("🚫 Ban",f"abn:{tid}","destructive")],
            [ibtn("✅ Unban",f"aub:{tid}"), ibtn("🔙 Back","adm:users","secondary")]
        ]
        send(cid,
             f"👤 {tus} | {ban_s}\n🆔 {tid}\n"
             f"💰 {tb:.2f}৳ | 📦 {to} orders\n"
             f"💸 Spent: {ts:.2f}৳ | 💳 Dep: {td:.2f}৳\n"
             f"📅 {tj[:10] if tj else 'N/A'}\n\n📦 Recent:\n{ord_txt}",
             kb=inline_kb(btns), edit_msg_id=mid); return

    if data.startswith("aab:"):
        if uid != ADMIN_ID: return
        tid = int(data[4:]); st_set(cid, adm_step="addbal_amt", adm_tid=tid)
        send(cid, f"💰 User {tid} কত টাকা?", edit_msg_id=mid); return

    if data.startswith("abn:"):
        if uid != ADMIN_ID: return
        tid = int(data[4:]); db_ban(tid,True); db_log(uid,"ban",tid,"panel")
        answer_cb(cb["id"],f"🚫 {tid} banned!",True); return

    if data.startswith("aub:"):
        if uid != ADMIN_ID: return
        tid = int(data[4:]); db_ban(tid,False); db_log(uid,"unban",tid,"panel")
        answer_cb(cb["id"],f"✅ {tid} unbanned!",True); return

# ═══════════════════════════════════════
# ADMIN PANEL SHORTCUT
# ═══════════════════════════════════════
def handle_admin_panel_msg(cid, uid):
    u2,o2,op2,oc2,rv2,pr2,dp2,bn2 = db_stats(); bal2,cur2 = smm_bal()
    kb2 = inline_kb([
        [ibtn("👥 All Users","adm:users"), ibtn("🔍 Search","adm:search")],
        [ibtn("📊 Stats","adm:stats"), ibtn("📦 Orders","adm:orders")],
        [ibtn("💳 Add Balance","adm:addbal"), ibtn("🚫 Ban","adm:ban","destructive")],
        [ibtn("✅ Unban","adm:unban"), ibtn("📢 Broadcast","adm:broadcast")],
        [ibtn("💼 Panel Bal","adm:panelbal","secondary"), ibtn("🚪 Exit","adm:exit","secondary")],
    ])
    send(cid,
         f"🔐 <b>Admin Panel</b>\n"
         f"👥 {u2} | 🚫 {bn2} | 📦 {o2}\n"
         f"💰 {rv2:.2f}৳ | 📈 {pr2:.2f}৳ | 💳 {dp2:.2f}৳\n"
         f"🖥️ {bal2} {cur2}",
         kb=kb2)

# ═══════════════════════════════════════
# HANDLE TEXT MESSAGES
# ═══════════════════════════════════════
def handle_text(msg):
    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    un  = msg["from"].get("username","")
    fn  = msg["from"].get("first_name","")
    txt = msg.get("text","").strip()
    s   = st(cid)
    typing(cid)

    if db_banned(uid) and uid != ADMIN_ID:
        send(cid,"🚫 আপনি এই বট ব্যবহার করতে পারবেন না।"); return

    step = s.get("step")
    adm_step = s.get("adm_step")

    # Admin steps
    if adm_step and uid == ADMIN_ID:
        handle_adm_step(cid, uid, fn, txt, adm_step, s); return

    # Order: link
    if step == "link":
        if not txt.startswith("http"):
            send(cid,"❌ সঠিক লিংক দাও! http দিয়ে শুরু হতে হবে।", kb=cancel_kb()); return
        svc = SVCS.get(s.get("skey",""))
        st_set(cid, link=txt, step="qty")
        send(cid,
             f"✅ লিংক পেয়েছি!\n\n"
             f"💰 ব্যালেন্স: {db_bal(uid):.2f}৳\n"
             f"📊 {svc['price']}৳/১০০০ | Min:{svc['min']:,} Max:{svc['max']:,}\n\n"
             f"🔢 পরিমাণ লিখো:", kb=cancel_kb()); return

    # Order: quantity
    if step == "qty":
        if not txt.isdigit():
            send(cid,"❌ শুধু সংখ্যা লিখো!", kb=cancel_kb()); return
        qty = int(txt); svc = SVCS.get(s.get("skey",""))
        if qty < svc["min"] or qty > svc["max"]:
            send(cid,f"❌ {svc['min']:,}–{svc['max']:,} এর মধ্যে হতে হবে!", kb=cancel_kb()); return
        amt  = round((qty/1000)*svc["price"],2)
        cost = round((qty/1000)*svc["cost"], 2)
        bal  = db_bal(uid)
        if bal < amt:
            send(cid,f"❌ ব্যালেন্স কম!\n💰 আছে: {bal:.2f}৳ | দরকার: {amt:.2f}৳", kb=deposit_kb())
            st_clear(cid); return
        st_set(cid, qty=qty, amt=amt, cost=cost, step="confirm")
        send(cid,
             f"📋 <b>অর্ডার সারসংক্ষেপ</b>\n━━━━━━━━━━━━━━━\n"
             f"🛒 {svc['name']}\n"
             f"🔗 {s['link']}\n"
             f"🔢 {qty:,} | 💸 {amt:.2f}৳\n"
             f"💰 অর্ডারের পরে: {bal-amt:.2f}৳\n"
             f"━━━━━━━━━━━━━━━\n✅ কনফার্ম করবে?",
             kb=confirm_kb()); return

    # Deposit: amount
    if step == "dep_amt":
        if not txt.isdigit() or int(txt)<10:
            send(cid,"❌ সর্বনিম্ন ১০ টাকা!", kb=back_kb()); return
        st_set(cid, dep_amt=int(txt), step="dep_phone")
        send(cid,"📱 ফোন নম্বর দাও:\n(যেটা দিয়ে পেমেন্ট করবে)\nযেমন: 01712345678"); return

    # Deposit: phone
    if step == "dep_phone":
        amt4  = s.get("dep_amt"); phone = txt
        dep_id = db_dep(uid, amt4, phone)
        send(cid,"⏳ পেমেন্ট লিংক তৈরি হচ্ছে...")
        url, raw = make_pay(uid, amt4, phone)
        st_clear(cid)
        if url:
            send(cid,
                 f"✅ <b>পেমেন্ট লিংক তৈরি!</b>\n━━━━━━━━━━━━━━━\n"
                 f"💰 {amt4} টাকা | 📱 {phone}\n🆔 Ref: #{dep_id}\n"
                 f"━━━━━━━━━━━━━━━\n"
                 f"⬇️ নিচের নীল বাটনে পেমেন্ট করো\n"
                 f"✅ সফল হলে ব্যালেন্স অটো যোগ হবে।",
                 kb=pay_kb(url))
        else:
            send(cid, f"❌ পেমেন্ট লিংক তৈরি হয়নি।\n{raw}\n\n🆘 @RKXPremiumZone")
        return

    # Fallback
    send(cid, f"{WELCOME}\n\nনিচের বাটন থেকে শুরু করুন:", kb=main_kb())

# ═══════════════════════════════════════
# ADMIN STEP HANDLER
# ═══════════════════════════════════════
def handle_adm_step(cid, uid, fn, txt, step, s):
    if step == "search":
        rows = db_search(txt)
        if not rows: send(cid,"❌ কেউ পাওয়া যায়নি।")
        else:
            msg = f"🔍 ({len(rows)}):\n"; btns = []
            for r in rows:
                u2,un2,fn2,b2,o2,ban2 = r
                us2 = ustr(un2,fn2); bm = "🚫" if ban2 else "✅"
                msg += f"{bm} {us2} | {u2} | {b2:.0f}৳\n"
                btns.append([ibtn(f"{bm} {us2} ({u2})", f"au:{u2}")])
            send(cid, msg, kb=inline_kb(btns))
        st_set(cid, adm_step=None); return

    if step == "addbal_uid":
        if not txt.isdigit(): send(cid,"❌ সঠিক User ID!"); return
        st_set(cid, adm_tid=int(txt), adm_step="addbal_amt")
        send(cid, f"💰 User {txt} কত টাকা?"); return

    if step == "addbal_amt":
        try:
            amt = float(txt); tid = s.get("adm_tid")
            db_add_bal(tid, amt); nb = db_bal(tid)
            db_log(uid,"addbalance",tid,f"+{amt}")
            send(cid, f"✅ {tid} এ {amt}৳ যোগ। নতুন: {nb:.2f}৳")
            try: tg("sendMessage", chat_id=tid, text=f"✅ {amt} টাকা যোগ!\n💰 নতুন: {nb:.2f}৳", parse_mode="HTML")
            except: pass
        except Exception as e: send(cid, f"❌ {e}")
        st_set(cid, adm_step=None, adm_tid=None); return

    if step == "ban_uid":
        if not txt.isdigit(): send(cid,"❌ সঠিক User ID!"); return
        tid=int(txt); db_ban(tid,True); db_log(uid,"ban",tid,"")
        send(cid,f"🚫 {tid} banned."); st_set(cid,adm_step=None); return

    if step == "unban_uid":
        if not txt.isdigit(): send(cid,"❌ সঠিক User ID!"); return
        tid=int(txt); db_ban(tid,False); db_log(uid,"unban",tid,"")
        send(cid,f"✅ {tid} unbanned."); st_set(cid,adm_step=None); return

    if step == "broadcast":
        uids = db_all_ids(); sent=fail=0
        send(cid, f"📢 Sending to {len(uids)}...")
        for u2 in uids:
            try:
                tg("sendMessage", chat_id=u2,
                   text=f"📢 <b>{BOT_NAME}</b>\n━━━━━━━━━━━━\n{txt}",
                   parse_mode="HTML", reply_markup=json.dumps(main_kb()))
                sent+=1
            except: fail+=1
        send(cid, f"✅ Done! ✅{sent} ❌{fail}")
        st_set(cid, adm_step=None); return

# ═══════════════════════════════════════
# DAILY MORNING BROADCAST
# ═══════════════════════════════════════
async def daily_morning():
    while True:
        now_t = datetime.utcnow()
        # সকাল ৬টা BD = UTC 0:00
        target = now_t.replace(hour=0, minute=0, second=0, microsecond=0)
        if now_t >= target:
            target = target.replace(day=target.day+1)
        wait = (target - now_t).total_seconds()
        await asyncio.sleep(wait)

        uids = db_all_ids(); sent=fail=0
        logging.info(f"📢 Daily morning → {len(uids)} users")
        for uid in uids:
            try:
                tg("sendMessage", chat_id=uid, text=MORNING,
                   parse_mode="HTML", reply_markup=json.dumps(main_kb()))
                sent+=1
            except: fail+=1
            await asyncio.sleep(0.05)
        logging.info(f"📢 Done: ✅{sent} ❌{fail}")
        try: tg("sendMessage", chat_id=ADMIN_ID, text=f"📢 Daily done! ✅{sent} ❌{fail}")
        except: pass

# ═══════════════════════════════════════
# POLLING LOOP
# ═══════════════════════════════════════
async def poll():
    offset = None
    logging.info(f"✅ {BOT_NAME} polling started")
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message","callback_query"]}
            if offset: params["offset"] = offset
            r = req.get(f"{API_URL}/getUpdates", params=params, timeout=35)
            updates = r.json().get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1
                try:
                    if "message" in upd:
                        msg = upd["message"]
                        txt = msg.get("text","")
                        if txt.startswith("/start"): handle_start(msg)
                        elif txt.startswith("/admin"): handle_admin(msg)
                        elif txt.startswith("/addbalance"):
                            parts = txt.split(); uid = msg["from"]["id"]
                            if uid == ADMIN_ID and len(parts)==3:
                                tid=int(parts[1]); amt=float(parts[2])
                                db_add_bal(tid,amt); nb=db_bal(tid)
                                send(msg["chat"]["id"],f"✅ {tid} → {amt}৳. নতুন: {nb:.2f}৳")
                                try: tg("sendMessage",chat_id=tid,text=f"✅ {amt} টাকা যোগ!\n💰 নতুন: {nb:.2f}৳",parse_mode="HTML")
                                except: pass
                        elif txt.startswith("/ban"):
                            parts=txt.split(); uid=msg["from"]["id"]
                            if uid==ADMIN_ID and len(parts)==2:
                                db_ban(int(parts[1]),True); send(msg["chat"]["id"],f"🚫 {parts[1]} banned")
                        elif txt.startswith("/unban"):
                            parts=txt.split(); uid=msg["from"]["id"]
                            if uid==ADMIN_ID and len(parts)==2:
                                db_ban(int(parts[1]),False); send(msg["chat"]["id"],f"✅ {parts[1]} unbanned")
                        elif txt.startswith("/stats"):
                            if msg["from"]["id"]==ADMIN_ID:
                                u2,o2,op2,oc2,rv2,pr2,dp2,bn2=db_stats(); bal2,cur2=smm_bal()
                                send(msg["chat"]["id"],f"📊 {BOT_NAME}\n{u2} users | {o2} orders\n{rv2:.2f}৳ revenue | {pr2:.2f}৳ profit\n{bal2} {cur2}")
                        elif txt.startswith("/myorders"):
                            uid=msg["from"]["id"]; rows=db_orders(uid,10)
                            if not rows: send(msg["chat"]["id"],"📦 কোনো অর্ডার নেই।")
                            else:
                                m="📦 <b>আপনার অর্ডার</b>\n━━━━━━━━━━━━━━━\n"
                                for rr in rows: m+=f"{se(rr[4])} #{rr[0]} {rr[1]}\n  🔢{rr[2]:,} | {rr[3]:.2f}৳\n"
                                send(msg["chat"]["id"],m)
                        else:
                            handle_text(msg)
                    elif "callback_query" in upd:
                        handle_cb(upd["callback_query"])
                except Exception as e:
                    logging.error(f"Update error: {e}")
        except Exception as e:
            logging.error(f"Poll error: {e}")
            await asyncio.sleep(5)

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
async def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s — %(message)s", level=logging.INFO)
    db_init()
    logging.info(f"✅ {BOT_NAME} starting...")
    await asyncio.gather(poll(), daily_morning())

if __name__ == "__main__":
    asyncio.run(main())
