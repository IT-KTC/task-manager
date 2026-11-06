
from django.core.exceptions import PermissionDenied

from .models import TeamMembership


def is_team_member(user, team):
    if not user.is_authenticated or not user.is_active:
        return False

    return TeamMembership.objects.filter(
        team=team,
        user=user,
    ).exists()


def is_team_leader(user, team):
    if not user.is_authenticated or not user.is_active:
        return False

    return TeamMembership.objects.filter(
        team=team,
        user=user,
        role=TeamMembership.Role.LEADER,
    ).exists()


def require_team_member(user, team):
    if not is_team_member(user, team):
        raise PermissionDenied(
            "Bạn không phải thành viên của nhóm này."
        )


def require_team_leader(user, team):
    if not is_team_leader(user, team):
        raise PermissionDenied(
            "Chỉ trưởng nhóm mới được thực hiện thao tác này."
        )
