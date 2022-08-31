# YoutubeAPIの利用
from apiclient.discovery import build

def create_youtube_model():
    # APIキーをファイルから取得
    # jupyter起動時の相対パスを利用
    f = open('../secret/apikey', 'r')
    api_key = f.read()
    f.close()

    # APIキーを用いてリクエスト用のクラスを作成
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key)
    return youtube