import os
import json
import datetime
import time
import re
import google.generativeai as genai
from pathlib import Path

DATA_DIR = "it_news_data"
OUTPUT_DIR = "_posts"

# Gemini API 키
GEMINI_API_KEY = "여기에-GEMINI-API-키-입력"

def clean_html_tags(text):
    """HTML 태그 제거"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

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

def chunk_list(data_list, chunk_size):
    """리스트를 청크 단위로 분할"""
    for i in range(0, len(data_list), chunk_size):
        yield data_list[i:i + chunk_size]

def generate_summary_with_gemini(articles):
    """Gemini API로 맵 리듀스 방식 요약 생성"""
    api_key = GEMINI_API_KEY if GEMINI_API_KEY != "여기에-GEMINI-API-키-입력" else os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == "여기에-GEMINI-API-키-입력":
        print("[ERROR] GEMINI_API_KEY is missing! Check Github Secrets.")
        return None
    
    # ==========================================
    # [디버깅 모드] 기사가 너무 많으면 테스트가 어려우므로
    # API 연결 확인을 위해 앞에서 5개만 잘라서 테스트합니다.
    # 테스트 성공 후에는 아래 두 줄을 지우거나 주석 처리하세요.
    print(f"[TEST MODE] 전체 {len(articles)}개 중 앞의 5개만 테스트합니다.")
    articles = articles[:5]
    # ==========================================

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print(f"[INFO] Processing {len(articles)} articles...")
        batch_size = 5 # 테스트를 위해 배치를 작게 잡음
        intermediate_summaries = []
        
        for i, batch in enumerate(chunk_list(articles, batch_size)):
            print(f"  - Processing batch {i+1}...")
            
            batch_text = ""
            for article in batch:
                title = article.get('title', '무제')
                link = article.get('link', '#')
                summary = clean_html_tags(article.get('summary', ''))[:200]
                source = article.get('source', 'Unknown')
                category = article.get('category', 'General')
                
                batch_text += f"제목: {title}\n카테고리: {category}\n출처: {source}\n내용: {summary}\n링크: {link}\n\n"

            map_prompt = f"""
            다음 IT 뉴스 기사들을 요약해주세요.
            
            [기사 목록]
            {batch_text}
            
            [요청사항]
            각 기사의 핵심을 1~2문장으로 요약하고, 링크를 포함해주세요.
            """
            
            response = model.generate_content(map_prompt)
            if response and response.text:
                intermediate_summaries.append(response.text)
            
            # API 과부하 방지를 위해 딜레이 추가
            time.sleep(5) 

        print("[INFO] Generating final summary...")
        all_summaries = "\n\n".join(intermediate_summaries)
        
        reduce_prompt = f"""
        다음 내용을 바탕으로 '주간 IT 뉴스 요약' 블로그 포스트를 작성해주세요.
        마크다운 형식으로 작성하고, 흥미로운 주제별로 묶어주세요.

        [내용]
        {all_summaries}
        """
        
        final_response = model.generate_content(reduce_prompt)
        
        if final_response and final_response.text:
            print("[OK] Final summary generated successfully")
            return final_response.text.strip()
            
    except Exception as e:
        # 에러가 발생하면 정확한 메시지를 출력합니다.
        print(f"[ERROR] Gemini API error details: {str(e)}")
    
    return None

def create_weekly_post(summary, article_count):
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=6)
    
    filename = f"{today.strftime('%Y-%m-%d')}-weekly-it-news.md"
    title = f"주간 IT 뉴스 요약 ({week_start.strftime('%m.%d')} - {today.strftime('%m.%d')})"
    
    if not summary:
        summary = f"""### 요약 생성 실패

이번 주 수집된 뉴스는 총 {article_count}개입니다.
로그(Actions)에서 [ERROR] 메시지를 확인해주세요.
"""
    
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
"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Created: {filename}")
    return filename

def main():
    print("[INFO] Starting weekly summary generation...")
    articles = load_week_data()
    
    if not articles:
        print("[WARN] No articles found for the past week")
        return
    
    summary = generate_summary_with_gemini(articles)
    create_weekly_post(summary, len(articles))
    print("[DONE] Weekly summary created!")

if __name__ == "__main__":
    main()
