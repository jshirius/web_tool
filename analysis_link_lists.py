# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import csv
import sys
import urllib.request as req

u"""
リンクリスト取得ツール
出力はCSVファイル(ファイル名：「タイトル」＋リンクリスト_日時.csv」)にて
第１引数 調べる階層 最小1より
第２引数　調べるサイトのURL(ダブルクフォーテーションで括る)
"""

LinkColumnName = ['no', 'リンク名','URL']


def get_link_lists(url):
    linkLists = []

    res = req.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')

    for s in soup.find_all("a"): 
        wordDict = {}

        #url
        link = s.get("href")

        if(link[0] == '/'):
            parsed_url = urlparse(url)
            link = parsed_url.scheme + "://" +parsed_url.netloc + link
        
        wordDict[LinkColumnName[0]] = 0
        wordDict[LinkColumnName[1]] = s.text
        wordDict[LinkColumnName[2]] = link

        #追加
        linkLists.append(wordDict)

        #出力
        print(s.text + "  "+  link) 


    return linkLists;


if __name__ == '__main__':

    #ネットからデータ取得
    param = sys.argv
    if (len(param) == 0):
        print ("Usage: $ python " + param[0] + " number")
        quit()
    if(len(param) < 3):
        print ("入力データが足りないです 第一引数:調べる階層  第２引数：URL")
        quit()      


    #調べる深度depthを取得する
    depth = param[1]

    #url取得
    url = param[2]


    #リンクリスト取得
    linkLists = get_link_lists(url)



    #ファイル書き込み
    with open('test.csv', 'w') as csv_file:
        fieldnames = LinkColumnName
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        #データ分出力する
        index = 0
        for data in linkLists:
            writer.writerow({LinkColumnName[0]:index, LinkColumnName[1]: data[LinkColumnName[1]], LinkColumnName[2]: data[LinkColumnName[2]]})
            index +=1



