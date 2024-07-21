import concurrent.futures
import gc
import select
import threading

from loguru import logger

from extracter import Extracter
from voicer import free_resources, get_audio, get_speakers, get_speeds, play_audio

logger.add("./logs/.log")


class ConsoleApp:
    def __init__(self):
        self.is_working = False
        self.worker_thread = None
        self.speed = None
        self.speaker = None

        self.extracter = Extracter()
        self.speeds_list = get_speeds()
        self.speakers_list = get_speakers()

        self.num_threads = 10
        self.prev_voiced_text = ""

    def voicing(self):
        self.is_working = True
        self.worker()
        if self.is_working:
            self.is_working = False
            if self.worker_thread is not None:
                self.worker_thread.join()
                self.worker_thread = None
        else:
            self.is_working = True
            self.worker_thread = threading.Thread(target=self.worker)
            self.worker_thread.start()

    def worker(self):
        try:
            while self.is_working:
                selected_text = self.extracter.get_selected_text()
                if selected_text == -2:
                    select.select([], [], [], 0.1)
                elif selected_text == self.prev_voiced_text:
                    logger.info("Skipped, select new text.")
                    select.select([], [], [], 2)
                elif len(selected_text):
                    logger.info(f"Voicing text: {selected_text[-5:]}")

                    sentences = selected_text.strip().split(".")
                    chunk_size = max(1, len(sentences) // self.num_threads)
                    max_workers = min(len(sentences), self.num_threads)

                    chunks = [
                        sentences[i : i + chunk_size]
                        for i in range(0, len(sentences), chunk_size)
                    ]

                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=max_workers
                    ) as executor:
                        futures = [
                            executor.submit(
                                get_audio, " ".join(chunk), self.speaker, self.speed
                            )
                            for chunk in chunks
                        ]
                        results = [None] * len(futures)
                        for i, future in enumerate(futures):
                            results[i] = future.result()

                    if results:
                        logger.info("Audio voicing...")
                        self.prev_voiced_text = selected_text
                        for r in results:
                            if r:
                                play_audio(r)
                else:
                    select.select([], [], [], 5)
        except KeyboardInterrupt:
            gc.collect()
            print("Exiting from voicing mode. Wait until started audio finished.")

    def start(self):
        try:
            while True:
                params = input("Write command: ").strip().lower().split()
                command = params[0] if len(params) else None
                match (command):
                    case "start":
                        print("Start voicing...")
                        self.voicing()
                    case "get_speed" | "speed":
                        print(self.speed or "default")
                    case "get_speaker" | "speaker":
                        print(self.speaker or "default")
                    case "set_speed":
                        value = float(params[1]) if len(params) > 1 else None

                        if value is None:
                            value = input(
                                f"Possible values: {self.speeds_list} or 'default'. Write speed value: "
                            )
                            value = float(value)
                        if not value in self.speeds_list:
                            print("Incorrect, try later")
                        else:
                            self.speed = value
                            print("Successfully changed")
                    case "set speaker":
                        value = params[1] if len(params) > 1 else None

                        if value is None:
                            value = input(
                                f"Possible values: {self.speakers_list} or 'default'. Write speed value: "
                            )
                        if not value in self.speakers_list:
                            print("Incorrect, try later")
                        else:
                            self.speaker = value
                            print("Successfully changed")
                    case "reset to defaults":
                        self.speaker = None
                        self.speed = None
                    case "exit":
                        print("Exiting...")
                        break
        except KeyboardInterrupt:
            print("Extra Exiting...")


if __name__ == "__main__":
    try:
        ca = ConsoleApp()
        ca.start()
    finally:
        free_resources()
