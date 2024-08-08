import loguru

from test.test_model_provider import test_get_models, test_provider_credentials_validate

if __name__ =="__main__":
    loguru.logger.info(f"test start")
    test_provider_credentials_validate()
    test_get_models()