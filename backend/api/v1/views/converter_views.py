import logging

from drf_spectacular.utils import OpenApiResponse, OpenApiParameter, extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.converter_serializers import GetRatesSerializer, ErrorResponseSerializer
from ..services import CurrencyServiceException, CurrencyService

from django.core.cache import cache

logger = logging.getLogger(__name__)


# Create your views here.

@extend_schema(

    summary="Convert currency",
    description="Конвертация валюты из одной в другую с указанием суммы. Возвращает конвертированную сумму.",
    methods=['GET'],
    responses={
        200: OpenApiResponse(
            description="Successful Response",
            response=GetRatesSerializer(),
            examples=[
                OpenApiExample(
                    name="Пример успешной конвертации",
                    value={"result": 123.45}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка клиента: отсутствуют или неверные параметры.",
            response=ErrorResponseSerializer(),
            examples=[
                OpenApiExample(
                    name="Пример отсутствующих параметров",
                    value={
                        "detail": {
                            "code": "INVALID_PARAMETERS",
                            "message": "Отсутствуют параметры. Необходимы: from, to, value"
                        }
                    }
                ),
                OpenApiExample(
                    name="Пример неверных кодов валюты",
                    value={
                        "detail": {
                            "code": "INVALID_CURRENCY_CODE",
                            "message": "Неверные коды валюты. Должны быть строками."
                        }
                    }
                ),
                OpenApiExample(
                    name="Пример неверного значения суммы",
                    value={
                        "detail": {
                            "code": "INVALID_VALUE",
                            "message": "Неверное значение параметра. Должно быть числом."
                        }
                    }
                )
            ]
        ),
        404: OpenApiResponse(
            description="Не найдена указанная валюта.",
            response=ErrorResponseSerializer(),
            examples=[
                OpenApiExample(
                    name="Пример не найденной валюты",
                    value={
                        "detail": {
                            "code": "CURRENCY_NOT_FOUND",
                            "message": "Не найдена валюта RUS. Список доступных валют ['USD', 'EUR', ...]"
                        }
                    }
                )
            ]
        ),
        500: OpenApiResponse(
            description="Ошибка сервера при обработке запроса.",
            response=ErrorResponseSerializer(),
            examples=[
                OpenApiExample(
                    name="Пример ошибки сервера",
                    value={
                        "detail": {
                            "code": "CURRENCY_SERVICE_ERROR",
                            "message": "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже."
                        }
                    }
                )
            ]
        ),
    },

    parameters=[
        OpenApiParameter(
            name="from",
            type=str,
            description="Код валюты, из которой конвертируем",
            required=True,
            enum=CurrencyService.DB_VALUES
        ),
        OpenApiParameter(
            name="to",
            type=str,
            description="Код валюты, в которую конвертируем",
            required=True,
            enum=CurrencyService.DB_VALUES
        ),
        OpenApiParameter(
            name="value",
            type=float,
            description="Сумма для конвертации",
            required=True
        )
    ],

    tags=['Rates']

)
class CurrencyConverterView(APIView):
    @staticmethod
    def get(request):
        currency_service = CurrencyService()

        from_currency = request.query_params.get('from')
        to_currency = request.query_params.get('to')
        value = request.query_params.get('value')

        if not all([from_currency, to_currency, value]):
            return Response(
                data={'detail': {'code': 'INVALID_PARAMETERS',
                                 'message': 'Отсутствуют параметры. Необходимы: from, to, value'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(from_currency, str) or not isinstance(to_currency, str):
            return Response(
                data={
                    'detail': {'code': 'INVALID_CURRENCY_CODE',
                               'message': 'Неверные коды валюты. Должны быть строками.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not currency_service.check_currency(name_currency=from_currency):
            return Response(
                data={
                    'detail': {'code': 'CURRENCY_NOT_FOUND',
                               'message': f'Не найдена валюта {from_currency}. Список доступных валют: {currency_service.DB_VALUES}'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not currency_service.check_currency(name_currency=to_currency):
            return Response(
                data={
                    'detail': {'code': 'CURRENCY_NOT_FOUND',
                               'message': f'Не найдена валюта {to_currency}. Список доступных валют: {currency_service.DB_VALUES}'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            value = float(value)

        except ValueError:
            return Response(
                data={
                    'detail': {'code': 'INVALID_VALUE',
                               'message': 'Неверное значение параметра. Должно быть числом.'},
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = f'exchange_rate_{from_currency}_{to_currency}_{value}'

        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info(f'Кэшированный результат для ключа {cache_key} был возвращен.')

            return Response({'result': cached_result})

        try:

            exchange_rate = currency_service.get_exchange_rate(from_currency=from_currency, to_currency=to_currency)
            result = round(exchange_rate * value, 2)

            cache.set(cache_key, result, timeout=300)
            logger.info(f'Результат {result} для {cache_key} был сохранен в кэше.')

            return Response({'result': result})
        except CurrencyServiceException as e:
            return Response(e.detail, status=e.status_code)
