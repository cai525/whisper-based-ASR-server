import os
import sys

os.chdir("..")
sys.path.append(os.getcwd())

from src.asr.transcribe import TranscribeConfig, Transcribe, WhisperModel, WhisperMode

path = ["/home/cpf/asr/audioRecord/test/trump.wav"]

config = TranscribeConfig(
    inputs=path,
    lang="en",
    whisper_model=WhisperModel.MEDIUM.value,
    whisper_mode=WhisperMode.FASTER.value,
    model_path="/home/cpf/asr/whisper_models/faster-whisper/medium"
)
model = Transcribe(config)
ret_list = model.run()
ret = ret_list[0]
print(ret)
