import logging
import time
import os
import sys
from typing import List, Type

os.chdir("../")
sys.path.append(os.getcwd())

import tornado
import tornado.websocket

from src.asr.transcribe import TranscribeConfig, Transcribe, WhisperModel, WhisperMode
from src.llm.chat import ChatBot


class WebRTCApplication(tornado.web.Application):

    def __init__(self, handlers, **settings) -> None:
        super().__init__(handlers, **settings)
        # Contain all the connections
        self.users = set()
        # members about ASR module
        asr_config = TranscribeConfig(
            inputs=[],
            lang="zh",
            whisper_model=WhisperModel.MEDIUM.value,
            whisper_mode=WhisperMode.FASTER.value,
            model_path="/home/cpf/asr/whisper_models/faster-whisper/medium",
            prompt="以下是普通话的句子:")
        self.model = Transcribe(asr_config)
        with open("./archive/private/llm/api_key", "r") as f:
            self.api_key = f.read()

        with open("./archive/private/llm/secret_key", "r") as f:
            self.secret_key = f.read()
        logging.info("<INFO>: Finish load whisper model")


class webRTCHandler(tornado.websocket.WebSocketHandler):

    def open(self, *args, **kwargs):
        logging.info("<INFO>: build connection with {ip}".format(ip=self.request.remote_ip))
        # add users when connection is established
        assert isinstance(self.application, WebRTCApplication)
        self.application.users.add(self)
        self.chat_bot = ChatBot(self.application.api_key, self.application.secret_key)

    def on_message(self, message):
        # get sender information
        sender = str(self.request.remote_ip)
        arrive_time = str(int(time.time()))

        # TODO: The below method  is inefficient, causing extra IO. Try to optimize it
        audio_name = "./archive/audio/" + sender + "_" + arrive_time
        with open(audio_name + ".ogg", "wb") as f:  # save .wav file
            f.write(message)
        os.system("ffmpeg -i {name}.ogg {name}.wav \n \
                  rm {name}.ogg".format(name=audio_name))

        self.write_message(message, binary=True)
        # text = "Hello World"
        asr_res = self._f_asr(audio_name + ".wav")
        logging.info("<INFO>: asr result is {text}".format(text=asr_res))
        self.write_message(asr_res)

    def on_close(self):
        assert isinstance(self.application, WebRTCApplication)
        self.application.users.remove(self)
        logging.info("<INFO>: close connection with {ip}".format(ip=self.request.remote_ip))

    def check_origin(self, origin):
        # allow cross-domain access
        return True

    def _f_asr(self, path: str):
        assert isinstance(self.application, WebRTCApplication)
        model = self.application.model
        model.args.inputs = [path]
        logging.debug("<DEBUG>: begin transcribing...")
        ret_list = model.run()
        ret = ret_list[0]
        logging.debug("<DEBUG> Finish asr transcribing. Begin to modify by LLM")
        if self.chat_bot.round <= 0:
            with open("./archive/prompts/asr_zh_prompt", "r") as f:
                prompt = f.read()
        else:
            prompt = "下面是函数输入，即ASR模型翻译结果，请直接返回对应输出。"
        ret = prompt + "\n\"{content}\"".format(content=ret)
        ret = self.chat_bot.request(ret)
        return ret


if __name__ == '__main__':
    # log setting
    logging.basicConfig(level=logging.DEBUG)
    logging.info("<INFO>: Starting the server...")
    # configure the server
    app = WebRTCApplication([
        (r"/", webRTCHandler),
    ], debug=True)

    # start the server
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.current().start()
