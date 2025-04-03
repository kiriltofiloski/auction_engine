import django_filters
from .models import Auction

class AuctionFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='current_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='current_price', lookup_expr='lte')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Auction
        fields = ['name', 'min_price', 'max_price']