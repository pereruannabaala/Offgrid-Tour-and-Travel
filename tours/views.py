from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import HeroSlide, WhatWeDoContent, Experience, TeamMember, PageHeader


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


# Public Homepage - Single Combined View
def index(request):
    # Fetch active hero slides (or fall back to all slides)
    hero_slides = HeroSlide.objects.filter(category='hero', is_active=True).order_by('-created_at')
    if not hero_slides.exists():
        hero_slides = HeroSlide.objects.filter(is_active=True).order_by('-created_at')

    # Fetch What We Do / Our Story content instance
    what_we_do = WhatWeDoContent.objects.first()

    # Fetch Experiences ordered by display position
    experiences = Experience.objects.all().order_by('order')

    # Extra slide categories for gallery or services sections
    gallery_images = HeroSlide.objects.filter(category='gallery', is_active=True)
    services = HeroSlide.objects.filter(category='services', is_active=True)

    context = {
        'hero_slides': hero_slides,
        'what_we_do': what_we_do,
        'experiences': experiences,
        'gallery_images': gallery_images,
        'services': services,
    }
    return render(request, 'tours/index.html', context)


# Superuser Upload View (Custom Admin Page)
@user_passes_test(is_superuser, login_url='/admin/login/')
def admin_upload_image(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        category = request.POST.get('category')
        image = request.FILES.get('image')

        if image:
            HeroSlide.objects.create(
                title=title,
                subtitle=subtitle,
                category=category,
                image=image
            )
            messages.success(request, 'Image uploaded successfully!')
            return redirect('admin_upload')
        else:
            messages.error(request, 'Please select an image to upload.')

    slides = HeroSlide.objects.all().order_by('-created_at')
    return render(request, 'tours/admin_upload.html', {'slides': slides})

# Meet Our Tribe section
def meet_the_tribe(request):
    team_members = TeamMember.objects.all().order_by('order')
    header = PageHeader.objects.filter(page_name='meet_the_tribe').first()
    
    return render(request, 'tours/meet_the_tribe.html', {
        'team_members': team_members,
        'header': header,
    })