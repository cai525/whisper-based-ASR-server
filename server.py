import io
import time
import os

import tornado
import tornado.websocket
from pydub import AudioSegment

import wave
import numpy as np

class webRTCServer(tornado.websocket.WebSocketHandler):
    users = set()

    def open(self, *args, **kwargs):
        # add users when connection is established
        self.users.add(self)

    def on_message(self, message):
        # get sender information
        sender = str(self.request.remote_ip)
        arrive_time = str(int(time.time()))
        # a bug occurs in the AudioSegment. 
        # bio = io.BytesIO()
        # bio.write(message)
        # audio = AudioSegment.from_file(bio, format="ogg")       # convert bytes to .ogg
        # wav_data = audio.export(format="wav").read()            # convert .ogg to .wav
        # with open("./audio/audio.wav", "wb") as wav_file:      # save .wav file
        #     wav_file.write(wav_data)
        
        # TODO: The below method  is inefficient, causing extra IO. Try to fix the
        # bugs above to optimize the conversion
        audio_name = "./audio/" + sender + "_" + arrive_time
        with open(audio_name + ".ogg", "wb") as f:      # save .wav file
            f.write(message)
        os.system("ffmpeg -i {name}.ogg {name}.wav \n \
                  rm {name}.ogg".format(name=audio_name))
        
        # broadcast when a message is received
        for user in self.users: 
            user.write_message(message, binary=True)

    def on_close(self):
        self.users.remove(self)

    def check_origin(self, origin):
        # allow cross-domain access
        return True


if __name__ == '__main__':
    # configure the server
    app = tornado.web.Application([
        (r"/", webRTCServer),
        ],
        debug=True
    )

    # start the server
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.current().start()