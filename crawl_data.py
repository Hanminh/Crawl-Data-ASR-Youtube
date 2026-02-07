import yt_dlp
import os
import glob
import subprocess
import json
from tqdm import tqdm

# CHANNEL_URL = "https://www.youtube.com/@donnhuloi1/videos"

DOWNLOAD_PATH = "./data/raw_audio" ## nơi lưu audio + subtitle tải về, xóa đi sau khi xử lý segments
SEGMENT_DIR = "./data/segments" ## nơi lưu các đoạn audio đã cắt
MANIFEST_PATH = "./data/manifest.jsonl" ## nơi lưu manifest cuối cùng

os.makedirs(SEGMENT_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def get_video_id_from_channel(channel_url):
    # channel_url = "https://www.youtube.com/@donnhuloi1/videos"
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "id", channel_url],
        capture_output=True,
        text=True
    )

    video_ids = result.stdout.strip().split("\n")
    return video_ids

def download_video_assets(video_id, download_path):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    os.makedirs(download_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',

        # subtitle
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['vi'],

        # output
        'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
        
        # 🔥 extract audio + resample 16kHz mono
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'postprocessor_args': [
            '-ar', '16000',   # sample rate
            '-ac', '1'        # mono
        ],

        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        video_id = info['id']

    audio_file = os.path.join(download_path, f"{video_id}.wav")

    # 🔍 tìm subtitle thật sự (auto hoặc manual)
    sub_files = glob.glob(os.path.join(download_path, f"{video_id}*.vtt"))
    vtt_file = sub_files[0] if sub_files else None

    return audio_file, vtt_file

def time_to_seconds(t):
    try:
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        print(f"Error converting time: {t}")
        # Raise exception 
        raise e

def process_vtt_file(vtt_path):
    start = 0.0
    end = 0.0
    count_line = 0
    list_segments = []
    with open(vtt_path, 'r', encoding='utf-8') as f:
        for id, line in enumerate(f):
            if id <= 3:
                continue
            # print(f"{id}: {line.strip()}")
            if (not line.strip()) and (count_line == 0):
                continue
            count_line += 1
            if count_line == 1: 
                line = line.strip().split('-->')
                # print(line)
                start = line[0].strip()
                start = time_to_seconds(start)
                # print(start)
                end = line[1].strip().split(' ')[0]
                end = time_to_seconds(end)
                # print(end)
            if count_line == 6:
                text = line.strip()
                # print(f"{id}: {start} --> {end} : {text}")
                list_segments.append((start, end, text))
                count_line = 0
    return list_segments
            
        # break

def cut_audio_segment(input_wav, output_wav, start, end):
    duration = end - start
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", input_wav,
        "-t", str(duration),
        "-ar", "16000",
        "-ac", "1",
        output_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_audio_duration(wav_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        wav_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def process_video_to_manifest(audio_file, segments, video_id):
    manifest_lines = []

    for idx, (start, end, text) in enumerate(segments):
        if not text.strip():
            continue

        segment_name = f"{video_id}_{idx:04d}.wav"
        segment_path = os.path.join(SEGMENT_DIR, segment_name)

        cut_audio_segment(
            input_wav=audio_file,
            output_wav=segment_path,
            start=start,
            end=end
        )

        if not os.path.exists(segment_path):
            continue

        duration = get_audio_duration(segment_path)

        manifest_lines.append({
            "audio_filepath": os.path.abspath(segment_path),
            "text": text,
            "duration": round(duration, 3)
        })

    return manifest_lines

def append_to_manifest(manifest_lines):
    with open(MANIFEST_PATH, "a", encoding="utf-8") as f:
        for line in manifest_lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    with open('List_channels.txt', 'r', encoding="utf-8") as f:
        for line in f:
            CHANNEL_URL = line.strip()
            print(f"Processing channel: {CHANNEL_URL}")   
            video_ids = get_video_id_from_channel(CHANNEL_URL)
            print(f"Found {len(video_ids)} videos in the channel.")

            for video_id in video_ids:
                print(f"Processing video ID: {video_id} in channel {CHANNEL_URL}")

                audio_file, vtt_file = download_video_assets(video_id, DOWNLOAD_PATH)

                if not vtt_file or not os.path.exists(vtt_file):
                    print("No subtitles, skip.")
                    continue

                segments = process_vtt_file(vtt_file)
                print(f"Extracted {len(segments)} segments.")

                manifest_lines = process_video_to_manifest(
                    audio_file=audio_file,
                    segments=segments,
                    video_id=video_id
                )

                append_to_manifest(manifest_lines)

                # 🗑 cleanup
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                # if os.path.exists(vtt_file):
                #     os.remove(vtt_file)

                print(f"Done video {video_id}, added {len(manifest_lines)} samples.")
                break # REMOVE TO PROCESS ALL VIDEOS
            break # REMOVE TO PROCESS ALL CHANNELS
        