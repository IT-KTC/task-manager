
from .models import Notification


def notification_menu(request):
    if not request.user.is_authenticated:
        return {
            "notification_count": 0,
            "notification_recent": [],
        }

    notifications = Notification.objects.filter(
        user=request.user
    )

    return {
        "notification_count": notifications.filter(
            is_read=False
        ).count(),
        "notification_recent": notifications[:5],
    }
