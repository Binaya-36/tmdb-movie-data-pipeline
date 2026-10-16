-- TABLE CREATION

CREATE TABLE genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name TEXT NOT NULL UNIQUE
);

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
);

CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);

-- REPORTING QUERIES

-- 1. Number of movies and average rating per genre (JOIN + GROUP BY)
SELECT g.genre_name,
               COUNT(*) AS total_movies,
               ROUND(AVG(m.rating), 2) AS average_rating
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        GROUP BY g.genre_name
        ORDER BY total_movies DESC;

-- 2. Top 10 highest-rated movies with at least 100 votes (WHERE + ORDER BY)
SELECT title, rating, votes
        FROM movies
        WHERE votes >= 100
        ORDER BY rating DESC
        LIMIT 10;

-- 3. Top 10 most profitable movies (known budget and revenue only)
SELECT title, budget, revenue, profit
        FROM movies
        WHERE budget IS NOT NULL AND revenue IS NOT NULL
        ORDER BY profit DESC
        LIMIT 10;

-- 4. Genres with at least 5 movies that have revenue (HAVING)
SELECT g.genre_name,
               COUNT(m.revenue) AS movies_with_revenue,
               ROUND(AVG(m.revenue), 0) AS average_revenue
        FROM movies m
        JOIN movie_genres mg ON m.movie_id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.genre_id
        GROUP BY g.genre_name
        HAVING COUNT(m.revenue) >= 5
        ORDER BY average_revenue DESC;

-- 5. Movies grouped by length (CASE)
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
        ORDER BY total_movies DESC;

-- 6. Movies with revenue above the average (subquery)
SELECT title, revenue
        FROM movies
        WHERE revenue > (SELECT AVG(revenue) FROM movies)
        ORDER BY revenue DESC
        LIMIT 10;

-- 7. Movies and average popularity by release month
SELECT release_month,
               COUNT(*) AS total_movies,
               ROUND(AVG(popularity), 2) AS average_popularity
        FROM movies
        GROUP BY release_month
        ORDER BY release_month;

-- 8. Original languages with at least 3 movies (HAVING)
SELECT original_language,
               COUNT(*) AS total_movies,
               ROUND(AVG(rating), 2) AS average_rating,
               ROUND(AVG(popularity), 2) AS average_popularity
        FROM movies
        GROUP BY original_language
        HAVING COUNT(*) >= 3
        ORDER BY total_movies DESC;

