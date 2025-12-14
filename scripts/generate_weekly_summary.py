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
        print("[ERROR] GEMINI_API_KEY not set!")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 1단계: 배치 처리 (Map) - 20개씩 끊어서 중간 요약 생성
        print(f"[INFO] Processing {len(articles)} articles...")
        batch_size = 20
        intermediate_summaries = []
        
        for i, batch in enumerate(chunk_list(articles, batch_size)):
            print(f"  - Processing batch {i+1}...")
            
            batch_text = ""
            for article in batch:
                title = article.get('title', '무제')
                link = article.get('link', '#')
                summary = clean_html_tags(article.get('summary', ''))[:200] # HTML 제거 및 길이 제한
                source = article.get('source', 'Unknown')
                category = article.get('category', 'General')
                
                batch_text += f"제목: {title}\n카테고리: {category}\n출처: {source}\n내용: {summary}\n링크: {link}\n\n"

            map_prompt = f"""
            다음은 IT 뉴스 기사 모음입니다. 각 기사의 핵심 내용을 파악하여 요약해주세요.
            
            [기사 목록]
            {batch_text}
            
            [요청사항]
            1. 각 기사별로 한 줄 요약을 작성하세요.
            2. 기사의 원래 제목, 링크, 카테고리 정보를 반드시 포함하세요.
            3. 결과물은 나중에 합쳐서 최종 뉴스레터를 만들 것이므로, 정보가 누락되지 않게 정리해주세요.
            """
            
            response = model.generate_content(map_prompt)
            if response and response.text:
                intermediate_summaries.append(response.text)
            time.sleep(2) # Rate limit 방지

        # 2단계: 최종 통합 (Reduce)
        print("[INFO] Generating final summary...")
        all_summaries = "\n\n".join(intermediate_summaries)
        
        reduce_prompt = f"""
        다음은 이번 주 IT 뉴스를 나누어 요약한 중간 결과물들입니다.
        이 내용들을 종합하여 블로그 포스팅용 '주간 IT 뉴스 요약'을 마크다운 형식으로 작성해주세요.

        [중간 요약 데이터]
        {all_summaries}

        [작성 형식]
        ## 🔥 이번 주 핫이슈
        (가장 중요하고 많이 언급된 이슈 3~4가지를 선정하여 상세히 서술)

        ## 💻 개발 트렌드
        (개발자들에게 유용한 도구, 라이브러리, 기술 블로그 글 위주로 3~5개 bullet point)

        ## 🚀 기술 & 스타트업 뉴스
        (일반적인 IT 기업 동향, 신제품 출시 등 3~5개 bullet point)

        ## 📌 기타 단신
        (흥미로운 나머지 소식들)

        [필수 규칙]
        - 각 항목의 끝에는 반드시 관련 기사의 [링크]를 걸어주세요.
        - 톤앤매너는 전문적이면서도 읽기 쉽게 작성해주세요.
        - 중복된 내용은 하나로 합쳐주세요.
        """
        
        final_response = model.generate_content(reduce_prompt)
        
        if final_response and final_response.text:
            print("[OK] Final summary generated successfully")
            return final_response.text.strip()
            
    except Exception as e:
        print(f"[ERROR] Gemini API error: {e}")
    
    return None

def create_weekly_post(summary, article_count):
    """주간 요약 블로그 포스트 생성"""
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=6)
    
    filename = f"{today.strftime('%Y-%m-%d')}-weekly-it-news.md"
    title = f"주간 IT 뉴스 요약 ({week_start.strftime('%m.%d')} - {today.strftime('%m.%d')})"
    
    if not summary:
        summary = f"""### 요약 생성 실패

이번 주 수집된 뉴스는 총 {article_count}개입니다.
API 호출 중 오류가 발생했거나 할당량이 초과되었을 수 있습니다.
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

*이 포스트는 자동으로 수집된 IT 뉴스를 요약한 것입니다.* *총 {article_count}개의 기사를 분석했습니다.*
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
    
    # 2. Gemini로 맵 리듀스 요약 생성
    summary = generate_summary_with_gemini(articles)
    
    # 3. 블로그 포스트 생성
    create_weekly_post(summary, len(articles))
    
    print(f"\n{'='*50}")
    print("[DONE] Weekly summary created!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
