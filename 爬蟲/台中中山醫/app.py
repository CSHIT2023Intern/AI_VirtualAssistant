import requests
from bs4 import BeautifulSoup

url = "http://web.csh.org.tw/web/doctor/?page_id=2401"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

科連結列表 = soup.select(".sub-menu li a")
with open("doctor_info1.txt", "w", encoding="utf-8") as file:
    for a in 科連結列表:
        連結 = a["href"]
        response_科 = requests.get(連結)
        soup_科 = BeautifulSoup(response_科.content, "html.parser")
        科名字 = a.text.strip()

        #file.write(f"連結: {連結}\n")  # 寫入連結到檔案中

        醫生陣容連結 = soup_科.select(".entry-content p a, .entry-content h4 a")  # 選取所有 <a> 標籤

        if 醫生陣容連結:  # 檢查是否找到連結
            for doc_link in 醫生陣容連結:
                doc_name = doc_link.text.strip()
                doc_url = doc_link["href"]
                #file.write(f" {科名字}\n")  # 寫入科名字到檔案中

                #file.write(f" {doc_name}\n")  # 寫入醫生名字到檔案中
                #file.write(f"醫生連結: {doc_url}\n")  # 寫入醫生連結到檔案中

                # 現在進入醫生的頁面，抓取專長
                response_doc = requests.get(doc_url)
                soup_doc = BeautifulSoup(response_doc.content, "html.parser")
                專長 = soup_doc.select_one("td:contains('專長')")  # 選取含有 '專長' 的 td 標籤
                if 專長:
                 #   file.write(f"{專長.text}\n")  # 寫入醫生專長到檔案中
                  file.write(f"UPDATE `醫院` SET `科別`={科名字},`醫生姓名`='{doc_name}',`專長`='{專長.text}',`掛號網址`='0',`看診查詢`='1',`取消掛號`='2' WHERE 1;\n") 
        file.write("\n")  # 寫入空行分隔不同的醫生資訊
