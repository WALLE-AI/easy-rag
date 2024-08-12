import base64

import loguru
from flask_restful import Resource, reqparse
from werkzeug.exceptions import NotFound, InternalServerError

from controllers.app import api
from controllers.utils.error import ConversationNotExistsError, ConversationCompletedError, AppModelConfigBrokenError, \
    AppUnavailableError, ProviderNotInitializeError, ProviderQuotaExceededError, ProviderModelCurrentlyNotSupportError, \
    CompletionRequestError
from model_runtime.errors.invoke import InvokeError
from services.file_service import FileService
from services.models_service import ModelService
from services.storge import storage
from utils.error.error import ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError, \
    AppInvokeQuotaExceededError
from utils.libs.helper import compact_generate_response


class ChatImageMessageApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('query', type=str, required=False, location='json')
        parser.add_argument('image_id', type=str, required=True, location='json')
        parser.add_argument('model_config', type=dict, required=True, location='json')
        parser.add_argument('conversation_id', type=str, location='json')
        parser.add_argument('response_mode', type=bool,default=False, location='json')
        parser.add_argument('retriever', type=bool, required=False, default=False, location='json')
        args = parser.parse_args()

        try:
            response_dict = {"hello":"world"}
            # image_id = 'upload_files/' + args.get("user_uuid") + '/' + args.get("image_id") + '.' + args.get("extension")
            try:
                data = FileService.get_public_image_preview(args.get("image_id"))
            except FileNotFoundError:
                loguru.logger.error(f'File not found: {args.get("image_id")}')
                return None
            encoded_string = base64.b64encode(data).decode('utf-8')
            image_data =  f'data:{args.get("mime_type")};base64,{encoded_string}'
            response = ModelService.invoke_llm(image_data,args)
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

api.add_resource(ChatImageMessageApi, '/chat-messages-image')