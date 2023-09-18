import pytest
from database import main_connection, set_database, test_connection


def create_tables(conn):
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
        FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id) ON DELETE CASCADE)
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS followers
        (follower_id INTEGER NOT NULL,
        followed_id INTEGER NOT NULL,
        PRIMARY KEY(follower_id, followed_id),
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE)
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
        conn.commit()

        users_data = [("test", "test"), ("test2", "test2")]
        cursor.executemany(
            """
            INSERT INTO users (name, api_key)
            VALUES (%s, %s)
        """,
            users_data,
        )
        conn.commit()

        cursor.execute(
            """
        INSERT INTO tweets
        (tweet_data, api_key)
        VALUES(%s, %s)
        """,
            ("test tweet", "test"),
        )
        conn.commit()


@pytest.fixture(scope="session")
def test_db():
    conn = main_connection()
    conn.autocommit = True
    with conn.cursor() as cursor:
        cursor.execute("DROP DATABASE IF EXISTS test_postgres")
        cursor.execute("CREATE DATABASE test_postgres")

    test_conn = test_connection()
    print("Connected to:", conn.dsn)
    create_tables(test_conn)
    yield test_conn
    test_conn.close()
    with conn.cursor() as cursor:
        cursor.execute("DROP DATABASE test_postgres")
    conn.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app(test_db):
    from flask_app.app import app as flask_app

    set_database(test_connection)  # Здесь мы передаём саму функцию
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def api_headers():
    return {"api-key": "test"}
