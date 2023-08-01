from selenium import webdriver
from bs4 import BeautifulSoup

# 使用 Chrome 瀏覽器
driver = webdriver.Chrome()

# 提取資訊並存成 txt 檔案
with open('output.txt', 'w', encoding='utf-8') as file:
    for doc_value in range(1, 41):  # 範圍包括從 1 到 41（但不包括 41）
        # 前往網址
        driver.get(f"https://www.csh.com.tw/division_group_doctor.php?doc=1&group={doc_value}")

        # 獲取網頁內容
        html = driver.page_source

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html, 'html.parser')

        # 找到包含科別的 h1 元素
        h1_element = soup.find('h1')
        if h1_element:
            department = h1_element.text.strip()
            # 將後面的 '醫療單位科別' 去掉
            department = department.replace('醫療單位科別', '')
        else:
            department = '無科別'

        # 找到包含 class="flexbox-wrap doctor-list" 的元素
        ul_element = soup.find('ul', class_='flexbox-wrap doctor-list')

        if ul_element is None:
            continue

        # 找到所有的 li 元素
        li_elements = ul_element.find_all('li')

        for li_element in li_elements:
            # 找到 h5 元素（包含醫生的名字）
            h5_element = li_element.find('h5')
            if h5_element:
                name = h5_element.text.strip()

            # 找到第一個 'a' 元素（包含醫生的介紹連結）
            a_element = li_element.find('a')
            if a_element:
                link = a_element.get('href')

            # 將資訊寫入檔案
            if h5_element and a_element:
                file.write(f"科別：{department} 醫師姓名：{name}")

            # 前往醫生的介紹連結
            driver.get("https://www.csh.com.tw/" + link)

            # 獲取網頁內容
            html = driver.page_source

            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 找到包含 class="col-md-8 doctor-info" 的元素
            div_element = soup.find('div', class_='col-md-8 doctor-info')

            if div_element is not None:
                # 找到 h6 元素（包含醫生代碼）
                h6_elements = div_element.find_all('h6')
                for h6 in h6_elements:
                    if '醫師代碼' in h6.text:
                        doctor_code = h6.text.split(': ')[-1]  # 分割字符串並取得代碼
                        break

                # 找到所有的 'a' 元素（包含門診時間表網址和網路掛號網址）
                a_elements = div_element.find_all('a')
                if len(a_elements) >= 2:
                    schedule_url = "https://www.csh.com.tw/" + a_elements[0].get('href')
                    register_url = "https://www.csh.com.tw" + a_elements[1].get('href')

                # 將資訊寫入檔案
                file.write(f" 醫師代碼：{doctor_code}")

                # 在這裡插入抓取醫生專長的程式碼
                # 找到包含 class="col-md-12 doctor-info-area" 的元素
                div_expertise = soup.find('div', class_='col-md-12 doctor-info-area')

                if div_expertise is not None:
                    # 找到所有的 'p' 元素
                    p_elements = div_expertise.find_all('p')
                    expertise = []
                    for p in p_elements:
                        # 如果在 'p' 元素的文字中找到 '專長'
                        if '專長' in p.text:
                            # 遍歷所有后續的 'p' 元素，直到遇到下一个不包含 '●' 的 'p' 元素
                            for p_expertise in p.next_siblings:
                                if p_expertise.name == 'p' and '●' in p_expertise.text:
                                    expertise.append(p_expertise.text.strip())
                                elif p_expertise.name == 'p':
                                    break
                    # 將專長信息寫入文件
                    if expertise:
                        file.write(f"專長：{'，'.join(expertise)}")

                file.write(f"\n門診時間表網址：{schedule_url}，網路掛號網址：{register_url}\n")

# 關閉瀏覽器
driver.quit()
