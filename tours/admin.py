from django.contrib import admin
from .models import HeroSlide,WhatWeDoContent,TeamMember, Experience, PageHeader

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at', 'image_preview')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'subtitle')
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; border-radius: 4px;"/>'
        return "No Image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Thumbnail'


@admin.register(WhatWeDoContent)
class WhatWeDoAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'updated_at')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    # Columns displayed in the admin list view
    list_display = ('number', 'title', 'order', 'is_featured')
    
    # Enable quick editing directly from the list view
    list_editable = ('order', 'is_featured')
    
    # Add search capability
    search_fields = ('title', 'description')
    
    # Default ordering in the admin list
    ordering = ('order',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'created_at')
    list_editable = ('order',)

@admin.register(PageHeader)
class PageHeaderAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'title')