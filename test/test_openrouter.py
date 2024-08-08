import os

from model_runtime.entities.llm_entities import LLMResult, LLMResultChunk, LLMResultChunkDelta
from model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage, AssistantPromptMessage
from model_runtime.model_providers.openrouter.llm.llm import OpenRouterLargeLanguageModel

from collections.abc import Generator


def test_invoke_model():
    model = OpenRouterLargeLanguageModel()

    response = model.invoke(
        model='openai/gpt-4o-2024-08-06',
        credentials={
            'api_key': os.environ.get('OPENROUTER_API_KEY'),
            'mode': 'completion'
        },
        prompt_messages=[
            SystemPromptMessage(
                content='You are a helpful AI assistant.',
            ),
            UserPromptMessage(
                content='有那些建筑大模型?，请使用中文回复'
            )
        ],
        model_parameters={
            'temperature': 1.0,
            'top_k': 2,
            'top_p': 0.5,
        },
        stop=['How'],
        stream=False,
        user="abc-123"
    )

    assert isinstance(response, LLMResult)
    assert len(response.message.content) > 0


def test_invoke_stream_model():
    model = OpenRouterLargeLanguageModel()

    response = model.invoke(
        model='01-ai/yi-large',
        credentials={
            'api_key': os.environ.get('OPENROUTER_API_KEY'),
            'mode': 'chat'
        },
        prompt_messages=[
            SystemPromptMessage(
                content='You are a helpful AI assistant.',
            ),
            UserPromptMessage(
                content='你是谁？'
            )
        ],
        model_parameters={
            'temperature': 1.0,
            'top_k': 2,
            'top_p': 0.5,
        },
        stop=['How'],
        stream=True,
        user="abc-123"
    )

    assert isinstance(response, Generator)

    for chunk in response:
        assert isinstance(chunk, LLMResultChunk)
        assert isinstance(chunk.delta, LLMResultChunkDelta)
        assert isinstance(chunk.delta.message, AssistantPromptMessage)
        print(chunk.delta.message.content)


def test_get_num_tokens():
    model = OpenRouterLargeLanguageModel()

    num_tokens = model.get_num_tokens(
        model='01-ai/yi-large',
        credentials={
            'api_key': os.environ.get('OPENROUTER_API_KEY'),
        },
        prompt_messages=[
            SystemPromptMessage(
                content='You are a helpful AI assistant.',
            ),
            UserPromptMessage(
                content='Hello World!'
            )
        ]
    )

    assert isinstance(num_tokens, int)
    assert num_tokens == 21