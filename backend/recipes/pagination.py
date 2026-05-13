from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Кастомный пагинатор.
    Позволяет менять размер страницы через параметр ?limit=
    """
    page_size_query_param = 'limit'
    page_size = 6  # Кол-во рецептов на странице по умолчанию

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
