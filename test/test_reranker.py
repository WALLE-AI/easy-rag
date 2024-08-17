import os

import loguru

from model_runtime.model_providers.siliconflow.rerank.rerank import SiliconflowRerankModel


def test_reranker_model():
    model = SiliconflowRerankModel()

    result = model.invoke(
        model='BAAI/bge-reranker-v2-m3',
        credentials={
            "api_key": os.environ.get("API_KEY"),
        },
        query="Who is Kasumi?",
        docs=[
            "Kasumi is a girl's name of Japanese origin meaning \"mist\".",
            "Her music is a kawaii bass, a mix of future bass, pop, and kawaii music ",
            "and she leads a team named PopiParty."
        ],
        score_threshold=0.8
    )
    loguru.logger.info(f"result:{result}")