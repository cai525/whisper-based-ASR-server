import time
import os

import tornado
import tornado.websocket

from src.asr.transcribe import TranscribeConfig, Transcribe, WhisperModel


def f_asr(path):
    config = TranscribeConfig(
        inputs=path,
        lang="en",
        whisper_model=WhisperModel.MEDIUM.value,
        model_path="/home/cpf/asr/autocut/archive/model/medium.pt",
    )
    model = Transcribe(config)
    ret_list = model.run()
    ret = ret_list[0]
    return ret


class webRTCServer(tornado.websocket.WebSocketHandler):
    users = set()

    def open(self, *args, **kwargs):
        # add users when connection is established
        self.users.add(self)

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

        # self.write_message(message, binary=True)
        text = f_asr(audio_name + ".wav")
        self.write_message(text)

    def on_close(self):
        self.users.remove(self)

    def check_origin(self, origin):
        # allow cross-domain access
        return True


if __name__ == '__main__':
    # configure the server
    app = tornado.web.Application([
        (r"/", webRTCServer),
    ], debug=True)

    # start the server
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.current().start()
