# Tweet-to-Signal Demo (Synthetic Data)

This repo shows how to generate synthetic data using Faker library. 
It’s split into two scripts, one for entry and other for analytics.

---

## 1. What’s in here?

- **`init.py`** (Entry file)
  - Creates a file called `tweets_ism.parquet`
  - Each row is a tweet-like record in the **last 24 hours**
  - Fields: `username`, `timestamp`, `content`, `engagement_metrics`, `mentions`, `hashtags`
  - Includes some **Indian-language** and emoji content to prove Unicode handling
  - Deduplicates on (`username`, `timestamp`, `content`) before saving

- **`analytics.py`** (analysis process)
  - Loads `tweets_ism.parquet`
  - Does **feature engineering** (bullish words, hashtag check, tweet length, engagement score)
  - Builds a **per-tweet signal** (0–1-ish)
  - Aggregates to **15-minute buckets** and computes a **95% confidence interval**
  - (Optional) builds a **TF-IDF** matrix to show text → vector conversion
  - Plots the aggregated signal

---

## 2. Why synthetic?

The original requirement was to scrape tweets (e.g. with `snscrape` or Selenium), but scraping didn’t work reliably in the environment.  
Then I resorted to selenium web-driver, due to its login activity issues, it was acting funny.          
So we **simulated** tweets using `faker` + domain hashtags (`#nifty50`, `#sensex`, `#intraday`, `#banknifty`).  
This keeps the *shape* of the data the same, so downstream text/NLP steps can still be demonstrated.

---

## 3. Installation

Create / activate a virtual env (optional) and install:

```bash
pip install pandas pyarrow faker scikit-learn matplotlib


## 4. Version control
I intend to use git flow for version control.
Will create a feature branch, commit my work to it and raise a PR to merge in main branch.
In Prod environment, merge will trigger a CI pipeline which will build my python code and CD will later deploy in target environment.
