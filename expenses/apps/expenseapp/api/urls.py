from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganisationViewSet, ExpenseTypeViewSet, PoolViewSet, ThrottledObtainAuthToken

router = DefaultRouter()
router.register(r'organisations', OrganisationViewSet, basename='organisation')
router.register(r'expensetypes', ExpenseTypeViewSet, basename='expensetype')
router.register(r'pool', PoolViewSet, basename='pool')

urlpatterns = [
    path('login/', ThrottledObtainAuthToken.as_view(), name='api_token_auth'),
    path('', include(router.urls)),
]
