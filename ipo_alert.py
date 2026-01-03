import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID")

INVESTORGAIN_URL = "https://www.investorgain.com/report/live-ipo-gmp/331/"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ================= TELEGRAM =================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload, timeout=10)

# ================= SUBSCRIPTION =================
def get_subscription(gmp_url):
    sub_url = gmp_url.replace("/gmp/", "/subscription/")
    r = requests.get(sub_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    subs = {"QIB": 0, "BNII": 0, "SNII": 0}

    table = soup.find("table")
    if not table:
        return subs

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        label = cols[0].get_text(strip=True).upper()
        value = cols[-1].get_text(strip=True).replace("x", "")

        try:
            val = float(value)
        except:
            continue

        if "QIB" in label:
            subs["QIB"] = val
        elif "BIG" in label or "BNII" in label:
            subs["BNII"] = val
        elif "SMALL" in label or "SNII" in label:
            subs["SNII"] = val

    return subs

# ================= MAIN =================
def main():
    today = datetime.now().strftime("%d-%b").lstrip("0")

    html = requests.get(INVESTORGAIN_URL, headers=HEADERS, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="report_table")
    rows = table.find("tbody").find_all("tr")

    for r in rows:
        cols = r.find_all("td")
        if len(cols) < 9:
            continue

        name = cols[0].get_text(strip=True)
        gmp_cell = cols[1].get_text(" ", strip=True)
        size = float(cols[5].get_text(strip=True))
        close_date = cols[8].get_text(strip=True)

        link = cols[0].find("a")
        if not link:
            continue

        gmp_url = "https://www.investorgain.com" + link["href"]

        if today not in close_date:
            continue

        if "(" not in gmp_cell:
            continue

        try:
            gmp_percent = float(gmp_cell.split("(")[1].split("%")[0])
        except:
            continue

        if gmp_percent < 20 or size < 50:
            continue

        subs = get_subscription(gmp_url)

        if max(subs["QIB"], subs["BNII"], subs["SNII"]) < 10:
            continue

        msg = (
            "🚀 <b>IPO MATCHED YOUR RULES</b>\n\n"
            f"📌 <b>{name}</b>\n"
            f"📅 Closing: Today\n"
            f"💰 IPO Size: ₹{size} Cr\n\n"
            f"📈 GMP: {gmp_percent}%\n"
            f"🏦 QIB: {subs['QIB']}x\n"
            f"👤 BNII (HNI): {subs['BNII']}x\n"
            f"🧑 SNII: {subs['SNII']}x\n\n"
            f"🔗 {gmp_url}"
        )

        send_telegram(msg)

if __name__ == "__main__":
    main()
