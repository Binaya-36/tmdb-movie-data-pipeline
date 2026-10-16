import os
import json
import requests
import pandas as pd
import sqlite3
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

# runs only if raw file doesn't exist
if not os.path.exists("data/details_raw.json"):

    # Step 1: get the list of popular movies
    popular = []
    for page in range(1, 16):
        url = "https://api.themoviedb.org/3/movie/popular"
        response = requests.get(url, params={"api_key": api_key, "page": page})
        popular.extend(response.json()["results"])

    print("Popular movies:", len(popular))

    #get full details for each movie
    details = []
    for i, movie in enumerate(popular, 1):
        url = f"https://api.themoviedb.org/3/movie/{movie['id']}"
        response = requests.get(url, params={"api_key": api_key})
        details.append(response.json())
        print("Fetched", i, "of", len(popular))

    #save the raw data
    os.makedirs("data", exist_ok=True)
    with open("data/details_raw.json", "w") as f:
        json.dump(details, f)

#LOAD RAW DATA
with open("data/details_raw.json") as f:
    details = json.load(f)

df = pd.DataFrame(details)

#EDA
print('The number of rows and columns',df.shape)
print("---------------------------------------------------------------------------------------------------")

print('\n Column names:')
print(df.columns)
print("---------------------------------------------------------------------------------------------------")

print("The available datatypes:")
print(df.dtypes)
print("---------------------------------------------------------------------------------------------------")

print('First 5 rows')
print(df.head())
print("---------------------------------------------------------------------------------------------------")

print("Summary Statistics")
print(df.describe())
print("---------------------------------------------------------------------------------------------------")

print(df.astype(str).nunique())

print("\nStatus:")
print(df["status"].value_counts())

print("\nOriginal language (top 10):")
print(df["original_language"].value_counts().head(10))

print("\nUnique movie titles:", df["title"].nunique())
print("Unique release dates:", df["release_date"].nunique())

print('\n Missing null values:\n',df.isnull().sum())

print("\n Duplicate Records")
print("Duplicate movie IDs:", df["id"].duplicated().sum())

print("\n Data Types")
print(df.dtypes)

print("\nRelease date data type:")
print(df["release_date"].dtype)

print("\n Invalid or Inconsistent Values")
print("Ratings below 0:", (df["vote_average"] < 0).sum())
print("Ratings above 10:", (df["vote_average"] > 10).sum())
print("Negative popularity:", (df["popularity"] < 0).sum())
print("Negative vote counts:", (df["vote_count"] < 0).sum())


print("\n Outlier Check")
print(df[["popularity", "vote_average", "vote_count"]].describe())

Q1 = df["popularity"].quantile(0.25)
Q3 = df["popularity"].quantile(0.75)
IQR = Q3 - Q1

lower_limit = Q1 - 1.5 * IQR
upper_limit = Q3 + 1.5 * IQR

outliers = df[
    (df["popularity"] < lower_limit) |
    (df["popularity"] > upper_limit)
]

print("Potential popularity outliers:", len(outliers))


print("\n Unexpected Categories")

print("\nMovie statuses:")
print(df["status"].value_counts(dropna=False))

print("\nOriginal languages (top 10):")
print(df["original_language"].value_counts(dropna=False).head(10))

print("\nAdult flag:")
print(df["adult"].value_counts(dropna=False))


print("\n Formatting Checks")

print(
    "Titles with leading/trailing spaces:",
    df["title"].ne(df["title"].str.strip()).sum()
)

release_dates = pd.to_datetime(
    df["release_date"],
    errors="coerce"
)

print("Invalid or missing release dates:", release_dates.isnull().sum())

print("\nDATA QUALITY CHECKS COMPLETED")

#PHASE 3: CLEANING

# 1. Keep only the columns we need
columns_needed = ["id", "title", "original_language", "release_date", "status",
                  "runtime", "budget", "revenue", "popularity",
                  "vote_average", "vote_count", "overview", "tagline"]
movies = df[columns_needed].copy()

# 2. Remove duplicate movies
movies = movies.drop_duplicates(subset="id")

# 3. Invalid values: 0 means "unknown" in TMDB, so make them missing
movies["budget"] = movies["budget"].replace(0, float("nan"))
movies["revenue"] = movies["revenue"].replace(0, float("nan"))
movies["runtime"] = movies["runtime"].replace(0, float("nan"))

# A rating with 0 votes is not a real rating
movies.loc[movies["vote_count"] == 0, "vote_average"] = float("nan")

# 4. Empty text becomes missing
movies["overview"] = movies["overview"].replace("", float("nan"))
movies["tagline"] = movies["tagline"].replace("", float("nan"))

# 5. Standardize text
movies["title"] = movies["title"].str.strip()
movies["original_language"] = movies["original_language"].str.upper()

# 6. Correct data types
movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")

# 7. Drop rows with missing or invalid release date
before = len(movies)
movies = movies.dropna(subset=["release_date"])
print("Rows removed (bad dates):", before - len(movies))

# 8. Rename columns
movies = movies.rename(columns={"id": "movie_id",
                                "vote_average": "rating",
                                "vote_count": "votes"})

# ---------- PHASE 3: TRANSFORMATION ----------

# 1. Extract year and month
movies["release_year"] = movies["release_date"].dt.year
movies["release_month"] = movies["release_date"].dt.month

# 2. Calculated columns
movies["profit"] = movies["revenue"] - movies["budget"]
movies["roi_percent"] = movies["profit"] / movies["budget"] * 100

# 3. Rating category
def rating_group(r):
    if pd.isna(r):
        return "Unrated"
    elif r >= 7:
        return "High"
    elif r >= 5:
        return "Medium"
    else:
        return "Low"

movies["rating_group"] = movies["rating"].apply(rating_group)

# 4. Genre tables (only for movies that survived cleaning)
valid_ids = movies["movie_id"].tolist()

genre_list = []
movie_genre_list = []

for index, row in df.iterrows():
    if row["id"] in valid_ids:
        for g in row["genres"]:
            genre_list.append({"genre_id": g["id"], "genre_name": g["name"]})
            movie_genre_list.append({"movie_id": row["id"], "genre_id": g["id"]})

genres = pd.DataFrame(genre_list).drop_duplicates()
movie_genres = pd.DataFrame(movie_genre_list).drop_duplicates()

# 5. Check the results
print("\nmovies:", movies.shape)
print(movies.isnull().sum())
print("\ngenres:", genres.shape)
print("movie_genres:", movie_genres.shape)
print(movies.head())

# ---------- PHASE 4: DATA ANALYSIS AND INSIGHTS ----------

# Q1. Top 10 movies by popularity
print("\nQ1. Top 10 Movies by Popularity")
q1 = movies.sort_values("popularity", ascending=False)
q1 = q1[["title", "popularity", "rating", "votes"]]
print(q1.head(10))


# Q2. Top 10 highest-rated movies (at least 100 votes)
print("\nQ2. Top 10 Highest-Rated Movies (Minimum 100 Votes)")
q2 = movies[movies["votes"] >= 100]
q2 = q2.sort_values("rating", ascending=False)
q2 = q2[["title", "rating", "votes"]]
print(q2.head(10))


# Q3. Number of movies and average rating by release year
print("\nQ3. Movies and Average Rating by Release Year")
q3 = movies.groupby("release_year").agg(
    total_movies=("movie_id", "count"),
    rated_movies=("rating", "count"),
    average_rating=("rating", "mean")
).round(2)
q3 = q3.sort_values("total_movies", ascending=False)
print(q3.head(15))


# Q4. Top 10 most profitable movies (known budget and revenue only)
print("\nQ4. Top 10 Most Profitable Movies")
q4 = movies.dropna(subset=["budget", "revenue", "profit"])
q4 = q4.sort_values("profit", ascending=False)
q4 = q4[["title", "budget", "revenue", "profit"]]
print(q4.head(10))


# Q5. Popularity and rating by rating category
print("\nQ5. Popularity by Rating Category")
q5 = movies.groupby("rating_group").agg(
    number_of_movies=("movie_id", "count"),
    average_popularity=("popularity", "mean"),
    average_rating=("rating", "mean")
).round(2)
print(q5)


# Q6. Genre analysis (uses the genre tables from Phase 3)
print("\nQ6. Genre Analysis")
genre_info = movie_genres.merge(genres, on="genre_id")
genre_info = genre_info.merge(movies, on="movie_id")

q6 = genre_info.groupby("genre_name").agg(
    total_movies=("movie_id", "count"),
    average_rating=("rating", "mean"),
    average_revenue=("revenue", "mean")
).round(2)
q6 = q6.sort_values("total_movies", ascending=False)
print(q6)


# Q7. Movies by original language
print("\nQ7. Movies by Original Language")
q7 = movies.groupby("original_language").agg(
    total_movies=("movie_id", "count"),
    average_rating=("rating", "mean")
).round(2)
q7 = q7.sort_values("total_movies", ascending=False)
print(q7.head(10))


# Q8. Average ROI by genre (known budget only)
print("\nQ8. Average ROI by Genre")
roi_info = genre_info.dropna(subset=["roi_percent"])
q8 = roi_info.groupby("genre_name").agg(
    movies_with_budget=("movie_id", "count"),
    average_roi=("roi_percent", "mean")
).round(2)
q8 = q8.sort_values("average_roi", ascending=False)
print(q8)


# ---------- END OF PHASE 4 ----------


# ---------- PHASE 5: DATABASE DESIGN ----------

conn = sqlite3.connect("data/tmdb_movies.db")
cursor = conn.cursor()

# Make SQLite enforce foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Start fresh so the script can be re-run (child table first)
cursor.execute("DROP TABLE IF EXISTS movie_genres")
cursor.execute("DROP TABLE IF EXISTS genres")
cursor.execute("DROP TABLE IF EXISTS movies")

# 1. movies table
cursor.execute("""
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    original_language TEXT,
    release_date TEXT NOT NULL,
    release_year INTEGER,
    release_month INTEGER CHECK (release_month BETWEEN 1 AND 12),
    status TEXT,
    runtime INTEGER CHECK (runtime > 0),
    budget REAL CHECK (budget > 0),
    revenue REAL CHECK (revenue > 0),
    popularity REAL CHECK (popularity >= 0),
    rating REAL CHECK (rating BETWEEN 0 AND 10),
    votes INTEGER CHECK (votes >= 0),
    overview TEXT,
    tagline TEXT,
    profit REAL,
    roi_percent REAL,
    rating_group TEXT
)
""")

# 2. genres table
cursor.execute("""
CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name TEXT NOT NULL UNIQUE
)
""")

# 3. movie_genres junction table
cursor.execute("""
CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
)
""")

conn.commit()

# Check the tables
cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
print("Tables in database:")
for table in cursor.fetchall():
    print(table[0])

conn.close()

# ---------- END OF PHASE 5 ----------


import sqlite3
import os

# ---------- PHASE 6: LOAD DATA INTO DATABASE ----------

db_path = "data/tmdb_movies.db"

# Make sure the data folder exists
os.makedirs("data", exist_ok=True)

# Connect to the database
conn = sqlite3.connect(db_path)

# Enable foreign-key checking
conn.execute("PRAGMA foreign_keys = ON")

try:
    with conn:
        # Clear old records so the pipeline can be rerun
        # Delete child records before parent records
        conn.execute("DELETE FROM movie_genres")
        conn.execute("DELETE FROM movies")
        conn.execute("DELETE FROM genres")

        # Prepare the movie data
        movies_to_load = movies.copy()

        # Store release dates in a consistent format
        movies_to_load["release_date"] = (
            movies_to_load["release_date"].dt.strftime("%Y-%m-%d")
        )

        # Load the three DataFrames into existing tables
        movies_to_load.to_sql(
            "movies", conn, if_exists="append", index=False
        )

        genres.to_sql(
            "genres", conn, if_exists="append", index=False
        )

        movie_genres.to_sql(
            "movie_genres", conn, if_exists="append", index=False
        )

    print("Data loaded successfully!")

    # Verify the number of records in each table
    for table in ["movies", "genres", "movie_genres"]:
        count = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {table}", conn
        )["total"][0]

        print(f"{table}: {count} records")

finally:
    conn.close()

# ---------- END OF PHASE 6 ----------

# ---------- PHASE 7: SQL ANALYSIS AND REPORTING ----------

conn = sqlite3.connect("data/tmdb_movies.db")

queries = {

    "1. Number of movies and average rating per genre (JOIN + GROUP BY)": """
        SELECT g.genre_name,
               COUNT(*) AS total_movies,
               ROUND(AVG(m.rating), 2) AS average_rating
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        GROUP BY g.genre_name
        ORDER BY total_movies DESC
    """,

    "2. Top 10 highest-rated movies with at least 100 votes (WHERE + ORDER BY)": """
        SELECT title, rating, votes
        FROM movies
        WHERE votes >= 100
        ORDER BY rating DESC
        LIMIT 10
    """,

    "3. Top 10 most profitable movies (known budget and revenue only)": """
        SELECT title, budget, revenue, profit
        FROM movies
        WHERE budget IS NOT NULL AND revenue IS NOT NULL
        ORDER BY profit DESC
        LIMIT 10
    """,

    "4. Genres with at least 5 movies that have revenue (HAVING)": """
        SELECT g.genre_name,
               COUNT(m.revenue) AS movies_with_revenue,
               ROUND(AVG(m.revenue), 0) AS average_revenue
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        GROUP BY g.genre_name
        HAVING COUNT(m.revenue) >= 5
        ORDER BY average_revenue DESC
    """,

    "5. Movies grouped by length (CASE)": """
        SELECT
            CASE
                WHEN runtime < 90 THEN 'Short (under 90 min)'
                WHEN runtime <= 120 THEN 'Medium (90-120 min)'
                ELSE 'Long (over 120 min)'
            END AS length_group,
            COUNT(*) AS total_movies,
            ROUND(AVG(rating), 2) AS average_rating
        FROM movies
        WHERE runtime IS NOT NULL
        GROUP BY length_group
        ORDER BY total_movies DESC
    """,

    "6. Movies with revenue above the average (subquery)": """
        SELECT title, revenue
        FROM movies
        WHERE revenue > (SELECT AVG(revenue) FROM movies)
        ORDER BY revenue DESC
        LIMIT 10
    """,

    "7. Movies and average popularity by release month": """
        SELECT release_month,
               COUNT(*) AS total_movies,
               ROUND(AVG(popularity), 2) AS average_popularity
        FROM movies
        GROUP BY release_month
        ORDER BY release_month
    """,

    "8. Original languages with at least 3 movies (HAVING)": """
        SELECT original_language,
               COUNT(*) AS total_movies,
               ROUND(AVG(rating), 2) AS average_rating,
               ROUND(AVG(popularity), 2) AS average_popularity
        FROM movies
        GROUP BY original_language
        HAVING COUNT(*) >= 3
        ORDER BY total_movies DESC
    """,
}

# Run the queries, print the results, and save them
os.makedirs("data/sql_results", exist_ok=True)
sql_file = open("data/tmdb_database.sql", "w", encoding="utf-8")

# Part 1 of the .sql file: the table creation statements
sql_file.write("-- TABLE CREATION\n\n")
for table_name in ["genres", "movies", "movie_genres"]:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = ?", (table_name,)
    ).fetchone()
    sql_file.write(row[0] + ";\n\n")

# Part 2 of the .sql file: the reporting queries
sql_file.write("-- REPORTING QUERIES\n\n")

for number, (title, sql) in enumerate(queries.items(), 1):
    result = pd.read_sql_query(sql, conn)
    print("\n" + title)
    print(result)
    result.to_csv(f"data/sql_results/query_{number}.csv", index=False)
    sql_file.write(f"-- {title}\n{sql.strip()};\n\n")

sql_file.close()
conn.close()

print("\nPIPELINE COMPLETED")

# ---------- END OF PHASE 7 ----------
