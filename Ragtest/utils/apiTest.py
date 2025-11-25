import requests
import json

url = "http://localhost:8012/v1/chat/completions"
headers = {"Content-Type": "application/json"}
SYSTEM_PROMPT = "你是一个专业的汽车换产换线设计师，你手头上有各类工艺流程和所需的工具和设备。请根据用户的问题，结合你的专业知识，提供准确且详细的换产换线方案设计。注意，你的回答必须简洁明了，避免冗长的解释。"

# 1、测试全局搜索  graphrag-global-search:latest
global_data = {
    "model": "graphrag-global-search:latest",
    "messages": [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "从A车型到B车型的换产，涉及到车门的更换，请给出产线中需要调整的地方？注意使用中文回答，不要用英文，注意回答必须简洁明了，"}
    ],  
    "temperature": 0.7,
    # "stream": True,#True or False
}

# 2、测试本地搜索  graphrag-local-search:latest
local_data = {
    "model": "graphrag-local-search:latest",
    "messages": [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "冲压工艺中质量检验这一过程需要使用什么设备？注意使用中文回答，不要用英文"}
    ],  
    "temperature": 0.7,
    # "stream": True,#True or False
}

# 1、测试全局搜索  graphrag-global-search:latest
response = requests.post(url, headers=headers, data=json.dumps(global_data))
# 2、测试本地搜索  graphrag-local-search:latest
#response = requests.post(url, headers=headers, data=json.dumps(local_data))

# print(response.json())
print(response.json()['choices'][0]['message']['content'])








