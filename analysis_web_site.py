# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request as req
import sys


u"""
WEBコンテンツの分析ツール
"""



if __name__ == '__main__':
    # 変換の元ファイルを読み込む
    param = sys.argv
    if (len(param) == 0):
        print ("Usage: $ python " + param[0] + " number")
        quit()

    #本来は引数から取得したいが、サンプルコードなのでURLはハードコーディング
    #url = param[1]

    #WEBサイトを取得
    #青空文庫のサイトからHTMLデータを取得する
    url = "http://www.aozora.gr.jp/index_pages/person148.html"
    res = req.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')

    #全てのh1タグのテキストを取得する
    print("----------h1のリスト----------")
    for s in soup.find_all("h1"): 
        print(s.text)

    #全てのh2タグのテキストを取得する
    print("----------h2のリスト----------")
    for s in soup.find_all("h2"): 
        print(s.text)
        

    #全てのh3タグのテキストを取得する       
    print("----------h3のリスト----------")
    for s in soup.find_all("h3"): 
        print(s.text)
            
    #currentクラスタグの情報
    print("----------1つ目のcurrentクラスの情報を取得する----------")
    print(soup.select_one(".current").string)

    #タグ以外の文字列のみ出力する（かなり汚いが・・・）
    print("----------タグ以外の全ての文字列----------")
    for s in soup(['script', 'style']):
        s.decompose()
        str = ' ' . join(soup.stripped_strings)
    print(str)

