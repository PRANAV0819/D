from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q

from apps.accounts.decorators import verified_required
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm


# ── Feed ─────────────────────────────────────────────────────────────

@login_required
@verified_required
def feed_view(request):
    """
    Show posts from:
      1. The current user themselves
      2. Users they are connected with (accepted connections)
    Falls back to all public posts if the user has no connections yet.
    """
    from apps.connections.models import Connection

    # Collect IDs of accepted connections
    connected_ids = Connection.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status=Connection.Status.ACCEPTED,
    ).values_list('sender_id', 'receiver_id')

    # Flatten the pairs, excluding the current user's own id
    user_ids = set()
    user_ids.add(request.user.pk)
    for sender_id, receiver_id in connected_ids:
        user_ids.add(sender_id)
        user_ids.add(receiver_id)

    posts = Post.objects.filter(
        Q(author_id__in=user_ids) |
        Q(visibility=Post.Visibility.PUBLIC)
    ).select_related('author', 'author__profile').distinct()

    # Annotate each post with whether the current user has liked it
    for post in posts:
        post.user_liked = post.is_liked_by(request.user)

    post_form = PostForm()
    return render(request, 'social/feed.html', {
        'posts':     posts,
        'post_form': post_form,
    })


# ── Create post ───────────────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def create_post_view(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, 'Post shared successfully.')
    else:
        messages.error(request, 'Could not create post. Please check the form.')
    return redirect('social:feed')


# ── Delete post ───────────────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('social:feed')


# ── Like / Unlike (AJAX) ──────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def toggle_like_view(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        # Already liked → unlike
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked':      liked,
        'like_count': post.like_count(),
    })


# ── Comment ───────────────────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def add_comment_view(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post   = post
        comment.author = request.user
        comment.save()

    return redirect(request.META.get('HTTP_REFERER', 'social:feed'))


@login_required
@verified_required
@require_POST
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, author=request.user)
    comment.delete()
    return redirect(request.META.get('HTTP_REFERER', 'social:feed'))


# ── Single post detail ────────────────────────────────────────────────

@login_required
@verified_required
def post_detail_view(request, post_id):
    post     = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('author', 'author__profile').all()
    post.user_liked = post.is_liked_by(request.user)
    form = CommentForm()
    return render(request, 'social/post_detail.html', {
        'post':     post,
        'comments': comments,
        'form':     form,
    })