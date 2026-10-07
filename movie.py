import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

# Step 1: get the list of popular movies
popular = []
for page in range(1, 16):
    url = "https://api.themoviedb.org/3/movie/popular"
    response = requests.get(url, params={"api_key": api_key, "page": page})
    popular.extend(response.json()["results"])

print("Popular movies:", len(popular))

# Step 2: get full details for each movie
details = []
for movie in popular:
    url = f"https://api.themoviedb.org/3/movie/{movie['id']}"
    response = requests.get(url, params={"api_key": api_key})
    details.append(response.json())

print("Details collected:", len(details))

# Step 3: save the raw data
os.makedirs("data", exist_ok=True)
with open("data/details_raw.json", "w") as f:
    json.dump(details, f)