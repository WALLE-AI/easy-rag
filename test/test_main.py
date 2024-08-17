import loguru

from test.test_llm import test_llm, test_invoke_model_tongyi
from test.test_model_provider import test_get_models, test_provider_credentials_validate,test_model_proveder
from test.test_openrouter import test_invoke_model, test_invoke_stream_model, test_invoke_image_model
from test.test_reranker import test_reranker_model

if __name__ =="__main__":
    loguru.logger.info(f"test start")
    # test_provider_credentials_validate()
    # test_get_models()
    test_reranker_model()