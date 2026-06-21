from collector.news_collector import collect_news
from collector.youtube_collector import collect_youtube
from nlp.keywords import extract_keywords

news = collect_news('Nike')
youtube = collect_youtube('Nike')
all_docs = news + youtube

print(f"\nTotal documents collected: {len(all_docs)} (news: {len(news)}, youtube: {len(youtube)})")

keywords = extract_keywords(all_docs, top_n=25, brand='Nike')
print('\nTop 25 keywords for Nike:')
for kw in keywords:
    print(f"  {kw['keyword']}: {kw['score']}")