import loguru
from flask_restful import Resource, reqparse
from werkzeug.exceptions import NotFound, InternalServerError

from controllers.app import api
from controllers.utils.error import ConversationNotExistsError, ConversationCompletedError, AppModelConfigBrokenError, \
    AppUnavailableError, ProviderNotInitializeError, ProviderQuotaExceededError, ProviderModelCurrentlyNotSupportError, \
    CompletionRequestError
from model_runtime.errors.invoke import InvokeError
from utils.error.error import ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError, \
    AppInvokeQuotaExceededError
from utils.libs.helper import compact_generate_response


class ChatMessageApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('inputs', type=dict, required=True, location='json')
        parser.add_argument('query', type=str, required=True, location='json')
        parser.add_argument('files', type=list, required=False, location='json')
        parser.add_argument('model_config', type=dict, required=True, location='json')
        parser.add_argument('conversation_id', type=uuid_value, location='json')
        parser.add_argument('response_mode', type=str, choices=['blocking', 'streaming'], location='json')
        parser.add_argument('retriever_from', type=str, required=False, default='dev', location='json')
        args = parser.parse_args()

        streaming = args['response_mode'] != 'blocking'
        args['auto_generate_name'] = False

        account = "flask_login.current_user"

        try:
            response = ""
            # response = AppGenerateService.generate(
            #     app_model=app_model,
            #     user=account,
            #     args=args,
            #     invoke_from=InvokeFrom.DEBUGGER,
            #     streaming=streaming
            # )

            return compact_generate_response(response)
        except ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except ConversationCompletedError:
            raise ConversationCompletedError()
        except AppModelConfigBrokenError:
            loguru.logger.info(f"App model config broken.")
            raise AppUnavailableError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except (ValueError, AppInvokeQuotaExceededError) as e:
            raise e
        except Exception as e:
            loguru.logger.info(f"internal server error.")
            raise InternalServerError()

api.add_resource(ChatMessageApi, '/apps/chat-messages')