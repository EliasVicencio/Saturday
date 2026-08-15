# test_news.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NEWS_API_KEY")
print(f"API Key: {api_key[:10] if api_key else 'NO'}...")

if not api_key:
    print("❌ NEWS_API_KEY no configurada")
    exit()

url = "https://newsapi.org/v2/top-headlines"
params = {
    'apiKey': api_key,
    'country': 'cl',
    'language': 'es',
    'pageSize': 5
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Total resultados: {data.get('totalResults', 0)}")
    if data.get('articles'):
        print(f"✅ {len(data['articles'])} artículos encontrados")
        for article in data['articles'][:3]:
            print(f"  - {article.get('title', 'Sin título')}")
    else:
        print("❌ No hay artículos")
else:
    print(f"❌ Error: {response.text}")