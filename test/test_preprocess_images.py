import base64
import hashlib
import json
import os
import time
import uuid
from io import BytesIO

import loguru
import numpy as np
import pandas as pd
import requests
from PIL import Image

from entities.provider_configuration import ProviderModelBundle, ProviderConfiguration
from entities.provider_entities import SystemConfiguration, CustomProviderConfiguration, CustomConfiguration
from model_manager import ModelInstance
from model_runtime.entities.message_entities import SystemPromptMessage, TextPromptMessageContent, UserPromptMessage, \
    ImagePromptMessageContent
from model_runtime.entities.model_entities import ModelType
from model_runtime.model_providers import ModelProviderFactory
from model_runtime.model_providers.xinference.text_embedding.text_embedding import XinferenceTextEmbeddingModel
from prompt.starchat_qs_prompt import STARCHAT_QS_TEST_PROMOPT, STARCHAT_QUALITY_TEST_PROMOPT, \
     STARCHAT_QS_TEST_EVALUTE_PROMOPT, STARCHAT_QS_QUESTION_GENERATOR_RPROMOPT, \
    STARCHAT_QS_ANSWER_GENERATOR_RPROMOPT, STARCHAT_QUALITY_MAIN_STRUCTURE_PROMOPT_LABEL
from rag.entities.document import Document
from rag.entities.entity_images import ImageTableProcess, ImageVlmQualityLabel, ImageVlmModelOutPut
from test_xinference_tgi_client import test_invoke_model_reranker_xinference
from test_vdb import test_chroma_vector, test_chroma_vector_search
from utils.models.provider import ProviderType

from openai import OpenAI
import loguru

def init_client():
    openai_api_key = "empty"
    openai_api_base = os.getenv("VLM_SERVE_HOST") +":9005/v1"
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )
    return client

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


def write_file(response_data_list):
    file_name_path = "data\\" + "quality_1000_result_recall.csv"
    data = pd.DataFrame(response_data_list)
    data.to_csv(file_name_path, index=False, encoding='GBK')


def download_image(url, filename):
    root_image = "data\\images\\"
    images_dir_path = root_image + filename
    # loguru.logger.info(f"images dir path {images_dir_path}")
    if filename in load_images_from_folder(root_image):
        loguru.logger.info(f"image is exist,no donwload")
        return False
    else:
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


def is_url_validation(image_url):
    ##验证url有效性
    try:
        # 发送GET请求获取图片内容
        response = requests.get(image_url)
        response.raise_for_status()  # 如果请求失败，这会抛出异常
        return True
    except requests.RequestException as e:
        print(f"download image error: {e}")
        return False


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


def local_model_execute(data_dict, prompt):
    client = init_client()
    models = client.models.list()
    model_name = models.data[0].id
    loguru.logger.info(f"model name {model_name}")
    response = client.chat.completions.create(
        model=model_name,
        messages=[{
            "role": "user",
            "content": [
                # NOTE: The prompt formatting with the image token `<image>` is not needed
                # since the prompt will be processed automatically by the API server.
                # {"type": "text", "text":"你是一个建筑施工行业资深的质量检查员，你能够高精度判别出施工工地中施工质量风险，请根据用户的场景图片进行高质量的回复,需要重点分析出隐患类别、质量分析、整改要求和法规依据" },
                {"type": "text",
                 "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_dict['image_oss_url'],
                    },
                },
            ],
        }],
        stream=False
    )
    response_dict = ImageVlmModelOutPut(
        prompt=prompt,
        model_name=response.model,
        content=response.choices[0].message.content,
        total_tokens=response.usage.total_tokens
    )
    return response_dict.to_dict()


def model_execute(data_dict, prompt):
    image_base64 = encode_image_base64_from_url(data_dict["image_id"], data_dict['image_oss_url'])
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
                        data=prompt
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
    response_dict = ImageVlmModelOutPut(
        prompt=prompt,
        model_name=response.model,
        content=response.message.content,
        total_tokens=response.usage.total_tokens
    )
    return response_dict.to_dict()


convesation_format_human_dict = {
    "from": "human",
    "value": "{content}\n<image>"
}
convesation_format_gpt_dict = {
    "from": "gpt",
    "value": ""
}


def llm_result_postprocess(llm_response_content):
    ##json的后处理
    from json_repair import repair_json
    json_string = repair_json(llm_response_content, return_objects=True)
    return json_string


def post_data_images_test_output(data_dict, prompt):
    data = ImageVlmQualityLabel(
        image_id=data_dict['image_id'],
        image_oss_url=data_dict['image_oss_url'],
        description=data_dict['description'],
        prompt=prompt,
        total_tokens="11234",
        score=0.0,
        human_review=""
    )
    return data.to_dict()


def exist_image_file():
    '''
    判断已经诊断过的图片
    :return:
    '''
    exist_image_file_list = []
    file_name_path = "data\\" + "quality_1000_result.csv"
    image_id_list = []
    if os.path.exists(file_name_path):
        data = pd.read_csv(file_name_path, encoding="gb2312")
        ##存储之前已经执行的图片
        # for index, row in data.iterrows():
        #     exist_image_file_list.append(row.to_dict())
        # return exist_image_file_list, data
    else:
        data_dict = ImageVlmQualityLabel().to_dict()
        data = pd.DataFrame([data_dict])
        data.to_csv(file_name_path, index=False, encoding='gb2312')
    for index, row in data.iterrows():
        exist_image_file_list.append(row.to_dict())
        image_id_list.append(row.to_dict()['image_id'])
    return exist_image_file_list, image_id_list


def image_generator_conversation_data(data_dict):
    q_prompt = STARCHAT_QS_QUESTION_GENERATOR_RPROMOPT
    a_prompt = STARCHAT_QS_ANSWER_GENERATOR_RPROMOPT
    response_dict2 = local_model_execute(data_dict, q_prompt.replace("{content}", data_dict['description']))
    question_dict_list = llm_result_postprocess(response_dict2['content'])
    for question in question_dict_list:
        convesation_format_human_dict = {
            "from": "human",
            "value": "{content}\n<image>"
        }
        convesation_format_gpt_dict = {
            "from": "gpt",
            "value": ""
        }
        convesation_format_human_dict["value"] = convesation_format_human_dict["value"].format(
            content=question)
        data_dict['conversations'].append(convesation_format_human_dict)
        response_dict3 = local_model_execute(data_dict,
                                             a_prompt.format(content1=data_dict['description'], content2=question))
        convesation_format_gpt_dict["value"] = response_dict3['content']
        data_dict['conversations'].append(convesation_format_gpt_dict)
    return data_dict


def image_generator_conversation_index(data_json_file):
    with open(data_json_file, "r", encoding="utf-8") as file:
        data = file.read()
        data = json.loads(data)
        loguru.logger.info(f"data size :{len(data)}")
        image_id_list = []
        data_dict_list = []
        # init_data_list,image_id_list = exist_image_file()
        # if init_data_list:
        #     test_data_list = init_data_list
        prompt = STARCHAT_QS_TEST_EVALUTE_PROMOPT
        for _data in data:
            ##先根据图片生成该图片描述的问题
            if _data['image_id'] not in image_id_list:
                ##url
                loguru.logger.info(f"accident_label:{_data['accident_label']},description:{_data['description']}")
                data_dict = image_generator_conversation_data(_data)
                data_dict_list.append(data_dict)
                save_file_name = "data/images_table_format_new" + ".json"
                write_json_file(data_dict_list, save_file_name)
                ##init output_data object
                # output_data = post_data_images_test_output(_data, prompt)
                # response_dict1 = model_execute(_data, prompt)
                # output_data[response_dict1['model_name']] = response_dict1['content']
                # output_data[response_dict2['model_name']] = response_dict2['content']
                # output_data['total_tokens'] = str(response_dict1["total_tokens"]) +";" + str(response_dict2["total_tokens"])
                # test_data_list.append(output_data)
                # loguru.logger.info(f"save local file .....")
                # write_file(test_data_list)

def tgi_inference_embedding(risk_doc):
    start_time = time.time()
    url = os.getenv("EMBEDDING_SERVE_HOST") + ':9991/embed'
    headers = {'Content-Type': 'application/json'}
    data = {'inputs': [risk_doc]}
    # data = {"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}
    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()
    execution_time = end_time - start_time
    # 打印响应内容
    print("Status Code:", response.status_code)
    print("TGI Execution time: {:.2f} seconds".format(execution_time))
    loguru.logger.info(f"risk doc:{risk_doc},embedding:{response.text}")
    return json.loads(response.text)

def tgi_inference_reranker(query,risk_doc_list):
    start_time = time.time()
    url = os.getenv("EMBEDDING_SERVE_HOST") + ':9992/rerank'
    headers = {'Content-Type': 'application/json'}
    data = {"query":query, "texts": risk_doc_list,  "raw_scores": False,"return_text": True,}
    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()
    execution_time = end_time - start_time
    # 打印响应内容
    print("Status Code:", response.status_code)
    print("TGI Execution time: {:.2f} seconds".format(execution_time))
    loguru.logger.info(f"query:{query},recal_risk_doc:{response.text}")
    return json.loads(response.text)



def read_xlsx_file_risk(risk_file_path):
    import polars as pl
    data = pl.read_excel(risk_file_path, sheet_name="Sheet1")
    data = data.to_pandas()
    risk_doc_list = []
    risk_doc_embed_list = []
    for index, row_data in data.iterrows():
        data_dict = row_data.to_dict()
        if data_dict['类型'] == "质量":
            content = data_dict['隐患描述'] + ";" + data_dict['整改要求']
            embed_result = tgi_inference_embedding(content)
            risk_doc_embed_list.append(embed_result[0])
            risk_doc = Document(
                page_content=content,
                metadata={
                    "doc_id": str(uuid.uuid4()),
                    "doc_hash": hashlib.sha3_256(content.encode('utf-8')).hexdigest(),
                    "document_id": data_dict['分类'],
                    # "model":embed_result.model
                },
            )
            risk_doc_list.append(risk_doc)
    ##获取documet data
    return risk_doc_list,risk_doc_embed_list


def test_invoke_model_xinference(risk_doc):
    model = XinferenceTextEmbeddingModel()
    start_time = time.time()
    result = model.invoke(
        model="jina-embeddings-v2-base-zh",
        credentials={
            "server_url": "http://localhost:9997",
            "model_uid": "jina-embeddings-v2-base-zh",
        },
        texts=[risk_doc],
        user="abc-123",
    )
    end_time = time.time()
    execution_time = end_time - start_time
    print("xinference dify Execution time: {:.2f} seconds".format(execution_time))
    return result


def risk_doc_create_embedding(risk_file_path):
    risk_doc_list,risk_doc_embed_list = read_xlsx_file_risk(risk_file_path)
    loguru.logger.info(f"embedding result {len(risk_doc_list)}")
    test_chroma_vector(risk_doc_list,risk_doc_embed_list)


def risk_doc_embedding_execuate():
    risk_file_path = os.getenv("RISK_DOC_PATH")
    risk_doc_create_embedding(risk_file_path)


def risk_doc_recall_reranker(query,recall_doc_list):
    reranker_result = tgi_inference_reranker(query,recall_doc_list)
    loguru.logger.info(f"reranker result {reranker_result}")
    return reranker_result

def risk_instance_search(query):
    query_embed = tgi_inference_embedding(query)
    search_result = test_chroma_vector_search(query_embed[0])
    loguru.logger.info(f"query:{query},search result {search_result}")
    if search_result:
        recall_doc_list = [recall_doc.page_content for recall_doc in search_result]
        reranker_result = risk_doc_recall_reranker(query,recall_doc_list)
    else:
        reranker_result = []
    return reranker_result

def test_risk_instance_recall_reranker():
    instance_risk_doc_path = "data\\quality_1000_result.csv"
    instance_risk_data = pd.read_csv(instance_risk_doc_path,encoding="gb2312")
    loguru.logger.info(f"instance risk data {len(instance_risk_data)}")
    new_quality_instance_risk_doc_list = []
    for index,row in instance_risk_data.iterrows():
        data_dict  = row.to_dict()
        risk_doc = data_dict['description']
        risk_recall_doc = risk_instance_search(risk_doc)
        if risk_recall_doc:
            data_dict['risk_recall'] = "\n".join([str(doc['index'])+"."+doc["text"] for doc in risk_recall_doc[:3]])
        else:
            data_dict['risk_recall'] = ""
        new_quality_instance_risk_doc_list.append(data_dict)
        write_file(new_quality_instance_risk_doc_list)

def load_images_from_folder(folder_path):
    images_list = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            images_list.append(filename)
    return images_list



def read_xlsx_file_to_save_json(file_path):
    import polars as pl
    data = pl.read_excel(file_path, sheet_name="Sheet1")
    data = data.to_pandas()
    loguru.logger.info(f"data size :{len(data)}")
    data_save_list = []
    for index, row_data in data.iterrows():
        data_dict = row_data.to_dict()
        if data_dict['类型'] == "质量":
            image_name = data_dict['照片'].split("https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/")[-1]
            ##download image dir
            if image_name in load_images_from_folder("data\\images"):
                loguru.logger.info(f"image is exist,no donwload")
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
                continue
            ##下载图片
            is_download = download_image(data_dict['照片'], image_name)
            if is_download:
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
        if len(data_save_list) == 10000:
            loguru.logger.info(f"data_save_list:{len(data_save_list)}")
            save_file_name = "data/images_table_format_" + str(len(data_save_list)) + ".json"
            write_json_file(data_save_list, save_file_name)
            break
    loguru.logger.info(f"data_save_list:{len(data_save_list)}")
    save_file_name = "data/images_table_format_" + str(len(data_save_list)) + ".json"
    write_json_file(data_save_list, save_file_name)



def read_main_structure_data(data_json_file):
    '''
    抽取主体结构的类似的数据
    :return:
    '''
    from json_repair import repair_json
    with open(data_json_file, "r", encoding="utf-8") as file:
        data = file.read()
        data = json.loads(data)
        loguru.logger.info(f"data size :{len(data)}")
        output_message_list = []
        user_total_tokens = 0
        for _data in data[:200]:
            if _data['accident_label'] == "主体结构":
                prompt = STARCHAT_QUALITY_MAIN_STRUCTURE_PROMOPT_LABEL.replace("{content}",_data["description"])
                response = local_model_execute(_data,prompt)
                json_content = repair_json(response['content'], return_objects = True)
                json_content_list=["",""]
                if isinstance(json_content,dict):
                    json_content_list =[text for text in json_content.values()]
                loguru.logger.info(f"reponse:{json_content}")
                output_message={
                    "图片地址":_data["image_oss_url"],
                    "隐患描述":_data["description"],
                    "一级隐患类别":_data['accident_label'],
                    "二级隐患类别":json_content_list[0],
                    "三级隐患类别":json_content_list[1],
                    "total_tokens":response['total_tokens']
                }
                output_message_list.append(output_message)
                user_total_tokens += response['total_tokens']
    loguru.logger.info(f"user_total_tokens:{user_total_tokens}")
    file_name_path = "data\\" + "quality_10000_result_cluster_200.csv"
    data = pd.DataFrame(output_message_list)
    data.to_csv(file_name_path, index=False, encoding='GBK')


def preprocee_table_images_data():
    file_path = "D:\\LLM\\need_product\\architecture\\images_table_05.xlsx"
    json_file_path = "data\\images_table_format_246.json"
    image_root = "data\\images\\"
    main_structure_data_path = "data\\images_table_format_10000.json"
    # image_generator_conversation_index(json_file_path)
    read_main_structure_data(main_structure_data_path)
