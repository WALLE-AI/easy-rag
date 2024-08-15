import json
import os

from controllers.entities.app_generator import AppGeneratorMessage
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
    def post_messages_generator(cls, response):
        for text in response:
            if text.delta.usage:
                app_generator = AppGeneratorMessage(
                    answer=text.delta.message.content,
                    usgae = text.delta.usage.to_dict()
                )
                yield f'data: {app_generator}\n\n'
            else:
                app_generator = AppGeneratorMessage(
                    answer=text.delta.message.content
                )
                yield f'data: {app_generator}\n\n'


    @classmethod
    def post_messages_direct_output(cls,response):
        app_generator = AppGeneratorMessage(
                answer=response.message.content,
                usage = response.usage.to_dict()
        )
        return app_generator.to_dict()

    @classmethod
    def get_env_credentials(cls, args):
        provider = args.get("model_config")['provider']
        if provider == "openrouter":
            return {
                'api_key': os.environ.get('OPENROUTER_API_KEY')
            }
        elif provider == "openai":
            return {
                'openai_api_key': os.environ.get('OPENAI_API_KEY')
            }
        elif provider == "tongyi":
            return {
                'dashscope_api_key': os.environ.get('TONGYI_DASHSCOPE_API_KEY')
            }
        elif provider == "siliconflow":
            return {
                'api_key': os.environ.get('API_KEY')
            }

    @classmethod
    def invoke_llm(cls, args):
        credentials = cls.get_env_credentials(args)
        model_config = args.get("model_config")
        if args.get("image_id"):
            image_content = UploadFileParser.get_image_data_from_upload_id(args.get("image_id"))
        else:
            image_content = ""
        provider_instance = ModelProviderFactory().get_provider_instance(model_config['provider'])
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
                        credentials=credentials
                    )
                ),
                model_settings=[]
            ),
            provider_instance=provider_instance,
            model_type_instance=model_type_instance
        )
        model_instance = ModelInstance(provider_model_bundle=provider_model_bundle, model=model_config['name'])
        response = model_instance.invoke_llm(
            prompt_messages=[
                SystemPromptMessage(
                    content=args.get("pre_prompt"),
                ),
                UserPromptMessage(
                    content=[
                        TextPromptMessageContent(
                            data=args.get("query"),
                        ),
                        ImagePromptMessageContent(
                            data=image_content
                        )
                    ]
                )

            ],
            stream=args.get('response_mode')['stream'],
            model_parameters=model_config['model_parameters']
        )
        if args.get('response_mode')['stream']:
            return cls.post_messages_generator(response)
        else:
            return cls.post_messages_direct_output(response)
