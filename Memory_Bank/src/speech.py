import wave
import requests
import time
import base64
from keybert import KeyBERT
from pyaudio import PyAudio, paInt16

framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2bytes
FILEPATH = 'temp.wav'

base_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
APIKey = "e4ZDrNDQ0oG1fLbGhoKy8iCA"
SecretKey = "BtkH9bZFw3zuVOsYea7CvAlODV3GvI8T"

HOST = base_url % (APIKey, SecretKey)


def getToken(host):
    res = requests.post(host)
    return res.json()['access_token']

def getBuiltInToken():
    return getToken(HOST)


def save_wave_file(filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()


def my_record():
    pa = PyAudio()
    stream = pa.open(
        format=paInt16,
        channels=channels,
        rate=framerate,
        input=True,
        frames_per_buffer=num_samples,
    )
    my_buf = []
    # count = 0
    t = time.time()
    print('start recording...')

    while time.time() < t + 10:  # 秒
        string_audio_data = stream.read(num_samples)
        my_buf.append(string_audio_data)
    print('end recording.')
    save_wave_file(FILEPATH, my_buf)
    stream.close()


def get_audio(file):
    with open(file, 'rb') as f:
        data = f.read()
    return data


def speech2text(speech_data, token, dev_pid=1537):
    FORMAT = 'wav'
    RATE = '16000'
    CHANNEL = 1
    CUID = '*******'
    SPEECH = base64.b64encode(speech_data).decode('utf-8')

    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid,
    }

    url = 'https://vop.baidu.com/server_api'
    headers = {'Content-Type': 'application/json'}
    # r=requests.post(url,data=json.dumps(data),headers=headers)
    print('recognizing...')
    r = requests.post(url, json=data, headers=headers)
    Result = r.json()
    if 'result' in Result:
        return Result['result'][0]
    else:
        return Result


def keywordextraction(doc):
    kw_model = KeyBERT()
    result_numbers = len(doc) // 15
    if result_numbers < 3:
        result_numbers = 3
    keywords = kw_model.extract_keywords(
        doc,
        keyphrase_ngram_range=(1, 2),
        use_mmr=True,
        diversity=0.7,
        top_n=result_numbers,
    )
    return keywords


if __name__ == '__main__':
    flag = input("begin to record?(y/n)")
    while flag.lower() == 'y':
        devpid = 1737
        my_record()
        TOKEN = getToken(HOST)
        speech = get_audio(FILEPATH)
        result = speech2text(speech, TOKEN, int(devpid))
        print(result)
        print("keywords:")
        print(keywordextraction(result))
        flag = input('Continue?(y/n):')
