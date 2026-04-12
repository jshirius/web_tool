import os
import re
import sys

def split_script(input_path):
    """
    行頭が【★ または ★ で始まる行を区切りとしてファイルを分割する。
    分割先フォルダ: 元ファイルと同じフォルダ内に「{stem}_分割」フォルダを作成。
    ファイル名: 1_{stem}.txt, 2_{stem}.txt, ...
    """
    input_path = os.path.abspath(input_path)
    if not os.path.isfile(input_path):
        print(f"エラー: ファイルが見つかりません: {input_path}")
        sys.exit(1)

    base_dir = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    stem, ext = os.path.splitext(filename)   # 例: stem="高校回想_寸劇台本", ext=".txt"

    output_dir = os.path.join(base_dir, f"{stem}_分割")
    os.makedirs(output_dir, exist_ok=True)

    # 行頭が【★ または ★ で始まるパターン
    split_pattern = re.compile(r'^(【★|★)')

    with open(input_path, encoding='utf-8') as f:
        lines = f.readlines()

    # チャンクに分割する
    # 最初の【★/★行の前にある行も chunk[0] としてまとめる
    chunks = []
    current = []

    for line in lines:
        if split_pattern.match(line):
            # 現在のチャンクを保存（空でも保存して番号を合わせる）
            chunks.append(current)
            current = [line]
        else:
            current.append(line)

    # 最後のチャンクを追加
    if current:
        chunks.append(current)

    # 空のチャンク（先頭に【★がない場合など）を除去
    chunks = [c for c in chunks if c]

    if not chunks:
        print("分割対象の区切り行が見つかりませんでした。")
        sys.exit(0)

    # 書き出し
    for i, chunk in enumerate(chunks, start=1):
        out_filename = f"{i}_{filename}"
        out_path = os.path.join(output_dir, out_filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.writelines(chunk)
        print(f"  書き出し: {out_path}")

    print(f"\n完了: {len(chunks)} ファイルを '{output_dir}' に出力しました。")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使い方: python split_script.py <対象ファイルパス>")
        print("例:     python split_script.py 高校回想_寸劇台本.txt")
        sys.exit(1)

    split_script(sys.argv[1])
