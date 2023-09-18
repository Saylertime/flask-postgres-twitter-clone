from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple, Union

import psycopg2

current_connection_function = None


def main_connection():
    """
    Подключение к основной базе данных
    """
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        # host="localhost",
        host="postgres",
        port="5432",
    )


def test_connection():
    """
    Подключение к тестовой базе данных (для тестов)
    """
    return psycopg2.connect(
        dbname="test_postgres",
        user="postgres",
        password="postgres",
        # host="localhost",
        host="postgres",
        port="5432",
    )


current_connection_function = main_connection


def set_database(conn_func):
    """Декоратор меняет переменную,
    которая отвечает за подключение к БД
    (тестовой или основной)"""
    global current_connection_function
    current_connection_function = conn_func


def get_users_params(api_key: str):
    """Функция для получения имени и ID юзера по его уникальному api_key"""
    conn = current_connection_function()
    with conn.cursor() as cursor:
        try:
            user = {}
            cursor.execute(
                """
            SELECT id, name
            FROM users
            WHERE api_key = %s
            """,
                (api_key,),
            )

            result = cursor.fetchone()
            if result:
                user["id"], user["name"], user["api_key"] = (
                    result[0],
                    result[1],
                    api_key,
                )
                return user
            else:
                print(f"Нет юзера с таким api-key: {api_key}")
                return None
        except Exception as e:
            print(f"Ошибка: {e}")
            return None


def post_tweets(api_key: str, tweet_data: str, tweet_media_ids: str) -> str:
    """
    Функция для публикации поста
    """
    conn = current_connection_function()
    with conn.cursor() as cursor:
        if tweet_media_ids:
            media_ids_string = ",".join(map(str, tweet_media_ids))
            cursor.execute(
                """
                INSERT INTO tweets
                (tweet_data, tweet_media_ids, api_key)
                VALUES (%s, %s, %s)
                RETURNING tweet_id
                """,
                (tweet_data, media_ids_string, api_key),
            )
            tweet_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                """
                INSERT INTO tweets
                (tweet_data, api_key)
                VALUES (%s, %s)
                RETURNING tweet_id
                """,
                (tweet_data, api_key),
            )
            tweet_id = cursor.fetchone()[0]
        conn.commit()
    return tweet_id


def get_tweets_data(
    user_id: int,
) -> Tuple[List[Dict[str, Union[str, List[str]]]], List[int]]:
    """
    Получение основной информации о твитах для указанного пользователя
    """
    with current_connection_function().cursor() as cursor:
        query = """
            WITH LikesCount AS (
                SELECT tweet_id, COUNT(*) as num_likes
                FROM likes
                GROUP BY tweet_id
            )
            SELECT t.tweet_id, t.tweet_data, t.tweet_media_ids, t.api_key
            FROM tweets t
            JOIN users u ON t.api_key = u.api_key
            LEFT JOIN followers f ON u.id = f.followed_id
            LEFT JOIN LikesCount lc ON t.tweet_id = lc.tweet_id
            WHERE f.follower_id = %s OR u.id = %s
            ORDER BY COALESCE(lc.num_likes, 0) DESC;
        """
        cursor.execute(query, (user_id, user_id))
        all_tweets = [
            {
                "id": str(row[0]),
                "content": row[1],
                "attachments": row[2],
                "api_key": row[3],
            }
            for row in cursor.fetchall()
        ]
        tweet_ids = [int(tweet["id"]) for tweet in all_tweets]
    return all_tweets, tweet_ids


def get_media_data(tweet_ids: List[int]) -> DefaultDict[int, List[str]]:
    """
    Получение информации о file_path для каждой загруженной картинки у твита
    """
    with current_connection_function().cursor() as cursor:
        cursor.execute(
            """
            SELECT t.tweet_id, m.file_path
            FROM media m
            JOIN tweets t ON m.id = t.tweet_media_ids
            WHERE t.tweet_id = ANY(%s)
        """,
            (tweet_ids,),
        )
        media_map = defaultdict(list)
        for tweet_id, file_path in cursor.fetchall():
            media_map[tweet_id].append(file_path)
    return media_map


def get_likes_data(tweet_ids: List[int]) -> DefaultDict[int, List[Dict[str, str]]]:
    """
    Получение основной информации о лайках на твитах
    """
    with current_connection_function().cursor() as cursor:
        cursor.execute(
            """
            SELECT l.tweet_id, l.user_id, u.name
            FROM likes l
            JOIN users u ON l.user_id = u.id
            WHERE l.tweet_id = ANY(%s)
        """,
            (tweet_ids,),
        )
        likes_map = defaultdict(list)
        for tweet_id, user_id, name in cursor.fetchall():
            likes_map[tweet_id].append({"user_id": str(user_id), "name": name})
    return likes_map


def get_authors_data(tweet_ids: List[int]) -> Dict[int, Dict[str, Union[str, int]]]:
    """
    Получение основной информации об авторе твита
    """
    with current_connection_function().cursor() as cursor:
        cursor.execute(
            """
            SELECT t.tweet_id, u.name, u.id
            FROM users u
            JOIN tweets t ON u.api_key = t.api_key
            WHERE t.tweet_id = ANY(%s)
        """,
            (tweet_ids,),
        )
        author_map = {
            tweet_id: {"name": name, "id": user_id}
            for tweet_id, name, user_id in cursor.fetchall()
        }
    return author_map


def get_tweets(api_key: str) -> Union[List[dict], bool]:
    """
    Функция для вывода всех твитов пользователя и его подписок на экран.
    Выводит сначала самые залайканные посты
    """
    user = get_users_params(api_key)
    try:
        all_tweets, tweet_ids = get_tweets_data(user["id"])
        media_map = get_media_data(tweet_ids)
        author_map = get_authors_data(tweet_ids)
        likes_map = get_likes_data(tweet_ids)

        for tweet in all_tweets:
            tweet["attachments"] = media_map.get(int(tweet["id"]), [])
            tweet["author"] = author_map.get(int(tweet["id"]))
            tweet["likes"] = likes_map.get(int(tweet["id"]), [])

        return all_tweets

    except Exception as e:
        print(e)
        return False


def media(file_path: str, api_key: str) -> str:
    """
    Добавляет ID загруженных картинок в базу данных
    """
    conn = current_connection_function()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO media (file_path, api_key) VALUES (%s, %s) RETURNING id",
            (file_path, api_key),
        )
        conn.commit()
        media_id = cursor.fetchone()[0]
        return media_id


def deleting(tweet_id: str) -> Union[Dict[str, bool], bool]:
    """
    Удаляет твит по его ID
    """
    conn = current_connection_function()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM tweets WHERE tweet_id = %s", (tweet_id,))
        if cursor.rowcount == 0:
            return False
        else:
            conn.commit()
            return {"result": True}


def check_likes(api_key: str, id: int) -> Dict[str, bool]:
    """
    Добавляет или удаляет лайк с поста
    """
    user = get_users_params(api_key)
    tweet_id = id
    conn = current_connection_function()
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO likes" "(user_id, tweet_id)" "VALUES(%s, %s)",
                (user["id"], tweet_id),
            )
            conn.commit()
            return {"result": True}
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.execute(
                "DELETE FROM likes " "WHERE user_id = %s AND tweet_id = %s",
                (user["id"], tweet_id),
            )
            conn.commit()
            return {"result": True}


def check_followers(
    id: int, api_key: str, request_method: str
) -> Union[Dict[str, bool], bool]:
    """
    Оформляет или отменяет подписку на пользователя
    """
    try:
        conn = current_connection_function()
        user = get_users_params(api_key)
        with conn.cursor() as cursor:
            if request_method == "POST":
                cursor.execute(
                    "INSERT INTO followers "
                    "(follower_id, followed_id) "
                    "VALUES(%s, %s)",
                    (user["id"], id),
                )
                conn.commit()
                return {"result": True}

            elif request_method == "DELETE":
                cursor.execute(
                    "DELETE FROM followers "
                    "WHERE follower_id = %s AND followed_id = %s",
                    (user["id"], id),
                )
                conn.commit()
                return {"result": True}

    except Exception as e:
        conn = current_connection_function()
        conn.rollback()
        print(f"Error: {e}")
        return False


def my_profile(api_key: str) -> Dict:
    """
    Показывает всю информацию о профиле авторизованного пользователя
    """
    try:
        user = get_users_params(api_key)
        conn = current_connection_function()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT f.followed_id, u.name
                              FROM followers f
                              JOIN users u ON u.id = f.followed_id
                              WHERE f.follower_id = %s AND f.followed_id != %s""",
                (user["id"], user["id"]),
            )

            following = [
                {"id": str(row[0]), "name": str(row[1])} for row in cursor.fetchall()
            ]
            user["following"] = following

            cursor.execute(
                """SELECT f.follower_id, u.name
                              FROM followers f
                              JOIN users u ON u.id = f.follower_id
                              WHERE f.followed_id = %s""",
                (user["id"],),
            )

            followers = [
                {"id": str(row[0]), "name": str(row[1])} for row in cursor.fetchall()
            ]
            user["followers"] = followers

        return user

    except Exception as e:
        conn = current_connection_function()
        conn.rollback()
        print(f"Error: {e}")


def any_profile(user_id: int) -> Dict:
    """
    Показывает всю информацию о профиле пользователя по ID
    """
    user = {}
    conn = current_connection_function()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM users " "WHERE id = %s", (user_id,))
            profile = cursor.fetchone()
            user["id"] = profile[0]
            user["name"] = profile[1]

            cursor.execute(
                """SELECT f.followed_id, u.name
                              FROM followers f
                              JOIN users u ON u.id = f.followed_id
                              WHERE f.follower_id = %s AND f.followed_id != %s""",
                (user["id"], user["id"]),
            )

            following = [
                {"id": str(row[0]), "name": str(row[1])} for row in cursor.fetchall()
            ]
            user["following"] = following

            cursor.execute(
                """SELECT f.follower_id, u.name
                              FROM followers f
                              JOIN users u ON u.id = f.follower_id
                              WHERE f.followed_id = %s""",
                (user["id"],),
            )

            followers = [
                {"id": str(row[0]), "name": str(row[1])} for row in cursor.fetchall()
            ]
            user["followers"] = followers
        return user

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
