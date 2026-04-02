from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from apps.accounts.decorators import verified_required
from .models import Project, ProjectMember, ProjectTask
from .forms import ProjectForm, TaskForm


@login_required
@verified_required
def project_list_view(request):
    projects = Project.objects.filter(status='open').select_related('owner')
    q = request.GET.get('q', '')
    if q:
        projects = projects.filter(Q(title__icontains=q) | Q(skills_needed__icontains=q))
    my_project_ids = ProjectMember.objects.filter(user=request.user, is_approved=True).values_list('project_id', flat=True)
    return render(request, 'projects/list.html', {
        'projects': projects, 'q': q, 'my_project_ids': set(my_project_ids)
    })


@login_required
@verified_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    members = project.project_members.filter(is_approved=True).select_related('user', 'user__profile')
    pending = project.project_members.filter(is_approved=False).select_related('user', 'user__profile')
    tasks   = project.tasks.all()
    is_member = project.project_members.filter(user=request.user, is_approved=True).exists()
    is_owner  = project.owner == request.user
    task_form = TaskForm(project=project)
    return render(request, 'projects/detail.html', {
        'project': project, 'members': members, 'pending': pending,
        'tasks': tasks, 'is_member': is_member, 'is_owner': is_owner,
        'task_form': task_form,
    })


@login_required
@verified_required
def create_project_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        # Owner auto-joins as approved member
        ProjectMember.objects.create(project=project, user=request.user, is_approved=True, role='Owner')
        messages.success(request, 'Project created!')
        return redirect('projects:detail', pk=project.pk)
    return render(request, 'projects/form.html', {'form': form})


@login_required
@verified_required
def join_project_view(request, pk):
    project = get_object_or_404(Project, pk=pk, status='open')
    if not ProjectMember.objects.filter(project=project, user=request.user).exists():
        role = request.POST.get('role', '')
        ProjectMember.objects.create(project=project, user=request.user, role=role, is_approved=False)
        messages.success(request, 'Application sent to the project owner.')
    else:
        messages.info(request, 'You already applied or are a member.')
    return redirect('projects:detail', pk=pk)


@login_required
@verified_required
def approve_member_view(request, pk, member_id):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    member  = get_object_or_404(ProjectMember, pk=member_id, project=project)
    member.is_approved = True
    member.save()
    messages.success(request, f'{member.user.get_full_name()} approved.')
    return redirect('projects:detail', pk=pk)


@login_required
@verified_required
def add_task_view(request, pk):
    project   = get_object_or_404(Project, pk=pk)
    is_member = project.project_members.filter(user=request.user, is_approved=True).exists()
    if not is_member:
        messages.error(request, 'Members only.')
        return redirect('projects:detail', pk=pk)
    form = TaskForm(request.POST, project=project)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        messages.success(request, 'Task added.')
    return redirect('projects:detail', pk=pk)


@login_required
@verified_required
def update_task_status_view(request, task_id):
    task   = get_object_or_404(ProjectTask, pk=task_id)
    status = request.POST.get('status')
    if status in ['todo', 'doing', 'done']:
        task.status = status
        task.save()
    return redirect('projects:detail', pk=task.project.pk)


@login_required
@verified_required
def my_projects_view(request):
    owned  = Project.objects.filter(owner=request.user)
    joined = Project.objects.filter(
        project_members__user=request.user,
        project_members__is_approved=True
    ).exclude(owner=request.user)
    return render(request, 'projects/my_projects.html', {'owned': owned, 'joined': joined})