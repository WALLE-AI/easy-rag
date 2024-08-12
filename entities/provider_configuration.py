import datetime
import json
import logging
from collections import defaultdict
from collections.abc import Iterator
from json import JSONDecodeError
from typing import Optional

from pydantic import BaseModel, ConfigDict

from entities.model_entities import ModelStatus, ModelWithProviderEntity, SimpleModelProviderEntity
from entities.provider_entities import (
    CustomConfiguration,
    ModelSettings,
    SystemConfiguration,
    SystemConfigurationStatus,
)

from model_runtime.entities.model_entities import FetchFrom, ModelType
from model_runtime.entities.provider_entities import (
    ConfigurateMethod,
    CredentialFormSchema,
    FormType,
    ProviderEntity,
)
from model_runtime.model_providers import model_provider_factory
from model_runtime.model_providers.__base.ai_model import AIModel
from model_runtime.model_providers.__base.model_provider import ModelProvider


from utils.models.provider import ProviderType

# from utils.models.provider import (
#     LoadBalancingModelConfig,
#     Provider,
#     ProviderModel,
#     ProviderModelSetting,
#     ProviderType,
#     TenantPreferredModelProvider,
# )

logger = logging.getLogger(__name__)

original_provider_configurate_methods = {}


class ProviderConfiguration(BaseModel):
    """
    Model class for provider configuration.
    """
    tenant_id: str
    provider: ProviderEntity
    preferred_provider_type: ProviderType
    using_provider_type: ProviderType
    system_configuration: SystemConfiguration
    custom_configuration: CustomConfiguration
    model_settings: list[ModelSettings]

    # pydantic configs
    model_config = ConfigDict(protected_namespaces=())

    def __init__(self, **data):
        super().__init__(**data)

        if self.provider.provider not in original_provider_configurate_methods:
            original_provider_configurate_methods[self.provider.provider] = []
            for configurate_method in self.provider.configurate_methods:
                original_provider_configurate_methods[self.provider.provider].append(configurate_method)

        if original_provider_configurate_methods[self.provider.provider] == [ConfigurateMethod.CUSTOMIZABLE_MODEL]:
            if (any(len(quota_configuration.restrict_models) > 0
                     for quota_configuration in self.system_configuration.quota_configurations)
                    and ConfigurateMethod.PREDEFINED_MODEL not in self.provider.configurate_methods):
                self.provider.configurate_methods.append(ConfigurateMethod.PREDEFINED_MODEL)

    def get_current_credentials(self, model_type: ModelType, model: str) -> Optional[dict]:
        """
        Get current credentials.

        :param model_type: model type
        :param model: model name
        :return:
        """
        if self.model_settings:
            # check if model is disabled by admin
            for model_setting in self.model_settings:
                if (model_setting.model_type == model_type
                        and model_setting.model == model):
                    if not model_setting.enabled:
                        raise ValueError(f'Model {model} is disabled.')

        if self.using_provider_type == ProviderType.SYSTEM:
            restrict_models = []
            for quota_configuration in self.system_configuration.quota_configurations:
                if self.system_configuration.current_quota_type != quota_configuration.quota_type:
                    continue

                restrict_models = quota_configuration.restrict_models

            copy_credentials = self.system_configuration.credentials.copy()
            if restrict_models:
                for restrict_model in restrict_models:
                    if (restrict_model.model_type == model_type
                            and restrict_model.model == model
                            and restrict_model.base_model_name):
                        copy_credentials['base_model_name'] = restrict_model.base_model_name

            return copy_credentials
        else:
            credentials = None
            if self.custom_configuration.models:
                for model_configuration in self.custom_configuration.models:
                    if model_configuration.model_type == model_type and model_configuration.model == model:
                        credentials = model_configuration.credentials
                        break

            if self.custom_configuration.provider:
                credentials = self.custom_configuration.provider.credentials

            return credentials

    def get_system_configuration_status(self) -> SystemConfigurationStatus:
        """
        Get system configuration status.
        :return:
        """
        if self.system_configuration.enabled is False:
            return SystemConfigurationStatus.UNSUPPORTED

        current_quota_type = self.system_configuration.current_quota_type
        current_quota_configuration = next(
            (q for q in self.system_configuration.quota_configurations if q.quota_type == current_quota_type),
            None
        )

        return SystemConfigurationStatus.ACTIVE if current_quota_configuration.is_valid else \
            SystemConfigurationStatus.QUOTA_EXCEEDED

    def is_custom_configuration_available(self) -> bool:
        """
        Check custom configuration available.
        :return:
        """
        return (self.custom_configuration.provider is not None
                or len(self.custom_configuration.models) > 0)

    def get_custom_credentials(self, obfuscated: bool = False) -> Optional[dict]:
        """
        Get custom credentials.

        :param obfuscated: obfuscated secret data in credentials
        :return:
        """
        if self.custom_configuration.provider is None:
            return None

        credentials = self.custom_configuration.provider.credentials
        if not obfuscated:
            return credentials

        # Obfuscate credentials
        return self.obfuscated_credentials(
            credentials=credentials,
            credential_form_schemas=self.provider.provider_credential_schema.credential_form_schemas
            if self.provider.provider_credential_schema else []
        )






class ProviderConfigurations(BaseModel):
    """
    Model class for provider configuration dict.
    """
    tenant_id: str
    configurations: dict[str, ProviderConfiguration] = {}

    def __init__(self, tenant_id: str):
        super().__init__(tenant_id=tenant_id)

    def get_models(self,
                   provider: Optional[str] = None,
                   model_type: Optional[ModelType] = None,
                   only_active: bool = False) \
            -> list[ModelWithProviderEntity]:
        """
        Get available models.

        If preferred provider type is `system`:
          Get the current **system mode** if provider supported,
          if all system modes are not available (no quota), it is considered to be the **custom credential mode**.
          If there is no model configured in custom mode, it is treated as no_configure.
        system > custom > no_configure

        If preferred provider type is `custom`:
          If custom credentials are configured, it is treated as custom mode.
          Otherwise, get the current **system mode** if supported,
          If all system modes are not available (no quota), it is treated as no_configure.
        custom > system > no_configure

        If real mode is `system`, use system credentials to get models,
          paid quotas > provider free quotas > system free quotas
          include pre-defined models (exclude GPT-4, status marked as `no_permission`).
        If real mode is `custom`, use workspace custom credentials to get models,
          include pre-defined models, custom models(manual append).
        If real mode is `no_configure`, only return pre-defined models from `model runtime`.
          (model status marked as `no_configure` if preferred provider type is `custom` otherwise `quota_exceeded`)
        model status marked as `active` is available.

        :param provider: provider name
        :param model_type: model type
        :param only_active: only active models
        :return:
        """
        all_models = []
        for provider_configuration in self.values():
            if provider and provider_configuration.provider.provider != provider:
                continue

            all_models.extend(provider_configuration.get_provider_models(model_type, only_active))

        return all_models

    def to_list(self) -> list[ProviderConfiguration]:
        """
        Convert to list.

        :return:
        """
        return list(self.values())

    def __getitem__(self, key):
        return self.configurations[key]

    def __setitem__(self, key, value):
        self.configurations[key] = value

    def __iter__(self):
        return iter(self.configurations)

    def values(self) -> Iterator[ProviderConfiguration]:
        return self.configurations.values()

    def get(self, key, default=None):
        return self.configurations.get(key, default)


class ProviderModelBundle(BaseModel):
    """
    Provider model bundle.
    """
    configuration: ProviderConfiguration
    provider_instance: ModelProvider
    model_type_instance: AIModel

    # pydantic configs
    model_config = ConfigDict(arbitrary_types_allowed=True,
                              protected_namespaces=())
