import requests
import pandas as pd
import time

# =========================================================
# 1. TMDB API 서비스 접속 및 기본 설정
# =========================================================
# TMDB 웹사이트에서 데이터를 가져오기 위한 개인 인증 키와 기본 인터넷 주소
API_KEY = "YOUR_TMDB_API_KEY"
BASE_URL = "https://api.themoviedb.org/3"

# =========================================================
# 2. TMDB API 요청 함수 (인기 영화 목록 & 상세 정보 수집)
# =========================================================
def get_popular_movies(page):
    """
    원하는 페이지(page) 번호를 전달받아 최신 인기 영화 목록 데이터 수집
    """
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "ko-KR",  # 한국어 버전으로 데이터 요청
        "page": page
    }
    # TMDB 서버 URL을 호출하여 결과값을 res에 저장
    res = requests.get(url, params=params)
    
    # 만약 인터넷 연결 에러나 잘못된 요청일 경우 즉시 프로그램 중단(안전장치)
    res.raise_for_status()
    
    # 서버에서 받은 JSON 문자열 데이터를 파이썬이 다룰 수 있는 자료구조(딕셔너리/리스트)로 변환
    return res.json()


def get_movie_detail(movie_id):
    """
    특정 영화의 고유 ID를 전달받아 상세 정보(장르, 감독 등 제작진 정보) 수집
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "ko-KR",
        "append_to_response": "credits"  # 영화 기본 정보에 감독/배우 정보(credits)를 한 번에 합쳐서 요청
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

# =========================================================
# 3. 데이터 수집 및 정제, CSV 파일 생성 메인 함수
# =========================================================
def collect_movies(max_pages=3):
    """
    위에서 만든 API 함수들을 호출하여 데이터를 수집하고,
    5개의 개별 CSV 파일로 분리하여 내 컴퓨터(EC2)에 저장
    """
    # 5개의 데이터베이스 테이블 구조에 맞춰 담아둘 빈 리스트 생성
    movies = []
    genres = []
    directors = []
    movie_genres = []
    movie_directors = []

    # 1페이지부터 max_pages(기본 3페이지)까지 반복문 수행
    for page in range(1, max_pages + 1):
        print(f"{page} 페이지 수집 중...")
        data = get_popular_movies(page)

        # 수집된 인기 영화 목록에서 한 편씩 꺼내어 작업
        for movie in data["results"]:
            movie_id = movie["id"]

            # 1) 영화 기본 정보 저장 (영화 ID, 제목, 개봉일, 평점, 투표수)
            movies.append({
                "movie_id": movie_id,
                "title": movie["title"],
                "release_date": movie.get("release_date"),  # 개봉일이 비어있을 경우 대비
                "rating": movie["vote_average"],
                "vote_count": movie["vote_count"]
            })

            # 2) 영화 상세 정보(장르 및 감독) 가져오기
            detail = get_movie_detail(movie_id)
        
            # 장르 데이터 수집 및 영화-장르 연결 관계(N:M) 데이터 추출
            for genre in detail.get("genres", []):
                genre_id = genre["id"]
                genres.append({
                    "genre_id": genre_id,
                    "name": genre["name"]
                })
                movie_genres.append({
                    "movie_id": movie_id,
                    "genre_id": genre_id
                })

            # 제작진(crew) 데이터 중 "Director(감독)" 정보만 추출 및 영화-감독 연결 관계 데이터 저장
            if "credits" in detail and "crew" in detail["credits"]:
                for crew in detail["credits"]["crew"]:
                    if crew.get("job") == "Director":
                        director_id = crew["id"]
                        directors.append({
                            "director_id": director_id,
                            "name": crew["name"]
                        })
                        movie_directors.append({
                            "movie_id": movie_id,
                            "director_id": director_id
                        })
        
            # [서버 과부하 방지]: TMDB 서버에 너무 빠르게 연속으로 요청하면 차단될 수 있어 0.3초 휴식
            time.sleep(0.3)

    # 3) 중복 데이터 제거
    # 장르와 감독 정보는 여러 영화에서 중복으로 수집될 수 있으므로 고유 ID 기준으로 중복 삭제
    genres_df = pd.DataFrame(genres).drop_duplicates(subset="genre_id")
    directors_df = pd.DataFrame(directors).drop_duplicates(subset="director_id")

    # 4) 가공된 데이터 리스트들을 판다스 데이터프레임으로 변환 후 CSV 파일로 저장
    pd.DataFrame(movies).to_csv("data/movies_raw.csv", index=False, encoding="utf-8-sig")
    genres_df.to_csv("data/genres.csv", index=False, encoding="utf-8-sig")
    directors_df.to_csv("data/directors.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(movie_genres).to_csv("data/movie_genres.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(movie_directors).to_csv("data/movie_directors.csv", index=False, encoding="utf-8-sig")

    print("🎉 CSV 파일 생성 완료!")

# =========================================================
# 4. 스크립트 직접 실행 제어
# =========================================================
# 다른 파일에서 이 모듈을 import할 때 원치 않게 API 수집이 자동 실행되는 것을 방지
if __name__ == "__main__":
    collect_movies(max_pages=3)
