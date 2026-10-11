from django.conf import settings


def campaign_dates(request):
    return {
        "campaign_start_date": settings.CAMPAIGN_START_DATE,
        "campaign_end_date": settings.CAMPAIGN_END_DATE,
    }
