from flask import Flask, request, jsonify, render_template
from collections import defaultdict
import openai
import azure.cognitiveservices.speech as speechsdk
import mysql.connector
import threading
import time
app = Flask(__name__, static_url_path='/static')

memory = defaultdict(list)
memory_lock = threading.Lock()

# Function to clear the memory dictionary periodically
def clear_memory():
    while True:
        print("Clearing memory...")
        with memory_lock:
            memory.clear()
        time.sleep(600)  # Clear the memory every 5 seconds

# Start the background thread to clear memory
memory_clear_thread = threading.Thread(target=clear_memory)
memory_clear_thread.daemon = True  # The thread will exit when the main program exits
memory_clear_thread.start()


openai.api_type = "azure"
openai.api_base = "https://cshitinterngpt4.openai.azure.com/"
openai.api_version = "2023-03-15-preview"
# 前端接收api_key------------------------------------------------------------------------------------
# Azure Open AI Key
openai.api_key = "71e9950da8c34bc7805520df08984c21"  # 這是您的API Key

@app.route('/getApiKey')
def get_api_key():
    return jsonify({"apiKey": openai.api_key})

# 前端接收 語音  Azure Key && Region------------------------------------------------------------------------------------
speech_key = "c9d3e6d440214af3bc175d4c31809a44"
speech_region = "eastasia"

@app.route('/getSpeechConfig')
def get_speech_config():
    # 為了安全性，只返回region，不要返回key
     return jsonify(apiKey=speech_key, region=speech_region)

@app.route('/')
def home():
    return render_template('your_file_name.html')
@app.route('/ai')
def ai():
    return render_template('ai.html')
@app.route('/caa')
def caa():
    return render_template('caa.html')


#文本轉語音---------------------------------------------------------------------------------------------------
@app.route('/synthesize_audio', methods=['POST'])
def synthesize_audio():
    text = request.form['text']
    
    # 直接設置語音樣式為預設值 var voice_name = "zh-CN-XiaoxiaoNeural";
    voice_name = "zh-CN-XiaoxiaoNeural";

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


# 資料庫連線--------------------------------------------------------------------------------------------------
cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='醫院資料'
)
cursor = cnx.cursor()
cursor.execute("SELECT 症狀名稱 FROM 科別_症狀")
keywords = [row[0] for row in cursor.fetchall()]

# 聊天Open AI ------------------------------------------------------------------------------------------------
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    prompt = data.get('prompt')
    api_key = request.headers.get('Authorization')
    session_id = request.headers.get('Session-Id')

    if not api_key:
        return jsonify({'error': 'Invalid request. Missing API key.'})

    if prompt:
        try:
            previous_messages = memory[session_id]

            messages = [
                {"role": "system", "content": "你是一名中山附醫AI醫療助理，一律顯示繁體中文。您可以提供有關健康和醫療問題的有用且準確的信息。"},
            ] + previous_messages + [{"role": "user", "content": prompt}]

            response = openai.ChatCompletion.create(
                engine="CSHInternGPT4-32K",
                messages=messages
            )

            assistant_reply = response['choices'][0]['message']['content'].strip()
            memory[session_id].append({"role": "user", "content": prompt})
            memory[session_id].append({"role": "assistant", "content": assistant_reply})

            # Check if the user's input contains a query for doctor names by specialty
            query_prefix = "查詢"
            doctor_suffix = "的醫師"

            if query_prefix in prompt and doctor_suffix in prompt:
                specialty_start = prompt.find(query_prefix)
                doctor_suffix_pos = prompt.find(doctor_suffix)

                if specialty_start != -1 and doctor_suffix_pos != -1:
                    specialty = prompt[specialty_start + len(query_prefix):doctor_suffix_pos]
                    specialty = specialty.strip()

                    # Now you can use the extracted specialty to query the database
                    cursor.execute("SELECT 醫師.醫師姓名, GROUP_CONCAT(專長.專長名稱 SEPARATOR '、') "
                                   "FROM 科別_醫師 "
                                   "JOIN 科別 ON 科別_醫師.科別ID = 科別.科別ID "
                                   "JOIN 醫師 ON 科別_醫師.醫師ID = 醫師.醫師ID "
                                   "JOIN 醫師_專長 ON 醫師.醫師ID = 醫師_專長.醫師ID "
                                   "JOIN 專長 ON 醫師_專長.專長ID = 專長.專長ID "
                                   "WHERE 科別.科別名稱 = %s "
                                   "GROUP BY 醫師.醫師姓名", (specialty,))
                    doctor_info = cursor.fetchall()

                    if doctor_info:
                        suggested_doctors = "該科別的醫師及專長：\n"
                        for i, (doctor_name, specialties) in enumerate(doctor_info, start=1):
                            suggested_doctors += f"{i}.{doctor_name}醫師---專長為： {specialties}。\n"

                        assistant_reply = suggested_doctors
                    else:
                        assistant_reply = "暫無該科別的醫師資訊。"
            else:
                is_keyword = any(keyword in prompt for keyword in keywords)

                if is_keyword:
                    for keyword in keywords:
                        if keyword in prompt:
                            cursor.execute("SELECT 科別ID FROM 科別_症狀 WHERE 症狀名稱 = %s", (keyword,))
                            matched_departments = [row[0] for row in cursor.fetchall()]

                            if matched_departments:
                                suggested_departments = "建議看診科別為："
                                for i, department_id in enumerate(matched_departments, start=1):
                                    cursor.execute("SELECT 科別名稱 FROM 科別 WHERE 科別ID = %s", (department_id,))
                                    department_name = cursor.fetchone()[0]
                                    suggested_departments += f"\n{i}.{department_name}"

                                assistant_reply += "\n" + suggested_departments
                                break

            return jsonify({'response': assistant_reply})
        

        except Exception as e:
            return jsonify({'error': str(e)})

    return jsonify({'error': '無效的請求。 缺少提示。'})
# 資料庫對話歷史------------------------------------------------------------------------------------------------
@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    cnx = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='醫院資料'
    )

    cursor = cnx.cursor()

    query = "SELECT * FROM 對話歷史 ORDER BY 時間戳 DESC"
    cursor.execute(query)

    results = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify({'conversations': results})

#語音辨識-語音轉文字--------------------------------------------------------------------------------------------
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