import mysql.connector

# 連接到資料庫
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

# 輸入一串對話語言
conversation = " 對不起，中山醫學大學附設醫院目前沒有設置專門的大腸直腸外科科別。建議您可向一般外科或消化內科尋求協助，醫生將根據您的病情進行評估與治療。如果需要進一步的協助，您可以詢問醫院的相關醫療人員。非常抱歉給您帶來困擾，謝謝您的理解。"

# 尋找輸入對話語言中的關鍵字
matched_keywords = [keyword for keyword in keywords if keyword in conversation]

# 若有找到關鍵字，則使用這些關鍵字進行科別查詢
if matched_keywords:
    # 建立查詢的WHERE條件，使用OR來組合多個關鍵字
    where_conditions = ' OR '.join([f"科別名稱 = '{keyword}'" for keyword in matched_keywords])

    # 執行SQL查詢
    query = f'''
    SELECT DISTINCT 科別.科別名稱, 醫師.醫師姓名, 醫師.專長
    FROM 科別
    INNER JOIN 科別_醫師 ON 科別.科別ID = 科別_醫師.科別ID
    INNER JOIN 醫師 ON 科別_醫師.醫師ID = 醫師.醫師ID
    WHERE {where_conditions};
    '''
    cursor.execute(query)

    # 擷取查詢結果
    results = cursor.fetchall()

    # 顯示結果
    if results:
        print("查詢結果:")
        for row in results:
            department_name = row[0]
            doctor_name = row[1]
            specialty = row[2]
            print(f"{department_name}:{doctor_name}  專長:{specialty}\n")
    else:
        print("沒有符合條件的結果。")

else:
    print("沒有找到關鍵字，請重新輸入對話語言或檢查註記詞。")

# 關閉游標和資料庫連線
cursor.close()
cnx.close()
