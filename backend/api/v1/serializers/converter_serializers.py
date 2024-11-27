from rest_framework import serializers


class GetRatesSerializer(serializers.Serializer):
    """Сериализатор для формата ответа API, который возвращает конвертированную валюту."""
    result = serializers.FloatField()


class ErrorDetailSerializer(serializers.Serializer):
    """Сериализатор для получения подробной информации об ошибках."""
    code = serializers.CharField(help_text="Код ошибки, идентифицирующий тип ошибки.")
    message = serializers.CharField(help_text="Сообщение об ошибке, которое объясняет, что пошло не так.")


class ErrorResponseSerializer(serializers.Serializer):
    """Сериализатор для универсального ответа на ошибку."""
    detail = ErrorDetailSerializer(help_text="Подробная информация об ошибке.")
