import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432",
)

with conn.cursor() as cursor:
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users
    (id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE)
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tweets
    (tweet_id SERIAL PRIMARY KEY,
    tweet_data TEXT NOT NULL,
    tweet_media_ids INTEGER,
    api_key TEXT NOT NULL)
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS likes (
    user_id INTEGER NOT NULL,
    tweet_id INTEGER NOT NULL,
    PRIMARY KEY(user_id, tweet_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id) ON DELETE CASCADE);
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS followers
    (follower_id INTEGER NOT NULL,
    followed_id INTEGER NOT NULL,
    PRIMARY KEY(follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (followed_id) REFERENCES users(id)ON DELETE CASCADE)
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS media
    (id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    api_key TEXT NOT NULL,
    FOREIGN KEY (api_key) REFERENCES users(api_key) ON DELETE CASCADE)
    """
    )

    # ДОБАВИТЬ ПОЛЬЗОВАТЕЛЕЙ И ФОЛЛОВЕРОВ В БД
    # cursor.execute("""
    # INSERT INTO followers
    # (follower_id, followed_id)
    # VALUES(%s, %s)
    # """, ('1', '2'))
    # conn.commit()

    # cursor.execute("""
    # INSERT INTO users
    # (name, api_key)
    # VALUES(%s, %s)
    # """, ('anna', 'anna'))
    # conn.commit()

    cursor.execute("SELECT * FROM tweets")
    print("ТВИТЫ: ", cursor.fetchall())

    cursor.execute("SELECT * FROM users")
    print("ЮЗЕРЫ: ", cursor.fetchall())

    cursor.execute("SELECT * FROM likes")
    print("ЛАЙКИ: ", cursor.fetchall())

    cursor.execute("SELECT * FROM likes WHERE user_id = 1")
    print("ЛАЙКИ 1 ЮЗЕРА: ", cursor.fetchall())

    cursor.execute("SELECT * FROM followers")
    print("ФОЛЛОВЕРЫ: ", cursor.fetchall())
