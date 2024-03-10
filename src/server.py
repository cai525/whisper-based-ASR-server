import logging
import time
import os
import sys
from typing import List, Type

os.chdir("../")
sys.path.append(os.getcwd())

import tornado
import tornado.websocket

from src.asr.transcribe import TranscribeConfig, Transcribe, WhisperModel


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
            model_path="/home/cpf/asr/autocut/archive/model",
        )
        self.model = Transcribe(asr_config)
        logging.info("<INFO>: Finish load whisper model")


class webRTCHandler(tornado.websocket.WebSocketHandler):

    def open(self, *args, **kwargs):
        logging.info("<INFO>: build connection with {ip}".format(ip=self.request.remote_ip))
        # add users when connection is established
        assert isinstance(self.application, WebRTCApplication)
        self.application.users.add(self)

    def on_message(self, message):
        # get sender information
        sender = str(self.request.remote_ip)
        arrive_time = str(int(time.time()))

        # TODO: The below method  is inefficient, causing extra IO. Try to optimize it
        audio_name = "./audio/" + sender + "_" + arrive_time
        with open(audio_name + ".ogg", "wb") as f:  # save .wav file
            f.write(message)
        os.system("ffmpeg -i {name}.ogg {name}.wav \n \
                  rm {name}.ogg".format(name=audio_name))

        self.write_message(message, binary=True)
        # text = "Hello World"
        text = self._f_asr(audio_name + ".wav")
        self.write_message(text)

    def on_close(self):
        assert isinstance(self.application, WebRTCApplication)
        self.application.users.remove(self)

    def check_origin(self, origin):
        # allow cross-domain access
        return True

    def _f_asr(self, path: str):
        assert isinstance(self.application, WebRTCApplication)
        model = self.application.model
        model.args.inputs = [path]
        logging.info("<INFO>: begin transcribing...")
        ret_list = model.run()
        ret = ret_list[0]
        return ret


if __name__ == '__main__':
    # log setting
    logging.basicConfig(level=logging.INFO)
    logging.info("<INFO>: Starting the server...")
    # configure the server
    app = WebRTCApplication([
        (r"/", webRTCHandler),
    ], debug=True)

    # start the server
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.current().start()
