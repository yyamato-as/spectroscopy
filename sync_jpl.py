import os
import re
import time
import requests
from bs4 import BeautifulSoup

SAVE_DIR = "./data/jpl/"

JPL_BASE_URL = 'https://spec.jpl.nasa.gov/ftp/pub/catalog/'

print(f"Fetching list of files in {JPL_BASE_URL} ...")
response = requests.get(JPL_BASE_URL)
matches = re.findall(r'([c]\d{6}\.cat)', response.text)
filename_list = sorted(list(set(matches)))
print(f"Number of species: {len(filename_list)}")

print("Syncronizing JPL data...")
t_s = time.time()
for filename in filename_list:
    # 常にクリーンなベースURLとファイル名を結合して直接リンクを叩く
    file_url = f"{JPL_BASE_URL}{filename}"
    save_path = os.path.join(SAVE_DIR, filename)
    
    # # 既にダウンロード済みの場合はスキップする（定期実行時に無駄な通信を省くため）
    # if os.path.exists(save_path):
    #     print(f"スキップ (既存): {filename}")
    #     continue

    print(f"Downloading: {filename}")
    try:
        file_data = requests.get(file_url).content
        with open(save_path, 'wb') as f:
            f.write(file_data)
            
        # サーバーへの負荷軽減
        time.sleep(1)
        
    except Exception as e:
        print(f" Error ({filename}): {e}")

# parition function file
file_url = "https://spec.jpl.nasa.gov/ftp/pub/catalog/catdir.cat"
save_path = "./data/jpl/catdir.cat"
try:
    file_data = requests.get(file_url).content
    with open(save_path, 'wb') as f:
        f.write(file_data)
except Exception as e:
    print(f" Error ({filename}): {e}")

t_e = time.time()
t_elapsed = (t_e - t_s) / 60.0

print(f"\nDone in {t_elapsed:.1f} min.")