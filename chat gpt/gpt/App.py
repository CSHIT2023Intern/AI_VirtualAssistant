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
subscription_key = "c9d3e6d440214af3bc175d4c31809a44"
region = "eastasia"
def text_to_speech(text):
    subscription_key = os.environ.get('SPEECH_KEY')
    region = os.environ.get('SPEECH_REGION')

    if not subscription_key or not region:
        return None

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region
        )

        speech_config.speech_synthesis_voice_name = 'zh-CN-XiaoxiaoNeural'
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data_stream.get_url()
        else:
            return None

    except Exception as e:
        print("Error during speech synthesis:", e)
        return None

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

            # 使用 Azure Text-to-Speech API 進行語音合成並獲取音頻 URL
            assistant_reply = response['choices'][0]['message']['content'].strip()
            audio_url = text_to_speech(assistant_reply)

            # 將音頻 URL 返回給前端
            return jsonify({'response': assistant_reply, 'audio_url': audio_url})
        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    subscription_key = os.environ.get('SPEECH_KEY')
    region = os.environ.get('SPEECH_REGION')

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
        return jsonify({'transcript': 'No speech detected'})
    elif result.reason == speechsdk.ResultReason.Canceled:
        return jsonify({'transcript': 'Speech recognition canceled: {}'.format(result.cancellation_details.reason)})
    else:
        return jsonify({'transcript': 'Error during speech recognition'})

if __name__ == '__main__':
    app.run(debug=True)
