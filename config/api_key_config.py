

from pydantic import Field
from pydantic_settings import BaseSettings


class ApiKeyInfo(BaseSettings):
    """
    Packaging build information
    """

    OPENROUTER_API_KEY: str = Field(
        description='Openrouter api key',
        default='',
    )

    TONGYI_DASHSCOPE_API_KEY: str = Field(
        description='tongyi api key',
        default='',
    )

    SILICONFLOW_API_KEY: str = Field(
        description='siliconflow api key',
        default='',
    )



