from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import OrganisationViewSet, ExpenseTypeViewSet, PoolViewSet

router = DefaultRouter()
router.register(r'organisations', OrganisationViewSet, basename='organisation')
router.register(r'expensetypes', ExpenseTypeViewSet, basename='expensetype')
router.register(r'pool', PoolViewSet, basename='pool')

urlpatterns = [
    path('login/', obtain_auth_token, name='api_token_auth'),
    path('', include(router.urls)),
]
