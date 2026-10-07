import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TMDB_API_KEY")

url = "https://api.themoviedb.org/3/movie/popular"

all_movies = []

for page in range(1, 11):

    params = {
        "api_key": api_key,
        "page": page
    }

    response = requests.get(url, params=params)

    print("Page:", page, "Status:", response.status_code)

    data = response.json()

    all_movies.extend(data["results"])

df = pd.DataFrame(all_movies)

print("Total movies:", len(df))
print(df.head())