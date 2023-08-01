import requests
from bs4 import BeautifulSoup

url = "https://sysint.csh.org.tw/Register/CshDiv.aspx"

# 發送 GET 請求
response = requests.get(url)

# 使用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 找到科室所在的表格
table = soup.find('table', id='tbBig_ctl00_tbBig2')

# 提取科室名称
departments = []
for link in table.find_all('a'):
    department = link.text.strip()
    departments.append(department)

# 打印科室名称
for department in departments:
    print(department)
