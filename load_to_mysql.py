import pandas as pd
import mysql.connector
from mysql.connector import Error

# =========================================================
# 1. AWS RDS 클라우드 데이터베이스 접속 설정
# =========================================================
# 데이터베이스에 문을 열고 들어가기 위한 정보들
DB_CONFIG = {
    "host": "YOUR_RDS_ENDPOINT",      # AWS RDS의 엔드포인트(서버 인터넷 주소)
    "user": "admin",                  # 데이터베이스 최고 관리자 계정 이름
    "password": "YOUR_RDS_PASSWORD",  # 데이터베이스 비밀번호
    "database": "tmdb",               # 데이터를 저장할 데이터베이스(방) 이름
    "port": 3306                      # MySQL 데이터베이스 전용 문(포트 번호)
}

def get_connection():
    """데이터베이스와 연결 통로를 만들어주는 함수"""
    return mysql.connector.connect(**DB_CONFIG)

# =========================================================
# 2. 데이터를 DB에 밀어 넣는 핵심 함수
# =========================================================
def insert_dataframe(df, table_name, columns):
    """
    파이썬이 다듬은 데이터(Dataframe)를 데이터베이스의 지정된 테이블(표)에 집어넣는 과정
    """
    # [데이터 정제] 비어있는 값(NaN)이 있으면 데이터베이스가 이해할 수 있는 '빈 값(None/NULL)'으로 대체
    df = df.where(pd.notnull(df), None)

    # DB 연결 통로 및 명령을 전달할 '일꾼(cursor)' 생성
    conn = get_connection()
    cursor = conn.cursor()

    # SQL 문장 틀 만들기 (%s는 나중에 실제 데이터가 들어갈 빈 자리를 의미)
    placeholders = ", ".join(["%s"] * len(columns))
    col_str = ", ".join(columns)

    # INSERT IGNORE: 혹시 이미 똑같은 영화 데이터가 들어있다면 에러를 내지 않고 넘어가라는 명령어
    sql = f"""
        INSERT IGNORE INTO {table_name} ({col_str})
        VALUES ({placeholders})
    """

    # [트러블슈팅 해결 포인트]
    # 판다스(Pandas)의 특수한 숫자 형태(numpy.int64 등)를 데이터베이스가 인식하지 못하는 문제가 있어,
    # 순수한 파이썬 기본 데이터 타입(튜플 리스트)으로 변환
    records = df[columns].to_dict('records')
    data = [tuple(record[col] for col in columns) for record in records]

    # 준비된 데이터를 데이터베이스에 한꺼번에 다량으로 전송
    cursor.executemany(sql, data)
    
    # 변경사항을 데이터베이스에 최종 저장
    conn.commit()

    # 사용이 끝난 DB 연결 통로 닫아주기 (안 닫아주면 DB가 과부하 걸릴 수 있음)
    cursor.close()
    conn.close()

# =========================================================
# 3. 전체 CSV 파일들을 하나씩 불러와 DB로 보내는 메인 함수
# =========================================================
def load_all():
    """
    collect_movies.py가 수집해서 만들어둔 CSV 파일들을 읽어와
    각각 알맞은 데이터베이스 테이블에 저장
    """
    # 1) EC2 내 data 폴더에 저장된 CSV 파일 읽어오기
    movies = pd.read_csv("data/movies_raw.csv")
    genres = pd.read_csv("data/genres.csv")
    directors = pd.read_csv("data/directors.csv")
    movie_genres = pd.read_csv("data/movie_genres.csv")
    movie_directors = pd.read_csv("data/movie_directors.csv")

    # 2) 각 데이터들을 DB의 알맞은 테이블에 하나씩 밀어 넣기
    insert_dataframe(movies, "movies", ["movie_id", "title", "release_date", "rating", "vote_count"])
    insert_dataframe(genres, "genres", ["genre_id", "name"])
    insert_dataframe(directors, "directors", ["director_id", "name"])
    insert_dataframe(movie_genres, "movie_genres", ["movie_id", "genre_id"])
    insert_dataframe(movie_directors, "movie_directors", ["movie_id", "director_id"])

# 이 파이썬 파일이 직접 실행될 때 작동하는 시작점
if __name__ == "__main__":
    load_all()
    print("🎉 AWS RDS 클라우드 DB로 데이터 적재 성공!")
