import os
from pydub import AudioSegment
import glob

# 対象ディレクトリ
base_directory = './input_dir'

# 再帰的にディレクトリ内のすべてのwavファイルを検索
wav_files = glob.glob(os.path.join(base_directory, '**', '*.wav'), recursive=True)

for wav_file in wav_files:
    try:
        # AudioSegmentを使ってwavファイルを読み込む
        audio = AudioSegment.from_wav(wav_file)

        # mp3の出力ファイル名（元のwavファイルと同じディレクトリに保存）
        mp3_file = wav_file.replace('.wav', '.mp3')

        # mp3ファイルとして保存
        audio.export(mp3_file, format='mp3')
        print(f"変換成功: {wav_file} -> {mp3_file}")

        # wavファイルを削除
        os.remove(wav_file)
        print(f"削除完了: {wav_file}")

    except Exception as e:
        print(f"エラー: {wav_file}, {e}")
