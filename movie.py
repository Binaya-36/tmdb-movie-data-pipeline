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
print("Duplicate rows:", df.duplicated().sum())
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
