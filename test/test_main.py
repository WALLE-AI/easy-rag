import loguru

from load_env import load_env
from test_preprocess_images import risk_doc_embedding_execuate, risk_instance_search, \
    test_risk_instance_recall_reranker, preprocee_table_images_data
from test_vllm_openai import test_vllm_openai_client

##加载.env file
load_env()

if __name__ =="__main__":
    loguru.logger.info(f"test start")
    # test_provider_credentials_validate()
    # test_get_models()
    preprocee_table_images_data()