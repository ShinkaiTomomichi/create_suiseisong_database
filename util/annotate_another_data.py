# Pythonの基本ライブラリ
from itertools import count
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# YoutubeAPIの利用
from apiclient.errors import HttpError

# 投稿時間の取得に利用
import datetime

# pasteboardを使う
import pyperclip

# jupyterで呼び出した場合はutlが必要だが、相対パスで表現できるようにしておきたい
import util.create_youtube_model as create_youtube_model

# 日付けでadd_dfをフィルタリング
def filter_add_df(df, base_date):
    youtube = create_youtube_model.create_youtube_model()
    base_date_ts = datetime.datetime.strptime(base_date, '%Y-%m-%d').timestamp()

    filter_ids = np.zeros(df.shape[0], dtype=bool)
    memory = {}

    for i, row in df.iterrows():
        video_id = row['videoid']
        if video_id in memory.keys():
            date_ts = memory[video_id]
        else:
            try:
                video_detail = youtube.videos().list(
                    part = 'snippet', 
                    id = video_id, 
                ).execute()
            except HttpError:
                print('データ参照中にエラーが発生しました')
            video_snippet = video_detail['items'][0]['snippet']
            date = video_snippet['publishedAt']
            date_ts = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').timestamp()
            memory[video_id] = date_ts
        filter_ids[i] = base_date_ts < date_ts

    df_tmp = df
    df_tmp['filter'] = filter_ids
    df_tmp = df_tmp[df_tmp['filter'] == True]
    df_tmp = df_tmp.drop(columns=['filter'])
    return df_tmp

# Youtubeのリンクを作成
def make_url(video_id, time):
    return "https://www.youtube.com/watch?v="+video_id+"&t="+str(time)+"s"

# ~h~m表記を数値に変換する
def fix_format_duration(time):
    if 'm' in time and 'h' in time:
        hour, tmp = time.split('h')
        minite, second = tmp.split('m')
        duration = int(hour)*3600 + int(minite)*60 + int(second)
    elif 'h' in time:
        hour, second = time.split('h')
        duration = int(hour)*3600 + int(second)
    elif 'm' in time:
        minite, second = time.split('m')
        duration = int(minite)*60 + int(second)
    else:
        duration = int(time)
    return duration

# 過去の確認済みデータを元にアーティスト名と終了時間の候補を返す
def check_base_df(base_df, song_name, start_time):
    checks = np.array(base_df['check'])
    song_names = np.array(base_df['songname'])
    artist_names = np.array(base_df['artistname'])
    start_times = np.array(base_df['starttime'])
    end_times = np.array(base_df['endtime'])
    for i in range(base_df.shape[0]):
        base_song_name = song_names[i]
        if checks[i] and song_name == base_song_name:
            duration = end_times[i] - start_times[i]
            return artist_names[i], start_time + duration
    return '存在しませんでした', 0

# 途中から再開する場合どうするか？
# add_dfをcheckごと作成 & ここでbase_dfに上書き保存するやり方で実現したい
def annotate_another_data_streams(add_path, base_path):
    add_df = pd.read_csv(add_path, header=0)
    base_df = pd.read_csv(base_path, header=0)
    checks = np.array(add_df['check'])
    identifier_base = np.max(np.array(base_df['id']))
    count = 1

    for i, row in add_df.iterrows():
        # 確認済みのデータはスキップ
        if row['check']:
            continue
                
        video_id = row['videoid']
        song_name = row['songname']
        start_time = row['starttime']
        url = make_url(video_id, start_time)
        # 確認しやすいようにペーストボードに貼る
        pyperclip.copy(url)
        print(song_name + '\n' + url)

        # 過去の情報からアーティストとendtimeを推論
        artist_name, end_time = check_base_df(base_df, song_name, start_time)
        
        # artist_nameを確認
        print('アーティスト名候補: ' + artist_name)
        input1 = input()
        if input1 == '':
            print(artist_name + ' をそのまま採用します')    
        else:
            artist_name = input1

        # 開始時刻を確認
        print('開始時刻候補: ' + str(start_time) + ' (該当リンクをペーストボードにコピーしました)')
        pyperclip.copy(url)
        input2 = input()
        if input2 == '':
            print('候補値をそのまま採用します') 
        else:
            start_time = fix_format_duration(input2)
        
        # 終了時刻を確認
        print('終了時刻候補: ' + str(end_time) + ' (該当リンクをペーストボードにコピーしました)')
        url = make_url(video_id, end_time)
        pyperclip.copy(url)
        input3 = input()
        if input3 == '':
            print('候補値をそのまま採用します') 
        else:
            end_time = fix_format_duration(input3)

        # 念の為、変な値の場合に警告
        if end_time-start_time < 0 or end_time-start_time > 600:
            print('不正な値になっている可能性があります')
                
        # 後に追加する情報には暫定値を入れておく
        identifier = identifier_base + count
        count += 1
        members = row['members']
        date = 0
        collaboration = False
        acappella = False
        live3d = False
        suisei = True
        stream = True
        listtype = 'None'
        check = True

        data = [[identifier, song_name, artist_name, start_time, end_time,
                 members, video_id, date, collaboration, acappella,
                 live3d, suisei, stream, listtype, check]]

        # dfに変換後concatenate
        add_df_tmp = pd.DataFrame(data=np.array(data), 
                                  columns=['id', 'songname', 'artistname', 'starttime', 'endtime', 
                                           'members', 'videoid', 'date', 'collaboration', 'acappella', 
                                           'live3d', 'suisei', 'stream', 'listtype', 'check'])

        base_df = pd.concat([base_df, add_df_tmp])
        base_df.to_csv(base_path, index=False)

        # checkを更新
        checks[i] = True
        add_df['check'] = checks
        add_df.to_csv(add_path, index=False)

        # print('アノテーションを終了する場合、何か文字を入力してください')
        # input4 = input()
        # if input4 != '' or i == add_df.shape[0]-1:
        #     print('アノテーションを終了します')
        #     break

# ISO表記の動画時間を秒に変換
def pt_to_sec(pt_time):
    s_list, m_list, h_list = [], [], []
    conc_s, conc_m, conc_h = '', '', ''
    flag = ''
    
    for i in reversed(pt_time):
        if i == 'S':
            flag = 'S'
        elif i == 'M':
            flag = 'M'
        elif i == 'H':
            flag = 'H'
        elif i == 'T':
            break
        else:
            if flag == 'S':
                s_list.append(i)
            elif flag == 'M':
                m_list.append(i)
            elif flag == 'H':
                h_list.append(i)
    
    for s in reversed(s_list):
        conc_s += s
    for m in reversed(m_list):
        conc_m += m
    for h in reversed(h_list):
        conc_h += h
    conc_s = 0 if conc_s == '' else int(conc_s)
    conc_m = 0 if conc_m == '' else int(conc_m)
    conc_h = 0 if conc_h == '' else int(conc_h)

    times = conc_h*3600 + conc_m*60 + conc_s
    return times

def annotate_another_data_songs(add_path, base_path):
    add_df = pd.read_csv(add_path, header=0)
    base_df = pd.read_csv(base_path, header=0)
    checks = np.array(add_df['check'])
    identifier_base = np.max(np.array(base_df['id']))
    count = 1
    youtube = create_youtube_model.create_youtube_model()

    for i, row in add_df.iterrows():
        # 確認済みのデータはスキップ
        if row['check']:
            continue
                
        video_id = row['videoid']
        song_name = row['songname']
        start_time = row['starttime']
        url = make_url(video_id, start_time)
        # 確認しやすいようにペーストボードに貼る
        pyperclip.copy(url)
        print(song_name + '\n' + url)

        # 過去の情報からアーティストとendtimeを推論
        artist_name, end_time = check_base_df(base_df, song_name, start_time)
        
        # artist_nameを確認
        print('アーティスト名候補: ' + artist_name)
        input1 = input()
        if input1 == '':
            print(artist_name + ' をそのまま採用します')    
        else:
            artist_name = input1

        # 開始時刻の確認は不要

        # 終了時刻の確認は自動化
        try:
            video_detail = youtube.videos().list(
                part = 'contentDetails', 
                id = video_id, 
            ).execute()
        except HttpError:
            print('データ参照中にエラーが発生しました')
        video_content_details = video_detail['items'][0]['contentDetails']
        duration = pt_to_sec(video_content_details['duration'])
        end_time = duration
                
        # 後に追加する情報には暫定値を入れておく
        identifier = identifier_base + count
        count += 1
        members = row['members']
        date = 0
        collaboration = False
        acappella = False
        live3d = False
        suisei = True
        stream = False
        listtype = 'None'
        check = True

        data = [[identifier, song_name, artist_name, start_time, end_time,
                 members, video_id, date, collaboration, acappella,
                 live3d, suisei, stream, listtype, check]]

        # dfに変換後concatenate
        add_df_tmp = pd.DataFrame(data=np.array(data), 
                                  columns=['id', 'songname', 'artistname', 'starttime', 'endtime', 
                                           'members', 'videoid', 'date', 'collaboration', 'acappella', 
                                           'live3d', 'suisei', 'stream', 'listtype', 'check'])

        base_df = pd.concat([base_df, add_df_tmp])
        base_df.to_csv(base_path, index=False)

        # checkを更新
        checks[i] = True
        add_df['check'] = checks
        add_df.to_csv(add_path, index=False)

        # print('アノテーションを終了する場合、何か文字を入力してください')
        # input4 = input()
        # if input4 != '' or i == add_df.shape[0]-1:
        #     print('アノテーションを終了します')
        #     break

# リンクから動画IDを取得する
# タイムスタンプが入っていると失敗するため注意
def get_videoid(url):
    # 短縮形とそれ以外で取得方法を分ける
    if "youtube" in url:
        stratid = url.find("v=")+2
        endid = url.find("&t=")
        videoid = url[stratid:]
    if "youtu.be" in url:
        stratid = url.find(".be")+4
        endid = url.find("?t=")
        videoid = url[stratid:]
    return videoid

def get_binary_3(num):
    if len(num) != 3:
        print('3文字の01で入力してください')
        return
    returns = []
    for i in range(3):
        if num[i] == '0':
            returns.append(False)
        else:
            returns.append(True)
    return returns[0], returns[1], returns[2]

def annotate_another_data_manual(base_path, list_name, suisei=False):
    base_df = pd.read_csv(base_path, header=0)
    identifier_base = np.max(np.array(base_df['id'])) + 1

    # 終了するまで終わらない
    for i in range(10000):
        print('動画のURLを入力')
        input1 = input()
        video_id = get_videoid(input1)

        print('曲名を入力')
        input2 = input()
        song_name = input2

        print('開始時刻を入力')
        input3 = input()
        start_time = fix_format_duration(input3)

        # 過去の情報からアーティストとendtimeを推論
        artist_name, end_time = check_base_df(base_df, song_name, start_time)

        print('終了時刻候補: ' + str(end_time) + ' (該当リンクをペーストボードにコピーしました)')
        url = make_url(video_id, end_time)
        pyperclip.copy(url)
        input4 = input()
        if input4 == '':
            print('候補値をそのまま採用します') 
        else:
            end_time = fix_format_duration(input4)

        # 念の為、変な値の場合に警告
        if end_time-start_time < 0 or end_time-start_time > 600:
            print('不正な値になっている可能性があります')

        print('アーティスト名候補: ' + artist_name)
        input5 = input()
        if input5 == '':
            print(artist_name + ' をそのまま採用します')    
        else:
            artist_name = input5
        
        print('メンバーを,区切りで入力')
        input6 = input()
        members = input6

        print('stream,live3d,acappellaを01で入力')
        input7 = input()
        stream, live3d, acappella = get_binary_3(input7)

        # 後に追加する情報には暫定値を入れておく
        identifier = identifier_base + i
        date = 0
        collaboration = False
        listtype = list_name
        check = True

        data = [[identifier, song_name, artist_name, start_time, end_time,
                 members, video_id, date, collaboration, acappella,
                 live3d, suisei, stream, listtype, check]]

        # dfに変換後concatenate
        add_df_tmp = pd.DataFrame(data=np.array(data), 
                                  columns=['id', 'songname', 'artistname', 'starttime', 'endtime', 
                                           'members', 'videoid', 'date', 'collaboration', 'acappella', 
                                           'live3d', 'suisei', 'stream', 'listtype', 'check'])
        base_df = pd.concat([base_df, add_df_tmp])
        base_df.to_csv(base_path, index=False)

        # print('アノテーションを終了する場合、何か文字を入力してください')
        # input_end = input()
        # if input_end != '':
        #     print('アノテーションを終了します')
        #     break
