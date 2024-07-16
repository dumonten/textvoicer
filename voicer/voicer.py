import gc
import os
import shutil

import pyrubberband as pyrb
import simpleaudio as sa
import soundfile as sf
import torch
import torchaudio
import yaml
from loguru import logger

from utils.functions import generate_uuid

with open("./voicer/config.yml", "r") as file:
    config = yaml.safe_load(file)

url = config["url"]
model_type = config["model_type"]
model_id = config["model_id"]
language = config["language"]
curr_speaker = config["curr_speaker"]
speakers = config["speakers"]
sample_rate = config["sample_rate"]
put_accent = config["put_accent"]
put_yo = config["put_yo"]
device_type = config["device_type"]
device = torch.device(device_type)
num_model_threads = config["num_model_threads"]
model_store_file_path = config["model_store_file_path"]

temp_audio_folder_path = config["temp_audio_folder_path"]
clean_audio_folder = config["clean_audio_folder"]

if not os.path.exists(temp_audio_folder_path):
    os.makedirs(temp_audio_folder_path)
elif clean_audio_folder:
    for filename in os.listdir(temp_audio_folder_path):
        file_path = os.path.join(temp_audio_folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error("Failed to delete %s. Reason: %s" % (file_path, e))

torch.set_num_threads(num_model_threads)
torch._C._jit_set_profiling_mode(False)
torch.set_grad_enabled(False)

if not os.path.isfile(model_store_file_path):
    torch.hub.download_url_to_file(url, model_store_file_path)

model = torch.package.PackageImporter(model_store_file_path).load_pickle(
    "tts_models", "model"
)

model.to(device)


def get_speakers():
    global speakers
    return speakers


def get_speeds():
    return [0.75, 0.5, 1.0, 1.5, 2.0, 2.5]


def change_speed(file_path, speed):
    y, sr = sf.read(file_path)
    y_stretch = pyrb.time_stretch(y, sr, speed)
    sf.write(file_path, y_stretch, sr, format="wav")


def get_audio(text, speaker=None, speed=None):
    global curr_speaker, model, sample_rate, temp_audio_folder_path, put_accent, put_yo

    try:
        path_to_wav_audio = f"{temp_audio_folder_path}/{generate_uuid()}.wav"

        if speaker is not None:
            curr_speaker = speaker

        tts_audio = model.apply_tts(
            text=text,
            speaker=curr_speaker,
            sample_rate=sample_rate,
            put_accent=put_accent,
            put_yo=put_yo,
        )

        if tts_audio.ndim == 1:
            tts_audio = tts_audio.unsqueeze(0)

        torchaudio.save(
            path_to_wav_audio,
            tts_audio,
            sample_rate=sample_rate,
            bits_per_sample=16,
            format="wav",
            backend="soundfile",
        )

        change_speed(path_to_wav_audio, speed)

        del tts_audio
        gc.collect()
        return path_to_wav_audio
    except Exception as e:
        logger.error(
            f"Error occurred while converting text to audio. Probably incorrect language."
        )
        return None


def play_audio(path_to_wav_audio):
    try:
        if not os.path.exists(path_to_wav_audio):
            raise FileNotFoundError(f"File {path_to_wav_audio} not found")

        wave_obj = sa.WaveObject.from_wave_file(path_to_wav_audio)
        play_obj = wave_obj.play()
        play_obj.wait_done()  # Wait until the audio has finished playing

        os.remove(path_to_wav_audio)
    except Exception as e:
        logger.error(f"An error occurred while playing audio: {e}")
    finally:
        gc.collect()


def free_resources():
    global model
    del model
