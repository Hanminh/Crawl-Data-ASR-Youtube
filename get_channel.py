import subprocess

### Chọn topic để tìm kiếm kênh YouTube
CHANNEL_TOPIC = "học tiếng anh"

def search_channels(query, limit=1):
    cmd = [
        "yt-dlp",
        f"ytsearch{limit}:{query}",
        "--print", "channel_url",
        "--skip-download"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    channels = list(set(result.stdout.strip().split("\n")))
    return channels


channels = search_channels(CHANNEL_TOPIC, limit=20)
with open("List_channels.txt", "w") as f:
    for channel in channels:
        f.write(channel + "\n")
    