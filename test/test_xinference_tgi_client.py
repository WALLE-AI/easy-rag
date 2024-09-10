import os
import time

from xinference.client import Client

from model_runtime.entities.text_embedding_entities import TextEmbeddingResult
from model_runtime.model_providers.xinference.rerank.rerank import XinferenceRerankModel
from model_runtime.model_providers.xinference.text_embedding.text_embedding import XinferenceTextEmbeddingModel

import requests
import json

# from load_env import load_env_file
#
# model_config =load_env_file()



def send_post_request():
    start_time = time.time()
    url = os.getenv("EMBEDDING_SERVE_HOST")+':9991/embed'
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

def compare_tgi_sentenece_transfomers():
    send_post_request()
    raw_xinference_client()
    test_invoke_model_xinference()

def raw_xinference_client():
    start_time = time.time()
    client = Client("http://localhost:9997")
    model = client.get_model("jina-embeddings-v2-base-zh")

    embedding_result = model.create_embedding(["你是谁", "你能够做什么"])
    end_time = time.time()
    execution_time = end_time - start_time
    print("text embedding {}".format(embedding_result))
    print("Xinference raw Execution time: {:.2f} seconds".format(execution_time))


def test_invoke_model_xinference():
    model = XinferenceTextEmbeddingModel()

    start_time = time.time()
    result = model.invoke(
        model="jina-embeddings-v2-base-zh",
        credentials={
            "server_url": "http://localhost:9997",
            "model_uid": "jina-embeddings-v2-base-zh",
        },
        texts=["你是谁", "你能够做什么"],
        user="abc-123",
    )
    end_time = time.time()
    execution_time = end_time - start_time
    print("text embedding {}".format(result))
    print("xinference dify Execution time: {:.2f} seconds".format(execution_time))

def test_invoke_model_reranker_xinference(query,recall_doc_list):
    model = XinferenceRerankModel()

    result = model.invoke(
        model="jina-reranker-v2-base-multilingual",
        credentials={
            "server_url": "http://localhost:9997",
            "model_uid": "jina-reranker-v2-base-multilingual",
        },
        query=query,
        docs=recall_doc_list,
        score_threshold=0.4,
    )
    print("text embedding {}".format(result))
    return result

if __name__ == "__main__":
    test_invoke_model_xinference()