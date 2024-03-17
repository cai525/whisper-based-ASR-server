import logging
import time
from typing import Any, List, Dict

import numpy as np
import torch

from src.asr import utils, whisper_model
from src.asr.type import WhisperMode, WhisperModel, SPEECH_ARRAY_INDEX, LANG


class TranscribeConfig:

    def __init__(self,
                 inputs: List[str] = [],
                 lang: LANG = "en",
                 prompt: str = "",
                 whisper_mode: str = WhisperMode.WHISPER.value,
                 openai_rpm: int = 3,
                 whisper_model: str = WhisperModel.SMALL.value,
                 model_path: str = "",
                 vad: bool = True,
                 device: bool = "cpu") -> None:
        """
        Initialize the Transcribe object.
        
        Args:
            inputs (list, optional): List of filenames containing audio files. Defaults to [].
            lang (str, optional): Language of the source audio. Defaults to "en".
            prompt (str, optional): Initial prompt to feed into the whisper model. Defaults to "".
            whisper_mode (str, optional): Whisper inference mode. Options are "whisper" (run whisper locally) 
                                          or "openai" (use OpenAI API). Defaults to WhisperMode.WHISPER.value.
            openai_rpm (int, optional): OpenAI Whisper API requests per minute. Defaults to 3.
            whisper_model (str, optional): Whisper model to use. Defaults to WhisperModel.SMALL.value.
            model_path (str, optional): Path to save the model file. Defaults to "".
            vad (bool, optional): Enable voice activity detection. Defaults to True.
            device (str, optional): Device to use for inference. Options are "cpu" or "cuda". Defaults to "cpu".
        """
        assert isinstance(inputs, list)
        self.inputs = inputs
        self.lang = lang
        self.prompt = prompt
        self.whisper_mode = whisper_mode
        self.openai_rpm = openai_rpm
        self.whisper_model = whisper_model
        self.model_path = model_path
        self.vad = vad
        self.device = device


class Transcribe:

    def __init__(self, args: TranscribeConfig):
        self.args = args
        self.sampling_rate = 16000
        self.whisper_model = None
        self.vad_model = None
        self.detect_speech = None

        tic = time.time()
        if self.whisper_model is None:
            if self.args.whisper_mode == WhisperMode.WHISPER.value:
                self.whisper_model = whisper_model.WhisperModel(self.sampling_rate)
                self.whisper_model.load(self.args.whisper_model, self.args.device,
                                        self.args.model_path)
            elif self.args.whisper_mode == WhisperMode.OPENAI.value:
                self.whisper_model = whisper_model.OpenAIModel(self.args.openai_rpm,
                                                               self.sampling_rate)
                self.whisper_model.load()
            elif self.args.whisper_mode == WhisperMode.FASTER.value:
                self.whisper_model = whisper_model.FasterWhisperModel(self.sampling_rate)
                self.whisper_model.load(self.args.whisper_model, self.args.device, self.args.model_path)
        logging.info(f"Done Init model in {time.time() - tic:.1f} sec")

    def run(self) -> List[str]:
        ret_list = []
        for input in self.args.inputs:
            logging.info(f"Transcribing {input}")
            audio = utils.load_audio(input, sr=self.sampling_rate)
            speech_array_indices = self._detect_voice_activity(audio)
            transcribe_results = self._transcribe(input, audio, speech_array_indices)
            ret = self._draw_text(transcribe_results)
            ret_list.append(ret)
        return ret_list

    def _detect_voice_activity(self, audio) -> List[SPEECH_ARRAY_INDEX]:
        """Detect segments that have voice activities"""
        if self.args.vad == "0" or self.args.whisper_mode == WhisperMode.FASTER.value:
            return [{"start": 0, "end": len(audio)}]

        tic = time.time()
        if self.vad_model is None or self.detect_speech is None:
            # torch load limit https://github.com/pytorch/vision/issues/4156
            torch.hub._validate_not_a_forked_repo = lambda a, b, c: True
            self.vad_model, funcs = torch.hub.load(repo_or_dir="snakers4/silero-vad",
                                                   model="silero_vad",
                                                   trust_repo=True)

            self.detect_speech = funcs[0]

        speeches = self.detect_speech(audio, self.vad_model, sampling_rate=self.sampling_rate)

        # Remove too short segments
        speeches = utils.remove_short_segments(speeches, 1.0 * self.sampling_rate)

        # Expand to avoid to tight cut. You can tune the pad length
        speeches = utils.expand_segments(speeches, 0.2 * self.sampling_rate,
                                         0.0 * self.sampling_rate, audio.shape[0])

        # Merge very closed segments
        speeches = utils.merge_adjacent_segments(speeches, 0.5 * self.sampling_rate)

        logging.info(f"Done voice activity detection in {time.time() - tic:.1f} sec")
        return speeches if len(speeches) > 1 else [{"start": 0, "end": len(audio)}]

    def _transcribe(
        self,
        input: str,
        audio: np.ndarray,
        speech_array_indices: List[SPEECH_ARRAY_INDEX],
    ) -> List[Any]:
        tic = time.time()
        res = (self.whisper_model.transcribe(audio, speech_array_indices, self.args.lang,
                                             self.args.prompt)
               if self.args.whisper_mode == WhisperMode.WHISPER.value or self.args.whisper_mode
               == WhisperMode.FASTER.value else self.whisper_model.transcribe(
                   input, audio, speech_array_indices, self.args.lang, self.args.prompt))

        logging.info(f"Done transcription in {time.time() - tic:.1f} sec")
        return res

    def _draw_text(self, ret_list: List[Dict[str, Any]]):
        if self.args.whisper_mode == WhisperMode.FASTER.value:
            ret = " ".join([ret.text for ret in ret_list[0]["segments"]])
        else:
            ret = " ".join([ret["text"] for ret in ret_list])
        return ret
