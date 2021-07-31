メモ

概要：
wordpressにtooltip(ツールチップ)の機能をプラグインなしで実現する。
tooltipは、adminlte(管理画面をつくるのに適しているツール)のなかにあるtooltipを利用する。

adminlteから、tooltipの部分のみ切り出したら、wordpressに反映させる。


ファイルの説明：

・tooltip_test.html
tooltipを導入したサンプルファイルです。

・adminlte_for_tooltip.css
tooltipのレイアウトを整えるためのcssファイル。
大本は、「adminlte.css」というファイル名でadminlteに存在するが、
wordpressに反映させると競合が起きる可能性があるため、tooltipに関係ないものを削除した。


・bootstrap.bundle.min.js(ここには同梱されていません)
adminlteに同梱されているbootstrapのjsファイル。
ファイルは、adminlteの公式サイト(参考サイト参照)からadminlteをダウンロードして取得してください。



参考サイト：
adminlte
https://adminlte.io/docs/2.4/license