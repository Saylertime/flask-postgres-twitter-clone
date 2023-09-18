import json
import os

from werkzeug.datastructures import FileStorage


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200


#
def test_tweets_post(client, test_db, api_headers):
    data = {"tweet_data": "test tweet", "tweet_media_ids": [1]}
    response = client.post(
        "/api/tweets",
        headers=api_headers,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == 201
    response_data = response.get_json()
    assert "result" in response_data
    assert response_data["result"] == True
    assert "tweet_id" in response_data


def test_tweets_get(client, test_db, api_headers):
    response = client.get(
        "/api/tweets", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["result"] == True


def test_medias_upload(client, test_db, api_headers):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(BASE_DIR, "test_file.jpg")

    with open(test_file_path, "rb") as f:
        test_file = FileStorage(f)
        response = client.post(
            "/api/medias",
            headers=api_headers,
            content_type="multipart/form-data",
            data={"file": test_file},
        )

    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data["result"] == True
    assert "media_id" in response_data


def test_delete_tweet_200(client, test_db, api_headers):
    tweet_id = 1
    response = client.delete(
        f"/api/tweets/{tweet_id}", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["result"] == True


def test_delete_tweet_404(client, test_db, api_headers):
    tweet_id = 10
    response = client.delete(
        f"/api/tweets/{tweet_id}", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data["result"] == False


def test_post_like(client, test_db, api_headers):
    id = "1"
    response = client.post(
        f"/api/tweets/{id}/likes", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200
    response = client.delete(
        f"/api/tweets/{id}/likes", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200


def test_follow_200(client, test_db, api_headers):
    id = "2"
    response = client.post(
        f"/api/users/{id}/follow", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["result"] == True


def test_follow_404(client, test_db, api_headers):
    id = "33"
    response = client.post(
        f"/api/users/{id}/follow", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data["result"] == False


def test_me(client, test_db, api_headers):
    response = client.get(
        "/api/users/me", headers=api_headers, content_type="application/json"
    )
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["result"] == True
    assert "test" in response_data["user"]["name"]
    assert response_data["user"]["id"] == 1
    assert len(response_data["user"]["followers"]) == 0


def test_get_user_200(client, test_db):
    id = 2
    response = client.get(f"/api/users/{id}", content_type="application/json")
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["result"] == True
    assert "test2" in response_data["user"]["name"]
    assert response_data["user"]["id"] == 2


def test_get_user_404(client, test_db):
    id = 33
    response = client.get(f"/api/users/{id}", content_type="application/json")
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data["result"] == False
