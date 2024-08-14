import os

from entities.provider_configuration import ProviderModelBundle, ProviderConfiguration
from entities.provider_entities import SystemConfiguration, CustomConfiguration, CustomProviderConfiguration
from model_manager import ModelInstance
from model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage, ImagePromptMessageContent, \
    TextPromptMessageContent
from model_runtime.entities.model_entities import ModelType
from model_runtime.model_providers import ModelProviderFactory
from services.utils.upload_file_parser import UploadFileParser
from utils.models.provider import ProviderType


class ModelService:
    def __init__(self):
        pass
    @classmethod
    def get_default_model(cls):
        return_dict = {}
        credentials = {
            'api_key': os.environ.get('OPENROUTER_API_KEY')
        }
        model_name = "openai/gpt-4o-mini-2024-07-18"
        client = "openrouter"
        return_dict["client"] = client
        return_dict['model_name'] = model_name
        return_dict["credentials"] = credentials
        return return_dict

    @classmethod
    def invoke_llm(cls,args):

        default_config = cls.get_default_model()
        image_content =UploadFileParser.get_image_data_from_upload_id(args.get("image_id"))

        provider_instance = ModelProviderFactory().get_provider_instance(default_config['client'])
        model_type_instance = provider_instance.get_model_instance(ModelType.LLM)
        provider_model_bundle = ProviderModelBundle(
            configuration=ProviderConfiguration(
                tenant_id='1',
                provider=provider_instance.get_provider_schema(),
                preferred_provider_type=ProviderType.CUSTOM,
                using_provider_type=ProviderType.CUSTOM,
                system_configuration=SystemConfiguration(
                    enabled=False
                ),
                custom_configuration=CustomConfiguration(
                    provider=CustomProviderConfiguration(
                        credentials=default_config['credentials']
                    )
                ),
                model_settings=[]
            ),
            provider_instance=provider_instance,
            model_type_instance=model_type_instance
        )
        model_instance = ModelInstance(provider_model_bundle=provider_model_bundle, model=default_config['model_name'])
        response = model_instance.invoke_llm(
            prompt_messages=[
                SystemPromptMessage(
                    content='You are a helpful AI assistant.',
                ),
                UserPromptMessage(
                    content=[
                        TextPromptMessageContent(
                            data=args.get("query"),
                        ),
                        ImagePromptMessageContent(
                            data = image_content
                        )
                    ]
                )

            ],
            stream=args.get('response_mode')
        )
        return response



