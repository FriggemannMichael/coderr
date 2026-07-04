from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from offers_app.models import Offer, OfferDetail

from .permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from .serializers import (
    OfferDetailSerializer,
    OfferReadSerializer,
    OfferSerializer,
)


class OfferViewSet(ModelViewSet):
    queryset = Offer.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsBusinessUser,
        IsOfferOwnerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return OfferReadSerializer

        return OfferSerializer


class OfferDetailViewSet(ModelViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
