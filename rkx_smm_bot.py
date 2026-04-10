"""
BD RAKIB 007 - Telegram Signal Bot
====================================
এই bot HTML সিগনালের মতোই একই API থেকে ডেটা নেয়
এবং প্রতিটি নতুন period এ Telegram channel/group এ সিগনাল পাঠায়।

SETUP:
1. pip install python-telegram-bot requests
2. BotFather থেকে bot token নাও
3. TELEGRAM_BOT_TOKEN এবং CHAT_ID নিচে দাও
4. python bot.py
"""

import asyncio
import requests
import json
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# ============================================================
# ✅ এখানে তোমার তথ্য দাও
# ============================================================
TELEGRAM_BOT_TOKEN = "8427105381:AAGGEm4CkQ1E1_lHuULdBBtFMv2gpsh5G_o"   # BotFather থেকে নাও
CHAT_ID = "7761133429"                 # Channel/Group ID (e.g. -1001234567890)

# API Endpoints (HTML এর মতোই)
CURRENT_API = "https://api.bdg88zf.com/api/webapi/GetGameIssue"
HISTORY_API = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

CHECK_INTERVAL = 8   # কত সেকেন্ড পর পর চেক করবে
# ============================================================

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== STATE =====================
last_period = None
prediction_log = []   # { period, prediction, result, status }
stats = {"wins": 0, "losses": 0}


# ===================== HELPERS =====================
def get_big_small(num: int) -> str:
    return "BIG" if num >= 5 else "SMALL"


def fetch_current_period():
    try:
        res = requests.post(
            CURRENT_API,
            json={
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(datetime.now().timestamp())
            },
            timeout=8
        )
        data = res.json()
        return data.get("data", {}).get("issueNumber")
    except Exception as e:
        logger.error(f"Period fetch error: {e}")
        return None


def fetch_history():
    try:
        res = requests.get(
            HISTORY_API,
            params={"ts": int(datetime.now().timestamp() * 1000)},
            timeout=8
        )
        data = res.json()
        return data.get("data", {}).get("list", [])
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return []


# ===================== PREDICTOR =====================
class AdvancedPredictor:
    def double_pattern(self, h):
        if len(h) < 3: return ("BIG", 50)
        if h[0] == h[1]:
            return ("SMALL" if h[0] == "BIG" else "BIG", 76)
        return (h[0], 62)

    def triple_pattern(self, h):
        if len(h) < 4: return ("BIG", 50)
        if h[0] == h[1] == h[2]:
            return ("SMALL" if h[0] == "BIG" else "BIG", 82)
        return (h[0], 64)

    def alternating_pattern(self, h):
        if len(h) < 4: return ("BIG", 50)
        alt = all(h[i] != h[i-1] for i in range(1, min(4, len(h))))
        if alt:
            return ("SMALL" if h[0] == "BIG" else "BIG", 78)
        return (h[0], 62)

    def streak_analysis(self, h):
        if len(h) < 3: return ("SMALL", 50)
        streak = 1
        for i in range(1, min(6, len(h))):
            if h[i] == h[0]: streak += 1
            else: break
        if streak >= 3:
            return ("SMALL" if h[0] == "BIG" else "BIG", 73 + min(10, (streak-3)*3))
        if streak == 2:
            return (h[0], 67)
        return (h[0], 60)

    def frequency_trend(self, h):
        if len(h) < 8: return ("BIG", 50)
        l8 = h[:8]
        big_c = l8.count("BIG")
        small_c = 8 - big_c
        if big_c >= 6: return ("SMALL", 77)
        if small_c >= 6: return ("BIG", 77)
        if big_c >= 5: return ("SMALL", 70)
        if small_c >= 5: return ("BIG", 70)
        return (l8[0], 65)

    def moving_average(self, h):
        if len(h) < 10: return ("SMALL", 50)
        big_c = h[:10].count("BIG")
        if big_c >= 7: return ("BIG", 72)
        if big_c <= 3: return ("SMALL", 72)
        return ("SMALL" if big_c > 5 else "BIG", 68)

    def probability_balance(self, h):
        if len(h) < 20: return ("BIG", 50)
        bp = h[:20].count("BIG") / 20
        if bp > 0.6: return ("SMALL", 75)
        if bp < 0.4: return ("BIG", 75)
        return (h[0], 65)

    def fibonacci_analysis(self, h):
        if len(h) < 5: return ("BIG", 50)
        fibs = [0, 1, 2, 4, 7]  # 0-indexed: positions 1,2,3,5,8
        score = {"BIG": 0, "SMALL": 0}
        for p in fibs:
            if p < len(h):
                score[h[p]] += 1
        pred = "BIG" if score["BIG"] >= score["SMALL"] else "SMALL"
        return (pred, 55 + min(20, abs(score["BIG"] - score["SMALL"]) * 5))

    def mirror_pattern(self, h):
        if len(h) < 4: return ("BIG", 50)
        if h[0] == h[3] and h[1] == h[2]:
            return ("SMALL" if h[1] == "BIG" else "BIG", 70)
        return (h[0], 60)

    def distribution_analysis(self, h):
        if len(h) < 15: return ("SMALL", 50)
        l15 = h[:15]
        clusters, cur, size = 0, l15[0], 1
        for i in range(1, len(l15)):
            if l15[i] == cur: size += 1
            else:
                if size >= 2: clusters += 1
                cur, size = l15[i], 1
        if size >= 2: clusters += 1
        return (l15[0], 70 if clusters >= 5 else 68)

    def is_prime(self, n):
        if n <= 1: return False
        if n <= 3: return True
        if n % 2 == 0 or n % 3 == 0: return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i+2) == 0: return False
            i += 6
        return True

    def prime_number_logic(self, h):
        if len(h) < 2: return ("SMALL", 50)
        if self.is_prime(len(h)):
            return ("SMALL" if h[0] == "BIG" else "BIG", 70)
        return (h[0], 65)

    def digital_root_analysis(self, h):
        if len(h) < 3: return ("BIG", 50)
        dr = len(h)
        while dr >= 10:
            dr = sum(int(d) for d in str(dr))
        return ("BIG" if dr % 2 == 1 else "SMALL", 60 + (dr % 3) * 5)

    def analyze(self, history_items):
        """
        history_items: list of dicts with 'resultType' key
        returns: { prediction, confidence, analysis }
        """
        h = [item["resultType"] for item in history_items]
        if len(h) < 3:
            return {"prediction": "BIG", "confidence": 50, "analysis": "Not enough data"}

        algorithms = [
            ("Double Pattern",    0.15, self.double_pattern),
            ("Triple Pattern",    0.12, self.triple_pattern),
            ("Alternating",       0.13, self.alternating_pattern),
            ("Mirror Pattern",    0.10, self.mirror_pattern),
            ("Streak Analysis",   0.14, self.streak_analysis),
            ("Freq Trend",        0.12, self.frequency_trend),
            ("Moving Average",    0.11, self.moving_average),
            ("Prob Balance",      0.10, self.probability_balance),
            ("Distribution",      0.09, self.distribution_analysis),
            ("Fibonacci",         0.08, self.fibonacci_analysis),
            ("Prime Logic",       0.07, self.prime_number_logic),
            ("Digital Root",      0.06, self.digital_root_analysis),
        ]

        scores = {"BIG": 0.0, "SMALL": 0.0}
        total_w = 0.0
        results = []

        for name, weight, fn in algorithms:
            pred, conf = fn(h)
            scores[pred] += conf * weight
            total_w += weight
            results.append((name, pred, conf))

        final = "BIG" if scores["BIG"] >= scores["SMALL"] else "SMALL"
        diff = abs(scores["BIG"] - scores["SMALL"]) / total_w
        base_conf = sum(r[2] for r in results) / len(results)
        final_conf = min(95, round(base_conf + diff * 25))

        agree_count = sum(1 for r in results if r[1] == final)
        agree_pct = round(agree_count / len(results) * 100)
        top3 = sorted(results, key=lambda x: -x[2])[:3]
        analysis = f"{agree_pct}% algorithms agree | Top: {', '.join(f'{r[0]}({r[2]}%)' for r in top3)}"

        return {"prediction": final, "confidence": final_conf, "analysis": analysis}


predictor = AdvancedPredictor()


# ===================== MESSAGE FORMATTER =====================
def format_signal_message(period, prediction, confidence, analysis, period_num):
    """নতুন সিগনাল message তৈরি"""
    pred_emoji = "🔴 BIG" if prediction == "BIG" else "🟢 SMALL"
    bar_filled = round(confidence / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    total = stats["wins"] + stats["losses"]
    win_rate = round(stats["wins"] / total * 100) if total > 0 else 0

    msg = (
        f"╔══════════════════════╗\n"
        f"║  🤖 BD RAKIB 007 AI  ║\n"
        f"╚══════════════════════╝\n\n"
        f"📌 *PERIOD:* `{str(period)[-8:]}`\n"
        f"⏰ *TIME:* `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *SIGNAL:*  {pred_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *CONFIDENCE:* `{confidence}%`\n"
        f"`{bar}` {confidence}%\n\n"
        f"🧠 *ANALYSIS:*\n"
        f"`{analysis[:80]}...`\n\n"
        f"📈 *SESSION STATS:*\n"
        f"✅ Wins: `{stats['wins']}`  ❌ Loss: `{stats['losses']}`  🎯 Rate: `{win_rate}%`\n\n"
        f"⚡ _12-Algorithm AI Engine_"
    )
    return msg


def format_result_message(period, prediction, actual, status):
    """Result update message"""
    status_emoji = "✅ WIN" if status == "WIN" else "❌ LOSS"
    pred_emoji = "🔴" if prediction == "BIG" else "🟢"
    act_emoji = "🔴" if actual == "BIG" else "🟢"

    total = stats["wins"] + stats["losses"]
    win_rate = round(stats["wins"] / total * 100) if total > 0 else 0

    msg = (
        f"📊 *RESULT UPDATE*\n\n"
        f"📌 Period: `{str(period)[-8:]}`\n"
        f"🎯 Signal: {pred_emoji} `{prediction}`\n"
        f"🎲 Actual: {act_emoji} `{actual}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Result: *{status_emoji}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ `{stats['wins']}` Win  |  ❌ `{stats['losses']}` Loss  |  🎯 `{win_rate}%` Rate"
    )
    return msg


# ===================== MAIN BOT LOOP =====================
async def run_bot():
    global last_period

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Startup message
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🚀 *BD RAKIB 007 AI BOT STARTED*\n\n"
                "✅ Connected to WinGo API\n"
                "🧠 12-Algorithm Engine Active\n"
                "📡 Live signals will appear here\n\n"
                "_Waiting for next period..._"
            ),
            parse_mode="Markdown"
        )
        logger.info("Bot started, startup message sent.")
    except TelegramError as e:
        logger.error(f"Startup message failed: {e}")

    while True:
        try:
            period = fetch_current_period()
            history_raw = fetch_history()

            if not history_raw or not period:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            history = [
                {"period": item["issueNumber"], "number": int(item["number"]),
                 "resultType": get_big_small(int(item["number"]))}
                for item in history_raw[:30]
            ]

            if period != last_period:
                logger.info(f"New period detected: {period}")

                # ---- Resolve previous prediction ----
                if prediction_log and prediction_log[-1]["status"] == "Pending":
                    prev = prediction_log[-1]
                    match = next((h for h in history if h["period"] == prev["period"]), None)
                    if match:
                        actual = get_big_small(match["number"])
                        status = "WIN" if prev["prediction"] == actual else "LOSS"
                        prev["result"] = actual
                        prev["status"] = status
                        if status == "WIN": stats["wins"] += 1
                        else: stats["losses"] += 1

                        try:
                            result_msg = format_result_message(
                                prev["period"], prev["prediction"], actual, status
                            )
                            await bot.send_message(
                                chat_id=CHAT_ID,
                                text=result_msg,
                                parse_mode="Markdown"
                            )
                            logger.info(f"Result sent: {status} for period {prev['period']}")
                        except TelegramError as e:
                            logger.error(f"Result message failed: {e}")

                # ---- New prediction ----
                result = predictor.analyze(history)
                prediction_log.append({
                    "period": period,
                    "prediction": result["prediction"],
                    "result": None,
                    "status": "Pending"
                })
                if len(prediction_log) > 20:
                    prediction_log.pop(0)

                try:
                    signal_msg = format_signal_message(
                        period, result["prediction"], result["confidence"],
                        result["analysis"], len(prediction_log)
                    )
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=signal_msg,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Signal sent: {result['prediction']} ({result['confidence']}%) for period {period}")
                except TelegramError as e:
                    logger.error(f"Signal message failed: {e}")

                last_period = period

        except Exception as e:
            logger.error(f"Main loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    print("=" * 50)
    print("  BD RAKIB 007 - Telegram Signal Bot")
    print("=" * 50)
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"Chat ID: {CHAT_ID}")
    print("Starting bot loop...")
    print("=" * 50)
    asyncio.run(run_bot())
