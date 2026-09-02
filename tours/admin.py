from django.contrib import admin
from .models import HeroSlide,WhatWeDoContent

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