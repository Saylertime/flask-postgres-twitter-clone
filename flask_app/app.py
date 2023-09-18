import os

from database import (
    any_profile,
    check_followers,
    check_likes,
    deleting,
    get_tweets,
    media,
    my_profile,
    post_tweets,
)
from flasgger import Swagger
from flask import Flask, jsonify, render_template, request

UPLOAD_FOLDER = "static/uploads"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

Swagger(app)


@app.route("/", methods=["GET"])
def index():
    """
    Главная страница приложения
    ---
    tags:
      - Web Interface
    responses:
      200:
        description: Главная HTML-страница приложения.
    """
    return render_template("index.html")


@app.route("/api/tweets", methods=["POST"])
def tweets_post():
    """
    Отправить твит
    ---
    tags:
      - Tweets
    parameters:
      - in: header
        name: api-key
        default: test
        example: test
        type: string
        required: true
        description: API ключ текущего пользователя.
      - in: "body"
        name: body
        required: true
        schema:
          type: object
          properties:
            tweet_data:
              type: string
              description: Содержимое нового твита
            tweet_media_ids:
              type: array
              items:
                type: integer
                description: Идентификаторы медиафайлов для твита (опционально)
    responses:
      201:
        description: Твит успешно создан
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        result:
                            type: boolean
                            description: Статус выполнения запроса
                        tweet_id:
                            type: integer
                            description: Идентификатор созданного твита
    """
    api_key = request.headers.get("api-key")
    data = request.json
    tweet_data = data.get("tweet_data")
    tweet_media_ids = data.get("tweet_media_ids", [])

    tweet_id = post_tweets(api_key, tweet_data, tweet_media_ids)
    return jsonify({"result": True, "tweet_id": tweet_id}), 201


@app.route("/api/tweets", methods=["GET"])
def tweets_get():
    """
    Посмотреть все твиты
    ---
    tags:
      - Tweets
    parameters:
      - in: header
        name: api-key
        default: test
        example: test
        type: string
        required: true
        description: API ключ текущего пользователя.
    responses:
      200:
        description: Все твиты для пользователя
      500:
        description: result = False
        schema:
          type: object
          properties:
            result:
              type: boolean
    """
    api_key = request.headers.get("api-key")
    all_tweets = get_tweets(api_key)
    if all_tweets:
        result = {"result": True, "tweets": all_tweets}
        return result, 200
    else:
        return jsonify({"error": "Пользователь с таким api-key не найден"}), 404


@app.route("/api/medias", methods=["POST"])
def medias():
    """
    Загрузить медиафайл
    ---
    tags:
      - Media
    parameters:
      - in: header
        name: api-key
        default: test
        type: string
        required: true
        description: API ключ текущего пользователя
      - in: formData
        name: file
        type: file
        required: true
        description: Медиафайл для загрузки
    responses:
      201:
        description: Медиафайл успешно загружен
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        result:
                            type: boolean
                            description: Статус выполнения запроса
                        media_id:
                            type: integer
                            description: Идентификатор загруженного медиа-файла
    """
    api_key = request.headers.get("api-key")
    file = request.files["file"]

    if file:
        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        media_id = media(file_path, api_key)
        return jsonify({"result": True, "media_id": media_id}), 201


@app.route("/api/tweets/<int:tweet_id>", methods=["DELETE"])
def delete_tweet(tweet_id):
    """
    Удаление твита по ID

    ---
    tags:
      - Tweets
    parameters:
      - in: path
        name: tweet_id
        type: string
        required: true
        description: ID твита
    responses:
      200:
        description: result = true
        schema:
          type: object
          properties:
            result:
              type: boolean
      404:
        description: result = False
        schema:
          type: object
          properties:
            result:
              type: boolean
    """
    try:
        result = deleting(tweet_id)
        if result:
            return jsonify(result), 200
        return jsonify({"result": False}), 404

    except Exception as e:
        print(f"Error: {e}")


@app.route("/api/tweets/<id>/likes", methods=["POST", "DELETE"])
def likes(id):
    """
    Поставить лайк
    ---
    tags:
      - Likes
    parameters:
      - in: header
        name: api-key
        default: test
        type: string
        required: true
        description: API ключ текущего пользователя.
      - in: path
        name: id
        default: 1
        type: string
        required: true
        description: ID твита
    responses:
      200:
        description: result = true
        schema:
          type: object
          properties:
            result:
              type: boolean
    """
    api_key = request.headers.get("api-key")
    result = check_likes(api_key, id)
    return result, 200


@app.route("/api/users/<id>/follow", methods=["POST", "DELETE"])
def follow(id):
    """
    Подписаться на пользователя или отписаться от него
    ---
    tags:
      - Follows
    parameters:
      - in: header
        name: api-key
        default: test
        required: true
        description: api-key пользователя
      - in: path
        name: id
        default: 1
        required: true
        description: ID пользователя, на которого нужно подписаться или отписаться
    responses:
      200:
        schema:
          type: object
          properties:
            result:
              type: boolean
      404:
        schema:
          type: object
          properties:
            result:
              type: boolean
    """
    api_key = request.headers.get("api-key")
    request_method = request.method
    result = check_followers(id, api_key, request_method)
    if result:
        return jsonify(result), 200
    return jsonify({"result": False}), 404


@app.route("/api/users/me", methods=["GET"])
def me():
    """
    Получить информацию о текущем пользователе
    ---
    tags:
      - Users
    parameters:
      - in: header
        name: api-key
        type: string
        default: test
        required: true
        description: API ключ текущего пользователя.
    responses:
      200:
        description: Информация о текущем пользователе
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        result:
                            type: boolean
                            description: Статус выполнения запроса
                        user:
                            type: object
                            description: Данные пользователя
                            properties:
                                id:
                                    type: integer
                                    description: Идентификатор пользователя
                                name:
                                    type: string
                                    description: Имя пользователя
    """
    api_key = request.headers.get("api-key")
    user = my_profile(api_key)
    result = {"result": True, "user": user}
    return jsonify(result), 200


@app.route("/api/users/<id>", methods=["GET"])
def get_user(id):
    """
    Получить информацию о пользователе по ID
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: id
        type: string
        default: 1
        required: true
        description: ID пользователя
    responses:
      200:
        description: Информация о пользователе
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        result:
                            type: boolean
                            description: Статус выполнения запроса
                        user:
                            type: object
                            description: Данные пользователя
                            properties:
                                id:
                                    type: integer
                                    description: Идентификатор пользователя
                                name:
                                    type: string
                                    description: Имя пользователя
      404:
        description: Нет такого пользователя

    """
    user = any_profile(id)
    if user:
        result = {"result": True, "user": user}
        return jsonify(result), 200
    return jsonify({"result": False, "message": "User not found"}), 404


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", debug=True, port=8080)
