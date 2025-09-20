import os
from pydub import AudioSegment
import glob

# 対象ディレクトリ
base_directory = './input_dir'

# MP3のビットレート設定（kbps）
# 128kbps: 標準品質（デフォルト）
# 192kbps: 高品質
# 256kbps: 高音質
# 320kbps: 最高品質
mp3_bitrate = "192k"  # 必要に応じて変更してください

# 再帰的にディレクトリ内のすべてのwavファイルを検索
wav_files = glob.glob(os.path.join(base_directory, '**', '*.wav'), recursive=True)

for wav_file in wav_files:
    try:
        # AudioSegmentを使ってwavファイルを読み込む
        audio = AudioSegment.from_wav(wav_file)

        # 最後の部分が切れないように、短い無音を追加（0.1秒）
        silence = AudioSegment.silent(duration=100)  # 100ms
        audio_with_silence = audio + silence

        # mp3の出力ファイル名（元のwavファイルと同じディレクトリに保存）
        mp3_file = wav_file.replace('.wav', '.mp3')

        # mp3ファイルとして保存（エンコーダーとパラメータを明示的に指定）
        audio_with_silence.export(
            mp3_file, 
            format='mp3', 
            bitrate=mp3_bitrate,
            parameters=["-q:a", "0"]  # 最高品質設定
        )
        print(f"変換成功: {wav_file} -> {mp3_file}")

        # wavファイルを削除
        os.remove(wav_file)
        print(f"削除完了: {wav_file}")

    except Exception as e:
        print(f"エラー: {wav_file}, {e}")
