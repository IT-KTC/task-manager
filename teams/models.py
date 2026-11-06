
from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_teams"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

class TeamMembership(models.Model):

    class Role(models.TextChoices):
        LEADER = "leader", "Trưởng nhóm"
        MEMBER = "member", "Thành viên"

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_user"
            ),
            models.UniqueConstraint(
                fields=["team"],
                condition=models.Q(role="leader"),
                name="unique_team_leader"
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.team.name} - "
            f"{self.get_role_display()}"
        )
