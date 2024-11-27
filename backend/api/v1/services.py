import logging

import requests
from django.conf import settings
from requests.exceptions import HTTPError
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class CurrencyServiceException(APIException):
    def __init__(self, status_code, detail, err_code='CURRENCY_SERVICE_ERROR'):
        self.status_code = status_code
        self.detail = {'code': err_code, 'message': detail}
        super().__init__(detail)


class CurrencyService:
    """
    Сервис для работы с валютами, включая проверку валют и получение курсов обмена.

    Атрибуты:
    - DB_VALUES: Множество, содержащее доступные коды/названия валют.
    """
    DB_VALUES = {
        "USD", "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN", "BAM", "BBD", "BDT", "BGN", "BHD",
        "BIF", "BMD", "BND", "BOB", "BRL", "BSD", "BTN", "BWP", "BYN", "BZD", "CAD", "CDF", "CHF", "CLP", "CNY", "COP",
        "CRC", "CUP", "CVE", "CZK", "DJF", "DKK", "DOP", "DZD", "EGP", "ERN", "ETB", "EUR", "FJD", "FKP", "FOK", "GBP",
        "GEL", "GGP", "GHS", "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF", "IDR", "ILS", "IMP",
        "INR", "IQD", "IRR", "ISK", "JEP", "JMD", "JOD", "JPY", "KES", "KGS", "KHR", "KID", "KMF", "KRW", "KWD", "KYD",
        "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "LYD", "MAD", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRU", "MUR",
        "MVR", "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "OMR", "PAB", "PEN", "PGK", "PHP",
        "PKR", "PLN", "PYG", "QAR", "RON", "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SLE",
        "SLL", "SOS", "SRD", "SSP", "STN", "SYP", "SZL", "THB", "TJS", "TMT", "TND", "TOP", "TRY", "TTD", "TVD", "TWD",
        "TZS", "UAH", "UGX", "UYU", "UZS", "VES", "VND", "VUV", "WST", "XAF", "XCD", "XDR", "XOF", "XPF", "YER", "ZAR",
        "ZMW", "ZWL"
    }

    def __init__(self):
        self.base_url = settings.BASE_URL
        self.api_key = settings.API_KEY

    def check_currency(self, name_currency: str) -> bool:
        """
        Метод для проверки наличия названия валюты в множестве(set) для запроса.
        :param name_currency: Название валюты (строка) для проверки.
        :return: Bool значение True, если валюта найдена в DB_VALUES, иначе False.
        """
        result = name_currency.upper() in self.DB_VALUES
        return result

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Метод для запроса курса валют у стороннего сервиса.
        :param from_currency: Название валюты, из которой конвертируем (строка).
        :param to_currency: Название валюты, в которую конвертируем (строка).
        :return: Курс обмена (float) между from_currency и to_currency.
        """
        try:
            url = f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Проверка на ошибки HTTP
            data = response.json()

            if data['result'] == 'success':
                rate = data['conversion_rate']
                if rate is None:
                    raise CurrencyServiceException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Не удалось получить обменный курс для {from_currency} на {to_currency}"
                    )
                return rate
            else:
                raise CurrencyServiceException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка внешнего API: {data.get('тип ошибки')}"
                )
        except HTTPError as e:
            logger.error(f"HTTP error from external API: {e}")
            raise CurrencyServiceException(
                status_code=e.response.status_code,
                detail=f"Ошибка при извлечении данных из внешнего API: {e}"
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Currency service unavailable: {e}")
            raise CurrencyServiceException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Услуга обмена валюты недоступна. Пожалуйста, повторите попытку позже."
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise CurrencyServiceException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка. Пожалуйста, повторите попытку позже."
            )
