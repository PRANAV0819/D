from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.db.models import Q
from apps.accounts.decorators import verified_required, student_required
from .models import MarketplaceItem, OrderRequest
from .forms import MarketplaceItemForm

@student_required
@verified_required
def marketplace_list_view(request):
    items = MarketplaceItem.objects.filter(status='active').select_related('seller')
    
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    condition = request.GET.get('condition', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '').strip()

    if q:
        items = items.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        items = items.filter(category=category)
    if condition:
        items = items.filter(condition=condition)
    if location:
        items = items.filter(location__icontains=location)
    if min_price and min_price.isdigit():
        items = items.filter(price__gte=min_price)
    if max_price and max_price.isdigit():
        items = items.filter(price__lte=max_price)

    return render(request, 'marketplace/list.html', {
        'items': items, 
        'q': q,
        'selected_category': category,
        'selected_condition': condition,
        'min_price': min_price,
        'max_price': max_price,
        'location': location,
        'categories': MarketplaceItem.MarketplaceCategory.choices,
        'conditions': MarketplaceItem.Condition.choices,
    })


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
    my_requests = OrderRequest.objects.filter(buyer=request.user).select_related('item')
    return render(request, 'marketplace/my_items.html', {'items': items, 'my_requests': my_requests})


@student_required
def mark_sold_view(request, pk):
    item = get_object_or_404(MarketplaceItem, pk=pk, seller=request.user)
    item.status = 'sold'
    item.save()
    messages.success(request, 'Item marked as sold.')
    return redirect('marketplace:my_items')

@student_required
@verified_required
def request_item_view(request, pk):
    if request.method != 'POST':
        return redirect('marketplace:detail', pk=pk)
    
    item = get_object_or_404(MarketplaceItem, pk=pk)
    
    if item.status != MarketplaceItem.ItemStatus.ACTIVE:
        messages.error(request, 'This item is no longer available.')
        return redirect('marketplace:detail', pk=pk)
        
    if item.seller == request.user:
        messages.error(request, 'You cannot request your own item.')
        return redirect('marketplace:detail', pk=pk)

    msg = request.POST.get('message', '').strip()
    
    order, created = OrderRequest.objects.get_or_create(
        item=item, 
        buyer=request.user,
        defaults={'message': msg}
    )
    
    if created:
        messages.success(request, 'Your request has been sent to the seller!')
    else:
        messages.info(request, 'You have already requested this item.')
        
    return redirect('marketplace:detail', pk=pk)

@student_required
@verified_required
def manage_request_view(request, request_id):
    if request.method != 'POST':
        return redirect('marketplace:my_items')
        
    order_req = get_object_or_404(OrderRequest, pk=request_id, item__seller=request.user)
    action = request.POST.get('action')
    item = order_req.item
    
    if action == 'accept':
        if item.status != MarketplaceItem.ItemStatus.ACTIVE:
            messages.error(request, 'Item is already reserved or sold.')
            return redirect('marketplace:my_items')
            
        order_req.status = OrderRequest.RequestStatus.ACCEPTED
        order_req.save()
        
        # Mark item as reserved
        item.status = MarketplaceItem.ItemStatus.RESERVED
        item.save()
        
        # Reject all other pending requests
        pending_others = OrderRequest.objects.filter(item=item, status=OrderRequest.RequestStatus.PENDING).exclude(pk=order_req.pk)
        pending_others.update(status=OrderRequest.RequestStatus.REJECTED)
        
        messages.success(request, f'You accepted the request from {order_req.buyer.get_full_name()}. Item is now Reserved.')
        
    elif action == 'reject':
        order_req.status = OrderRequest.RequestStatus.REJECTED
        order_req.save()
        messages.info(request, f'You rejected the request from {order_req.buyer.get_full_name()}.')
        
    return redirect('marketplace:my_items')