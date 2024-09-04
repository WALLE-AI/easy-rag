import base64
import json
import os
from io import BytesIO

import loguru
import requests
from PIL import Image

from entities.provider_configuration import ProviderModelBundle, ProviderConfiguration
from entities.provider_entities import SystemConfiguration, CustomProviderConfiguration, CustomConfiguration
from model_manager import ModelInstance
from model_runtime.entities.message_entities import SystemPromptMessage, TextPromptMessageContent, UserPromptMessage, \
    ImagePromptMessageContent
from model_runtime.entities.model_entities import ModelType
from model_runtime.model_providers import ModelProviderFactory
from prompt.starchat_qs_prompt import STARCHAT_QS_TEST_PROMOPT, STARCHAT_QUALITY_TEST_PROMOPT, \
    STARCHAT_QUALITY_TEST_PROMOPT_LABEL
from rag.entities.entity_images import ImageTableProcess
from utils.models.provider import ProviderType

input_args = {
    "stream": False,
    "model_config": {"model_parameters": {"temperature": 0.2}, "mode": "chat",
                     "name": "openai/gpt-4o-mini-2024-07-18", "provider": "openrouter"},
}


##{'单号': '0000096ed25ec73466f0bbc48061acc4', '项目id': 232, '照片': 'https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/af0d013d-2f52-2c97-413b-55970976ec61.jpg', '隐患部位': 'S3首层', '标准隐患编号': 'dba507c450c247da989bc154c0f80612', '隐患内容': '构造柱钢筋未满绑', 'company_hidden_id': 'dba507c450c247da989bc154c0f80612', 'name': '建筑装饰装修'}


def write_json_file(data_dict, save_file_name):
    jsonn_str_data = json.dumps(data_dict, ensure_ascii=False)
    with open(save_file_name, "w", encoding="utf-8") as file:
        loguru.logger.info(f"save json file {save_file_name}")
        file.write(jsonn_str_data)


def download_image(url, filename):
    images_dir_path = "data\\images\\" + filename
    loguru.logger.info(f"images dir path {images_dir_path}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        with open(images_dir_path, 'wb') as f:
            f.write(response.content)
            loguru.logger.info(f"image save：{filename}")
            return True
    except requests.RequestException as e:
        loguru.logger.info(f"request error：{e}")
        return False
    except IOError as e:
        loguru.logger.info(f"request io error：{e}")


def encode_image_base64_from_url(image_id, image_url):
    mime_type = image_id.split(".")[-1]
    try:
        # 发送GET请求获取图片内容
        response = requests.get(image_url)
        response.raise_for_status()  # 如果请求失败，这会抛出异常
        # 获取图片内容
        image_content = response.content
        # 将图片内容转换为base64编码
        base64_encoded = base64.b64encode(image_content).decode('utf-8')
        base64_encoded = f'data:image/{mime_type};base64,{base64_encoded}'
        return base64_encoded
    except requests.RequestException as e:
        print(f"download image error: {e}")
        return None
    except Exception as e:
        print(f"transformer process error: {e}")
        return None


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


def image_to_base64(image_path):
    root_path = "data\\images\\"
    images_path_new = root_path + image_path
    if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
        mime_type = image_path.split(".")[-1]
        with Image.open(images_path_new) as img:
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
        return f'data:image/{mime_type};base64,{img_base64}'


def model_execute(image_base64,query):
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
                        data=STARCHAT_QUALITY_TEST_PROMOPT_LABEL.format(content=query)
                    ),
                    ImagePromptMessageContent(
                        data=image_base64
                    )
                ]
            )

        ],
        stream=input_args['stream'],
        model_parameters=model_config['model_parameters']
    )
    # loguru.logger.info(f"response execute time:{response.usage.latency}")
    return response


convesation_format_human_dict = {
    "from": "human",
    "value": "{content}\n<image>"
}
convesation_format_gpt_dict = {
    "from": "gpt",
    "value": "The scene depicts a lively plaza area with several people walking and enjoying their time. A man is standing in the plaza with his legs crossed, holding a kite in his hand. The kite has multiple sections attached to it, spread out in various directions as if ready for flight.\n\nNumerous people are scattered throughout the plaza, walking and interacting with others. Some of these individuals are carrying handbags, and others have backpacks. The image captures the casual, social atmosphere of a bustling plaza on a nice day."
}


def image_generator_conversation_index(data_json_file):
    with open(data_json_file, "r", encoding="utf-8") as file:
        data = file.read()
        data = json.loads(data)
        for _data in data:
            ##先根据图片生成该图片描述的问题
            if _data['accident_label'] =="主体结构":
                ##url
                images_base64 = encode_image_base64_from_url(_data["image_id"], _data['image_oss_url'])
                # images_base64 = image_to_base64(_data["image_id"])
                q_response = model_execute(images_base64,_data['description'])
                loguru.logger.info(f"reponse:{q_response}")
            # temp_conversation_list.append(q_response)
            # ##根据描述图片的问题生成对应隐患类别以及解释
            # question = ""
            # a_reponse = model_execute(images_base64, question)


def read_xlsx_file_to_save_json(file_path):
    import polars as pl
    data = pl.read_excel(file_path, sheet_name="Sheet1")
    data = data.to_pandas()
    # data = pd.read_excel(file_path,sheet_name="Sheet1")
    # data.index.names = ["单号","项目id","照片","隐患部位","标准隐患编号","隐患内容","company_hidden_id","name","类型"]
    data = data.head(51)
    data_save_list = []
    for index, row_data in data.iterrows():
        data_dict = row_data.to_dict()
        if data_dict['类型'] == "质量":
            image_name = data_dict['照片'].split("https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/")[-1]
            ##download image dir
            if download_image(data_dict['照片'], image_name):
                data_entity = ImageTableProcess(
                    id=str(index),
                    image_id=image_name,
                    image_correct_id="",
                    image_oss_url=data_dict['照片'],
                    conversations=[{}],
                    position=data_dict["隐患部位"] if isinstance(data_dict['隐患部位'], str) else "",
                    accident_label=data_dict['name'] if isinstance(data_dict['name'], str) else "",
                    description=data_dict['隐患内容'],
                    correct_description="",
                    type=data_dict['类型'],
                    risk="",
                    correct_basic="",
                    label="0"
                )
                data_save_list.append(data_entity.to_dict())
            if not index % 50 and index != 0:
                save_file_name = "data/images_table_format_" + str(index) + ".json"
                write_json_file(data_save_list, save_file_name)
                ##每超过10W，保存一次，清洗之前的数组中数据
                data_save_list.clear()


def preprocee_table_images_data():
    file_path = "D:\\LLM\\need_product\\architecture\\images_table_05.xlsx"
    json_file_path = "data\\images_table_format_50.json"
    image_root = "data\\images\\"
    image_generator_conversation_index(json_file_path)
    # read_xlsx_file_to_save_json(file_path)
