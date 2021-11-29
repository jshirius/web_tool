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




def __google_search__( target_keyword):
    """google検索を使って該当データを取得する(ページ遷移する)

    Args:
        target_keyword ([type]):検索用のキーワード

    Returns:
        [dict]: 検索結果
    """
    out_puts = []
    
    #一回目の検索
    url = 'https://www.google.com/search?q={}&safe=off'.format(target_keyword)
    out_put = __google_result__(url, target_keyword)
    out_puts.extend(out_put)
    
    print(out_puts)
    page_limit = 1
    sleep(2)
    try:
        for i in range(page_limit - 1):
            #url作成
            #次へを取得
            elems = driver.find_elements_by_xpath('//*[@id="pnnext"]')
            elem = elems[0]

            url = elem.get_attribute('href')

            #２ページ以降の処理
            out_put = __google_result__(url, target_keyword)
            out_puts.extend(out_put)
            sleep(2.1)
    except  Exception as e:
        traceback.print_exc()
        
    return out_puts

#Google検索
def __google_result__( url, target_keyword):
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
    

    elems = driver.find_elements_by_xpath('//*[@id="rso"]/div[*]/div/div/div[1]/a')
    out_puts = []
    for elem in elems:
        url = elem.get_attribute('href')
        #print(url)
        
        #title = elem.find_elements_by_xpath('h3')[0].text
        d = elem.find_elements_by_xpath('h3')
        title = ""
        if(len(d)>0):
            title = d[0].text

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

def page_scraping( url:str, colum_name:str):

    res = req.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')
        
    #scriptタグなど削除
    for s in soup(['script', 'style']):
        s.decompose()

    tag = soup.html.body

    data_list = []


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
                    text = elem.text.replace("\n","")
                    
                    h = re.sub(r"\D", "", elem.name)
                    h = int(h) - 1
                    
                    
                    
                    t = "%s %s" % ("-" * h,text)
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


#webサイトを検索してキーワード一覽を取得する
def read_web_site_words(target_keyword):
    
    #########################################
    #googleから元のデータを取りに行く
    #########################################

    #リスト取得
    columns = ["source",'query_key','rs_title','rs_summary','rs_link']
    search_lists = __get_google_search_data__(target_keyword)
    df=pd.DataFrame(search_lists, columns=columns) 

    #処理リスト
    print("処理リスト")
    print(df)

    #pageデータ取得
    page_datas = []

    #blog_info
    blog_info_base = {"h1":"","h2":"","h3":"","h4":"","description":""}
    blog_info_list =[]
    for index, row in df.iterrows():
        try:
            blog_info_dict = blog_info_base.copy()

            #スクレイピングデータ
            soup, text = __page_scraping__(row['rs_link'])


        
        except Exception as e:
            print(e)    
            continue
    
        finally:
            blog_info_list.append(blog_info_dict)
            
        #前処理
        text = st_tool.format_text(text)
        page_datas.append(text)


    data_f = pd.concat([df, pd.DataFrame(blog_info_list)], axis=1)

    csv_file_name = target_keyword + "_webdata" + ".csv"
    data_f.to_csv(csv_file_name, encoding="utf_8_sig", line_terminator='\n')
    
    #形態素
    documents = get_morpheme_janome(page_datas)
    """
    documents=[]
    morpheme_janome = JanomeDataSet('neologd')
    for t in page_datas:

        #形態素に分ける
        data = morpheme_janome.text_morpheme(t,'名詞')

        #形態素単位の前処理
        data = st_tool.clean_keyword_list(data)
        #data = morpheme_janome.text_morpheme(t)
        if(len(data) == 0):
            continue
        documents.append(set(data))
    """
    return documents

#WEBサイトのカウントする
def get_keyword_web_site_count( target_keyword):
    """ターゲットキーワードを元に10サイトからキーワードを取得する

    Args:
        target_keyword ([type]):検索キーワード

    Returns:
        [list]: キーワードのリスト(使われているサイト数の情報)
    """

    #webサイトを検索してキーワード一覽を取得する
    web_sites = read_web_site_words(target_keyword)

    print(web_sites)
    keyword_dict = {}
    for keyword_list in web_sites:
        
        for keyword in keyword_list:
            #存在するか
            if(keyword in keyword_dict):
                keyword_dict[keyword] = keyword_dict[keyword] + 1
            else:
                keyword_dict[keyword] = 1


    sorted_patterns = sorted(keyword_dict.items(),reverse=True,key=lambda x:x[1])
    #2以上のみ出す
    #sorted_patterns = [i for i in sorted_patterns if i[1]>1]
    #pprint.pprint(sorted_patterns)
    return sorted_patterns

def main():

    #webドライバ初期化
    driver = webdriver.Chrome('./chromedriver')


    #引数取得
    parser = argparse.ArgumentParser(description='検索上位10位までのキーワード出現回数を出力する(1サイト１回とする)')  
    parser.add_argument("-k", "--keyword",required=True,  help='対象のキーワードを設定')
    parser.add_argument("-u", "--baseurl",required=False,  help='比較対象のurl')
    args = parser.parse_args()

    #引数を取得する
    #-u ベースサイトのURL
    #-p キーワードリストのファイルpath (キーワードリストの比較)
    #上位10サイトにおいて、使われているキーワードの回数(1サイト1回としてカウント)を取得する
    #オプションとして使われていないキーワードの検出をする
    print(args)

    #キーワード取得
    target_keyword = args.keyword
    results = get_keyword_web_site_count(target_keyword)

    #ベースサイトありか
    base_url_documents = []
    if(args.baseurl != None):
        #比較元サイトの取得
        page_datas = __page_scraping__(args.baseurl)
        page_datas = st_tool.format_text(page_datas)
        base_url_documents = get_morpheme_janome([page_datas])

        print("base_url_documents")
        print(base_url_documents)

    #結果を出力する
    for info in results:
        mark_b = ""
        #baseがあるか
        if(len(base_url_documents) > 0):
            if( info[0] in base_url_documents[0]):
                mark_b = "▲ "
        
        string = "%s%s, %ssite" % (mark_b, info[0], info[1])
        print(string)


    driver.quit()
if __name__=='__main__':
    main()