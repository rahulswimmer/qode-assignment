from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import random
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from webdriver_manager.chrome import ChromeDriverManager

TAGS = ["#nifty50", "#sensex", "#intraday", "#banknifty"]
LOOKBACK_HOURS = 24
PER_TAG_LIMIT = 800          # per-tag soft cap
MAX_SCROLLS = 150            # safety cap
OUTPUT = Path("data/tweets_raw.parquet")
HEADLESS = True

def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def jitter(a: float=0.6, b: float=1.2) -> None:
    time.sleep(random.uniform(a,b))

def last_n_hours(n: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=n)
    return start, end

def build_driver(headless: bool = True):
    """Create and return a configured Chrome WebDriver."""
    ua = UserAgent()
    opts = Options()

    # Headless keeps the browser invisible; toggle via HEADLESS flag
    if headless:
        opts.add_argument("--headless=new")

    # Standard stability flags
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--lang=en-US,en;q=0.9")

    # Slightly disguise automation
    opts.add_argument(f"--user-agent={ua.random}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # Instantiate the driver (webdriver-manager downloads the correct version)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    # Remove the webdriver flag from JS context (anti-bot tweak)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"},
        )
    except Exception:
        pass

    log("Chrome driver initialized")
    return driver

# ---------- SECTION 3: open page, scroll, get HTML ----------

def open_tag_live(driver, tag: str) -> None:
    """Go to the X 'Live' search feed for the given tag/query."""
    url = f"https://x.com/search?q={tag.replace('#','%23')}&src=typed_query&f=live"
    log(f"open {tag}: {url}")
    driver.get(url)
    jitter(1.0, 2.0)  # let first batch render

def scroll_once(driver) -> None:
    """One END key press to load more tweets."""
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
    jitter()  # small human-ish pause

def get_page_html(driver) -> str:
    """Return current page HTML."""
    return driver.page_source

def grab_html_batch_for_tag(driver, tag: str, n_scrolls: int = 2) -> str:
    """
    Open the tag's live feed and perform n_scrolls.
    Returns final HTML after the last scroll.
    """
    open_tag_live(driver, tag)
    for _ in range(max(0, n_scrolls)):
        scroll_once(driver)
    return get_page_html(driver)


if __name__ == "__main__":
    start_utc, end_utc = last_n_hours(LOOKBACK_HOURS)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    driver = build_driver(headless=HEADLESS)
    try:
        tag = TAGS[0]
        html = grab_html_batch_for_tag(driver, tag, n_scrolls=3)
        log(f"HTML length for {tag}: {len(html)}")

        # quick sanity: count tweets/time tags present
        soup = BeautifulSoup(html, "lxml")
        arts = soup.select("article")
        times = soup.select("article time")
        log(f"articles: {len(arts)} | time tags: {len(times)}")
    finally:
        driver.quit()