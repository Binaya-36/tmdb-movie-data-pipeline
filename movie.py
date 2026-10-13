import os
import json
import requests
import pandas as pd
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
