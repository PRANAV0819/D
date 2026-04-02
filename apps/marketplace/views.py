from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.accounts.decorators import verified_required, student_required
from .models import MarketplaceItem
from .forms import MarketplaceItemForm


@student_required
@verified_required
def marketplace_list_view(request):
    items = MarketplaceItem.objects.filter(status='active').select_related('seller')
    q = request.GET.get('q', '')
    if q:
        items = items.filter(title__icontains=q)
    return render(request, 'marketplace/list.html', {'items': items, 'q': q})


@student_required
@verified_required
def marketplace_detail_view(request, pk):
    item = get_object_or_404(MarketplaceItem, pk=pk)
    return render(request, 'marketplace/detail.html', {'item': item})


@student_required
@verified_required
def post_item_view(request):
    form = MarketplaceItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.seller = request.user
        item.save()
        messages.success(request, 'Item listed!')
        return redirect('marketplace:detail', pk=item.pk)
    return render(request, 'marketplace/form.html', {'form': form})


@student_required
@verified_required
def my_items_view(request):
    items = MarketplaceItem.objects.filter(seller=request.user)
    return render(request, 'marketplace/my_items.html', {'items': items})


@student_required
def mark_sold_view(request, pk):
    item = get_object_or_404(MarketplaceItem, pk=pk, seller=request.user)
    item.status = 'sold'
    item.save()
    messages.success(request, 'Item marked as sold.')
    return redirect('marketplace:my_items')