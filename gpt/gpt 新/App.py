from flask import Flask, request, jsonify, render_template
from collections import defaultdict
import openai
import azure.cognitiveservices.speech as speechsdk
import mysql.connector
app = Flask(__name__, static_url_path='/static')

# 建立一個簡單的內存儲存來保存會話歷史
memory = defaultdict(list)

openai.api_type = "azure"
openai.api_base = "https://cshitinternopenai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

# Azure Open AI Key
openai.api_key = "0be4adcd512d4b09b7e44d50325f4bf9"

# 語音  Azure Key %% Region
speech_key = "c9d3e6d440214af3bc175d4c31809a44"
speech_region = "eastasia"

@app.route('/')
def home():
    return render_template('your_file_name.html')

#文本轉語音---------------------------------------------------------------------------------------------
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


# 資料庫連線--------------------------------------------------------------------------------------------
cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='醫院資料'
)

# 建立游標物件
cursor = cnx.cursor()

# 查詢科別表中的所有科別名稱作為註記詞
cursor.execute("SELECT 科別名稱 FROM 科別")
keywords = [row[0] for row in cursor.fetchall()]

# 輸入Chat gpt一串產出對話
conversation = "查詢一般內科"  # Update the conversation prompt here

# 關閉游標和資料庫連線
cursor.close()
cnx.close()

# 聊天Open AI -------------------------------------------------------------------------------------------
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
            # Check if the user input matches the format "查詢科別名稱的醫師"
            if prompt.startswith("查詢") and "的" in prompt:
                # Extract the department name and doctor name from the user input
                department_and_doctor = prompt[2:]
                department_name, doctor_name = department_and_doctor.split("的")

                # Connect to the database
                cnx = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='醫院資料'
                )

                # Create a cursor object
                cursor = cnx.cursor()

                # Build the WHERE conditions for the database query
                where_conditions = f"科別名稱 = '{department_name}' AND 醫師姓名 = '{doctor_name}'"

                # Execute the SQL query
                query = f'''
                SELECT DISTINCT 科別.科別名稱, 醫師.醫師姓名, 醫師.專長
                FROM 科別
                INNER JOIN 科別_醫師 ON 科別.科別ID = 科別_醫師.科別ID
                INNER JOIN 醫師 ON 科別_醫師.醫師ID = 醫師.醫師ID
                WHERE {where_conditions};
                '''
                cursor.execute(query)

                # Fetch the query results
                results = cursor.fetchall()

                # Close the cursor and database connection
                cursor.close()
                cnx.close()

                if results:
                    # Build the response based on the database query results
                    response = "\n".join([f"{i + 1}. {row[0]} {row[1]} {row[2]}" for i, row in enumerate(results)])
                    return jsonify({'response': response})
                else:
                    return jsonify({'response': f"No data found for '{doctor_name}' in '{department_name}' department."})

            # Check if the user input matches the format "查詢科別名稱"
            elif prompt.startswith("查詢"):
                # Extract the department name from the user input
                department_name = prompt[2:]

                # Connect to the database
                cnx = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='醫院資料'
                )

                # Create a cursor object
                cursor = cnx.cursor()

                # Build the WHERE conditions for the database query
                where_conditions = f"科別名稱 = '{department_name}'"

                # Execute the SQL query
                query = f'''
                SELECT DISTINCT 科別.科別名稱, 醫師.醫師姓名, 醫師.專長
                FROM 科別
                INNER JOIN 科別_醫師 ON 科別.科別ID = 科別_醫師.科別ID
                INNER JOIN 醫師 ON 科別_醫師.醫師ID = 醫師.醫師ID
                WHERE {where_conditions};
                '''
                cursor.execute(query)

                # Fetch the query results
                results = cursor.fetchall()

                # Close the cursor and database connection
                cursor.close()
                cnx.close()

                if results:
                    # Build the response based on the database query results
                    response = "\n".join([f"{i + 1}. {row[0]} {row[1]} {row[2]}" for i, row in enumerate(results)])
                    return jsonify({'response': response})
                else:
                    return jsonify({'response': f"No data found for '{department_name}' department."})

            # If the user input does not match any format, proceed with OpenAI chatbot response
            # 從 memory 中取出先前的訊息
            previous_messages = memory[session_id]

            messages = [
                {"role": "system", "content": "你是一名中山附醫AI醫療助理。您可以提供有關健康和醫療問題的有用且準確的信息。當回答醫療問題時，請提醒使用者僅供參考，尋求專業醫療建議。醫療建議請準確精準提供以下科別一般外科, 乳房甲狀腺外科, 兒童心臟科, 兒童急診科, 兒童感染科, 兒童神經科, 兒童腎臟科, 兒童腸胃科, 兒童血液腫瘤科, 兒童過敏免疫風濕科, 內分泌及遺傳代謝科, 內分泌科, 大腸肛門外科, 婦女泌尿暨骨盆重建科, 婦癌科, 小兒外科, 心臟內科, 心臟外科, 感染科, 整形外科, 新生兒科, 海扶刀中心, 生殖醫學科"},
            ] + previous_messages + [{"role": "user", "content": prompt}]

            response = openai.ChatCompletion.create(
                engine="CSHITIntern",
                messages=messages
            )

            # 取得助手的回應並顯示在訊息框中
            assistant_reply = response['choices'][0]['message']['content'].strip()
            memory[session_id].append({"role": "user", "content": prompt})
            memory[session_id].append({"role": "assistant", "content": assistant_reply})
             # Connect to the database
            cnx = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='醫院資料'
            )

            # Create a cursor object
            cursor = cnx.cursor()

            # Prepare the insert SQL statement
            insert_sql = "INSERT INTO 對話歷史 (用戶_問題, AI_回復) VALUES (%s, %s)"
            data_tuple = (prompt, assistant_reply)

            # Execute the SQL statement
            cursor.execute(insert_sql, data_tuple)

            # Commit the transaction
            cnx.commit()

            # Close the cursor and database connection
            cursor.close()
            cnx.close()
           
            return jsonify({'response': assistant_reply})

        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})
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

#語音辨識-語音轉文字-----------------------------------------------------------------------------------
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