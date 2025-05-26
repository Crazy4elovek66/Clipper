import os
import time
import json
import logging
from twitch_parser import TwitchClipParser
from video_editor import VerticalVideoProcessor
from youtube_uploader import upload_video

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('automation.log')
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
CHANNELS = [c.strip() for c in os.getenv("CHANNELS", "shroud,xqc").split(",") if c]
OUTPUT_DIR = "processed"
MEMORY_FILE = "memory.json"
DELAY_HOURS = 12


def load_memory():
    """Загружает множество обработанных клипов из файла"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки memory.json: {e}")
        return set()


def run_once():
    """Основной цикл обработки одного клипа"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        memory = load_memory()

        twitch = TwitchClipParser()
        clip = twitch.get_best_new_clip(CHANNELS, memory)
        
        if not clip:
            logger.info("Нет новых клипов для обработки")
            return

        logger.info(f"Обработка клипа: {clip['title']} (ID: {clip['id']}, Просмотров: {clip['view_count']}")

        # Загрузка клипа
        downloaded_path, clip_id = twitch.download_clip(clip, OUTPUT_DIR)
        if not downloaded_path or not os.path.exists(downloaded_path):
            raise FileNotFoundError(f"Не удалось загрузить клип {clip_id}")

        # Конвертация в вертикальный формат
        output_path = os.path.join(OUTPUT_DIR, f"{clip_id}_vertical.mp4")
        processor = VerticalVideoProcessor()
        processor.convert_to_vertical(downloaded_path, output_path)
        
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Не удалось создать вертикальное видео {output_path}")

        # Загрузка на YouTube
        upload_video(
            video_path=output_path,
            title=clip['title'],
            description=f"Клип с Twitch: {clip['title']}\n#shorts #twitch #{clip['broadcaster']['name']}",
            tags=["shorts", "twitch", clip['broadcaster']['name']]
        )

        # Обновление памяти
        memory.add(clip_id)
        save_memory(memory)
        
        # Очистка временных файлов
        for f in [downloaded_path, output_path]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                logger.warning(f"Не удалось удалить файл {f}: {e}")

        logger.info(f"Успешно обработан клип {clip_id}")

    except Exception as e:
        logger.error(f"Критическая ошибка в run_once: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("Запуск автоматизации клипов Twitch")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Остановка по запросу пользователя")
            break
        except Exception as e:
            logger.error(f"Необработанная ошибка в основном цикле: {e}", exc_info=True)
        
        logger.info(f"Ожидание {DELAY_HOURS} часов до следующей проверки...")
        time.sleep(DELAY_HOURS * 3600)
