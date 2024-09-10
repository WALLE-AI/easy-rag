import time

import requests
import json

def send_post_request():
    start_time = time.time()
    url = 'http://xxxxx:9991/embed'
    headers = {'Content-Type': 'application/json'}
    data = {'inputs': ["你是谁","你能够做什么"]}
    # data = {"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}


    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))

    end_time = time.time()
    execution_time = end_time - start_time

    # 打印响应内容
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

    print("TGI Execution time: {:.2f} seconds".format(execution_time))
