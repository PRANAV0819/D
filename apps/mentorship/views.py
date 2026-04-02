from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from .models import MentorProfile, MentorshipRequest, MentorSession
from .forms import MentorProfileForm, MentorshipRequestForm, MentorSessionForm


@login_required
@verified_required
def mentor_list_view(request):
    mentors = MentorProfile.objects.filter(is_active=True).select_related('user', 'user__profile', 'user__department')
    q = request.GET.get('q', '')
    if q:
        mentors = mentors.filter(expertise__icontains=q)
    return render(request, 'mentorship/mentor_list.html', {'mentors': mentors, 'q': q})


@login_required
@verified_required
def mentor_detail_view(request, user_id):
    mentor_user = get_object_or_404(User, pk=user_id)
    mentor_profile = get_object_or_404(MentorProfile, user=mentor_user, is_active=True)
    existing = MentorshipRequest.objects.filter(mentee=request.user, mentor=mentor_user).first()
    form = MentorshipRequestForm()
    return render(request, 'mentorship/mentor_detail.html', {
        'mentor_user': mentor_user,
        'mentor_profile': mentor_profile,
        'existing': existing,
        'form': form,
    })


@login_required
@verified_required
def become_mentor_view(request):
    profile, _ = MentorProfile.objects.get_or_create(user=request.user)
    form = MentorProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        # Update profile flag
        request.user.profile.is_open_to_mentor = True
        request.user.profile.save(update_fields=['is_open_to_mentor'])
        messages.success(request, 'Mentor profile saved!')
        return redirect('mentorship:list')
    return render(request, 'mentorship/become_mentor.html', {'form': form})


@login_required
@verified_required
def send_request_view(request, user_id):
    mentor_user = get_object_or_404(User, pk=user_id)
    if MentorshipRequest.objects.filter(mentee=request.user, mentor=mentor_user).exists():
        messages.info(request, 'Request already sent.')
        return redirect('mentorship:detail', user_id=user_id)
    form = MentorshipRequestForm(request.POST)
    if form.is_valid():
        req = form.save(commit=False)
        req.mentee  = request.user
        req.mentor  = mentor_user
        req.save()
        messages.success(request, f'Request sent to {mentor_user.get_full_name()}.')
    return redirect('mentorship:detail', user_id=user_id)


@login_required
@verified_required
def my_mentorship_view(request):
    as_mentee = MentorshipRequest.objects.filter(mentee=request.user).select_related('mentor', 'mentor__profile')
    as_mentor = MentorshipRequest.objects.filter(mentor=request.user).select_related('mentee', 'mentee__profile')
    return render(request, 'mentorship/my_mentorship.html', {
        'as_mentee': as_mentee,
        'as_mentor': as_mentor,
    })


@login_required
@verified_required
def handle_request_view(request, req_id, action):
    req = get_object_or_404(MentorshipRequest, pk=req_id, mentor=request.user)
    if action == 'accept':
        req.status = MentorshipRequest.Status.ACCEPTED
        messages.success(request, f'Accepted mentorship request from {req.mentee.get_full_name()}.')
    elif action == 'reject':
        req.status = MentorshipRequest.Status.REJECTED
        messages.info(request, 'Request declined.')
    req.save()
    return redirect('mentorship:my')


@login_required
@verified_required
def book_session_view(request, req_id):
    req = get_object_or_404(
        MentorshipRequest, pk=req_id, status=MentorshipRequest.Status.ACCEPTED
    )
    # Only mentee or mentor can book
    if request.user not in [req.mentee, req.mentor]:
        messages.error(request, 'Permission denied.')
        return redirect('mentorship:my')
    form = MentorSessionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        session = form.save(commit=False)
        session.request = req
        session.save()
        messages.success(request, 'Session booked!')
        return redirect('mentorship:my')
    return render(request, 'mentorship/book_session.html', {'form': form, 'req': req})