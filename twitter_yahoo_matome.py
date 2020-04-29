# -*- coding: utf-8 -*-
#yahoo知恵袋、Google検索、TwitterAPIから該当キーワードの情報を取得する

from datetime import datetime
import csv
import sys
from selenium import webdriver
import pandas as pd
from time import sleep

##########################
#設定関連
##########################
PAGE_LIMIT = 2 #ページ遷移の最大の回数
SQRAPING_URL = "https://chiebukuro.yahoo.co.jp/"
csv_file_name_format = "matome_%s.csv"


#デバイスをオープンする
driver = webdriver.Chrome('./chromedriver')

#該当ページを解析する
def analysis_action(target_keyword):

    elems = driver.find_elements_by_xpath('//*[@id="sr"]/ul/li[*]')
    # 取得した要素を1つずつ表示

    out_puts = []

    if(len(elems) == 0):
        print("ページは存在しないよ〜")
    else:
        for elem in elems:
            out_dic ={}
            out_dic['source'] = "知恵袋"
            out_dic['query_key'] = target_keyword
            out_dic['rs_title'] = elem.find_elements_by_xpath('h3/a')[0].text
            out_dic['rs_link']  = elem.find_elements_by_xpath('h3/a')[0].get_attribute('href')
            out_dic['rs_summary'] = elem.find_elements_by_xpath('p[1]')[0].text
            #print(out_dic)
            out_puts.append(out_dic)
            #print("*" * 60)
            
    return out_puts

def next_page_action():
    """
    現在のページから次のページを読み込むアクションを実行する
    """
    rtn = False
    
    #次へボタンのクリック
    elems = driver.find_elements_by_xpath('//*[@id="pg_low"]/div/a[*]')

    #現在のページ
    print("ページ遷移前のurl:")
    print(driver.current_url)
    if(len(elems) == 0):
        print("次のページは存在しないよ〜")
    else:
        for elem in elems:
            #print(elem.text)
            if(elem.text != "次へ"):
                continue
            url = elem.get_attribute('href')
            driver.get(url)
            rtn = True
            break

    return rtn


#yahoo知恵袋
def chiebukuro_yahoo(target_keyword):
    #知恵袋ページを読み込む
    driver.get(SQRAPING_URL)

    #キーワードを入力する
    search_box = driver.find_element_by_css_selector('input.txtKeyword')
    search_box.send_keys(target_keyword)
    search_button_container = driver.find_element_by_css_selector('p.btnSearch')
    search_button = search_button_container.find_element_by_css_selector('input')
    search_button.click()
    sleep(2)

    d = analysis_action(target_keyword)
    #df=pd.DataFrame(d)  
    #df.to_csv(csv_file_name, encoding="utf_8_sig")

    analysis_list = []
    analysis_list.extend(d)

    for page in range(PAGE_LIMIT):
        
        print("ページ %dを実行中" % page)
        sleep(5)
        
        #次のページに遷移する
        rtn = next_page_action()
        if(rtn == False):
            break
            
        #知恵袋の質問リストを格納する
        d = analysis_action(target_keyword)
        if(len(d) > 0):
            analysis_list.extend(d)
            #df=pd.DataFrame(analysis_list)  
            #df.to_csv(csv_file_name, encoding="utf_8_sig")
    
    print(analysis_list)
    return analysis_list

#Google検索
def google_result(target_keyword):
    url = 'https://www.google.com/search?q={}'.format(target_keyword)
    driver.get(url)
    elems = driver.find_elements_by_xpath('//*[@id="rso"]/div[*]/div/div[1]/a')

    out_puts = []
    for elem in elems:
        #print(elem.text)
        url = elem.get_attribute('href')
        print(url)
        
        title = elem.find_elements_by_xpath('h3')[0].text

        out_dic ={}
        out_dic['source'] = "google検索"
        out_dic['query_key'] = target_keyword
        out_dic['rs_title'] = title
        out_dic['rs_link']  = url
        out_dic['rs_summary'] = ""
        out_puts.append(out_dic)

    print("google検索結果の一覧")
    print(out_puts)

    return out_puts

#twitterAPI


if __name__ == '__main__':
    
    #入力パラメータ
    param = sys.argv
    if (len(param) < 2):
        print ("キーワードを入力してください")
        quit()

    target_keyword = param[1]
    print(target_keyword)

    #yahoo知恵袋の結果を返す
    analysis_list = chiebukuro_yahoo(target_keyword)
    csv_file_name = csv_file_name_format % target_keyword

    df=pd.DataFrame(analysis_list) 
    df.to_csv(csv_file_name, encoding="utf_8_sig")

    #Gooleの結果
    d = google_result(target_keyword)
    analysis_list.extend(d)
    df=pd.DataFrame(analysis_list) 
    df.to_csv(csv_file_name, encoding="utf_8_sig")

    #twitter api

    driver.close()
