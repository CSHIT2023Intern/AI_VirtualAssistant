import os
import jieba
import jieba.posseg as pseg

# 取得繁體中文詞庫字典檔案的絕對路徑
# dict_path = os.path.join(os.path.dirname(__file__), 'traditional_chinese_dict.txt')
jieba.load_userdict('path_to_custom_dict.txt')

# 設定詞庫字典
# jieba.set_dictionary(dict_path)

# 讀取文本文件
with open('014.txt', 'r', encoding='utf-8') as file:
    text = file.read()
    text = text.replace("\n", "")

# 分詞和詞性標註
words = pseg.cut(text)

# 輸出分詞和詞性標註結果
print("分詞和詞性標註結果:")
for word, pos in words:
    print(f"{word}\t{pos}")
