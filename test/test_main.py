import loguru

from test_vllm_openai import test_vllm_openai_client
# from test.test_llm import test_llm, test_invoke_model_tongyi
# from test.test_model_provider import test_get_models, test_provider_credentials_validate,test_model_proveder
# from test.test_node_plan import test_node_plan
# from test.test_openrouter import test_invoke_model, test_invoke_stream_model, test_invoke_image_model
from test_preprocess_images import preprocee_table_images_data
from test_xinference_client import test_invoke_model_xinference, test_invoke_model_reranker_xinference

# from test.test_reranker import test_reranker_model
# from test.test_vision_model_qs import write_file, llm_execute

if __name__ =="__main__":
    loguru.logger.info(f"test start")
    # test_provider_credentials_validate()
    # test_get_models()
    test_invoke_model_xinference()