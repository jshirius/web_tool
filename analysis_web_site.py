# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request as req
import sys
import MeCab

u"""
WEBコンテンツの分析ツール
"""

def morphological(text):
    mecab = MeCab.Tagger("-Ochasen")
    node = mecab.parseToNode(text)  ## 解析を実行

    words = []
    wordDict = {}

    while node:

        surface = node.feature.split(',')

        #print(surface)
    # if len(surface) != 3:
        #    node = node.next
        #   continue
        if surface[0] == '名詞':
            # if True:
            words.append(surface[6])   
            key = surface[6]
            #重複判定
            if(key in wordDict):
                #存在する
                wordDict[key] = wordDict[key]  + 1
            else: 
                wordDict[key] = 1
        node = node.next


    return wordDict


if __name__ == '__main__':
    # 変換の元ファイルを読み込む
    param = sys.argv
    if (len(param) == 0):
        print ("Usage: $ python " + param[0] + " number")
        quit()

    #本来は引数から取得したいが、サンプルコードなのでURLはハードコーディング
    url = param[1]

    #WEBサイトを取得
    #青空文庫のサイトからHTMLデータを取得する
    #url = "http://www.aozora.gr.jp/index_pages/person148.html"
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
           
    #タグ以外の文字列のみ出力する（かなり汚いが・・・）
    print("----------タグ以外の全ての文字列----------")
    for s in soup(['script', 'style']):
        s.decompose()
        str = ' ' . join(soup.stripped_strings)
    print(str)

    #文字解析
    wordDict = morphological(str)
    sortedDict = sorted(wordDict.items(),key=lambda x: x[1])
    print (sortedDict)
