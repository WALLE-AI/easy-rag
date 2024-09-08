# from xinference.client import Client

from model_runtime.entities.text_embedding_entities import TextEmbeddingResult
from model_runtime.model_providers.xinference.rerank.rerank import XinferenceRerankModel
from model_runtime.model_providers.xinference.text_embedding.text_embedding import XinferenceTextEmbeddingModel

# client = Client("http://localhost:9997")
# model = client.get_model("jina-embeddings-v2-base-zh")
#
# embedding_result = model.create_embedding("What is the capital of China?")
# print(embedding_result)


def test_invoke_model_xinference():
    model = XinferenceTextEmbeddingModel()

    result = model.invoke(
        model="jina-embeddings-v2-base-zh",
        credentials={
            "server_url": "http://localhost:9997",
            "model_uid": "jina-embeddings-v2-base-zh",
        },
        texts=["你是谁", "你能够做什么"],
        user="abc-123",
    )
    print("text embedding {}".format(result))



def test_invoke_model_reranker_xinference():
    model = XinferenceRerankModel()

    result = model.invoke(
        model="jina-reranker-v2-base-multilingual",
        credentials={
            "server_url": "http://localhost:9997",
            "model_uid": "jina-reranker-v2-base-multilingual",
        },
        query="Who is Kasumi?",
        docs=[
            'Kasumi is a girl\'s name of Japanese origin meaning "mist".',
            "Her music is a kawaii bass, a mix of future bass, pop, and kawaii music ",
            "and she leads a team named PopiParty.",
        ],
        score_threshold=0.4,
    )
    print("text embedding {}".format(result))

if __name__ == "__main__":
    test_invoke_model_xinference()