
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TeamCreateForm, TeamMemberAddForm
from .models import Team, TeamMembership
from .permissions import require_team_leader
from .services import (
    add_team_member,
    create_team,
    remove_team_member,
)

User = get_user_model()


@login_required
def team_list(request):
    teams = Team.objects.filter(
        memberships__user=request.user
    ).distinct().order_by("-created_at")

    return render(
        request,
        "teams/team_list.html",
        {"teams": teams}
    )


@login_required
def team_create(request):
    if request.method == "POST":
        form = TeamCreateForm(request.POST)

        if form.is_valid():
            create_team(
                user=request.user,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"]
            )

            messages.success(
                request,
                "Tạo nhóm thành công!"
            )

            return redirect("team_list")

    else:
        form = TeamCreateForm()

    return render(
        request,
        "teams/team_create.html",
        {"form": form}
    )

@login_required
def team_detail(request, pk):

    team = get_object_or_404(
        Team.objects.filter(
            memberships__user=request.user
        ).distinct(),
        pk=pk
    )

    memberships = (
        TeamMembership.objects
        .filter(team=team)
        .select_related("user")
        .order_by("role", "joined_at")
    )

    is_leader = memberships.filter(
        user=request.user,
        role=TeamMembership.Role.LEADER
    ).exists()


    context = {
        "team": team,
        "memberships": memberships,
        "is_leader": is_leader,
    }

    return render(
        request,
        "teams/team_detail.html",
        context
    )

@login_required
def team_member_add(request, pk):

    team = get_object_or_404(
        Team.objects.filter(
            memberships__user=request.user
        ).distinct(),
        pk=pk
    )

    require_team_leader(request.user, team)

    if request.method == "POST":
        form = TeamMemberAddForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]

            new_member = User.objects.filter(
                username=username
            ).first()

            if new_member is None:
                form.add_error(
                    "username",
                    "Không tìm thấy tài khoản này."
                )
            else:
                try:
                    add_team_member(
                        actor=request.user,
                        team=team,
                        new_member=new_member,
                    )
                except ValidationError as exc:
                    form.add_error("username", exc)
                else:
                    messages.success(
                        request,
                        f"Đã thêm {new_member.username} vào nhóm."
                    )

                    return redirect(
                        "team_detail",
                        pk=team.pk
                    )

    else:
        form = TeamMemberAddForm()

    return render(
        request,
        "teams/team_member_add.html",
        {
            "team": team,
            "form": form,
        }
    )

@login_required
@require_POST
def team_member_remove(request, pk, membership_id):

    team = get_object_or_404(
        Team.objects.filter(
            memberships__user=request.user
        ).distinct(),
        pk=pk
    )

    require_team_leader(request.user, team)

    membership = get_object_or_404(
        TeamMembership.objects.select_related("user"),
        pk=membership_id,
        team=team,
    )

    try:
        remove_team_member(
            actor=request.user,
            team=team,
            member=membership.user,
        )

    except ValidationError as exc:
        messages.error(
            request,
            "; ".join(exc.messages)
        )

    else:
        messages.success(
            request,
            "Đã xóa thành viên khỏi nhóm."
        )

    return redirect(
        "team_detail",
        pk=team.pk
    )
