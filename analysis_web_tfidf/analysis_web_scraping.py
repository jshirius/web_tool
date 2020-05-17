
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as req


def scraping_main(url:str, all_text_mode = False):

    res = req.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')

    out_dict = {}

    print("処理中URL：" + url)

    #タイトル
    print("----------タイトル----------")
    title = soup.find("title")
    print(title.text)
    out_dict["title"] = title.text

    #URL
    print("----------URL----------")
    print(url)
    #out_dict["url"] = title.text 

    #description
    print("----------Description----------")
    out_dict["description"]  = ""
    og_des = soup.find('meta', attrs={'property': 'og:description', 'content': True})
    if og_des is not None:
        print(og_des['content'])
        out_dict["description"]  = og_des['content']
    else:
        print('Not found og:description tag')    
    

    #全てのh1タグのテキストを取得する
    print("----------h1のリスト----------")
    d = [i.text.strip() for i in soup.find_all("h1") ]
    print(d)
    out_dict["h1"]  = "\n" . join(d)


    #全てのh2タグのテキストを取得する
    print("----------h2のリスト----------")
    d = [i.text.strip() for i in soup.find_all("h2") ]
    print(d)
    out_dict["h2"]  = "\n" . join(d)

        

    #全てのh3タグのテキストを取得する       
    print("----------h3のリスト----------")
    d = [i.text.strip() for i in soup.find_all("h3") ]
    print(d)
    out_dict["h3"]  = "\n" . join(d)

    print("----------h4のリスト----------")
    d = [i.text.strip() for i in soup.find_all("h4") ]
    print(d)
    out_dict["h4"]  = "\n" . join(d)


    #タグ以外の文字列のみ出力する（かなり汚いが・・・）
    print("----------タグ以外の全ての文字列----------")
    out_dict["text"]  = ""
    for s in soup(['script', 'style']):
        s.decompose()
    text=soup.get_text()
    lines= [line.strip() for line in text.splitlines() if len(line.strip())>1]
    out_dict["text"]  = "\n" . join(lines)
    print(out_dict["text"])
    
    return out_dict

def main():

    #modeでテキストすべて保存するかの選択を出来るようにする

    #スクレイピング対象のファイルを読み込む
    df = pd.read_csv("scraping_list.csv" , sep="\t")
    print(df)

    #カラム追加
    df['title'] = ""
    df['description'] = ""
    df['h1'] = ""
    df['h2'] = ""
    df['h3'] = ""
    df['h4'] = ""
    df['text'] = ""


    #print(data)
    for index, row in df.iterrows():
        dict_data = scraping_main(row['url'],False)

        #更新
        df.loc[index,'title'] = dict_data["title"]
        df.loc[index,'description'] = dict_data["description"]
        df.loc[index,'h1'] = dict_data["h1"]
        df.loc[index,'h2'] = dict_data["h2"]
        df.loc[index,'h3'] = dict_data["h3"]
        df.loc[index,'h4'] = dict_data["h4"]
        df.loc[index,'text'] = dict_data["text"]
        

    #csvに出力する
    df = df.to_csv("scraping_list_result.csv",encoding='utf_8_sig' )



if __name__ == '__main__':
    main()
    
    

    