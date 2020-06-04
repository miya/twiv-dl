import config
import os
import re
import uuid
import tweepy
import requests
from io import BytesIO
from flask import Flask, request, session, jsonify, render_template, send_file, send_from_directory

twitter_keys = config.twitter_keys
auth = tweepy.OAuthHandler(twitter_keys["CONSUMER_KEY"], twitter_keys["CONSUMER_SECRET"])
auth.set_access_token(twitter_keys["ACCESS_KEY"], twitter_keys["ACCESS_SECRET"])
api = tweepy.API(auth)

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY


def get_tweet_id(url) -> str:
    """
    フロント側で入力されたURLからtweet_idを取得する

    Arg:
        url: フロントから入力さ得れたURL
    """
    tweet_id = re.findall("https://twitter\.com/.+?/status/(\d+)", url)
    if len(tweet_id) != 0:
        return tweet_id[0]


def get_video_data(tweet_id) -> dict:
    """
    動画データ（ツイートの情報を取得したか、ステータスメッセージ、動画URL）を返す

    Arg:
        tweet_id: ツイートの識別番号
    """
    data = {}

    try:
        res = api.statuses_lookup(id_=[tweet_id], tweet_mode="extended")
    except tweepy.TweepError:
        status = False
        message = "APIの呼び出し回数を超えました。しばらくしてからご利用ください"
        return {"status": status, "message": message}

    try:
        # tweet_idに該当するツイートがあるか
        if len(res) != 0:
            response_json_dic = res[0]._json

            # 画像、動画を含むメディア付きツイートかどうか
            if "extended_entities" in response_json_dic:
                media = response_json_dic["extended_entities"]["media"][0]

                # 動画付きツイートかどうか
                if media["type"] == "video":
                    status = True
                    message = "動画のURLを取得しました。"

                    content = [i for i in media["video_info"]["variants"] if i["content_type"] == "video/mp4"]
                    for i in content:
                        data.update({i["bitrate"]: i["url"]})

                    data = sorted_data(data)

                else:
                    status = False
                    message = "動画付きツイートではありません。"

            else:
                status = False
                message = "メディア付きツイートではありません。"

        else:
            status = False
            message = "ツイートが見つかりません。"

    except Exception as e:
        print(e)
        status = False
        message = "原因不明のエラーが発生しました。"
        return {"status": status, "message": message}

    return {"status": status, "message": message, "data": data}


def sorted_data(data) -> dict:
    """
    ビットレートの高さでソートして
    small, medium, large に振り分ける

    Arg:
        data(dict):
    """
    res_data = {}
    size_label = ["small", "medium", "large"]
    keys = sorted(data)
    for i, j in zip(size_label, keys):
        size = re.findall("vid/(.+)/", data[j])[0]
        url = data[j]
        res_data.update({
            i: {
                "size": size,
                "url": url
            }
        })
    return res_data


def create_file_name() -> str:
    """
    UUIDを用いてランダムな文字列でファイル名を生成
    """
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
def post():
    if request.headers["Content-Type"] == "application/json":
        input_url = request.json["inputUrl"]
        tweet_id = get_tweet_id(input_url)
        if tweet_id:
            session.clear()
            video_data = get_video_data(tweet_id)
            data = video_data["data"]
            if "small" in data:
                session["small"] = data["small"]["url"]
            if "medium" in data:
                session["medium"] = data["medium"]["url"]
            if "large" in data:
                session["large"] = data["large"]["url"]
        else:
            video_data = {"status": False, "message": "Twitterの動画付きURLを入力してください。"}
        print(video_data)
        return jsonify(video_data)
    else:
        return jsonify({"status": False, "message": "何かがおかしいよ。"})


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
