from config.deloy_config import DeploymentConfig
from config.file_config import FileUploadConfig
from config.storge import MiddlewareConfig
from config.version_config import PackagingInfo


class AppConfig(
        FileUploadConfig,
        PackagingInfo,
        DeploymentConfig,
        MiddlewareConfig
):
    pass

