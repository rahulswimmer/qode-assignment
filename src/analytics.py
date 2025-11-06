import json
import math
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

INPUT_PARQUET = "synthetic_tweets.parquet"
RESAMPLE_FREQ = "15min" 
MAX_TFIDF_FEATURES = 2000 


BULLISH_WORDS = [
    "up", "rally", "breakout", "bullish", "buy", "long",
    "तेज़", "ऊपर", "ऊपर जा रहा", "high", "gain", "green"
]
HASHTAGS = ["#nifty50", "#nifty", "#banknifty", "#sensex", "#intraday"]


def load_tweets(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df

def simple_bullish_score(text: str) -> int:
    if not isinstance(text, str):
        return 0
    t = text.lower()
    return sum(1 for w in BULLISH_WORDS if w in t)


def has_nifty_tag(text: str) -> int:
    if not isinstance(text, str):
        return 0
    t = text.lower()
    return int(any(tag in t for tag in HASHTAGS))


def engagement_to_score(val) -> float:
    if val is None:
        return 0.0
   
    if isinstance(val, dict):
        likes = val.get("likes", 0)
        rts = val.get("retweets", 0)
        reps = val.get("replies", 0)
    else:
        try:
            d = json.loads(val)
            likes = d.get("likes", 0)
            rts = d.get("retweets", 0)
            reps = d.get("replies", 0)
        except Exception:
            return 0.0

    return likes * 1.0 + rts * 2.0 + reps * 1.5


def add_handcrafted_features(df: pd.DataFrame) -> pd.DataFrame:
    df["feat_bullish"] = df["content"].apply(simple_bullish_score)
    df["feat_has_nifty"] = df["content"].apply(has_nifty_tag)
    df["feat_len"] = df["content"].astype(str).str.len()
    df["feat_engagement"] = df["engagement_metrics"].apply(engagement_to_score)
    return df


def add_tfidf_features(df: pd.DataFrame, max_features: int = 2000) -> pd.DataFrame:
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2)
    )
    tfidf_matrix = vectorizer.fit_transform(df["content"].fillna(""))
    return df, tfidf_matrix, vectorizer

def build_per_tweet_signal(df: pd.DataFrame) -> pd.DataFrame:
    df["norm_bullish"] = df["feat_bullish"].clip(0, 5) / 5.0
    df["norm_len"] = df["feat_len"].clip(1, 280) / 280.0
    df["norm_eng"] = (df["feat_engagement"] / 2000.0).clip(0, 1)

    df["tweet_signal"] = (
        0.5 * df["norm_bullish"] +
        0.3 * df["feat_has_nifty"] +
        0.2 * df["norm_eng"]
    )
    return df


def aggregate_signal(df: pd.DataFrame, freq: str = "15min") -> pd.DataFrame:
    # set timestamp index for resampling
    g = (
        df.set_index("timestamp")
          .resample(freq)["tweet_signal"]
          .agg(["mean", "std", "count"])
    )

    g["stderr"] = g["std"] / g["count"].pow(0.5)
    g["stderr"] = g["stderr"].fillna(0)

    g["upper"] = g["mean"] + 1.96 * g["stderr"]
    g["lower"] = g["mean"] - 1.96 * g["stderr"]

    return g.reset_index()

def plot_signal(agg_df: pd.DataFrame):
    plt.figure()
    plt.plot(agg_df["timestamp"], agg_df["mean"], label="signal (mean)")
    plt.fill_between(
        agg_df["timestamp"],
        agg_df["lower"],
        agg_df["upper"],
        alpha=0.2,
        label="95% CI"
    )
    plt.title("Tweet-based bullishness (15 min)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_path = os.path.join(script_dir, "tweets_ism.parquet")

    df = load_tweets(parquet_path)

    # Dedup
    before = len(df)
    df = df.drop_duplicates(subset=["username", "timestamp", "content"])
    after = len(df)
    print(f"Deduplicated {before - after} rows")

    df = add_handcrafted_features(df)

    df = build_per_tweet_signal(df)

    # 5. aggregate to time window
    agg = aggregate_signal(df, freq=RESAMPLE_FREQ)
    print(agg.head())

    plot_signal(agg)

if __name__ == "__main__":
    main()
