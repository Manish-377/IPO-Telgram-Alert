# 🚀 IPO Alert Telegram Bot

Automatically monitors and alerts about IPOs closing today that meet your criteria via Telegram.

## ✨ Features

- Scrapes live IPO data from InvestorGain
- Filters IPOs based on:
  - GMP > 20%
  - IPO Size > ₹50 Cr
  - Subscription levels (QIB/BNII/SNII > 10x)
- Sends formatted alerts to Telegram
- Runs automatically daily at 10:00 AM IST via GitHub Actions

## 🔐 Setup

### 1. Get Telegram Credentials

**Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy your bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Chat ID:**
1. Start a chat with your bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your `chat_id` in the response

### 2. Local Testing

**Windows (PowerShell):**
```powershell
$env:TG_BOT_TOKEN="your_bot_token_here"
$env:TG_CHAT_ID="your_chat_id_here"
python ipo_alert.py
```

**Linux/Mac:**
```bash
export TG_BOT_TOKEN="your_bot_token_here"
export TG_CHAT_ID="your_chat_id_here"
python ipo_alert.py
```

### 3. GitHub Actions Setup

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Add GitHub Secrets:**
   - Go to your repo → **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Add:
     - Name: `TG_BOT_TOKEN`, Value: Your bot token
     - Name: `TG_CHAT_ID`, Value: Your chat ID

3. **Enable Actions:**
   - Go to **Actions** tab
   - Enable workflows if prompted
   - Workflow will run daily at 10:00 AM IST automatically
   - Or click **Run workflow** to test immediately

## 📋 Requirements

```bash
pip install requests beautifulsoup4
```

## 🎯 Filtering Criteria

The bot alerts only when ALL conditions are met:
- IPO closing **today**
- GMP ≥ **20%**
- IPO Size ≥ **₹50 Cr**
- At least one subscription category (QIB/BNII/SNII) ≥ **10x**

## 📱 Alert Format

```
🚀 IPO MATCHED YOUR RULES

📌 Company Name
📅 Closing: Today
💰 IPO Size: ₹XXX Cr

📈 GMP: XX%
🏦 QIB: XXx
👤 BNII (HNI): XXx
🧑 SNII: XXx

🔗 [Details Link]
```

## 🔄 Schedule

- **Cron:** `30 4 * * *` (4:30 AM UTC = 10:00 AM IST)
- **Manual:** Via GitHub Actions "Run workflow" button

## 📝 License

MIT
