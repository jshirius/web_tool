#自分のサイトと競合10サイトとの比較ツール
#別途JanomeDataSetクラス、前処理用のモジュールを以下のURLからダウンロードして設定してください。
#https://github.com/jshirius/nlp_tools/blob/master/janome_data_set.py
#https://github.com/jshirius/nlp_tools/blob/master/string_preprocessing_tool.py

from janome_data_set import JanomeDataSet
import string_preprocessing_tool as st_tool

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Tag
import urllib.request as req
import time
import pandas as pd
import re
import random
from time import sleep
import traceback
import pprint
import argparse

from collections import Counter




#形態素の初期化
#morpheme_janome = JanomeDataSet('neologd')
morpheme_janome = JanomeDataSet()
#print(args)




def google_search(driver,  target_keyword, page_limit = 1):
    """google検索を使って該当データを取得する(ページ遷移する)

    Args:
        target_keyword ([type]):検索用のキーワード

    Returns:
        [dict]: 検索結果
    """
    out_puts = []
    
    #一回目の検索
    url = 'https://www.google.com/search?q={}&safe=off'.format(target_keyword)
    out_put = __google_result__(driver, url, target_keyword)
    out_puts.extend(out_put)
    
    #print(out_puts)
    sleep(2)
    try:
        for i in range(page_limit - 1):
            #url作成
            #次へを取得
            elems = driver.find_elements_by_xpath('//*[@id="pnnext"]')
            elem = elems[0]

            url = elem.get_attribute('href')

            #２ページ以降の処理
            out_put = __google_result__(driver, url, target_keyword)
            out_puts.extend(out_put)
            sleep(2.1)
    except  Exception as e:
        traceback.print_exc()
        
    return out_puts

#Google検索
def __google_result__(driver,  url, target_keyword):
    """ページごとの検索結果(タイトル、urlなど)を取得する

    Args:
        url ([type]): url
        target_keyword ([type]): 検索キーワード

    Returns:
        [type]: [description]
    """

    print("検索結果ページのURL")
    print(url)
    
    driver.get(url)
    time.sleep(2)
    

    #elems = driver.find_elements_by_xpath('//*[@id="rso"]/div[*]/div/div/div[1]/a')
    #１位と最下位が取れないときの対応
    elems = driver.find_elements_by_xpath('//*[@id="rso"]/div[*]/div/div/div[1]//*') 
    out_puts = []
    for elem in elems:
        url = elem.get_attribute('href')
        if(url == None):
            continue
        #print(url)
        
        #title = elem.find_elements_by_xpath('h3')[0].text
        d = elem.find_elements_by_xpath('h3')
        title = ""
        if(len(d)>0):
            title = d[0].text
        else:
            continue
        out_dic ={}
        out_dic['source'] = "google検索"
        out_dic['query_key'] = target_keyword
        out_dic['rs_title'] = title
        out_dic['rs_link']  = url
        out_dic['rs_summary'] = ""
        out_puts.append(out_dic)

    #print("google検索結果の一覧")
    #print(out_puts)

    return out_puts

def __get_google_search_data__( target_keyword):
    csv_file_name_format = "matome_%s.csv"
    csv_file_name = csv_file_name_format % target_keyword
    columns = ["source",'query_key','rs_title','rs_summary','rs_link']

    #Gooleの一覧結果
    search_lists = None
    try:
        print("Googleの結果の検索開始します")
        d = __google_search__(target_keyword)
        search_lists = d

        #df=pd.DataFrame(d, columns=columns) 
        #df.to_csv(csv_file_name, encoding="utf_8_sig")
    except Exception as e:
        traceback.print_exc()
    

    return search_lists

def get_index_lable():
    #ラベルを作る
    labels = []
    #labels.append("項目")
    labels.append("検索結果タイトル")
    labels.append("タイトル")
    labels.append("URL")
    labels.append("文字数")
    labels.append("キーワード出現回数")
    labels.append("description")
    labels.append("気づき")
    labels.append("h1〜h5")

    df = pd.DataFrame(labels)
    df.columns = ["項目"]

    return df

def page_scraping( url:str, rs_title,colum_name:str):

    res = req.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')
        
    #scriptタグなど削除
    for s in soup(['script', 'style']):
        s.decompose()

    tag = soup.html.body

    data_list = []

    #検索結果のタイトル(切れているのがわかる)
    data_list.append(rs_title)
    
    #タイトル
    t = soup.find('title').text
    data_list.append(t)

    #URL
    data_list.append(url)

    #文字数
    text=soup.get_text()
    data_list.append(len(text))

    #キーワード出現回数
    datas = __get_keyword_count(soup)
    data_list.append(datas[0:20])

    #descriptin
    og_des = soup.find('meta', attrs={'property': 'og:description', 'content': True})
    if og_des is not None:
        #print(og_des['content'])
        t = og_des['content'].replace(" ", "")
        data_list.append(t)
    else:
        data_list.append("")
        


    #気づき
    data_list.append("")

    #h1〜5
    h1_flag = False
    for elem in tag.descendants:
        if isinstance(elem, Tag):
            if("h1" == elem.name or"h2" == elem.name or "h3" == elem.name or "h4" == elem.name):
                if("h1" == elem.name ) :h1_flag = True
                if(h1_flag == True):
                    text = elem.text.replace("\n","").replace("\t","")
                    
                    h = re.sub(r"\D", "", elem.name)
                    h = int(h) - 1
                    
                    
                    
                    t = "%s %s" % ("■" * h,text)
                    data_list.append(t)
    df = pd.DataFrame(data_list)
    df.columns = [colum_name]

    return df

def __get_keyword_count(soup):
    text=soup.get_text()
    text = st_tool.format_text(text)
    data = morpheme_janome.text_morpheme(text,'名詞')
    data = [i.lower() for i in data]
    data = st_tool.clean_keyword_list(data)
    datas = Counter(data).most_common()

    return datas

def _get_site_infos_detail(base_url, sites ):
    #URLリストからサイト個別情報を取り出す


    #検索順位の確認
    base_url_rank = 0
    for i , site_info in enumerate(sites):
        
        if(base_url in site_info['rs_link']):
            #ランキング存在した
            base_url_rank = i + 1
            break
            
    #自分のサイトの情報を取り出す
    t = "圏外"
    if(base_url_rank > 0):
        t = "%d位" % base_url_rank
        
    text = "元サイト(ランキング:%s)" % t
    label_df = get_index_lable()
    df = page_scraping(base_url, "", text)
    df_summary = pd.concat([label_df,df ], axis=1)

    #競合10サイト情報
    limit = 10
    for i , site_info in enumerate(sites):
        if(i >= limit):
            #リミット超えた
            break
            
        #自分のサイトか
        if(base_url in site_info['rs_link']):
            continue
            
        print(site_info)
        t = "競合 %d位" % (i+1)
        try:
            #ページを読み込んでタイトルなどの情報を読み出す
            df = page_scraping(site_info["rs_link"], site_info["rs_title"], t)
            df_summary = pd.concat([df_summary,df ], axis=1)
        except Exception as e:
            print("個別情報取得エラー", i)
            print(e, site_info)

            #補填する
            data_list = []
            #タイトル
            data_list.append(site_info['rs_title'])
            data_list.append("情報なし")
            data_list.append(site_info['rs_link'])
            data_list.append("情報なし")
            data_list.append("情報なし")
            data_list.append("情報なし")
            data_list.append("")
            data_list.append("情報なし")
            df = pd.DataFrame(data_list)
            df.columns = [t]
            df_summary = pd.concat([df_summary,df ], axis=1)



    return df_summary

#WEBサイトの情報を取り出す
def get_keyword_web_info(base_url,  target_keyword):
    """ターゲットキーワードを元に10サイトからキーワードを取得する

    Args:
        base_url:ベースになるURL
        target_keyword ([type]):検索キーワード

    Returns:
        [list]: キーワードのリスト(使われているサイト数の情報)
    """

    #webドライバ初期化
    driver = webdriver.Chrome('./chromedriver')

    #google検索は３ページまで遷移する
    sites = google_search(driver,target_keyword, 3)
    df_summary = _get_site_infos_detail(base_url, sites )

    file_name = "「%s」の検索結果.csv" % target_keyword
    df_summary.to_csv(file_name, encoding='utf_8_sig', index = False)
    driver.quit()

    return df_summary

def main():
    #引数取得
    parser = argparse.ArgumentParser(description='競合10サイトの比較をする')  
    parser.add_argument("-k", "--keyword",required=True,  help='対象のキーワードを設定')
    parser.add_argument("-u", "--baseurl",required=True,  help='比較対象のurl')
    args = parser.parse_args()

    #引数を取得する
    #-u ベースサイトのURL
    #-p キーワードリストのファイルpath (キーワードリストの比較)
    #上位10サイトにおいて、使われているキーワードの回数(1サイト1回としてカウント)を取得する
    #オプションとして使われていないキーワードの検出をする
    print(args)

    #キーワード取得
    target_keyword = args.keyword
    results = get_keyword_web_info(args.baseurl, args.keyword)

    
if __name__=='__main__':
    main()