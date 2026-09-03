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


class Experience(models.Model):
    number = models.CharField(max_length=5, help_text="e.g. 01., 02.")
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order of display")
    is_featured = models.BooleanField(default=False, help_text="Check for full-width highlight card (like #07)")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.number} {self.title}"

# Meet the tribe header section
class PageHeader(models.Model):
    page_name = models.CharField(max_length=50, unique=True, help_text="e.g. meet_the_tribe")
    title = models.CharField(max_length=100, default="Meet the Tribe")
    subtitle = models.CharField(max_length=150, blank=True, default="The heart and soul behind your safari")
    background_image = models.ImageField(upload_to='headers/')

    def __str__(self):
        return f"Header: {self.page_name}"

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='team/')
    order = models.PositiveIntegerField(default=0, help_text="Order in which team member appears on page")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.name} - {self.role}"