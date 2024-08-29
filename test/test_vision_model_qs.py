'''
problem:测试主流的vlm模型在质量安全场景上面识别精度
label:临边洞口，高空跌落，安全帽，电气安全
model:GPT4-o/mini,yi-version, Claude-3.5，qwen-max
'''
import os
from decimal import Decimal
from io import BytesIO

import loguru
from PIL import Image
import base64
from pydantic import BaseModel

from entities.provider_configuration import ProviderModelBundle, ProviderConfiguration
from entities.provider_entities import SystemConfiguration, CustomConfiguration, CustomProviderConfiguration
from model_manager import ModelInstance
from model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage, TextPromptMessageContent, \
    ImagePromptMessageContent
from model_runtime.entities.model_entities import ModelType
from model_runtime.model_providers import ModelProviderFactory
from model_runtime.utils.encoders import jsonable_encoder
from prompt.starchat_qs_prompt import STARCHAT_QS_TEST_PROMOPT
from utils.models.provider import ProviderType

model_list_openrouter = [
# "openai/gpt-4o-mini-2024-07-18",
    "qwen-vl-max",
]

model_list_qwen = [

]

input_args = {
    "stream":True,
    "model_config": {"model_parameters": {"temperature": 0.2}, "mode": "chat",
                     "name": "qwen-vl-max", "provider": "tongyi"},
}
import pandas as pd
class TestVlmSafeOutPut(BaseModel):
    """
    Model class for provider quota configuration.
    """
    model_name: str="01-ai/yi-vision"
    provider: str="openrouter"
    image_name:str=""
    description:str="昆明东货运站项目垂直洞口短边边长大于或等于500mm时，未在临空一侧设置高度不小于1.2m的防护栏杆密目式安全立网或工具式栏板封闭挡脚板"
    prompt:str="你是一个智能助手"
    response: str="shdhshadhsahd"
    total_tokens: int=122343
    total_price:Decimal=0.01
    currency:str = "USD"
    score:float=0.0
    human_review:str=""

    def to_dict(self) -> dict:
        return jsonable_encoder(self)
def read_image_file():
    folder_path = 'D:\\LLM\\need_product\\architecture\\building_acident_datasets\\safe'
    # folder_path = 'D:\\LLM\\need_product\\architecture\\building_acident_datasets'
    file_dict = {}
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 构建文件的完整路径
        file_path = os.path.join(folder_path, filename)
        # 检查文件是否是图片（这里以常见的图片格式为例）
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
            with Image.open(file_path) as img:
                # 定义新的尺寸，例如缩小到原来的一半
                new_width = img.width // 2
                new_height = img.height // 2
                # 调整图片大小
                img_resized = img.resize((new_width, new_height))
                # 将图片转换为字节流
                buffered = BytesIO()
                img_resized.save(buffered, format=img.format)
                # 将字节流转换为Base64编码
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            file_dict[filename] = img_base64
    loguru.logger.info(f"image num {len(file_dict)}")
    return file_dict

def get_execute_dir_path():
    return os.path.dirname(os.path.abspath(__file__))

def image_to_base64(encoded_string,mime_type):
    return f'data:{mime_type};base64,{encoded_string}'


def get_env_credentials(args):
        provider = args["model_config"]['provider']
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

def model_execute(image_base64):
    credentials = get_env_credentials(input_args)
    model_config = input_args["model_config"]
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
                    content='',
                ),
                UserPromptMessage(
                content=[
                    TextPromptMessageContent(
                        data=STARCHAT_QS_TEST_PROMOPT
                    ),
                    ImagePromptMessageContent(
                        data = image_base64
                    )
                ]
            )


        ],
        stream=input_args['stream'],
        model_parameters=model_config['model_parameters']
    )
    # loguru.logger.info(f"response execute time:{response.usage.latency}")
    return response

def preproce_modem_name_char(image_name):
    return image_name.replace('/', '')

def write_file(reponse_data_list,model_name):
    file_name= preproce_modem_name_char(model_name) + "_"+"safe_test_result.csv"
    write_path = get_execute_dir_path() +"\\" +file_name
    data =pd.DataFrame(reponse_data_list)
    loguru.logger.info(f"save file")
    data.to_csv(write_path,index=False,encoding='gb2312')

def reponse_post_process(result,response_data_list,input_arg):
    content = ""
    if input_arg["stream"]:
        for text in result:
            if text.delta.finish_reason == "stop":
                usage = text.delta.usage
                content += text.delta.message.content
            else:
                content += text.delta.message.content
    else:
        usage = result.usage
        content = result.message.content
    model_config = input_arg['model_config']
    data = TestVlmSafeOutPut(
            model_name =model_config["name"],
            provider=model_config["provider"],
            image_name = input_arg['image_name'],
            description = input_arg['description'],
            prompt=STARCHAT_QS_TEST_PROMOPT,
            response=content,
            total_tokens=usage.total_tokens,
            total_price = usage.total_price,
            currency=usage.currency
    )
    response_data_list.append(data.to_dict())

def exist_image_file(model_name):
    '''
    判断已经诊断过的图片
    :return:
    '''
    exist_image_file_list = []
    file_name= preproce_modem_name_char(model_name) + "_"+"safe_test_result.csv"
    image_file_path = get_execute_dir_path() +"\\" +file_name
    if os.path.exists(image_file_path):
        data = pd.read_csv(image_file_path,encoding="gb2312")
        ##存储之前已经执行的图片
        # for index, row in data.iterrows():
        #     exist_image_file_list.append(row.to_dict())
        # return exist_image_file_list, data
    else:
        data_dict = TestVlmSafeOutPut().to_dict()
        data = pd.DataFrame([data_dict])
        data.to_csv(image_file_path,index=False,encoding='gb2312')
    for index, row in data.iterrows():
        exist_image_file_list.append(row.to_dict())
    return exist_image_file_list, data

def llm_execute():
    image_path = read_image_file()
    for model_name in model_list_openrouter:
        response_data_list = []
        exist_image_file_list, data = exist_image_file(model_name)
        if exist_image_file_list:
            response_data_list = exist_image_file_list
        for key,value in image_path.items():
            loguru.logger.info(f"image name {key}")
            image_name,image_format = key.split(".")
            if key in data.image_name.values:
                continue
            input_args['image_name'] =key
            input_args['description'] = image_name
            mime_type = "image/" + image_format
            base64_string = image_to_base64(value, mime_type)
            input_args['model_config']["name"] = model_name
            ##模型执行
            loguru.logger.info(f"llm name:{model_name},execute image: {image_name}")
            result = model_execute(base64_string)
            reponse_post_process(result,response_data_list,input_args)
            write_file(response_data_list,model_name)


