import requests
import pandas as pd
import time

API_KEY = "825e2dda4d7a4fd014b85ba055e2d788"
BASE_URL = "https://api.themoviedb.org/3"

# 원하는 page에 있는 인기영화목록 수집 
def get_popular_movies(page):
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "ko-KR",
        "page": page
    }
    res = requests.get(url, params=params) # url을 호출해서 결과값을 res에 넣기
    res.raise_for_status() # 에러 발생 시 프로그램 중단
    return res.json() # json문자열을 python자료구조로 변환


# 원하는 영화의 기본정보 및 제작자정보 수집
def get_movie_detail(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "ko-KR",
        "append_to_response": "credits"
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


# 위 두 함수를 호출하여 csv파일 생성
def collect_movies(max_pages=3):
    movies = []
    genres = []
    directors = []
    movie_genres = []
    movie_directors = []

    for page in range(1, max_pages + 1):
        print(f"{page} 페이지 수집 중...")
        data = get_popular_movies(page)

        for movie in data["results"]:
            movie_id = movie["id"]

            movies.append({
                "movie_id": movie_id,
                "title": movie["title"],
                "release_date": movie["release_date"],
                "rating": movie["vote_average"],
                "vote_count": movie["vote_count"]
            })

            detail = get_movie_detail(movie_id)
        
            for genre in detail["genres"]:
                genre_id = genre["id"]
                genres.append({
                    "genre_id": genre_id,
                    "name": genre["name"]
                })
                movie_genres.append({
                    "movie_id": movie_id,
                    "genre_id": genre_id
                })

            for crew in detail["credits"]["crew"]:
                if crew["job"] == "Director":
                    director_id = crew["id"]
                    directors.append({
                        "director_id": director_id,
                        "name": crew["name"]
                    })
                    movie_directors.append({
                        "movie_id": movie_id,
                        "director_id": director_id
                    })
        
            time.sleep(0.3)

    # genres와 directors 테이블 중복제거
    genres_df = pd.DataFrame(genres).drop_duplicates(subset="genre_id")
    directors_df = pd.DataFrame(directors).drop_duplicates(subset="director_id")


    # 위에서 만든 리스트들을 csv파일로 변환 후 저장
    pd.DataFrame(movies).to_csv("data/movies_raw.csv", index=False)
    pd.DataFrame(genres_df).to_csv("data/genres.csv", index=False)
    pd.DataFrame(directors_df).to_csv("data/directors.csv", index=False)
    pd.DataFrame(movie_genres).to_csv("data/movie_genres.csv", index=False)
    pd.DataFrame(movie_directors).to_csv("data/movie_directors.csv", index=False)

    print("CSV파일 생성 완료")


# 다른 파일에서 import하지 못하도록 방지(원치 않는 API수집 방지)
if __name__ == "__main__":
    collect_movies(max_pages=3)