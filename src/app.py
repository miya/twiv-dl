import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from io import BytesIO

import requests
from twython import Twython, TwythonError, TwythonAuthError, TwythonRateLimitError
from flask import Flask, request, session, jsonify, render_template, send_file, send_from_directory

import config

twitter_keys = config.twitter_keys
twitter = Twython(
    twitter_keys["CONSUMER_KEY"],
    twitter_keys["CONSUMER_SECRET"],
    twitter_keys["ACCESS_KEY"],
    twitter_keys["ACCESS_SECRET"]
)

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY


def get_tweet_id(url):
    """フロントで入力されたURLから正規表現を用いてツイートIDを抽出する"""
    tweet_id = re.findall("https://twitter\.com/.+?/status/(\d+)", url)
    if len(tweet_id) > 0:
        return tweet_id[0]


def get_rate_limit():
    """残りのAPI利用可能回数を取得する"""
    rate_limit_data = twitter.get_application_rate_limit_status()["resources"]["statuses"]["/statuses/lookup"]
    jst = timezone(timedelta(hours=+9), "JST")
    reset_time = str(datetime.fromtimestamp(rate_limit_data["reset"], jst))
    limit = rate_limit_data["remaining"]
    return {"remaining": limit, "reset_time": reset_time}


def get_video_data(tweet_id):
    """TwitterAPIを利用して動画のURLを取得する"""
    try:
        tweet_data = twitter.lookup_status(id=tweet_id, include_entities=True)
        rate_limit = get_rate_limit()
    except TwythonAuthError as e:
        print(e)
        return {"status": False, "message": "アプリケーションの認証に何らかの問題があります。"}
    except TwythonRateLimitError as e:
        print(e)
        return {"status": False, "message": "APIの呼び出し回数制限を超えました。時間をおいてからやり直してください。"}
    except TwythonError as e:
        print(e)
        return {"status": False, "message": "エラーが発生しました"}

    # ツイートが存在しているかどうか
    if len(tweet_data) > 0:

        # 動画、画像を含むメディア付きツイートかどうか
        if "extended_entities" in tweet_data[0]:
            media = tweet_data[0]["extended_entities"]["media"][0]

            # 動画付きツイートかどうか
            if media["type"] == "video":

                # ビットレートとURLを取り出して辞書に追加
                video = {}
                for i in media["video_info"]["variants"]:
                    if i["content_type"] == "video/mp4":
                        video.update({i["bitrate"]: i["url"]})

                display_video_url, download_video_sizes = sorted_video(video)

                return {
                    "status": True,
                    "message": "動画のURLを取得しました。",
                    "display_video_url": display_video_url,
                    "download_video_sizes": download_video_sizes,
                    "rate_limit": rate_limit
                }

            else:
                return {"status": False, "message": "動画付きツイートではありません。", "rate_limit": rate_limit}

        else:
            return {"status": False, "message": "動画付きツイートではありません。", "rate_limit": rate_limit}

    else:
        return {"status": False, "message": "ツイートが見つかりませんでした。", "rate_limit": rate_limit}


def sorted_video(video):
    """
    ビットレートの高さでソートしてsmall, medium, largeに振り分け動画のURLをセッションに格納
    フロントで表示させる動画URLとダウンロードできる動画サイズを返す
    """
    size_label = ["small", "medium", "large"]
    sorted_bitrate = sorted(video)
    sizes = []

    for i in range(len(video)):
        video_url = video[sorted_bitrate[i]]
        session[size_label[i]] = video_url
        sizes.append(re.findall("vid/(.+)/", video_url)[0])

    return video[sorted_bitrate[-1]], sizes


def create_file_name():
    """UUIDを用いてランダムな文字列でファイル名を生成"""
    return str(uuid.uuid4())[:8] + ".mp4"


@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
@app.route("/apple-touch-icon-120x120.png")
@app.route("/apple-touch-icon-120x120-precomposed.png")
def logo():
    return send_from_directory(os.path.join(app.root_path, "static/images"), "logo.png")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/images"), "favicon.ico")


@app.route("/robots.txt")
def robots():
    return send_from_directory(os.path.join(app.root_path, "static"), "robots.txt")


@app.route("/keybase.txt")
def keybase():
    return send_from_directory(os.path.join(app.root_path, "static"), "keybase.txt")


@app.route("/")
def top():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template("404.html"), 404


@app.route("/search", methods=["POST"])
def search():
    if request.headers["Content-Type"] == "application/json":
        input_url = request.json["inputUrl"]
        tweet_id = get_tweet_id(input_url)
        if tweet_id:
            session.clear()
            video_data = get_video_data(tweet_id)
            print(video_data)
        else:
            video_data = {"status": False, "message": "Twitterの動画付きURLを入力してください。"}
        return jsonify(video_data)


@app.route("/download/<string:dl_type>")
def download(dl_type):
    file_name = create_file_name()
    req = requests.get(session[dl_type])
    if req.status_code == 200:
        video_obj = BytesIO(req.content)
        return send_file(video_obj, attachment_filename=file_name, as_attachment=True)


if __name__ == "__main__":
    app.run()

    # debug
    # app.run(host="0.0.0.0", port=8080, threaded=True, debug=True)
