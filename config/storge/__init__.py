from pydantic import Field
from pydantic_settings import BaseSettings

from config.storge.aliyun_config import AliyunOSSStorageConfig


class StorageConfig(BaseSettings):
    STORAGE_TYPE: str = Field(
        description='storage type,'
                    ' default to `local`,'
                    ' available values are `local`, `s3`, `azure-blob`, `aliyun-oss`, `google-storage`.',
        default='local',
    )

    STORAGE_LOCAL_PATH: str = Field(
        description='local storage path',
        default='storage',
    )

class MiddlewareConfig(
    # place the configs in alphabet order

    # configs of storage and storage providers
    StorageConfig,
    AliyunOSSStorageConfig,

):
    pass