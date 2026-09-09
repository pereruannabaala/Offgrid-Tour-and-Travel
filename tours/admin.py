from django.contrib import admin
from .models import HeroSlide,WhatWeDoContent,TeamMember, Experience, PageHeader,ExpeditionPhoto, BlogPost, BlogHeader,Product, Order, OrderItem


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

@admin.register(ExpeditionPhoto)
class ExpeditionPhotoAdmin(admin.ModelAdmin):
    # Controls which columns appear in the admin list table view
    list_display = ('image_preview',)

    # Explicitly define ONLY the fields you want to show on the edit form
    fields = ('image', 'thumb')

    # Optional: If you want to show an image thumbnail in the list view
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


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'delivery_type', 'total_amount', 'payment_status', 'order_status', 'created_at']
    list_filter = ['delivery_type', 'payment_status', 'order_status', 'is_gift']
    search_fields = ['full_name', 'email', 'tracking_token', 'hotel_name']
    inlines = [OrderItemInline]
    readonly_fields = ['tracking_token']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_usd', 'price_kes', 'stock', 'is_active']
    prepopulated_fields = {'slug': ('name',)}