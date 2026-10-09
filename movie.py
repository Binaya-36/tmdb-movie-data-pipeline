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

print("Duplicate rows:")
print(df.duplicated().sum())

