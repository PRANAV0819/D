from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import Item, ClaimRequest
from .forms import ItemForm, ClaimForm

# ─────────────────────────────────────────────
# Access Control: Student & Teacher only
# ─────────────────────────────────────────────

def lost_found_access_check(user):
    # Only Students and Teachers allowed. Alumni denied.
    return user.is_authenticated and user.role in ['student', 'teacher']

@login_required
@user_passes_test(lost_found_access_check, login_url='/feed/', redirect_field_name=None)
def item_list(request):
    """List all open Lost & Found items with search and filters."""
    items = Item.objects.filter(status=Item.Status.OPEN)

    # Search
    q = request.GET.get('q', '')
    if q:
        items = items.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Filters
    category = request.GET.get('category')
    location = request.GET.get('location')
    item_type = request.GET.get('type')

    if category:
        items = items.filter(category=category)
    if location:
        items = items.filter(location__icontains=location)
    if item_type:
        items = items.filter(item_type=item_type)

    context = {
        'items': items,
        'categories': Item.Category.choices,
        'types': Item.ItemType.choices,
    }
    return render(request, 'lost_found/list.html', context)

@login_required
@user_passes_test(lost_found_access_check)
def item_detail(request, pk):
    """Show item details and possible matches."""
    item = get_object_or_404(Item, pk=pk)
    matches = calculate_matches(item)
    
    context = {
        'item': item,
        'matches': matches,
        'claim_form': ClaimForm(),
    }
    return render(request, 'lost_found/detail.html', context)

@login_required
@user_passes_test(lost_found_access_check)
def item_create(request):
    """Post a new lost or found item."""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            
            # Smart Matching Notification
            matches = calculate_matches(item)
            if matches:
                messages.info(request, "Possible match found for your item!")
            
            messages.success(request, f"Successfully posted {item.get_item_type_display()} item.")
            return redirect('lost_found:item_detail', pk=item.pk)
    else:
        form = ItemForm()
    
    return render(request, 'lost_found/form.html', {'form': form, 'title': 'Post New Item'})

@login_required
@user_passes_test(lost_found_access_check)
def claim_item(request, pk):
    """Submit a claim for an item."""
    item = get_object_or_404(Item, pk=pk)
    if item.user == request.user:
        messages.error(request, "You cannot claim your own item.")
        return redirect('lost_found:item_detail', pk=pk)

    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim, created = ClaimRequest.objects.get_or_create(
                item=item,
                claimant=request.user,
                defaults={'message': form.cleaned_data['message']}
            )
            if created:
                messages.success(request, "Claim request sent to the owner.")
            else:
                messages.info(request, "You have already pending claim for this item.")
    
    return redirect('lost_found:item_detail', pk=pk)

@login_required
@user_passes_test(lost_found_access_check)
def manage_claim(request, pk, action):
    """Accept or Reject a claim."""
    claim = get_object_or_404(ClaimRequest, pk=pk)
    
    # Only item owner can manage claims
    if claim.item.user != request.user:
        messages.error(request, "Unauthorized.")
        return redirect('lost_found:item_list')

    if action == 'accept':
        claim.status = ClaimRequest.ClaimStatus.ACCEPTED
        claim.item.status = Item.Status.RESOLVED
        claim.item.save()
        messages.success(request, "Claim accepted. Item marked as Resolved.")
    elif action == 'reject':
        claim.status = ClaimRequest.ClaimStatus.REJECTED
        messages.warning(request, "Claim rejected.")
    
    claim.save()
    return redirect('lost_found:item_detail', pk=claim.item.pk)

# ─────────────────────────────────────────────
# Smart Matching Logic
# ─────────────────────────────────────────────

def calculate_matches(item):
    """
    Compare item with opposite type (Lost <-> Found)
    Rules:
    - Category match: +3
    - Title/keyword overlap: +2
    - Location match: +2
    - Date proximity (within 3 days): +1
    Threshold: 5
    """
    opposite_type = item.opposite_type
    # Only match against OPEN items of opposite type
    potential_matches = Item.objects.filter(
        item_type=opposite_type, 
        status=Item.Status.OPEN
    ).exclude(id=item.id)

    scored_items = []
    item_title_words = set(item.title.lower().split())

    for target in potential_matches:
        score = 0
        
        # 1. Category match (+3)
        if target.category == item.category:
            score += 3
        
        # 2. Title word overlap (+2)
        target_title_words = set(target.title.lower().split())
        if item_title_words.intersection(target_title_words):
            score += 2
            
        # 3. Location match (+2)
        # Check if location strings are similar (basic containment)
        if item.location.lower() in target.location.lower() or target.location.lower() in item.location.lower():
            score += 2
            
        # 4. Date proximity (+1)
        # Within 3 days
        date_diff = abs((target.date - item.date).days)
        if date_diff <= 3:
            score += 1
            
        if score >= 5:
            scored_items.append({
                'item': target,
                'score': score
            })

    # Sort by descending score
    scored_items.sort(key=lambda x: x['score'], reverse=True)
    return scored_items