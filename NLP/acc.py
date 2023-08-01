

# 將文字轉換為單行
import json

text = input("請輸入中文文本: ")

# 將文字序列化為JSON格式
serialized_text = json.dumps(text)

print(serialized_text)
