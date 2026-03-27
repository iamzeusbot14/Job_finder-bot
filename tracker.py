import yaml
import os
import requests
import pandas as pd
from jobspy import scrape_jobs

# 1. Setup History (Memory)
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

TARGET_COMPANIES = config["companies"]
all_new_jobs = []

# 3. Scrape and Hard Filter
for company in TARGET_COMPANIES:
    for kw in config["keywords"]:
        try:
            # Search for the specific company + keyword
            jobs = scrape_jobs(
                site_name=["linkedin"],
                search_term=f"{company} {kw}",
                location=config["location"],
                results_wanted=15,
                hours_old=config["past_hours"]
            )
            
            if not jobs.empty:
                # HARD FILTER: Only keep results where the 'company' column matches our list
                # This removes "Associative", "Infosys", etc.
                mask = jobs['company'].str.contains('|'.join(TARGET_COMPANIES), case=False, na=False)
                filtered_jobs = jobs[mask]
                
                # MEMORY FILTER: Remove jobs already in sent_jobs.txt
                new_jobs = filtered_jobs[~filtered_jobs['job_url'].astype(str).isin(sent_ids)]
                
                if not new_jobs.empty:
                    all_new_jobs.append(new_jobs)
        except Exception as e:
            print(f"Error scraping {company}: {e}")

# 4. Generate Report and Update History
if all_new_jobs:
    df = pd.concat(all_new_jobs).drop_duplicates(subset=['job_url'])
    df = df.sort_values(by='company')
    
    report = f"🚀 **Target Hiring Report ({len(df)} New)**\n---\n"
    new_history = []

    for _, row in df.iterrows():
        line = f"• **{row['company']}**: [{row['title']}]({row['job_url']})\n"
        
        # Split message if it exceeds Telegram's limit
        if len(report) + len(line) > 4000:
            send_telegram(report)
            report = ""
        report += line
        new_history.append(row['job_url'])

    if report:
        send_telegram(report)

    # Write new IDs to history file
    with open(HISTORY_FILE, "a") as f:
        for job_id in new_history:
            f.write(f"{job_id}\n")
else:
    print("No new jobs found for target companies.")
