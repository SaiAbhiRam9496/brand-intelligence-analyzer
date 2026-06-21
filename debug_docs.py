from collector.news_collector import collect_news
from collector.youtube_collector import collect_youtube
from nlp.text_cleaning import clean_text

news = collect_news('Nike')
youtube = collect_youtube('Nike')

print("=== NEWS SAMPLES ===")
for doc in news[:5]:
    print(clean_text(doc['text'])[:200])
    print("---")

print("\n=== YOUTUBE SAMPLES ===")
for doc in youtube[:5]:
    print(clean_text(doc['text'])[:200])
    print("---")