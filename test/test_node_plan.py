import loguru
import pandas as pd


class NodePlanProject():
    def __init__(self):
        self.desc = "node plan project"

    def __str__(self):
        return self.desc

    @classmethod
    def preprocess_xlsx_data(cls, file_path):
        data = cls()._read_xlsx_file_data(file_path)
        loguru.logger.info(f"data file {data.head()}")

    def _read_xlsx_file_data(self, file_path):
        return pd.read_excel(file_path)



def test_node_plan():
    file_path = "D:\\LLM\\planNode\\A项目.xlsx"
    NodePlanProject.preprocess_xlsx_data(file_path)