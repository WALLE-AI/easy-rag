from typing import Any
from urllib.parse import quote_plus

from pydantic import Field, NonNegativeInt, PositiveInt, computed_field
class DatabaseConfig:
    DB_HOST: str = Field(
        description='db host',
        default='localhost',
    )

    DB_PORT: PositiveInt = Field(
        description='db port',
        default=5432,
    )

    DB_USERNAME: str = Field(
        description='db username',
        default='postgres',
    )

    DB_PASSWORD: str = Field(
        description='db password',
        default='',
    )

    DB_DATABASE: str = Field(
        description='db database',
        default='dify',
    )

    DB_CHARSET: str = Field(
        description='db charset',
        default='',
    )

    DB_EXTRAS: str = Field(
        description='db extras options. Example: keepalives_idle=60&keepalives=1',
        default='',
    )

    SQLALCHEMY_DATABASE_URI_SCHEME: str = Field(
        description='db uri scheme',
        default='postgresql',
    )

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        db_extras = (
            f"{self.DB_EXTRAS}&client_encoding={self.DB_CHARSET}"
            if self.DB_CHARSET
            else self.DB_EXTRAS
        ).strip("&")
        db_extras = f"?{db_extras}" if db_extras else ""
        return (f"{self.SQLALCHEMY_DATABASE_URI_SCHEME}://"
                f"{quote_plus(self.DB_USERNAME)}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}" 
                f"{db_extras}")

    SQLALCHEMY_POOL_SIZE: NonNegativeInt = Field(
        description='pool size of SqlAlchemy',
        default=30,
    )

    SQLALCHEMY_MAX_OVERFLOW: NonNegativeInt = Field(
        description='max overflows for SqlAlchemy',
        default=10,
    )

    SQLALCHEMY_POOL_RECYCLE: NonNegativeInt = Field(
        description='SqlAlchemy pool recycle',
        default=3600,
    )

    SQLALCHEMY_POOL_PRE_PING: bool = Field(
        description='whether to enable pool pre-ping in SqlAlchemy',
        default=False,
    )

    SQLALCHEMY_ECHO: bool | str = Field(
        description='whether to enable SqlAlchemy echo',
        default=False,
    )

    @computed_field
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, Any]:
        return {
            'pool_size': self.SQLALCHEMY_POOL_SIZE,
            'max_overflow': self.SQLALCHEMY_MAX_OVERFLOW,
            'pool_recycle': self.SQLALCHEMY_POOL_RECYCLE,
            'pool_pre_ping': self.SQLALCHEMY_POOL_PRE_PING,
            'connect_args': {'options': '-c timezone=UTC'},
        }
