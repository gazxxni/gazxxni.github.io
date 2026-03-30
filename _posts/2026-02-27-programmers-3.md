---
layout: post
title: "[프로그래머스] Level 3 베스트앨범 (Python)"
date: 2026-02-27
categories: ["Algorithm", "Programmers"]
tags: ["python", "algorithm", "programmers", "level3", "3", "코딩테스트 연습 > 해시"]
---

## 문제 링크
[https://school.programmers.co.kr/learn/courses/30/lessons/3](https://school.programmers.co.kr/learn/courses/30/lessons/3)

## 문제
스트리밍 사이트에서 장르 별로 가장 많이 재생된 노래를 두 개씩 모아 베스트 앨범을 출시하려 합니다. 노래는 고유 번호로 구분하며, 노래를 수록하는 기준은 다음과 같습니다.


속한 노래가 많이 재생된 장르를 먼저 수록합니다.
장르 내에서 많이 재생된 노래를 먼저 수록합니다.
장르 내에서 재생 횟수가 같은 노래 중에서는 고유 번호가 낮은 노래를 먼저 수록합니다.


노래의 장르를 나타내는 문자열 배열 genres와 노래별 재생 횟수를 나타내는 정수 배열 plays가 주어질 때, 베스트 앨범에 들어갈 노래의 고유 번호를 순서대로 return 하도록 solution 함수를 완성하세요.

제한사항


genres[i]는 고유번호가 i인 노래의 장르입니다.
plays[i]는 고유번호가 i인 노래가 재생된 횟수입니다.
genres와 plays의 길이는 같으며, 이는 1 이상 10,000 이하입니다.
장르 종류는 100개 미만입니다.
장르에 속한 곡이 하나라면, 하나의 곡만 선택합니다.
모든 장르는 재생된 횟수가 다릅니다.


입출력 예

        
genres
plays
return


        
["classic", "pop", "classic", "classic", "pop"]
[500, 600, 150, 800, 2500]
[4, 1, 3, 0]


      
입출력 예 설명

classic 장르는 1,450회 재생되었으며, classic 노래는 다음과 같습니다.


고유 번호 3: 800회 재생
고유 번호 0: 500회 재생
고유 번호 2: 150회 재생


pop 장르는 3,100회 재생되었으며, pop 노래는 다음과 같습니다.


고유 번호 4: 2,500회 재생
고유 번호 1: 600회 재생


따라서 pop 장르의 [4, 1]번 노래를 먼저, classic 장르의 [3, 0]번 노래를 그다음에 수록합니다.


장르 별로 가장 많이 재생된 노래를 최대 두 개까지 모아 베스트 앨범을 출시하므로 2번 노래는 수록되지 않습니다.


※ 공지 - 2019년 2월 28일 테스트케이스가 추가되었습니다.


> 출처: 프로그래머스 코딩 테스트 연습, https://school.programmers.co.kr/learn/challenges

## 풀이
### 풀이 핵심 로직
주어진 노래의 장르와 재생 횟수를 기반으로 장르별로 총 재생 횟수를 계산한 후, 각 장르 내에서 재생 횟수가 높은 노래를 정렬하여 베스트 앨범을 구성합니다. 장르별로 최대 두 곡을 선택하여 최종 결과를 반환합니다.

### 동작 과정
1. **입력 예시**: 
   - `genres = ["classic", "pop", "classic", "classic", "pop"]`
   - `plays = [500, 600, 150, 800, 2500]`

2. **장르별 총 재생 횟수 계산**:
   - classic: 500 + 150 + 800 = 1450
   - pop: 600 + 2500 = 3100

3. **장르별 재생 횟수 정렬**:
   - pop (3100) > classic (1450)

4. **각 장르 내에서 재생 횟수로 정렬**:
   - classic: [(3, 800), (0, 500), (2, 150)] -> 고유 번호 기준으로 정렬 후 상위 2개: [3, 0]
   - pop: [(4, 2500), (1, 600)] -> 상위 2개: [4, 1]

5. **최종 결과**: 
   - 베스트 앨범: [4, 1, 3, 0]

### 시간 복잡도
O(n log n) - 노래 목록을 정렬하는 데 O(n log n)의 시간이 소요되고, 장르별로 노래를 선택하는 과정은 O(n)입니다. 전체적으로 정렬이 지배적인 요소입니다.

## 코드
```python
def solution(genres, plays):
    n = len(genres)
    arr = [(genres[i], plays[i], i) for i in range(n)]
    arr.sort(key=lambda x:(x[0], -x[1], x[2]))
    
    dic = {}
    for i in range(n):
        if genres[i] not in dic:
            dic[genres[i]] = plays[i]
        else:
            dic[genres[i]] += plays[i]
    
    dic = sorted(dic.items(), key=lambda x:-x[1])
    ans = []
    for i in dic:
        cnt = 0
        for j in arr:
            if i[0] == j[0]:
                cnt += 1
                
                if cnt > 2:
                    break
                else:
                    ans.append(j[2])
    
    return ans
```
