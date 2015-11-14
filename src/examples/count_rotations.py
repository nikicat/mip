import argparse
import logging
import random
import subprocess
import time
import queue

import mippy
import speech_recognition as sr

class Recognizer:
    def __init__(self):
        self.q = queue.Queue()
        def recognize(r, audio):
            try:
                print('> ', end='', flush=True)
                text = r.recognize_google(audio, language='ru-RU')
                print(text)
                self.last_phrase = text.lower().replace(' ', '')
                self.q.put(self.last_phrase)
            except Exception as e:
                logging.debug("exception while recognizing: {}".format(e))

        r = sr.Recognizer()
        r.phrase_threshold = 0.1
        r.pause_threshold = 0.5
        source = sr.Microphone()
        with source as s:
            print("adjusting for ambient noise")
            r.adjust_for_ambient_noise(s)
        print("done adjusting")
        r.listen_in_background(source, recognize)

    def get_phrases(self):
        while True:
            yield self.q.get() 

    def get_phrase(self):
        self.q.queue.clear()
        return self.q.get()

ANGLE90=100
DISTANCE=0.2

def follow_commands(mip, rotations, r):
    for phrase in r.get_phrases():
        print('got phrase: {}'.format(phrase))
        if 'лев' in phrase:
            mip.turnByAngle(-ANGLE90)
        if 'право' in phrase:
            mip.turnByAngle(ANGLE90)
        if 'вперед' in phrase or 'перевод' in phrase or 'прямо' in phrase:
            mip.distanceDrive(DISTANCE)
        if 'назад' in phrase:
            mip.distanceDrive(-DISTANCE)
        if 'игра' in phrase:
            play_count(mip, rotations, r)
        else:
            print('unknown phrase, skipping')


def play_count(mip, rotations, recog):
    result = 0
    for rounds in args.rotations:
        result += rounds
        logging.debug("rotating by {} rounds {}".format(rounds, "left" if rounds > 0 else 'right'))
        for r in range(abs(rounds)):
            mip.turnByAngle(angle=440 * (1 if rounds > 0 else -1))
    print("result should be {}".format(result))

    answer = 0
    if 1:
        try:
            answer = int(recog.get_phrase())
            logging.debug("listened answer is {}".format(answer))
        except:
            logging.debug("answer is not a number")
    elif 0:
        # Yandex Speech Kit
        out = subprocess.check_output(["sh", "-c", "timeout --foreground 3 ffmpeg -loglevel quiet  -f alsa -i pulse -acodec libspeex -y speech-mmpc.ogg; curl -s -X POST --data-binary @speech-mmpc.ogg 'https://asr.yandex.net/asr_xml?uuid=6c88f5de8ae711e5a6a300265eeda1db&key=a4842bb7-929b-4d4d-9982-4a1eff599563&topic=queries&lang=ru-RU' -H 'Content-Type: audio/x-speex' | grep variant | head -1 | sed -r 's/.*>(.+)<.*/\\1/'"])[:-1].decode('utf-8')
        logging.debug("answer from Yandex.SpeechKit: {0}".format(out))
        answer = int(out.replace('- ', '-').split()[0])
        logging.debug("listened answer is {}".format(answer))
    elif 0:
        # Claps
        print("clap the answer now")

        mip.clapEnable(0x1)
        #clapStatus = mip.requestClapStatus()
        # Now detect claps
        totalclaps = 0
        timeouts = 0
        while timeouts < 5:
            claps = mip.getClapTimes()
            logging.debug("detected {} claps".format(claps))
            if claps == 0:
                timeouts += 1
            totalclaps += claps

        logging.debug("total claps: {}".format(totalclaps))
        answer = totalclaps

    if answer == result:
        print("You are right!")
        mip.playSound(16) # Ohaye
    else:
        print("You are stupid! The answer is {}".format(result))
        mip.playSound(55) # Cry

if __name__ == '__main__':
    random.seed()
    rotations = [random.randint(0, 10)]
    parser = argparse.ArgumentParser(description='MiP counter.')
    mippy.add_arguments(parser)
    parser.add_argument('--rotations', '-r', dest='rotations', type=int, nargs='+', default=rotations, help='number of rotations')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("rotating by {} rounds".format(args.rotations))
    gt = mippy.GattTool(args.adaptor, args.device)
    mip = mippy.Mip(gt)

    r = Recognizer()
    follow_commands(mip, args.rotations, r)


