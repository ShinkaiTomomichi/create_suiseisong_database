# Pythonの基本ライブラリ
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# YoutubeAPIの利用
from apiclient.errors import HttpError

# 投稿時間の取得に利用
import datetime

import util.create_youtube_model as create_youtube_model

def output_html_diff_video(base_path):
    base_df = pd.read_csv(base_path, header=0)
    video_ids = []
    for i, row in base_df.iterrows():
        date = row['date']
        video_id = row['videoid']
        if date == 0 and video_id not in video_ids:
            video_ids.append(video_id)
    return output_html(video_ids)

def output_html(video_ids):
    html = '<div style="float:left;">'
    for i, video_id in enumerate(video_ids):
        html += ('<img src="http://img.youtube.com/vi/'+video_id+'/sddefault.jpg "alt="取得できませんでした" width="100">')
        url = "https://www.youtube.com/watch?v="+video_id
        html += ('<a href="'+url+'">  '+video_id+'  </a>')
        if (i+1) % 5 == 0:
            html += '<br>'
    html += '</div>'
    return html

def annotate_another_data_auto(base_path):
    # 既存のデータを見て、date==0のデータに追加情報を付与する
    base_df = pd.read_csv(base_path, header=0)
    # アカペラ動画と3Dライブ動画のID一覧を取得
    acappella_ids = np.loadtxt('data/acappella_ids.csv', dtype='str', delimiter=',')
    live3d_ids = np.loadtxt('data/live3d_ids.csv', dtype='str', delimiter=',')

    # Youtube APIに必要なモデル
    youtube = create_youtube_model.create_youtube_model()

    # 以下の情報を上書きする
    collabs = np.array(base_df['collaboration'])
    dates = np.array(base_df['date'])
    acappellas = np.array(base_df['acappella'])
    live3ds = np.array(base_df['live3d'])

    for i, row in base_df.iterrows():
        # 確認済みのデータはスキップ
        date = row['date']
        if date != 0:
            continue

        # コラボ情報の追加
        members = row['members']
        collabs[i] = len(members.split(',')) > 1

        # 投稿時刻の追加
        video_id = row['videoid']
        # アカペラ、ライブ情報の追加
        acappellas[i] = video_id in acappella_ids
        live3ds[i] = video_id in live3d_ids
        
        clear = True
        try:
            video_detail = youtube.videos().list(
                part = 'snippet', 
                id = video_id, 
            ).execute()
        except HttpError:
            clear = False
            print('データ参照中にエラーが発生しました')

        if clear:
            video_snippet = video_detail['items'][0]['snippet']
            date = video_snippet['publishedAt']
            date_ts = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').timestamp()
            dates[i] = date_ts
        else:
            dates[i] = 0

    base_df['collaboration'] = collabs
    base_df['date'] = dates
    base_df['acappella'] = acappellas
    base_df['live3d'] = live3ds

    base_df.to_csv(base_path, index=False)
