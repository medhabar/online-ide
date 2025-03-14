from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import redis
import os
import uuid
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


def get_redis_connection():
    try:
        redis_client = redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=True,
        )
        redis_client.ping()
        return redis_client
    except redis.ConnectionError as e:
        app.logger.error(f"Redis connection error: {e}")
        return None


TEMP_FILE_URL = os.getenv("TEMP_FILE_URL")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/temp-file-upload", methods=["POST"])
def upload_file():
    redis_client = get_redis_connection()
    if not redis_client:
        return jsonify({"error": "Failed to connect to Redis"}), 503

    try:
        data = request.get_json()

        if (
            not data
            or not data.get("code")
            or not data.get("language")
            or not data.get("title")
            or not data.get("expiryTime")
        ):
            return (
                jsonify(
                    {"error": "Code, language, title, and expiry time are required"}
                ),
                400,
            )

        valid_expiry_times = (10, 30, 60, 1440, 10080)
        expiry_time_minutes = int(data["expiryTime"])

        if expiry_time_minutes not in valid_expiry_times:
            return (
                jsonify({"error": "Invalid expiry time. Please choose a valid value."}),
                400,
            )

        code = data["code"]
        language = data["language"]
        title = data["title"]

        current_time = datetime.utcnow()
        expiry_time = current_time + timedelta(minutes=expiry_time_minutes)
        formatted_expiry_time = expiry_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        file_id = str(uuid.uuid4())

        file_data = {
            "title": title,
            "code": code,
            "language": language,
            "expiry_time": formatted_expiry_time,
        }

        redis_client.set(
            f"file:{language}-{file_id}:data",
            json.dumps(file_data),
            ex=expiry_time_minutes * 60,
        )

        file_url = f"{TEMP_FILE_URL}/file/{language}-{file_id}"

        return jsonify(
            {
                "message": "Code uploaded successfully",
                "fileUrl": file_url,
                "expiry_time": formatted_expiry_time,
            }
        )

    except redis.RedisError as e:
        app.logger.error(f"Redis error during file upload: {e}")
        return jsonify({"error": "Failed to store code in Redis"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error during file upload: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        redis_client.close()


@app.route("/file/<file_id>", methods=["GET"])
def get_file(file_id):
    redis_client = get_redis_connection()
    if not redis_client:
        return jsonify({"error": "Failed to connect to Redis"}), 503

    try:
        language, file_id = file_id.split("-", 1)

        file_key = f"file:{language}-{file_id}:data"
        file_data = redis_client.get(file_key)

        ttl = redis_client.ttl(file_key)

        if ttl == -2:
            return jsonify({"error": "File not found"}), 404
        elif ttl == -1 or ttl == 0:
            return jsonify({"error": "File has expired"}), 410

        if file_data:
            file_data = json.loads(file_data)
            return jsonify(file_data), 200

        return jsonify({"error": "File not found"}), 404

    except redis.RedisError as e:
        app.logger.error(f"Redis error during file retrieval: {e}")
        return jsonify({"error": "Failed to retrieve code from Redis"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error during file retrieval: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        redis_client.close()


@app.route("/file/<file_id>/delete", methods=["DELETE"])
def delete_file(file_id):
    redis_client = get_redis_connection()
    if not redis_client:
        return jsonify({"error": "Failed to connect to Redis"}), 503

    try:
        language, file_id = file_id.split("-", 1)

        file_key = f"file:{language}-{file_id}:data"
        file_data = redis_client.get(file_key)

        if file_data:
            redis_client.delete(file_key)
            return jsonify({"message": "File deleted successfully"}), 200
        else:
            return jsonify({"error": "File not found"}), 404

    except redis.RedisError as e:
        app.logger.error(f"Redis error during file deletion: {e}")
        return jsonify({"error": "Failed to delete file from Redis"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error during file deletion: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        redis_client.close()


if __name__ == "__main__":
    app.run(debug=False)
