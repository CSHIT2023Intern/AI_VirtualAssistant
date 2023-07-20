from flask import Flask, request, jsonify, render_template
from collections import defaultdict
import openai
import os
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__, static_url_path='/static')

# 建立一個簡單的內存儲存來保存會話歷史
memory = defaultdict(list)

openai.api_type = "azure"
openai.api_base = "https://cshitinternopenai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"
openai.api_key  =  "0be4adcd512d4b09b7e44d50325f4bf9"

@app.route('/')
def home():
    return render_template('your_file_name.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    prompt = data.get('prompt')
    api_key = request.headers.get('Authorization')
    session_id = request.headers.get('Session-Id')  # 獲取使用者或會話的唯一識別碼

    if not api_key:
        return jsonify({'error': 'Invalid request. Missing API key.'})

    if prompt:
        try:
            # 從 memory 中取出先前的訊息
            previous_messages = memory[session_id]

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
            ] + previous_messages + [{"role": "user", "content": prompt}]

            response = openai.ChatCompletion.create(
                engine="CSHITIntern",
                messages=messages
            )

            # 將此次使用者的訊息及 AI 的回應保存到 memory 中
            memory[session_id].append({"role": "user", "content": prompt})
            memory[session_id].append({"role": "assistant", "content": response['choices'][0]['message']['content'].strip()})

            return jsonify(response['choices'][0]['message']['content'].strip())
        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    subscription_key = os.environ.get('SPEECH_KEY')  #利用環境變數的方式收SPEECH_KEY。
    region = os.environ.get('SPEECH_REGION')     #利用環境變數的方式收SPEECH_KEY。

    speech_config = speechsdk.SpeechConfig(
        subscription=subscription_key,
        region=region
    )
    speech_config.speech_recognition_language = "zh-TW"  # 設置語音辨識語言為中文 (台灣)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return jsonify({'transcript': result.text})
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return jsonify({'transcript': '沒有收到講話的語音'})
    elif result.reason == speechsdk.ResultReason.Canceled:
        return jsonify({'transcript': 'Speech recognition canceled: {}'.format(result.cancellation_details.reason)})
    else:
        return jsonify({'transcript': 'Error during speech recognition'})

if __name__ == '__main__':
    app.run(debug=True)
