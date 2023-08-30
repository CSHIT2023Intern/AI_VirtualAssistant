import base64
from flask import Flask, request, jsonify, render_template
from collections import defaultdict
import openai
import azure.cognitiveservices.speech as speechsdk
import mysql.connector
import threading
import time

import pymysql
app = Flask(__name__, static_url_path='/static')

memory = defaultdict(list)
memory_lock = threading.Lock()

def clear_memory():
    while True:
        print("Clearing memory...")
        with memory_lock:
            memory.clear()
        time.sleep(600)  

memory_clear_thread = threading.Thread(target=clear_memory)
memory_clear_thread.daemon = True  # The thread will exit when the main program exits
memory_clear_thread.start()

openai.api_type = "azure"
openai.api_base = "https://cshitinterngpt4.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

# 前端接收api_key------------------------------------------------------------------------------------
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
            
            response = openai.ChatCompletion.create(engine="CSHInternGPT4-32K", messages=messages)
            assistant_reply = response['choices'][0]['message']['content'].strip()
            
            memory[session_id].append({"role": "user", "content": prompt})
            memory[session_id].append({"role": "assistant", "content": assistant_reply})

            # 查詢診斷代碼或診斷問題
            cursor.execute("SELECT 診斷代碼, 診斷問題 FROM QA")
            all_diagnosis_codes_and_questions = cursor.fetchall()

            # 檢查每個診斷代碼或診斷問題是否在輸入中
            matched_diagnosis = None
            for code, question in all_diagnosis_codes_and_questions:
                if code == prompt or question in prompt:
                    matched_diagnosis = (code, question)
                    break

            if matched_diagnosis:
                code, question = matched_diagnosis
                cursor.execute("SELECT 診斷說明 FROM QA WHERE 診斷代碼 = %s OR 診斷問題 = %s", (code, question))
                description_data = cursor.fetchone()

                response_data = {}
                suggested_departments = "請根據您的問題輸入正確的診斷代碼即可觀看問題，如：Q2.1、Q1.3.1"
                assistant_reply = "\n"+suggested_departments + "\n"+ question+"\n"

                if description_data:
                    description = description_data[0]
                    assistant_reply += description
                    response_data["response"] = assistant_reply
                else:
                    response_data['response'] = "找不到相關的診斷說明。"

                return jsonify(response_data)
            


            cursor.execute("SELECT 醫師姓名 FROM 醫師")
            all_doctor_names = [row[0] for row in cursor.fetchall()]

            # 檢查每個醫師姓名是否在輸入中  
            doctor_name = None
            for name in all_doctor_names:
                if name in prompt:
                    doctor_name = name
                    break

            if doctor_name:
                cursor.execute("SELECT 醫師圖 FROM 醫師 WHERE 醫師姓名 = %s", (doctor_name,))
                image_data = cursor.fetchone()

                cursor.execute(
                    "SELECT 科別.科別名稱, GROUP_CONCAT(專長.專長名稱 SEPARATOR '、') "
                    "FROM 醫師 "
                    "JOIN 科別_醫師 ON 醫師.醫師ID = 科別_醫師.醫師ID "
                    "JOIN 科別 ON 科別_醫師.科別ID = 科別.科別ID "
                    "JOIN 醫師_專長 ON 醫師.醫師ID = 醫師_專長.醫師ID "
                    "JOIN 專長 ON 醫師_專長.專長ID = 專長.專長ID "
                    "WHERE 醫師.醫師姓名 = %s "
                    "GROUP BY 醫師.醫師姓名", (doctor_name,)
                )
                doctor_info = cursor.fetchone()

                response_data = {}

                if image_data:
                    image_format = "jpg"
                    image_base64 = base64.b64encode(image_data[0]).decode('utf-8')
                    response_data["image_base64"] = image_base64

                if doctor_info:
                    department, specialties = doctor_info
                    response_data['response'] = f"醫師姓名：{doctor_name}。\n科別：{department}。\n專長：{specialties}。"

                if not response_data:
                    response_data['response'] = "找不到該醫生的資訊。"

                return jsonify(response_data)
            
            cursor.execute("SELECT 科別名稱 FROM 科別")
            all_specialties = [row[0] for row in cursor.fetchall()]

            # 檢查每個科別名稱是否在輸入中
            selected_specialty = None
            for specialty in all_specialties:
                if specialty in prompt:
                    selected_specialty = specialty
                    break

            if selected_specialty:
                cursor.execute(
                    "SELECT 醫師.醫師姓名, GROUP_CONCAT(專長.專長名稱 SEPARATOR '、') "
                    "FROM 科別_醫師 "
                    "JOIN 科別 ON 科別_醫師.科別ID = 科別.科別ID "
                    "JOIN 醫師 ON 科別_醫師.醫師ID = 醫師.醫師ID "
                    "JOIN 醫師_專長 ON 醫師.醫師ID = 醫師_專長.醫師ID "
                    "JOIN 專長 ON 醫師_專長.專長ID = 專長.專長ID "
                    "WHERE 科別.科別名稱 = %s "
                    "GROUP BY 醫師.醫師姓名", (selected_specialty,)
                )
                doctor_info = cursor.fetchall()

                if doctor_info:
                    suggested_doctors = f"在{selected_specialty}科別下的醫師及專長：\n"
                    for i, (doctor_name, doctor_specialties) in enumerate(doctor_info, start=1):
                        suggested_doctors += f"{i}. {doctor_name}醫師 - 專長為：{doctor_specialties}。\n"

                    assistant_reply = suggested_doctors
                else:
                    assistant_reply = f"暫無{selected_specialty}科別的醫師資訊。"
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
if __name__ == '__main__':
    
    app.run(debug=True)
