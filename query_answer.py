import requests

url = "http://127.0.0.1:8080/query_answer"

query = {
    "kb_name" : "知识库名称",
    "question" : "问题",
    "top_k" : 20,
    "score_threshold" : 0
}

response = requests.post(url, json=query)
if response.status_code == 200:
    print(str("".join(response.json().get("answer"))))
else:
    print("Error code: ", response.status_code)
    print(response.text)