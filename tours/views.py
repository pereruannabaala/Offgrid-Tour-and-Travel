from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import HeroSlide, WhatWeDoContent


def is_superuser(user):
    return user.is_authenticated and user.is_superuser

# Public Homepage
def index(request):
    hero_slides = HeroSlide.objects.filter(category='hero', is_active=True).order_by('-created_at')
    gallery_images = HeroSlide.objects.filter(category='gallery', is_active=True)
    services = HeroSlide.objects.filter(category='services', is_active=True)
    
    context = {
        'hero_slides': hero_slides,
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

def index(request):
    hero_slides = HeroSlide.objects.all()
    what_we_do = WhatWeDoContent.objects.first()
    
    context = {
        'hero_slides': hero_slides,
        'what_we_do': what_we_do,
    }
    return render(request, 'tours/index.html', context)