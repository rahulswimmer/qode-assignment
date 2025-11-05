from faker import Faker
import random
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---- CONFIG ----
HASHTAG_LIST = ["#nifty50", "#sensex", "#intraday", "#banknifty"]
MENTION_LIST = ["@rahul", "@analyst101", "@traderjoe", "@deskbot", "@quantclub"]

NUM_ROWS = 2000
OUTPUT_FILE = "synthetic_tweets.csv"


def generate_random_timestamp():
    now = datetime.now(timezone.utc)
    random_offset_seconds = random.randint(0, 24 * 3600)
    ts = now - timedelta(seconds=random_offset_seconds)
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")

def main():
    try:
        fake = Faker()
        rows = []

        for _ in range(2000):
            try:
                username = fake.user_name()
                timestamp = generate_random_timestamp()

                tweet_content = fake.sentence(nb_words=random.randint(10,15))
                hashtag = random.sample(HASHTAG_LIST, 1)
                mention = random.sample(MENTION_LIST, 1)
                likes = random.randint(0, 2000)
                retweets = random.randint(0, 500)
                replies = random.randint(0, 200)
                engagement_metrics = (
                    f'{{"likes": {likes}, "retweets": {retweets}, "replies": {replies}}}'
                )

                rows.append(
                    {
                        "username": username,
                        "timestamp": timestamp,
                        "content": tweet_content,
                        "engagement_metrics": engagement_metrics,
                        "mentions": mention,
                        "hashtags": hashtag,
                    }
                )

                if rows:
                    try:
                        rows_df = pd.DataFrame(rows)
                        rows_df.to_parquet("tweets_ism.parquet")

                        rows_df = rows_df.drop_duplicates(subset=["username","timestamp","content"])
                    except Exception as e:
                        print("Something went wrong when converting dataframe to parquet: {e}")
                else:
                    print("No data in rows variable.")
            except Exception as e:
                print(f"Issue with a row because of: {e}")
    except Exception as e:
        print(f"Critical issue with program itself: {e}")

if __name__ == "__main__":
    main()
