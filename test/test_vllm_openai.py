from openai import OpenAI
import loguru
openai_api_key = "empty"
openai_api_base = "http://36.103.239.202:9005/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
def test_vllm_openai_client():
    models = client.models.list()
    model = models.data[0].id
    loguru.logger.info(f"model name {model}")
    chat_response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                # NOTE: The prompt formatting with the image token `<image>` is not needed
                # since the prompt will be processed automatically by the API server.
                {"type": "text", "text": "该图片主要描述质量安全问题有那些"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://zhgd-prod-oss.oss-cn-shenzhen.aliyuncs.com/b16f009e-030d-4028-8866-45385891d97d.jpg",
                    },
                },
            ],
        }],
        stream=False
    )
    loguru.logger.info(f"reponse:{chat_response}")
