from pydantic_settings import SettingsConfigDict

from config.api_key_config import ApiKeyInfo
from config.chroma_config import ChromaConfig
from config.database_config import DatabaseConfig
from config.deloy_config import DeploymentConfig
from config.file_config import FileUploadConfig, ImageFormatConfig
from config.redis_config import RedisConfig
from config.storge import MiddlewareConfig
from config.version_config import PackagingInfo


class AppConfig(
        FileUploadConfig,
        PackagingInfo,
        DeploymentConfig,
        MiddlewareConfig,
        DatabaseConfig,
        ImageFormatConfig,
        ApiKeyInfo,
        ChromaConfig,
        RedisConfig
):
    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file='.env',
        env_file_encoding='utf-8',
        frozen=True,

        # ignore extra attributes
        extra='ignore',
    )
    pass

