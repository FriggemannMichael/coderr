from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profiles_app.models import UserProfile
from reviews_app.models import Review


class BaseInfoView(APIView):
    """Return aggregate platform statistics for the landing page."""

    permission_classes = [AllowAny]

    def get(self, request):
        average = Review.objects.aggregate(value=Avg('rating'))['value']
        business_count = UserProfile.objects.filter(
            type=UserProfile.ProfileType.BUSINESS,
        ).count()
        return Response(
            {
                'review_count': Review.objects.count(),
                'average_rating': round(average, 1) if average is not None else 0,
                'business_profile_count': business_count,
                'offer_count': Offer.objects.count(),
            }
        )
