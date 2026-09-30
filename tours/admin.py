from django.contrib import admin
from .models import (
    HeroSlide, WhatWeDoContent, TeamMember, Experience, 
    PageHeader, ExpeditionPhoto, BlogPost, BlogHeader, 
    Product, ProductVariant, Order, OrderItem, SafariInquiry
)


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
    list_display = ('number', 'title', 'order', 'is_featured')
    list_editable = ('order', 'is_featured')
    search_fields = ('title', 'description')
    ordering = ('order',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'created_at')
    list_editable = ('order',)


@admin.register(PageHeader)
class PageHeaderAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'title')


@admin.register(ExpeditionPhoto)
class ExpeditionPhotoAdmin(admin.ModelAdmin):
    list_display = ('image_preview',)
    fields = ('image', 'thumb')

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px;"/>'
        return "No Image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'is_published')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogHeader)
class BlogHeaderAdmin(admin.ModelAdmin):
    pass



# --- NEW: Product Variant Inline ---
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # Shows 1 empty row by default for quick adding


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_usd', 'price_kes', 'created_at')
    search_fields = ('name',)
    exclude = ('description',)
    inlines = [ProductVariantInline]  # <-- This links the variants to the Product page!


@admin.register(SafariInquiry)
class SafariInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'travelers', 'experience', 'start_date', 'created_at')
    list_filter = ('created_at', 'start_date')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)