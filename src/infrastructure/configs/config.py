import logging
import os
from enum import Enum
from typing import (
    Any,
    Dict,
    Optional,
)

import hvac
from hvac.exceptions import (
    InvalidPath,
    UnexpectedError,
    VaultError,
)
from pydantic import (
    AnyUrl,
    Field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)


class ConfigModelField(str, Enum):
    MODEL_FIELDS = 'model_fields'
    ENV_PREFIX = 'env_prefix'


class VaultHandleFields(str, Enum):
    VAULT_HOST = 'VAULT_HOST'
    VAULT_TOKEN = 'VAULT_TOKEN'
    VAULT_NAMESPACE = 'VAULT_NAMESPACE'
    VAULT_PATH = 'VAULT_PATH'
    VAULT_RESPONSE_DATA = 'data'


class VaultSettingsSource(EnvSettingsSource):
    """
    Super modified SettingsSource for Vault! It can do everything!
    """

    _instance = None
    dotenv_vars: dict = None

    def __init__(
        self, settings_cls: type[BaseSettings], case_sensitive: bool = False
    ) -> None:
        super().__init__(settings_cls)
        self.case_sensitive = case_sensitive

    def __new__(cls, settings_cls: type[BaseSettings], case_sensitive: bool = False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __call__(self) -> Dict[str, Any]:
        result_env_dict: Dict[str, Any] = {}
        # для каждого поля в классе конфига
        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key = self.get_field_value(field_name, field)
            if field_value is not None:
                result_env_dict[field_key] = field_value
        return result_env_dict

    def get_field_value(self, field: str, field_info: Any) -> tuple[Any, str]:
        env_val = self._read_vault_config(case_sensitive=self.case_sensitive)
        # обработка конфиг классов
        if hasattr(field_info.annotation, ConfigModelField.MODEL_FIELDS):
            prefix = field_info.annotation.model_config.get(
                ConfigModelField.ENV_PREFIX, ''
            )
            nested_values = {}
            for nested_field in field_info.annotation.model_fields:
                env_key = f'{prefix}{nested_field}'.lower()
                if env_key in env_val:
                    nested_values[nested_field] = env_val.get(env_key)
            return nested_values, field

        # обработка обычных полей конфига
        value = env_val.get(field.lower())
        return value, field

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        if value_is_complex:
            return field.annotation(**value)
        return value

    def flatten_json(self, json_obj: dict, prefix: str = '') -> dict:
        items = {}
        for key, value in json_obj.items():
            key_with_prefix = f'{prefix}_{key}' if prefix else key
            if isinstance(value, dict):
                items.update(self.flatten_json(value, prefix=key_with_prefix))
            else:
                items[key_with_prefix] = value
        return items

    def _read_vault_config(self, case_sensitive: bool) -> Dict[str, Optional[str]]:
        if self.dotenv_vars is not None:
            return self.dotenv_vars

        if (
            VaultHandleFields.VAULT_HOST not in os.environ
            or VaultHandleFields.VAULT_TOKEN not in os.environ
        ):
            self.dotenv_vars = {}
            return self.dotenv_vars

        client = hvac.Client(
            url=os.environ.get(VaultHandleFields.VAULT_HOST),
            token=os.environ.get(VaultHandleFields.VAULT_TOKEN),
        )

        dotenv_vars = {}
        try:
            # Сначала пробуем KV v2
            try:
                response = client.secrets.kv.v2.read_secret_version(
                    path=os.environ.get(VaultHandleFields.VAULT_PATH),
                    mount_point=os.environ.get(VaultHandleFields.VAULT_NAMESPACE),
                )
                # Для KV v2 данные в response['data']['data']
                secret_data = response.get(
                    VaultHandleFields.VAULT_RESPONSE_DATA, {}
                ).get(VaultHandleFields.VAULT_RESPONSE_DATA, {})
                logger.info('Using KV v2 engine')
            except Exception as e:
                logger.error(f'Error using kv2 {e}')
                # Если не получилось, пробуем KV v1
                response = client.secrets.kv.v1.read_secret(
                    path=os.environ.get(VaultHandleFields.VAULT_PATH),
                    mount_point=os.environ.get(VaultHandleFields.VAULT_NAMESPACE),
                )
                # Для KV v1 данные в response['data']
                secret_data = response.get(VaultHandleFields.VAULT_RESPONSE_DATA, {})
                logger.info('Using KV v1 engine')

            dotenv_vars = self.flatten_json(secret_data)

        except (VaultError, InvalidPath, UnexpectedError) as e:
            logger.error(f'Error reading from Vault: {e}')
        except (ConnectionError, TimeoutError) as e:
            logger.error(f'Connection error with Vault: {e}')
        finally:
            self.dotenv_vars = dotenv_vars

        if not case_sensitive:
            self.dotenv_vars = {k.lower(): v for k, v in self.dotenv_vars.items()}

        return self.dotenv_vars


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra='ignore')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            VaultSettingsSource(
                settings_cls, case_sensitive=False
            ),  # Add Vault as a settings source
        )


class _AsyncPostgresDsn(AnyUrl):
    allowed_schemes = {'postgres', 'postgresql', 'postgresql+asyncpg'}
    user_required = True


class PostgresConfig(BaseConfig):
    HOST: str = Field(default='localhost')
    PORT: int = Field(default=5432)
    USER: str = Field(default='postgres')
    PASSWORD: str = Field(default='postgres')
    DB: str = Field(default='postgres')
    URI: Optional[str] = None

    @field_validator('URI', mode='before')
    def assemble_async_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        db = info.data.get('DB')
        path = f'{db}' if db else ''
        url = _AsyncPostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=info.data.get('USER'),
            password=info.data.get('PASSWORD'),
            host=info.data.get('HOST'),
            port=info.data.get('PORT'),
            path=path,
        )
        return str(url)

    model_config = SettingsConfigDict(env_prefix='POSTGRES_')


class PostgresMasterConfig(PostgresConfig):
    model_config = SettingsConfigDict(env_prefix='POSTGRES_MASTER_')


class PostgresSlaveConfig(PostgresConfig):
    model_config = SettingsConfigDict(env_prefix='POSTGRES_SLAVE_')


class PostgresMasterSlaveConfig(BaseConfig):
    MASTER: PostgresMasterConfig = Field(default_factory=PostgresMasterConfig)
    SLAVE: PostgresSlaveConfig = Field(default_factory=PostgresSlaveConfig)


class CORSConfig(BaseConfig):
    ORIGINS: list = Field(default_factory=lambda: ['*'])
    METHODS: list = Field(default_factory=lambda: ['*'])
    HEADERS: list = Field(default_factory=lambda: ['*'])

    model_config = SettingsConfigDict(env_prefix='CORS_')


class Config(BaseConfig):
    PROJECT_NAME: str = Field(default='project-name')
    ENVIRONMENT: str = Field(default='dev')
    DEBUG: bool = Field(default=False)

    CORS_CONFIG: CORSConfig = Field(default_factory=CORSConfig)
    POSTGRES_CONFIG: PostgresMasterSlaveConfig = Field(
        default_factory=PostgresMasterSlaveConfig
    )


config = Config()
