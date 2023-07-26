import threading
from flask import Flask, request, jsonify, render_template
from collections import defaultdict
import openai
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__, static_url_path='/static')

# 建立一個簡單的內存儲存來保存會話歷史
memory = defaultdict(list)

openai.api_type = "azure"
openai.api_base = "https://cshitinternopenai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

# Replace "YOUR_OPENAI_API_KEY" with your actual OpenAI API key
openai.api_key = "0be4adcd512d4b09b7e44d50325f4bf9"

# Replace "YOUR_SPEECH_KEY" and "YOUR_SPEECH_REGION" with your actual Speech API key and region
speech_key = "c9d3e6d440214af3bc175d4c31809a44"
speech_region = "eastasia"

# 设置中文语言和声音样式
speech_language = "zh-CN"
voice_name = "en-US-JennyNeural"

@app.route('/')
def home():
    return render_template('your_file_name.html')


@app.route('/synthesize_audio', methods=['POST'])
def synthesize_audio():
    text = request.form['text']
    voice_name = request.form['voice_name']

    # 使用 Azure 文字转语音服务生成语音
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = voice_name

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()

    # 保存生成的语音文件
    output_file = 'static/output.wav'
    with open(output_file, 'wb') as f:
        f.write(result.audio_data)

    # 返回语音文件的URL
    audio_url = "/static/output.wav"
    return jsonify({'audio_url': audio_url})



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

            # 取得助手的回應並顯示在訊息框中
            assistant_reply = response['choices'][0]['message']['content'].strip()
            memory[session_id].append({"role": "user", "content": prompt})
            memory[session_id].append({"role": "assistant", "content": assistant_reply})
            return jsonify({'response': assistant_reply})
        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})
    

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    speech_key = "c9d3e6d440214af3bc175d4c31809a44"
    speech_region = "eastasia"

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=speech_region
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
        return jsonify({'transcript': '沒有接收到講話的聲音喔!'})
    elif result.reason == speechsdk.ResultReason.Canceled:
        return jsonify({'transcript': 'Speech recognition canceled: {}'.format(result.cancellation_details.reason)})
    else:
        return jsonify({'transcript': 'Error during speech recognition'})

if __name__ == '__main__':
    app.run(debug=True)