from pydantic import  Field, NonNegativeInt
from pydantic_settings import BaseSettings


class ImageFormatConfig(BaseSettings):
    MULTIMODAL_SEND_IMAGE_FORMAT: str = Field(
        description='multi model send image format, support base64, url, default is base64',
        default='base64',
    )


class FileUploadConfig(BaseSettings):
    """
    File Uploading configs
    """
    UPLOAD_FILE_SIZE_LIMIT: NonNegativeInt = Field(
        description='size limit in Megabytes for uploading files',
        default=15,
    )

    UPLOAD_FILE_BATCH_LIMIT: NonNegativeInt = Field(
        description='batch size limit for uploading files',
        default=5,
    )

    UPLOAD_IMAGE_FILE_SIZE_LIMIT: NonNegativeInt = Field(
        description='image file size limit in Megabytes for uploading files',
        default=10,
    )

    BATCH_UPLOAD_LIMIT: NonNegativeInt = Field(
        description='',  # todo: to be clarified
        default=20,
    )