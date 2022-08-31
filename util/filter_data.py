# Pythonの基本ライブラリ
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Durationが小さすぎるデータは除外する
def filter_duration(base_path, threshold=30):
    base_df = pd.read_csv(base_path, header=0)
    filter_ids = np.zeros(base_df.shape[0], dtype=bool)

    for i, row in base_df.iterrows():
        start_time = row['starttime']
        end_time = row['endtime']
        filter_ids[i] = (end_time-start_time) > threshold

    df_tmp = base_df
    df_tmp['filter'] = filter_ids
    df_tmp = df_tmp[df_tmp['filter'] == True]
    base_df = df_tmp.drop(columns=['filter'])

    base_df.to_csv(base_path, index=False)
