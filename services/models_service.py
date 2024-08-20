import json
import os
import time
import uuid

import loguru

from controllers.entities.app_generator import AppGeneratorMessage
from entities.provider_configuration import ProviderModelBundle, ProviderConfiguration
from entities.provider_entities import SystemConfiguration, CustomConfiguration, CustomProviderConfiguration
from model_manager import ModelInstance
from model_runtime.entities.llm_entities import LLMResult
from model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage, ImagePromptMessageContent, \
    TextPromptMessageContent
from model_runtime.entities.model_entities import ModelType
from model_runtime.model_providers import ModelProviderFactory
from prompt.starchat_qs_prompt import STARCHAT_QS_CHAT_PROMPT_DEFAULT
from prompt.utils.PromptTemplateParser import PromptTemplateParser
from prompt.utils.prompt_message_util import PromptMessageUtil
from services.database.postgres_db import db
from services.db_model.message import Message
from services.utils.upload_file_parser import UploadFileParser
from utils.models.provider import ProviderType




class ModelService:
    def __init__(self):
        pass
    @classmethod
    def _save_message_db(cls,args,llm_result,prompt_messages):
        model_config = args.get("model_config")
        usage = llm_result.usage
        message = Message(
            query = args.get("query"),
            model_provider = model_config["provider"],
            model_id = model_config["name"],
            conversation_id = args.get("conversation_id"),
            file_id =args.get("file_id"),
            message= PromptMessageUtil.prompt_messages_to_prompt_for_saving(
            "chat",
            prompt_messages),
            from_account_id=args.get("account_id"),
            message_tokens = usage.prompt_tokens,
            message_unit_price = usage.prompt_unit_price,
            message_price_unit = usage.prompt_price_unit,
            answer = PromptTemplateParser.remove_template_variables(llm_result.message.content.strip()) \
            if llm_result.message.content else '',
            answer_tokens = usage.completion_tokens,
            answer_unit_price = usage.completion_unit_price,
            answer_price_unit = usage.completion_price_unit,
            provider_response_latency = usage.latency,
            total_price = usage.total_price,
            currency = usage.currency,
            file_type=args.get("file_type")
        )
        db.session.add(message)
        db.session.commit()

    @classmethod
    def post_messages_generator(cls, args,response):
        message_id = str(uuid.uuid4())
        message_content = ""
        for text in response:
            ##finsh_reason获取usage内容
            if text.delta.finish_reason == "stop":
                usage_info_dict = text.delta.usage.to_dict()
                message_content += text.delta.message.content
                app_generator = AppGeneratorMessage(
                    message_id = message_id,
                    conversation_id=args.get("conversation_id"),
                    answer=text.delta.message.content,
                    usage=usage_info_dict
                )
                ##TODO:当前message保持在数据库中
                loguru.logger.info(f"message_content:{message_content}")
                yield f'data: {app_generator}\n\n'
                text.delta.message.content = message_content
                cls._save_message_db(args,text.delta,text.prompt_messages)
            else:
                message_content += text.delta.message.content
                app_generator = AppGeneratorMessage(
                    message_id=message_id,
                    conversation_id=args.get("conversation_id"),
                    answer=text.delta.message.content
                )
                yield f'data: {app_generator}\n\n'


    @classmethod
    def post_messages_direct_output(cls,args,response):
        ##save message db
        cls._save_message_db(args,response,response.prompt_messages)
        app_generator = AppGeneratorMessage(
                message_id=str(uuid.uuid4()),
                conversation_id=args.get("conversation_id"),
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
        ##获取client key值
        credentials = cls.get_env_credentials(args)
        model_config = args.get("model_config")
        if args.get("file_id"):
            image_content,file_type = UploadFileParser.get_image_data_from_upload_id(args.get("file_id"))
            args['file_type'] = file_type
        else:
            image_content = ""
        if args.get("system_prompt")['use_prompt'] and args.get("system_prompt")['prompt']:
            args["system_prompt"] = args.get("system_prompt")['prompt']
        else:
            ##默认系统的
            args["system_prompt"] = STARCHAT_QS_CHAT_PROMPT_DEFAULT
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
                    content=args.get("system_prompt"),
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
            return cls.post_messages_generator(args,response)
        else:
            return cls.post_messages_direct_output(args,response)
