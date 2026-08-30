import pandas as pd
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "YOUR_RDS_ENDPOINT",
    "user": "YOUR_USER_NAME",
    "password": "YOUR_RDS_PASSWORD",
    "database": "tmdb",
    "port": 3306
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def insert_dataframe(df, table_name, columns):
    df = df.where(pd.notnull(df), None)

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ", ".join(["%s"] * len(columns))
    col_str = ", ".join(columns)

    sql = f"""
        INSERT IGNORE INTO {table_name} ({col_str})
        VALUES ({placeholders})
    """

    records = df[columns].to_dict('records')
    data = [tuple(record[col] for col in columns) for record in records]

    cursor.executemany(sql, data)
    conn.commit()

    cursor.close()
    conn.close()

def load_all():
    movies = pd.read_csv("data/movies_raw.csv")
    genres = pd.read_csv("data/genres.csv")
    directors = pd.read_csv("data/directors.csv")
    movie_genres = pd.read_csv("data/movie_genres.csv")
    movie_directors = pd.read_csv("data/movie_directors.csv")

    insert_dataframe(movies, "movies", ["movie_id", "title", "release_date", "rating", "vote_count"])
    insert_dataframe(genres, "genres", ["genre_id", "name"])
    insert_dataframe(directors, "directors",["director_id", "name"])
    insert_dataframe(movie_genres, "movie_genres", ["movie_id", "genre_id"])
    insert_dataframe(movie_directors, "movie_directors", ["movie_id", "director_id"])

if __name__ == "__main__":
    load_all()
