from django.db import models

class HeroSlide(models.Model):
    title = models.CharField(max_length=200, help_text="e.g. Tour & Travel")
    subtitle = models.CharField(max_length=200, blank=True, help_text="e.g. Offgrid Maasai Adventures Ltd")
    image = models.ImageField(upload_to='hero_slides/')
    category = models.CharField(max_length=50, choices=[
        ('hero', 'Hero Slider'),
        ('what_we_do', 'What We Do'),
        ('services', 'Our Services'),
        ('gallery', 'Gallery Grid'),
    ], default='hero')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"


class WhatWeDoContent(models.Model):
    title = models.CharField(max_length=200, default="What We Do")
    subtitle = models.CharField(max_length=200, default="Wild. Exclusive. Unforgettable.")
    top_image = models.ImageField(upload_to='what_we_do/', help_text="Top right feature image (e.g., Lion/Wildlife)")
    bottom_image = models.ImageField(upload_to='what_we_do/', help_text="Bottom left feature image (e.g., Savanna Sunset)")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "What We Do Section"
        verbose_name_plural = "What We Do Section"

    def __str__(self):
        return "What We Do Content"