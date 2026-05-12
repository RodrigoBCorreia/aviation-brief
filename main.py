import os
import sys
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from scraper import fetch_aviation_news
from formatter import format_brief
from sender import send_whatsapp

SEND_TIME = os.getenv("SEND_TIME", "07:00")


def run_brief():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching aviation news...")
    try:
        articles = fetch_aviation_news()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(articles)} articles.")
        message = format_brief(articles)
        send_whatsapp(message)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Morning brief sent successfully!")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise


if __name__ == "__main__":
    # Pass --now to send immediately (useful for testing)
    if "--now" in sys.argv:
        print("Running brief now (--now flag detected)...")
        run_brief()
        sys.exit(0)

    print(f"Aviation Brief Bot started. Will send daily at {SEND_TIME}.")
    print("Press Ctrl+C to stop.\n")

    schedule.every().day.at(SEND_TIME).do(run_brief)

    while True:
        schedule.run_pending()
        time.sleep(30)
