import os
import time
import json
from twitch_parser import TwitchClipParser
from video_editor import VerticalVideoProcessor
from youtube_uploader import upload_video

CHANNELS = [c.strip() for c in os.getenv("CHANNELS", "shroud,xqc").split(",") if c]
OUTPUT_DIR = "processed"
MEMORY_FILE = "memory.json"
DELAY_HOURS = 12


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(list(memory), f)


def run_once():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    memory = load_memory()

    twitch = TwitchClipParser()
    clip = twitch.get_best_new_clip(CHANNELS, memory)
    if not clip:
        print("Нет новых клипов")
        return

    print(f"Выбран клип: {clip['title']} ({clip['view_count']} views)")
    downloaded_path, clip_id = twitch.download_clip(clip, OUTPUT_DIR)

    output_path = downloaded_path.replace(".mp4", "_vertical.mp4")
    processor = VerticalVideoProcessor()
    processor.convert_to_vertical(downloaded_path, output_path)

    upload_video(
        video_path=output_path,
        title=clip['title'],
        description="#shorts #twitch",
        tags=["shorts", "twitch"]
    )

    memory.add(clip_id)
    save_memory(memory)
    print("Цикл завершён.")


if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Ошибка: {e}")
        print(f"Ожидание {DELAY_HOURS} ч...")
        time.sleep(DELAY_HOURS * 3600)
