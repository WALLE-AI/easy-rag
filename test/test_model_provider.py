import os

from model_runtime.entities.model_entities import ModelType
from model_runtime.entities.provider_entities import ProviderConfig, SimpleProviderEntity
from model_runtime.model_providers import ModelProviderFactory

def test_provider_credentials_validate():
    factory = ModelProviderFactory()
    factory.provider_credentials_validate(
        provider='openrouter',
        credentials={
            'api_key': os.environ.get('OPENROUTER_API_KEY')
        }
    )
    print(factory)


def test_model_proveder():
    provider_instance = ModelProviderFactory().get_provider_instance('openrouter')
    model_type_instance = provider_instance.get_model_instance(ModelType.LLM)
    print(model_type_instance)


def test_get_models():
    factory = ModelProviderFactory()
    providers = factory.get_models(
        model_type=ModelType.LLM,
        provider_configs=[
            ProviderConfig(
                provider='openrouter',
                credentials={
                    'openrouter_api_key': os.environ.get('OPENROUTER_API_KEY')
                }
            )
        ]
    )

    assert len(providers) >= 1
    assert isinstance(providers[0], SimpleProviderEntity)


    providers = factory.get_models(
        provider='openrouter',
        provider_configs=[
            ProviderConfig(
                provider='openrouter',
                credentials={
                    'openai_api_key': os.environ.get('OPENROUTER_API_KEY')
                }
            )
        ]
    )

    assert len(providers) == 1
    assert isinstance(providers[0], SimpleProviderEntity)
    assert providers[0].provider == 'openrouter'


