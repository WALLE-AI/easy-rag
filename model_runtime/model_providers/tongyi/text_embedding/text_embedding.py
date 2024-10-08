import time
from typing import Optional

import dashscope

from model_runtime.entities.model_entities import PriceType
from model_runtime.entities.text_embedding_entities import (
    EmbeddingUsage,
    TextEmbeddingResult,
)
from model_runtime.errors.validate import CredentialsValidateFailedError
from model_runtime.model_providers.__base.text_embedding_model import (
    TextEmbeddingModel,
)
from model_runtime.model_providers.tongyi._common import _CommonTongyi


class TongyiTextEmbeddingModel(_CommonTongyi, TextEmbeddingModel):
    """
    Model class for Tongyi text embedding model.
    """

    def _invoke(
            self,
            model: str,
            credentials: dict,
            texts: list[str],
            user: Optional[str] = None,
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding model

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :param user: unique user id
        :return: embeddings result
        """
        credentials_kwargs = self._to_credential_kwargs(credentials)
        embeddings, embedding_used_tokens = self.embed_documents(
            credentials_kwargs=credentials_kwargs,
            model=model,
            texts=texts
        )

        return TextEmbeddingResult(
            embeddings=embeddings,
            usage=self._calc_response_usage(model, credentials_kwargs, embedding_used_tokens),
            model=model
        )

    def get_num_tokens(self, model: str, credentials: dict, texts: list[str]) -> int:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :return:
        """
        if len(texts) == 0:
            return 0
        total_num_tokens = 0
        for text in texts:
            total_num_tokens += self._get_num_tokens_by_gpt2(text)

        return total_num_tokens

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            # transform credentials to kwargs for model instance
            credentials_kwargs = self._to_credential_kwargs(credentials)

            # call embedding model
            self.embed_documents(credentials_kwargs=credentials_kwargs, model=model, texts=["ping"])
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    @staticmethod
    def embed_documents(credentials_kwargs: dict, model: str, texts: list[str]) -> tuple[list[list[float]], int]:
        """Call out to Tongyi's embedding endpoint.

        Args:
            credentials_kwargs: The credentials to use for the call.
            model: The model to use for embedding.
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text, and tokens usage.
        """
        embeddings = []
        embedding_used_tokens = 0
        for text in texts:
            response = dashscope.TextEmbedding.call(
                api_key=credentials_kwargs["dashscope_api_key"],
                model=model,
                input=text,
                text_type="document"
            )
            data = response.output["embeddings"][0]
            embeddings.append(data["embedding"])
            embedding_used_tokens += response.usage["total_tokens"]

        return [list(map(float, e)) for e in embeddings], embedding_used_tokens

    def _calc_response_usage(
            self, model: str, credentials: dict, tokens: int
    ) -> EmbeddingUsage:
        """
        Calculate response usage

        :param model: model name
        :param tokens: input tokens
        :return: usage
        """
        # get input price info
        input_price_info = self.get_price(
            model=model,
            credentials=credentials,
            price_type=PriceType.INPUT,
            tokens=tokens
        )

        # transform usage
        usage = EmbeddingUsage(
            tokens=tokens,
            total_tokens=tokens,
            unit_price=input_price_info.unit_price,
            price_unit=input_price_info.unit,
            total_price=input_price_info.total_amount,
            currency=input_price_info.currency,
            latency=time.perf_counter() - self.started_at
        )

        return usage
