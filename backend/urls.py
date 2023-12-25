from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .api.views import (
    index_view,
    BlockchainViewSet,
    BlockViewSet,
    NodeViewSet,
    NodeGroupViewSet,
)

router = routers.SimpleRouter()
router.register('blockchains', BlockchainViewSet)
router.register('nodes', NodeViewSet)
router.register('node-groups', NodeGroupViewSet)

block_router = routers.NestedSimpleRouter(
    router,
    r'blockchains',
    lookup='blockchain')

block_router.register(
    r'blocks',
    BlockViewSet,
    basename='blockchain-blocks'
)


urlpatterns = [
    path('', index_view, name='index'),
    # login
    path('api/account/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/account/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # admin
    path('api/admin/', admin.site.urls),
    # router
    path('api/', include(router.urls)),
    path('api/', include(block_router.urls)),
]

