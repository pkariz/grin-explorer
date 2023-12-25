from django_filters import rest_framework as additional_filters
from rest_framework import authentication, filters, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication


class DefaultMixin(object):
    """
    Default settings for authentication, authorization and filtering. We support
    3 types of authentication:

    1. Session authentication
    2. Basic authentication sending username/password in every request
    """

    paginate_by = 50
    paginate_by_param = 'page_size'

    authentication_classes = (
        JWTAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    filter_backends = (
        additional_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    permission_classes = []


class CustomModelViewSet(
    DefaultMixin,
    viewsets.ModelViewSet
):
    """Default viewset for models."""
    pass

