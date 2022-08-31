# Pythonの基本ライブラリ
import numpy as np
import pandas as pd

# 切り上げ用
import math

# スクレイピング用
import requests
from bs4 import BeautifulSoup

# soupクラスを作成する
def create_soup():
    # 星街すいせいの歌枠
    url = "https://seesaawiki.jp/hololivetv/d/%c0%b1%b3%b9%a4%b9%a4%a4%a4%bb%a4%a4%a1%da%b2%ce%be%a7%b3%da%b6%ca%b0%ec%cd%f7%a1%db"
    r = requests.get(url)
    # 文字化けが発生しているので予めデコードしてから利用
    soup = BeautifulSoup(r.content.decode("euc-jp", "ignore"), "html.parser")
    return soup

# リンクがある曲だけ取得する
def check_cell_streams(cells):
    # リンクそのものが存在しない場合はFalse
    if cells[2].a == None:
        return False
    
    href = cells[2].a["href"]
    # Youtubeへのリンクかを確認
    # 短縮URLもあるため"youtu"で判別
    if "youtu" not in href:
        return False

    # 備考欄に非公開とある場合はFalse
    text = cells[3].text
    if "非公開" in text:
        return False
    return True

# リンクから動画IDと開始時間を取得する
def get_videoid_time_streams(cells):
    href = cells[2].a["href"]
    # 短縮形とそれ以外で取得方法を分ける
    if "youtube" in href:
        stratid = href.find("v=")+2
        endid = href.find("&t=")
        videoid = href[stratid:endid]
        time = href[endid+3:-1]
    if "youtu.be" in  href:
        stratid = href.find(".be")+4
        endid = href.find("?t=")
        videoid = href[stratid:endid]
        time = href[endid+3:]
    return videoid, time
    
# メンバーと備考からアーティストを取得する
def get_members_streams(cells):
    members = []
    holo_members = list(cells[0].children)
    for i in range(len(holo_members)//2 + 1):
        members.append(holo_members[i*2])
    detail = cells[3].text
    # 備考欄に記載されたケースをこちらで追加する
    guests = ["戌亥とこ", "獅子神レオナ"]
    for guest in guests:
        if guest in detail:
            members.append(guest)
    return members

# 歌枠のデータベースを返す
def create_streams():
    soup = create_soup()
    # 楽曲を管理しているテーブルから情報を取得
    songs = soup.find_all("table", {"id":"content_block_19"})[0]
    rows = songs.find_all("tr")

    # video_idとt、アーティスト、曲名を取り出す
    # rows[1:]~: 先頭だけ特殊なセルなためスキップする
    data = []
    for row in rows[1:]:
        row_cells = row.find_all('td')
        if check_cell_streams(row_cells):
            videoid, time = get_videoid_time_streams(row_cells)
            members = get_members_streams(row_cells)
            members_string = ','.join(members)
            song_title = row_cells[2].text
            data.append([members_string, song_title, videoid, time])
            
    df = pd.DataFrame(data=np.array(data), 
                      columns=['members', 'songname', 'videoid', 'starttime'])
    return df

# 星街すいせいの曲だけを取得する
def check_cell_songs(cells):
    text = cells[1].text
    # 星街すいせいが参加していない場合はFalse
    if "星街すいせい" not in text:
        return False
    # コーラス参加などの場合はFalse
    if "(星街すいせい)" in text:
        return False
    return True

# リンクから動画IDを取得する
def get_videoid_songs(cells):
    # 短縮形とそれ以外で取得方法を分ける
    href = cells[2].a["href"]
    if "youtube" in href:
        stratid = href.find("v=")+2
        videoid = href[stratid:]
    if "youtu.be" in  href:
        stratid = href.find(".be")+4
        videoid = href[stratid:]
    return videoid
    
# メンバーと備考からアーティストを取得する
def get_members_songs(cells):
    artists = []
    holo_members = list(cells[1].children)
    for i in range(math.ceil(len(holo_members) / 2)):
        if '(' not in holo_members[i*2] and ')' not in holo_members[i*2]:
            artists.append(holo_members[i*2])        
    # 基本ゲスト名しか入っていないが、一部例外は除外する
    guests = list(cells[3].children)
    expects = ['スターアニマル']
    if len(guests) > 0:
        for i in range(math.ceil(len(guests) / 2)):
            guest = guests[i*2]
            if '(' not in guest and ')' not in guest and guest not in expects:
                artists.append(guest)
    return artists

# 歌動画のデータベースを返す
def create_songs():
    soup = create_soup()
    # 楽曲を管理しているテーブルから情報を取得
    songs = soup.find_all("table", {"id":"content_block_34"})[0]
    rows = songs.find_all("tr")

    # video_idとt、アーティスト、曲名を取り出す
    # rows[1:]~: 先頭だけ特殊なセルなためスキップする
    data = []
    for row in rows[1:]:
        row_cells = row.find_all('td')
        if check_cell_songs(row_cells):
            videoid = get_videoid_songs(row_cells)
            members = get_members_songs(row_cells)
            members_string = ','.join(members)
            song_title = row_cells[2].text
            data.append([members_string, song_title, videoid, 0])
            
    df = pd.DataFrame(data=np.array(data), 
                      columns=['members', 'songname', 'videoid', 'starttime'])
    return df


