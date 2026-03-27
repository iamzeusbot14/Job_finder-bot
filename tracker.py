import yaml
import os
import requests
from jobspy import scrape_jobs

# 1. Load Sent History
HISTORY_FILE = "sent_jobs.txt"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        sent_ids = set(f.read().splitlines())
else:
    sent_ids = set()

def send_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

# 2. Load Config
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)["search"]

# 3. Scrape and Filter
all_jobs = []
for kw in config["keywords"]:
    jobs = scrape_jobs(
        site_name=["linkedin"],
        search_term=f"{config['company']} {kw}",
        location=config["location"],
        results_wanted=15,
        hours_old=config["past_hours"]
    )
    if not jobs.empty:
        # Filter out jobs already in our history file using the Job URL as a unique ID
        new_jobs = jobs[~jobs['job_url'].astype(str).isin(sent_ids)]
        if not new_jobs.empty:
            all_jobs.append(new_jobs)

# 4. Process and Save History
if all_jobs:
    import pandas as pd
    df = pd.concat(all_jobs).drop_duplicates(subset=['job_url'])
    
    report = f"🔍 **New Google Openings ({len(df)})**\n---\n"
    new_history = []

    for _, row in df.iterrows():
        report += f"• [{row['title']}]({row['job_url']}) | {row['location']}\n"
        new_history.append(row['job_url'])

    send_telegram(report)

    # Append new IDs to the history file
    with open(HISTORY_FILE, "a") as f:
        for job_id in new_history:
            f.write(f"{job_id}\n")
else:
    print("No unique new jobs found.")
