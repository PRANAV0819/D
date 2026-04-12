from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.contrib import messages

from apps.accounts.decorators import verified_required, student_required
from .models import Resource
from .forms import ResourceForm


@student_required
@verified_required
def resource_list_view(request):
    resources = Resource.objects.select_related('uploaded_by')
    category = request.GET.get('category', '')
    dept     = request.GET.get('dept', '')
    q        = request.GET.get('q', '')

    if category:
        resources = resources.filter(category=category)
    if dept:
        resources = resources.filter(department=dept)
    if q:
        resources = resources.filter(title__icontains=q)

    from apps.accounts.models import DEPARTMENT_CHOICES
    from .models import ResourceCategory

    return render(request, 'resources/list.html', {
        'resources': resources,
        'departments': DEPARTMENT_CHOICES,
        'category': category,
        'dept': dept,
        'q': q,
        'categories': ResourceCategory.choices,
    })


@student_required
@verified_required
def upload_resource_view(request):
    form = ResourceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        r = form.save(commit=False)
        r.uploaded_by = request.user
        r.save()
        from apps.gamification.models import UserActivity
        UserActivity.log(user=request.user, action=UserActivity.Action.UPLOAD)
        messages.success(request, 'Resource uploaded!')
        return redirect('resources:list')
    return render(request, 'resources/form.html', {'form': form})


@student_required
@verified_required
def download_resource_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    resource.download_count += 1
    resource.save(update_fields=['download_count'])
    
    # Give 1 point to author on every 10 downloads
    if resource.download_count % 10 == 0:
        from apps.gamification.models import UserActivity
        UserActivity.log(user=resource.uploaded_by, action=UserActivity.Action.RESOURCE_DOWNLOADS)

    return FileResponse(resource.file.open('rb'), as_attachment=True, filename=resource.file.name.split('/')[-1])