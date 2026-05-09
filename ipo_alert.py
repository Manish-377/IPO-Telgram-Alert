import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import re
import sys

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID")

GMP_URL = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
SUB_URL = "https://ipowatch.in/ipo-subscription-status-today/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Filter thresholds
MIN_GMP_PCT = 20
MIN_SUB_X = 10


# ================= TELEGRAM =================
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [!] Telegram credentials not set. Printing message instead:")
        print(f"  {msg}\n")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"  [X] Telegram send failed: {e}")
        return False


# ================= PARSING HELPERS =================
def parse_float(text):
    text = text.strip().replace(",", "").replace("₹", "")
    if not text or text in ("-", "–", ""):
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_name(name):
    name = name.lower().strip()
    for suffix in [" ltd", " ltd.", " limited", " ipo", " sme", " reit"]:
        name = name.replace(suffix, "")
    return re.sub(r"[^a-z0-9\s]", "", name).strip()


def parse_close_date(date_text):
    """Parse close date from format like '5-7 May' or '12-14 May'."""
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s+(\w+)", date_text)
    if not m:
        return None
    day = int(m.group(2))
    month_str = m.group(3)
    year = datetime.now().year
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(f"{day} {month_str} {year}", fmt)
        except ValueError:
            continue
    return None


# ================= SCRAPE GMP =================
def fetch_gmp_data():
    print("[*] Fetching GMP data from ipowatch.in ...")
    resp = requests.get(GMP_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the live GMP table (has 8-9 columns with IPO data, no <th> headers)
    gmp_table = None
    for t in soup.find_all("table"):
        first_row = t.find("tr")
        if not first_row:
            continue
        cols = first_row.find_all("td")
        # GMP table rows have 8-9 columns: Name|GMP|Trend|Price|Est.Listing|Date|Type|Status|Updated
        if len(cols) >= 8:
            gmp_table = t
            break

    if not gmp_table:
        print("[X] Could not find GMP table")
        return []

    rows = gmp_table.find("tbody")
    rows = rows.find_all("tr") if rows else gmp_table.find_all("tr")

    ipos = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
        try:
            name = cols[0].get_text(strip=True)
            # Skip header-like rows
            if name.lower() in ("ipo name", "name", ""):
                continue
            gmp_text = cols[1].get_text(strip=True)
            price_text = cols[3].get_text(strip=True)
            listing_text = cols[4].get_text(strip=True)
            date_text = cols[5].get_text(strip=True)
            ipo_type = cols[6].get_text(strip=True) if len(cols) > 6 else ""
            status = cols[7].get_text(strip=True) if len(cols) > 7 else ""

            pct_match = re.search(r"\(([0-9.]+)%\)", listing_text)
            gmp_pct = float(pct_match.group(1)) if pct_match else 0.0

            gmp_val = parse_float(gmp_text)
            price_val = parse_float(price_text)
            close_date = parse_close_date(date_text)

            link = cols[0].find("a")
            detail_url = ""
            if link and link.get("href"):
                href = link["href"]
                detail_url = href if href.startswith("http") else "https://ipowatch.in" + href

            ipos.append({
                "name": name,
                "gmp": gmp_val,
                "gmp_pct": gmp_pct,
                "price": price_val,
                "close_date": close_date,
                "date_text": date_text,
                "type": ipo_type,
                "status": status,
                "url": detail_url,
            })
        except Exception as e:
            print(f"  [!] Error parsing GMP row: {e}")
    print(f"[+] Found {len(ipos)} IPOs in GMP table")
    return ipos


# ================= SCRAPE SUBSCRIPTION =================
def fetch_subscription_data():
    print("[*] Fetching subscription data from ipowatch.in ...")
    resp = requests.get(SUB_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    sub_table = None
    for t in soup.find_all("table"):
        text = t.get_text()
        if "QIB" in text or "Retail" in text:
            sub_table = t
            break
    if not sub_table:
        for t in soup.find_all("table"):
            first_row = t.find("tr")
            if first_row and len(first_row.find_all(["td", "th"])) >= 6:
                sub_table = t
                break
    if not sub_table:
        print("[X] Could not find subscription table")
        return {}

    rows = sub_table.find("tbody")
    rows = rows.find_all("tr") if rows else sub_table.find_all("tr")[1:]

    subs = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        try:
            name = cols[0].get_text(strip=True)
            qib = parse_float(cols[4].get_text(strip=True))
            nii = parse_float(cols[5].get_text(strip=True))
            retail = parse_float(cols[6].get_text(strip=True))
            total = parse_float(cols[7].get_text(strip=True)) if len(cols) > 7 else 0.0
            subs[normalize_name(name)] = {
                "qib": qib, "nii": nii, "retail": retail, "total": total,
            }
        except Exception:
            continue
    print(f"[+] Found subscription data for {len(subs)} IPOs")
    return subs


def find_subscription(sub_data, ipo_name):
    key = normalize_name(ipo_name)
    if key in sub_data:
        return sub_data[key]
    for k, v in sub_data.items():
        if key in k or k in key:
            return v
        w1, w2 = key.split()[:2] if len(key.split()) >= 2 else (key, ""), k.split()[:2] if len(k.split()) >= 2 else (k, "")
        if w1 and w2 and w1 == w2:
            return v
    return None


# ================= MAIN =================
def main():
    today = datetime.now()

    print(f"=== IPO Alert Bot  |  {today.strftime('%d %b %Y')} ===")
    print(f"Criteria: GMP >= {MIN_GMP_PCT}%  |  Subscription >= {MIN_SUB_X}x")
    print(f"Filter:   Open IPOs closing today\n")

    gmp_data = fetch_gmp_data()
    sub_data = fetch_subscription_data()

    if not gmp_data:
        print("[X] No GMP data. Exiting.")
        return

    found_any = False

    for ipo in gmp_data:
        name = ipo["name"]
        print(f"\n--- {name} ---")
        print(f"  Date: {ipo['date_text']}  |  Status: {ipo['status']}  |  Type: {ipo['type']}")
        print(f"  GMP: Rs {ipo['gmp']} ({ipo['gmp_pct']}%)  |  Price: Rs {ipo['price']}")

        # Only Open IPOs
        if ipo["status"].lower() != "open":
            print(f"  -> SKIP: Status is '{ipo['status']}', not Open")
            continue

        # Must be closing today
        if not ipo["close_date"] or ipo["close_date"].date() != today.date():
            closing = ipo['close_date'].strftime('%d %b') if ipo['close_date'] else 'unknown'
            print(f"  -> SKIP: Closes on {closing}, not today")
            continue

        # GMP filter
        if ipo["gmp_pct"] < MIN_GMP_PCT:
            print(f"  -> SKIP: GMP {ipo['gmp_pct']}% < {MIN_GMP_PCT}%")
            continue

        # Subscription filter
        sub = find_subscription(sub_data, name)
        if not sub:
            print("  -> SKIP: No subscription data yet")
            continue

        max_sub = max(sub["qib"], sub["nii"], sub["retail"])
        print(f"  Sub: QIB={sub['qib']}x  NII={sub['nii']}x  Retail={sub['retail']}x  Total={sub['total']}x")

        if max_sub < MIN_SUB_X:
            print(f"  -> SKIP: Max sub {max_sub}x < {MIN_SUB_X}x")
            continue

        print("  >> MATCHED ALL CRITERIA!")
        found_any = True

        msg = (
            "🚀 <b>IPO ALERT — Closing Today!</b>\n\n"
            f"📌 <b>{name}</b>\n"
            f"📅 {ipo['date_text']}  |  Last day to apply!\n"
            f"🏷️ {ipo['type']}  |  Price: ₹{ipo['price']}\n\n"
            f"📈 GMP: ₹{ipo['gmp']} ({ipo['gmp_pct']}%)\n"
            f"🏦 QIB: {sub['qib']}x\n"
            f"👤 NII (HNI): {sub['nii']}x\n"
            f"🧑 Retail: {sub['retail']}x\n"
            f"📊 Total: {sub['total']}x\n"
        )
        if ipo["url"]:
            msg += f"\n🔗 {ipo['url']}"

        if send_telegram(msg):
            print("  -> Telegram alert sent!")

    if not found_any:
        print(f"\n[i] No Open IPOs closing today matched all criteria.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Testing Telegram connection ...\n")
        test_msg = (
            "✅ <b>TEST MESSAGE</b>\n\n"
            "Your IPO Alert Bot is working!\n\n"
            "Criteria:\n"
            f"• GMP ≥ {MIN_GMP_PCT}%\n"
            f"• Subscription ≥ {MIN_SUB_X}x\n"
            f"• Only Open IPOs closing today\n\n"
            "🤖 Bot Status: Active"
        )
        if send_telegram(test_msg):
            print("Test message sent! Check Telegram.")
        else:
            print("Failed. Set TG_BOT_TOKEN and TG_CHAT_ID env vars.")
    else:
        main()
