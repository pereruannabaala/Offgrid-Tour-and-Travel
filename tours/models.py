import uuid
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
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

class ExpeditionPhoto(models.Model):
    image = models.ImageField(upload_to="expeditions/")
    thumb = models.ImageField(upload_to="expeditions/thumbs/", blank=True)

class BlogHeader(models.Model):
    title = models.CharField(max_length=200, default="Stories from the Bush")
    subtitle = models.CharField(max_length=200, default="The heart and soul behind your safari")
    background_image = models.ImageField(upload_to="blog/headers/", blank=True, null=True)

    class Meta:
        verbose_name = "Blog Header"
        verbose_name_plural = "Blog Header"

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=100, default="Maasai Adventures Team")
    featured_image = models.ImageField(upload_to="blog/")
    excerpt = models.TextField(help_text="A brief 2-3 sentence summary for grid cards.")
    
    # Rich text editor field
    content = CKEditor5Field('Content', config_name='default')
    
    category = models.CharField(max_length=100, default="Safari Insights")
    read_time = models.CharField(max_length=50, default="5 min read")
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = CKEditor5Field('Description', config_name='default')
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price in USD")
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in KES")
    image = models.ImageField(upload_to="shop/products/")
    stock = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    DELIVERY_TYPE_CHOICES = [
        ('home', 'Home / International Address'),
        ('hotel', 'Hotel / Lodging / Airbnb (Kenya)'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    ORDER_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped / Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # Guest Tracking Security
    tracking_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Guest Contact
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    
    # Delivery Type & Address
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES, default='home')
    full_name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="Kenya")
    
    # Hotel / Airbnb Specifics
    hotel_name = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Mara Serena Safari Lodge")
    room_number = models.CharField(max_length=50, blank=True, null=True)
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)

    # Gift Options
    is_gift = models.BooleanField(default=False)
    gift_message = models.TextField(blank=True, null=True)

    # Order Totals & Status
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='processing')
    
    # M-Pesa Transaction Tracking
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True, help_text="Safaricom CheckoutRequestID")
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. QKH7183920")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name} ({self.email})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_total(self):
        return self.price * self.quantity