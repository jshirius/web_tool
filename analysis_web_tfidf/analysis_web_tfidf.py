
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from janome.tokenizer import Tokenizer


#参考にしたページ・ソースコード
#https://blog.amedama.jp/entry/tf-idf


#tokenizerの初期化
janome_tokenizer  = Tokenizer()

def text_morpheme( text, part = "", part2 = ""):
    """janomeで形態素に分ける

    Arguments:
        text {[type]} -- 形態素に分ける文字列

    Keyword Arguments:
        part {str} -- 取得する品詞を指定(品詞の設定がない場合はすべて取得)
        part2 {str} -- サ変名詞などの２つ目の品詞

    Returns:
        [type] -- 形態素に分けた結果(リストで返す)
    """
    text_list = []
    for token in janome_tokenizer.tokenize(text):
        #print(token.part_of_speech)
        #場合分け

        #品詞指定なし
        if(len(part) == 0):
            text_list.append(token.surface)
        elif(len(part) > 0 and len(part2) > 0 ):
            #品詞１、２が設定されているケース
            if(part in token.part_of_speech):
                if(part2 in token.part_of_speech):
                    text_list.append(token.surface)
        elif(len(part) > 0 and len(part2) == 0):
            #品詞１のみ設定されているケース
            if(part in token.part_of_speech):
                text_list.append(token.surface)

    return text_list


def main():
    # データフレームを表示するときカラムを省略しない
    pd.set_option('display.max_columns', None)
    # 浮動小数点を表示するときは小数点以下 2 桁で揃える
    pd.options.display.float_format = '{:0.2f}'.format

    #スクレイピング対象のファイルを読み込む
    #「サイトID」でグループ化する
    df = pd.read_csv("scraping_list_result.csv" )

    #サイトIDのユニークな値を出す
    site_ids = df['サイトID'].unique()
    print(site_ids)

    #サイト毎にtf_idfの元データを作る
    site_list = []
    for site_id in site_ids:
        site_df = df[df['サイトID'] == site_id]
        site_df = site_df.reset_index()

        datas = []
        for index, row in site_df.iterrows():
            #text

            #TODO:ここにSTOPワード除去などの処理を入れる
            datas.extend(text_morpheme(row['text'],'名詞'))

        site_list.append( (site_df.loc[0]['サイト名'] , datas) )
  
    #前処理として形態素に分けること
    #分ける範囲 title,description,h1〜4,text
    #print(site_list)

    #corpusの設定をする
    corpus = []
    for word in site_list:
        d = " " . join(word[1])
        corpus.append(d)
    

    # 単語の数をカウントする
    count_vectorizer = CountVectorizer()
    X_count = count_vectorizer.fit_transform(corpus)

    # 見やすさのために表示するときは pandas のデータフレームにする
    df = pd.DataFrame(data=X_count.toarray().T,
                      index=count_vectorizer.get_feature_names(),
                      columns=[i[0] for i in site_list],
                      )
    #df = pd.DataFrame(data=X_count.toarray(),
    #                  columns=count_vectorizer.get_feature_names())
    print('--- BoW (Bag of Words) ---')
    print(df)
    df.to_csv("scraping_list_words.csv",encoding='utf_8_sig' )

    # scikit-learn の TF-IDF 実装
    tfidf_vectorizer = TfidfVectorizer()
    X_tfidf = tfidf_vectorizer.fit_transform(corpus)

    # IDF を表示する
    print('--- IDF (Inverse Document Frequency) ---')
    df = pd.DataFrame(data=[tfidf_vectorizer.idf_],
                      columns=tfidf_vectorizer.get_feature_names())
    print(df)

    # TF-IDF を表示する
    print('--- TF-IDF ---')
    #df = pd.DataFrame(data=X_tfidf.toarray(),
    #                  columns=tfidf_vectorizer.get_feature_names())
    df = pd.DataFrame(data=X_tfidf.toarray().T,
                      index=tfidf_vectorizer.get_feature_names(),
                      columns=[i[0] for i in site_list],
                      )
    print(df)
    #ファイルに書き出す
    df.to_csv("scraping_list_tfidf.csv",encoding='utf_8_sig' )


if __name__ == '__main__':
    main()
    
    