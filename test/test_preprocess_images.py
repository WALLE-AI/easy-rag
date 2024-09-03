import json

import loguru
import pandas as pd
import requests

from rag.entities.entity_images import ImageTableProcess

sheet_name = ["Sheet1","Sheet1(2)","Sheet1(3),Sheet1(4),Sheet1(5)"]


##{'单号': '0000096ed25ec73466f0bbc48061acc4', '项目id': 232, '照片': 'https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/af0d013d-2f52-2c97-413b-55970976ec61.jpg', '隐患部位': 'S3首层', '标准隐患编号': 'dba507c450c247da989bc154c0f80612', '隐患内容': '构造柱钢筋未满绑', 'company_hidden_id': 'dba507c450c247da989bc154c0f80612', 'name': '建筑装饰装修'}


def write_json_file(data_dict,save_file_name):
    jsonn_str_data = json.dumps(data_dict,ensure_ascii=False)
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
    except requests.RequestException as e:
        loguru.logger.info(f"request error：{e}")
    except IOError as e:
        loguru.logger.info(f"request io error：{e}")


def read_xlsx_file_to_save_json(file_path):
    data = pd.read_excel(file_path)
    data = data.head(10)
    data_save_list = []
    for index, row_data in data.iterrows():
        data_dict = row_data.to_dict()
        image_name = data_dict['照片'].split("https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/")[-1]
        ##download image dir
        download_image(data_dict['照片'],image_name)
        data_entity = ImageTableProcess(
            id=str(index),
            image_id=image_name,
            image_correct_id="",
            image_oss_url=data_dict['照片'],
            conversations=[{}],
            position=data_dict["隐患部位"] if isinstance(data_dict['隐患部位'], str) else "",
            accident_label=data_dict['name'],
            description=data_dict['隐患内容'],
            correct_description="",
            type = data_dict['类型'],
            risk="",
            correct_basic="",
            label="0"
        )
        data_save_list.append(data_entity.to_dict())
        if not index % 5 and index !=0:
            save_file_name = "data/images_table_format_"+str(index) +".json"
            write_json_file(data_save_list,save_file_name)
            ##每超过10W，保存一次，清洗之前的数组中数据
            data_save_list.clear()


def preprocee_table_images_data():
    file_path = "D:\\LLM\\need_product\\architecture\\split_part1.xlsx"
    read_xlsx_file_to_save_json(file_path)
