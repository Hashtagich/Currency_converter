import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services import CurrencyServiceException, CurrencyService

logger = logging.getLogger(__name__)


# Create your views here.


class CurrencyConverterView(APIView):
    def get(self, request):
        currency_service = CurrencyService()

        from_currency = request.query_params.get('from')
        to_currency = request.query_params.get('to')
        value = request.query_params.get('value')

        if not all([from_currency, to_currency, value]):
            return Response(
                {'error': 'Missing parameters. Required: from, to, value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(from_currency, str) or not isinstance(to_currency, str):
            return Response(
                {'error': 'Invalid currency codes. Must be strings.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not currency_service.check_currency(name_currency=from_currency):
            return Response(
                {'error': f'Not find {from_currency}. List of data {currency_service.DB_VALUES}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not currency_service.check_currency(name_currency=to_currency):
            return Response(
                {'error': f'Not find {to_currency}. List of data {currency_service.DB_VALUES}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            value = float(value)
        except ValueError:
            return Response(
                {'error': 'Invalid value parameter. Must be a number.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exchange_rate = currency_service.get_exchange_rate(from_currency=from_currency, to_currency=to_currency)
            result = exchange_rate * value
            return Response({'result': result})
        except CurrencyServiceException as e:
            return Response(e.detail, status=e.status_code)
