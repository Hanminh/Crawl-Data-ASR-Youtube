import subprocess
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Get YouTube channel IDs based on topics")
    parser.add_argument(
        "--output_file",
        type=str,
        default="List_channels.txt",
        help="Path to output file containing channel URLs"
    )
    return parser.parse_args()


TOPICS = [
    "học tiếng anh",
    "công nghệ thông tin",
    "viễn thông",
    "viettel telecom",
    "mạng máy tính",
    # "vtv24",
    "tin tức công nghệ",
    "trí tuệ nhân tạo",
    "dịch vụ số",
    "an ninh mạng"
]

MAX_CHANNELS_PER_TOPIC = 15


def search_channels(query, limit=15):
    # cmd = [
    #     "yt-dlp",
    #     f"ytsearch{limit}:{query}",
    #     "--print", "channel_id",
    #     "--skip-download",
    #     "--quiet"
    # ]
    cmd = [
        "yt-dlp",
        f"ytsearch{limit}:{query}",
        "--print", "uploader_url",
        "--skip-download",
        "--quiet"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    channel_ids = [
        c.strip() for c in result.stdout.split("\n")
        if c.strip()
    ]

    return list(set(channel_ids))


def main():
    args = parse_args()
    all_channels = set()

    for topic in TOPICS:
        print(f"Searching channels for topic: {topic}")
        channel_ids = search_channels(topic, MAX_CHANNELS_PER_TOPIC)
        print(f"  Found {len(channel_ids)} channel IDs")
        all_channels.update(channel_ids)

    with open(args.output_file, "w", encoding="utf-8") as f:
        for cid in sorted(all_channels):
            # channel_url = f"https://www.youtube.com/channel/{cid}"
            channel_url = f"{cid}/videos"
            f.write(channel_url + "\n")
            print(f"Saved: {channel_url}")

    print(f"\nDone! Total unique channels: {len(all_channels)}")


if __name__ == "__main__":
    main()
