import os
import re
import subprocess
import datetime
import requests

POSTS_DIR = "_posts"
GITHUB_REPO = "gazxxni/Baekjoon_py"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/commits"

def get_commit_date_from_github(problem_id):
    """GitHub API로 특정 문제의 최초 커밋 날짜 가져오기"""
    try:
        # auto_upload/백준 폴더에서 해당 문제 검색
        search_path = f"auto_upload/백준"
        
        # GitHub API로 커밋 검색
        params = {
            "path": search_path,
            "per_page": 100
        }
        
        response = requests.get(GITHUB_API, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
        
        commits = response.json()
        
        # 커밋 중에서 해당 문제 번호가 포함된 것 찾기
        for commit in reversed(commits):  # 오래된 것부터
            message = commit.get('commit', {}).get('message', '')
            if problem_id in message or f"{problem_id}." in message:
                date_str = commit.get('commit', {}).get('author', {}).get('date', '')
                if date_str:
                    date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return date_obj.strftime("%Y-%m-%d")
        
        # 특정 파일 경로로 다시 시도
        for tier in ['Bronze', 'Silver', 'Gold', 'Platinum']:
            file_path = f"{search_path}/{tier}"
            params['path'] = file_path
            
            response = requests.get(GITHUB_API, params=params, timeout=10)
            if response.status_code == 200:
                commits = response.json()
                for commit in reversed(commits):
                    if problem_id in str(commit.get('commit', {})):
                        date_str = commit.get('commit', {}).get('author', {}).get('date', '')
                        if date_str:
                            date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            return date_obj.strftime("%Y-%m-%d")
        
    except Exception as e:
        print(f"[WARN] API error for {problem_id}: {e}")
    
    return None

def get_commit_date_from_local_git(problem_id):
    """로컬 Baekjoon_py 레포에서 Git 날짜 가져오기"""
    try:
        # 상위 폴더들을 탐색
        possible_paths = [
            r"D:\OneDrive\바탕 화면\Baekjoon_py",
            r"..\Baekjoon_py",
            r"..\..\Baekjoon_py",
        ]
        
        for base_path in possible_paths:
            if not os.path.exists(base_path):
                continue
            
            # auto_upload/백준 폴더에서 문제 번호 검색
            search_dir = os.path.join(base_path, "auto_upload", "백준")
            
            if not os.path.exists(search_dir):
                continue
            
            # 문제 번호를 포함하는 폴더 찾기
            for root, dirs, files in os.walk(search_dir):
                if f"{problem_id}." in root:
                    py_files = [f for f in files if f.endswith(".py")]
                    if py_files:
                        file_path = os.path.join(root, py_files[0])
                        
                        # Git 커밋 날짜 가져오기
                        result = subprocess.run(
                            ['git', 'log', '--diff-filter=A', '--follow', '--format=%aI', '--', file_path],
                            capture_output=True,
                            text=True,
                            cwd=base_path
                        )
                        
                        if result.stdout.strip():
                            date_str = result.stdout.strip().split('\n')[-1]
                            date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            return date_obj.strftime("%Y-%m-%d")
    
    except Exception as e:
        print(f"[WARN] Local Git error for {problem_id}: {e}")
    
    return None

def update_post_date(filepath):
    """포스트 파일의 날짜 자동 수정"""
    try:
        filename = os.path.basename(filepath)
        
        # 파일명에서 문제 번호 추출
        problem_match = re.search(r'baekjoon-(\d+)\.md', filename)
        if not problem_match:
            return False
        
        problem_id = problem_match.group(1)
        
        # 1순위: 로컬 Git에서 날짜 가져오기 (빠름)
        commit_date = get_commit_date_from_local_git(problem_id)
        
        # 2순위: GitHub API에서 날짜 가져오기 (느림)
        if not commit_date:
            print(f"[INFO] Trying GitHub API for {problem_id}...")
            commit_date = get_commit_date_from_github(problem_id)
        
        if not commit_date:
            print(f"⏭️  Skip: {problem_id} (could not find commit date)")
            return False
        
        # 파일 내용 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Front matter의 date 수정
        new_content = re.sub(
            r'^date:\s*\d{4}-\d{2}-\d{2}',
            f'date: {commit_date}',
            content,
            flags=re.MULTILINE
        )
        
        # 파일명 변경
        new_filename = f"{commit_date}-baekjoon-{problem_id}.md"
        new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
        
        # 기존 파일과 이름이 같으면 내용만 수정
        if filepath == new_filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated content: {filename} (date: {commit_date})")
        else:
            # 새 파일명으로 저장
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 기존 파일 삭제
            if os.path.exists(filepath):
                os.remove(filepath)
            
            print(f"✅ Updated: {filename} → {new_filename} (date: {commit_date})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {filepath}: {e}")
        return False

def main():
    if not os.path.exists(POSTS_DIR):
        print(f"❌ {POSTS_DIR} not found!")
        print(f"[INFO] Make sure you're in gazxxni.github.io repository")
        return
    
    print("🔧 Automatically updating post dates from Git history...\n")
    
    files = [f for f in os.listdir(POSTS_DIR) if f.endswith('.md') and 'baekjoon' in f]
    
    if not files:
        print("[INFO] No baekjoon posts found")
        return
    
    print(f"[INFO] Found {len(files)} posts to process\n")
    
    updated = 0
    failed = 0
    
    for filename in files:
        filepath = os.path.join(POSTS_DIR, filename)
        if update_post_date(filepath):
            updated += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"✨ Updated: {updated} posts")
    if failed > 0:
        print(f"⚠️  Failed: {failed} posts")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
