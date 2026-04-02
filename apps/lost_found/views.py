from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.accounts.decorators import verified_required, student_required
from .models import LostFoundItem
from .forms import LostFoundForm


@student_required
@verified_required
def lf_list_view(request):
    item_type = request.GET.get('type', '')
    items = LostFoundItem.objects.filter(status='open')
    if item_type in ['lost', 'found']:
        items = items.filter(item_type=item_type)
    return render(request, 'lost_found/list.html', {'items': items, 'item_type': item_type})


@student_required
@verified_required
def lf_detail_view(request, pk):
    item = get_object_or_404(LostFoundItem, pk=pk)
    return render(request, 'lost_found/detail.html', {'item': item})


@student_required
@verified_required
def lf_post_view(request):
    form = LostFoundForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        lf = form.save(commit=False)
        lf.posted_by = request.user
        lf.save()
        messages.success(request, 'Post created!')
        return redirect('lost_found:list')
    return render(request, 'lost_found/form.html', {'form': form})


@student_required
def lf_resolve_view(request, pk):
    item = get_object_or_404(LostFoundItem, pk=pk, posted_by=request.user)
    item.status = 'claimed'
    item.save()
    messages.success(request, 'Marked as resolved.')
    return redirect('lost_found:list')