from django.urls import path
from .views.converter_views import CurrencyConverterView

urlpatterns = [
    path('rates/', CurrencyConverterView.as_view(), name='currency_converter'),
]