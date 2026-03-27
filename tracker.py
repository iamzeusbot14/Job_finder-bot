import yaml
import os
import requests
from jobspy import scrape_jobs

def send_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Disable link previews to keep the message compact
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

# 1. Load Config
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)["search"]

# 2. Scrape Jobs for Google
all_jobs = []
for kw in config["keywords"]:
    jobs = scrape_jobs(
        site_name=["linkedin"],
        search_term=f"{config['company']} {kw}",
        location=config["location"],
        results_wanted=10,
        hours_old=config["past_hours"]
    )
    if not jobs.empty:
        all_jobs.append(jobs)

# 3. Aggregate and Send "Hidden" Report
if all_jobs:
    import pandas as pd
    df = pd.concat(all_jobs).drop_duplicates(subset=['job_url'])
    
    report = f"🔍 **Google Hiring Report ({len(df)} New Posts)**\n"
    report += "---" + "\n"
    
    for _, row in df.iterrows():
        # Clean up title and create a compact line
        line = f"• [{row['title']}]({row['job_url']}) | {row['location']}\n"
        # Telegram has a 4096 character limit per message
        if len(report) + len(line) > 4000:
            send_telegram(report)
            report = ""
        report += line
    
    if report:
        send_telegram(report)
else:
    print("No new Google posts found today.")
