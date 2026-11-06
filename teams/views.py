
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.services import assign_task

from .forms import (
    TeamCreateForm,
    TeamMemberAddForm,
    TeamTaskAssignForm,
    TeamTaskCreateForm,
)
from .models import Team, TeamMembership
from .permissions import require_team_leader
from .services import (
    add_team_member,
    create_team,
    remove_team_member,
)

User = get_user_model()

def _get_member_team(request, pk):
    return get_object_or_404(
        Team.objects.filter(
            memberships__user=request.user
        ).distinct(),
        pk=pk,
    )


@login_required
def team_task_create(request, pk):
    # Bước 1: Tìm đúng nhóm
    team = _get_member_team(request, pk)

    # Bước 2: Kiểm tra quyền trưởng nhóm
    require_team_leader(request.user, team)

    # Bước 3: Nhận dữ liệu form
    if request.method == "POST":
        form = TeamTaskCreateForm(
            request.POST,
            request.FILES,
            team=team,
        )

        if form.is_valid():
            assignee = form.cleaned_data["assignee"]

            with transaction.atomic():
                # Chưa lưu vào database
                task = form.save(commit=False)

                # Backend tự thiết lập quyền sở hữu
                task.user = request.user
                task.team = team
                task.assignee = None
                task._activity_actor = request.user

                # Tạo Task
                task.save()

                # Giao việc nếu có chọn thành viên
                if assignee is not None:
                    assign_task(
                        actor=request.user,
                        task=task,
                        assignee=assignee,
                    )

            messages.success(
                request,
                "Đã tạo công việc nhóm thành công."
            )

            return redirect(
                "team_detail",
                pk=team.pk,
            )

    else:
        form = TeamTaskCreateForm(team=team)

    return render(
        request,
        "teams/team_task_create.html",
        {
            "team": team,
            "form": form,
        }
    )

@login_required
def team_task_assign(request, pk, task_pk):
    team = _get_member_team(request, pk)

    # Chỉ trưởng nhóm có quyền phân công
    require_team_leader(request.user, team)

    # Task phải thực sự thuộc nhóm này
    task = get_object_or_404(
        Task,
        pk=task_pk,
        team=team,
    )

    if request.method == "POST":
        form = TeamTaskAssignForm(
            request.POST,
            team=team,
        )

        if form.is_valid():
            try:
                assign_task(
                    actor=request.user,
                    task=task,
                    assignee=form.cleaned_data["assignee"],
                )
            except ValidationError as exc:
                form.add_error("assignee", exc)

            else:
                messages.success(
                    request,
                    "Cập nhật người phụ trách thành công."
                )

                return redirect(
                    "team_detail",
                    pk=team.pk,
                )

    else:
        form = TeamTaskAssignForm(
            team=team,
            initial={
                "assignee": task.assignee_id,
            },
        )

    return render(
        request,
        "teams/team_task_assign.html",
        {
            "team": team,
            "task": task,
            "form": form,
        },
    )

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
    team = _get_member_team(request, pk)

    memberships = (
        TeamMembership.objects
        .filter(team=team)
        .select_related("user")
        .order_by("role", "joined_at")
    )

    is_leader = memberships.filter(
        user=request.user,
        role=TeamMembership.Role.LEADER,
    ).exists()

    team_tasks = (
        Task.objects
        .visible_to(request.user)
        .filter(team=team)
        .select_related("user", "assignee")
        .order_by("-created_at", "-pk")
    )

    task_stats = team_tasks.aggregate(
        total=Count("id"),
        in_progress=Count(
            "id",
            filter=Q(status=Task.Status.IN_PROGRESS),
        ),
        completed=Count(
            "id",
            filter=Q(status=Task.Status.COMPLETED),
        ),
    )

    return render(
        request,
        "teams/team_detail.html",
        {
            "team": team,
            "memberships": memberships,
            "is_leader": is_leader,
            "team_tasks": team_tasks,
            "task_stats": task_stats,
        }
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

@login_required
def team_progress(request, pk):
    team = _get_member_team(request, pk)

  
    require_team_leader(request.user, team)

    team_tasks = Task.objects.filter(team=team)

    totals = team_tasks.aggregate(
        total=Count("id"),
        pending=Count(
            "id",
            filter=Q(status=Task.Status.PENDING),
        ),
        in_progress=Count(
            "id",
            filter=Q(status=Task.Status.IN_PROGRESS),
        ),
        completed=Count(
            "id",
            filter=Q(status=Task.Status.COMPLETED),
        ),
    )

    memberships = (
        TeamMembership.objects
        .filter(team=team)
        .select_related("user")
        .order_by("role", "joined_at")
    )

    member_stats = []

    for membership in memberships:
        assigned_tasks = team_tasks.filter(
            assignee_id=membership.user_id
        )

        total = assigned_tasks.count()

        completed = assigned_tasks.filter(
            status=Task.Status.COMPLETED
        ).count()

        in_progress = assigned_tasks.filter(
            status=Task.Status.IN_PROGRESS
        ).count()

        pending = assigned_tasks.filter(
            status=Task.Status.PENDING
        ).count()

        percent = (
            round(completed / total * 100)
            if total > 0 else 0
        )

        member_stats.append({
            "membership": membership,
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "percent": percent,
        })

    member_ids = [
        membership.user_id
        for membership in memberships
    ]

    unassigned_count = team_tasks.filter(
        assignee__isnull=True
    ).count()

    former_member_count = (
        team_tasks
        .filter(assignee__isnull=False)
        .exclude(assignee_id__in=member_ids)
        .count()
    )

    return render(
        request,
        "teams/team_progress.html",
        {
            "team": team,
            "totals": totals,
            "member_stats": member_stats,
            "unassigned_count": unassigned_count,
            "former_member_count": former_member_count,
        },
    )
