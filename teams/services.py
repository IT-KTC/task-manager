
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Team, TeamMembership
from .permissions import require_team_leader


@transaction.atomic
def create_team(user, name, description=""):
    if not user.is_authenticated or not user.is_active:
        raise ValidationError(
            "Tài khoản không có quyền tạo nhóm."
        )

    name = name.strip()

    if not name:
        raise ValidationError(
            "Tên nhóm không được để trống."
        )

    team = Team.objects.create(
        name=name,
        description=description,
        created_by=user,
    )

    TeamMembership.objects.create(
        team=team,
        user=user,
        role=TeamMembership.Role.LEADER,
    )

    return team

@transaction.atomic
def add_team_member(actor, team, new_member):

    require_team_leader(actor, team)

  
    if not new_member.is_active:
        raise ValidationError(
            "Không thể thêm tài khoản đã bị vô hiệu hóa."
        )

    if TeamMembership.objects.filter(
        team=team,
        user=new_member,
    ).exists():
        raise ValidationError(
            "Người dùng đã là thành viên của nhóm."
        )

  
    membership = TeamMembership.objects.create(
        team=team,
        user=new_member,
        role=TeamMembership.Role.MEMBER,
    )

    return membership

@transaction.atomic
def remove_team_member(actor, team, member):


    require_team_leader(actor, team)


    membership = TeamMembership.objects.filter(
        team=team,
        user=member,
    ).first()

    if membership is None:
        raise ValidationError(
            "Người dùng không thuộc nhóm này."
        )

  
    if membership.role == TeamMembership.Role.LEADER:
        raise ValidationError(
            "Không thể xóa trưởng nhóm bằng chức năng này."
        )

  
    membership.delete()
