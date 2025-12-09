import os
import json
import datetime
import time
import google.generativeai as genai
from pathlib import Path

DATA_DIR = "it_news_data"
OUTPUT_DIR = "_posts"

# Gemini API 키 (코드 상단에 직접 입력 or 환경변수)
GEMINI_API_KEY = "여기에-GEMINI-API-키-입력"

def load_week_data():
    """지난 7일간의 뉴스 데이터 불러오기"""
    today = datetime.date.today()
    articles = []
    
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        filename = f"{DATA_DIR}/{date.strftime('%Y-%m-%d')}.json"
        
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                articles.extend(data.get("articles", []))
            print(f"[INFO] Loaded {len(data.get('articles', []))} articles from {date}")
    
    return articles

def categorize_articles(articles):
    """카테고리별로 기사 분류"""
    categories = {}
    
    for article in articles:
        category = article.get("category", "기타")
        if category not in categories:
            categories[category] = []
        categories[category].append(article)
    
    return categories

def generate_summary_with_gemini(articles_by_category):
    """Gemini API로 주간 요약 생성"""
    api_key = GEMINI_API_KEY if GEMINI_API_KEY != "여기에-GEMINI-API-키-입력" else os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == "여기에-GEMINI-API-키-입력":
        print("[ERROR] GEMINI_API_KEY not set!")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 카테고리별 기사 리스트 생성
        prompt = "다음은 이번 주 IT 업계 주요 뉴스입니다. 카테고리별로 핵심 내용을 요약해주세요.\n\n"
        
        for category, articles in articles_by_category.items():
            prompt += f"## {category}\n\n"
            for i, article in enumerate(articles[:10], 1):  # 카테고리당 최대 10개
                prompt += f"{i}. [{article['title']}]({article['link']})\n"
                prompt += f"   출처: {article['source']}\n\n"
        
        prompt += """
위 뉴스들을 다음 형식으로 요약해주세요:

### 🔥 이번 주 핫이슈

### 💻 개발 트렌드

### 🚀 기술 뉴스

### 📌 주목할 만한 소식

각 섹션마다 3-5개의 핵심 내용을 bullet point로 정리하고, 
중요한 기사는 링크를 포함해주세요.
"""
        
        print("[INFO] Generating summary with Gemini...")
        response = model.generate_content(prompt)
        
        if response and response.text:
            print("[OK] Summary generated successfully")
            time.sleep(4)  # Rate limit 방지
            return response.text.strip()
        
    except Exception as e:
        print(f"[ERROR] Gemini API error: {e}")
        time.sleep(4)
    
    return None

def create_weekly_post(summary, article_count):
    """주간 요약 블로그 포스트 생성"""
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=6)
    
    filename = f"{today.strftime('%Y-%m-%d')}-weekly-it-news.md"
    title = f"주간 IT 뉴스 요약 ({week_start.strftime('%m.%d')} - {today.strftime('%m.%d')})"
    
    if not summary:
        summary = """### 요약 생성 실패

이번 주 수집된 뉴스는 총 {article_count}개입니다.
상세 내용은 수집된 데이터를 확인해주세요.
""".format(article_count=article_count)
    
    content = f"""---
layout: post
title: "{title}"
date: {today.strftime('%Y-%m-%d')}
categories: [IT, News]
tags: [it-news, weekly-summary, tech-trends]
---

## 📰 이번 주 IT 뉴스 요약

{summary}

---

*이 포스트는 자동으로 수집된 IT 뉴스를 요약한 것입니다.*  
*총 {article_count}개의 기사를 분석했습니다.*
"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Created: {filename}")
    return filename

def main():
    """주간 요약 생성 메인 함수"""
    print("[INFO] Starting weekly summary generation...")
    
    # 1. 일주일치 데이터 불러오기
    articles = load_week_data()
    
    if not articles:
        print("[WARN] No articles found for the past week")
        return
    
    print(f"[INFO] Total articles collected: {len(articles)}")
    
    # 2. 카테고리별 분류
    articles_by_category = categorize_articles(articles)
    
    for category, items in articles_by_category.items():
        print(f"[INFO] {category}: {len(items)} articles")
    
    # 3. Gemini로 요약 생성
    summary = generate_summary_with_gemini(articles_by_category)
    
    # 4. 블로그 포스트 생성
    create_weekly_post(summary, len(articles))
    
    print(f"\n{'='*50}")
    print("[DONE] Weekly summary created!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
