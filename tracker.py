import yaml
import os
import requests
from jobspy import scrape_jobs

# 1. Load Config
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)["search"]

# 2. Scrape Jobs
jobs = scrape_jobs(
    site_name=["linkedin"],
    search_term=config["keywords"][0], # You can loop these if needed
    location=config["location"],
    results_wanted=5,
    hours_old=config["past_hours"],
    linkedin_fetch_description=True
)

# 3. Send to Telegram
if not jobs.empty:
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    for _, row in jobs.iterrows():
        message = (
            f"🚀 **New Google Opening!**\n\n"
            f"**Title:** {row['title']}\n"
            f"**Location:** {row['location']}\n"
            f"🔗 [Apply Here]({row['job_url']})"
        )
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
else:
    print("No new jobs found in the last 24 hours.")
