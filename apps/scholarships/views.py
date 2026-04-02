from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from apps.accounts.decorators import verified_required
from .models import Scholarship
from .forms import ScholarshipForm


@login_required
@verified_required
def scholarship_list_view(request):
    scholarships = Scholarship.objects.filter(is_active=True)
    q    = request.GET.get('q', '')
    stype = request.GET.get('type', '')
    if q:
        scholarships = scholarships.filter(Q(title__icontains=q) | Q(provider__icontains=q))
    if stype:
        scholarships = scholarships.filter(scholarship_type=stype)
    return render(request, 'scholarships/list.html', {
        'scholarships': scholarships, 'q': q, 'stype': stype,
        'type_choices': Scholarship.ScholarshipType.choices,
    })


@login_required
@verified_required
def scholarship_detail_view(request, pk):
    s = get_object_or_404(Scholarship, pk=pk)
    return render(request, 'scholarships/detail.html', {'scholarship': s})


@login_required
@verified_required
def post_scholarship_view(request):
    form = ScholarshipForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        s = form.save(commit=False)
        s.posted_by = request.user
        s.save()
        messages.success(request, 'Scholarship posted!')
        return redirect('scholarships:detail', pk=s.pk)
    return render(request, 'scholarships/form.html', {'form': form})