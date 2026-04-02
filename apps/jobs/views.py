from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from apps.accounts.decorators import verified_required
from .models import Job, JobApplication
from .forms import JobForm, JobApplicationForm


@login_required
@verified_required
def job_list_view(request):
    jobs = Job.objects.filter(status='open').select_related('posted_by')

    q         = request.GET.get('q', '')
    job_type  = request.GET.get('type', '')
    work_mode = request.GET.get('mode', '')

    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(company__icontains=q) | Q(description__icontains=q))
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)

    applied_ids = set(
        JobApplication.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    )
    return render(request, 'jobs/job_list.html', {
        'jobs': jobs, 'applied_ids': applied_ids,
        'q': q, 'job_type': job_type, 'work_mode': work_mode,
        'job_type_choices': Job.JobType.choices,
        'work_mode_choices': Job.WorkMode.choices,
    })


@login_required
@verified_required
def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    already_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    form = JobApplicationForm()
    return render(request, 'jobs/job_detail.html', {
        'job': job, 'already_applied': already_applied, 'form': form
    })


@login_required
@verified_required
def apply_job_view(request, pk):
    job = get_object_or_404(Job, pk=pk, status='open')
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('jobs:detail', pk=pk)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job       = job
            app.applicant = request.user
            # Use profile resume if none uploaded
            if not app.resume and request.user.profile.resume:
                app.resume = request.user.profile.resume
            app.save()
            messages.success(request, f'Applied to "{job.title}" successfully!')
            return redirect('jobs:detail', pk=pk)
    return redirect('jobs:detail', pk=pk)


@login_required
@verified_required
def post_job_view(request):
    form = JobForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.posted_by = request.user
        job.save()
        messages.success(request, 'Job posted successfully!')
        return redirect('jobs:detail', pk=job.pk)
    return render(request, 'jobs/job_form.html', {'form': form, 'title': 'Post a Job / Internship'})


@login_required
@verified_required
def my_jobs_view(request):
    posted = Job.objects.filter(posted_by=request.user)
    applied = JobApplication.objects.filter(applicant=request.user).select_related('job')
    return render(request, 'jobs/my_jobs.html', {'posted': posted, 'applied': applied})


@login_required
@verified_required
def toggle_job_status_view(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.status = 'closed' if job.status == 'open' else 'open'
    job.save()
    messages.success(request, f'Job marked as {job.status}.')
    return redirect('jobs:my_jobs')