from rest_framework.routers import DefaultRouter

from .views import OfferDetailViewSet, OfferViewSet

router = DefaultRouter()
router.register('offers', OfferViewSet, basename='offer')
router.register('offerdetails', OfferDetailViewSet, basename='offerdetail')

urlpatterns = router.urls
