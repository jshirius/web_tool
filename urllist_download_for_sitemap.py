#サイトマップを取り出す(２階層対応)
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time

xml_sitemap_url = 'あなたのサイトマップのURL  例：http://samplepage/sitemap.xml'



def get_site_info(sitemap):
    """
    以下の様なsitemapにある情報を取り出す
    <url>
    <loc>https://sample.jp/content1</loc>
    <lastmod>2021-11-07T23:59:17+00:00</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.2</priority>
    </url>
    <url>
    <loc>https://sample.jp/content2</loc>
    <lastmod>2021-11-04T11:40:38+00:00</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.2</priority>
    </url>
    """

    # 対象サイトのsitemap.xmlを指定
    response = requests.get(sitemap)
    result = response.content
    url_lists = ''

    bs = BeautifulSoup(result, 'xml')


    #url分のループ
    xml_url_list = bs.select('url')

    output_url_list = []
    for url in xml_url_list:
        url_dict = {}
        #urlの取り出し
        loc = url.select('loc')
        loc = re.sub('<[a-z]>', '', loc[0].text)
        url_dict["loc"] = loc

        #更新時間取り出し
        lastmod = url.select('lastmod')
        lastmod = re.sub('<[a-z]>', '', lastmod[0].text)
        url_dict["lastmod"] = lastmod
        output_url_list.append(url_dict)
        
    return output_url_list



#サイトマップ一覧(サイトマップ インデックス ファイル)を取得する
response = requests.get(xml_sitemap_url)
result = response.content
url_lists = ''

bs = BeautifulSoup(result, 'xml')
xml_sitemap_list = bs.select('sitemap')

sitemap_list = []
for url in xml_sitemap_list:
    url_dict = {}
    #urlの取り出し
    loc = url.select('loc')
    loc = re.sub('<[a-z]>', '', loc[0].text)
    sitemap_list.append(loc)
    


output_url_list = []
for sitemap in sitemap_list:
    time.sleep(2) #負荷対策で地味に重要
    d_list = get_site_info (sitemap)
    output_url_list.extend(d_list)


sitemap_df = pd.DataFrame(output_url_list)
sitemap_df.to_csv("sitemap_list.csv")

