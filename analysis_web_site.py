# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from urllib.parse import urlparse
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

    #タイトル
    print("----------タイトル----------")
    title = soup.find("title")
    print(title.text)

    #URL
    print("----------URL----------")
    print(url)    

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


    #リンクリストを出力する
    print("----------リンクのリスト----------")
    for s in soup.find_all("a"): 
        #print(s.text)  
        #URL取得部分 https://www.python.ambitious-engineer.com/archives/35
        #url
        link = s.get("href")
        if(link is None):
            continue

        if(link[0] == '/'):
            parsed_url = urlparse(url)
            link = parsed_url.scheme + "://" +parsed_url.netloc + link
        
        # /staff_entry/jobs/city/13のように「http,https」から始まらないケースがあるよって、ドメイン名取得しておく
        print(s.text + "  "+  link)


    #タグ以外の文字列のみ出力する（かなり汚いが・・・）
    print("----------タグ以外の全ての文字列----------")
    for s in soup(['script', 'style']):
        s.decompose()
        data = "\n" . join(soup.stripped_strings)
    
    print(data)




    #文字解析
    wordDict = morphological(data)
    sortedDict = sorted(wordDict.items(),key=lambda x: -x[1])
    #print (sortedDict)
    #見やすくする

    print("----------キーワード一覧----------")
    datas = ''
    for k, v in sortedDict:
        value = str(v)
        datas +=  '(' + k + ' ' + value + ') '
       
        #print(k, v)
    print(datas)



