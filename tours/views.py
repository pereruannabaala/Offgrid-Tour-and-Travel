import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .cart import Cart
from .mpesa import trigger_stk_push
from .models import SafariInquiry, Product, ProductVariant

from .models import (
    HeroSlide, WhatWeDoContent, Experience, TeamMember, 
    PageHeader, ExpeditionPhoto, BlogPost, BlogHeader, 
    Product, Order, OrderItem, ProductVariant
)



def format_phone_number(phone):
    """
    Normalizes Kenyan phone numbers to standard Safaricom format: 2547XXXXXXXX or 2541XXXXXXXX
    """
    cleaned = re.sub(r'\D', '', str(phone))  # Strip non-digit characters
    
    if cleaned.startswith('0') and len(cleaned) == 10:
        return f"254{cleaned[1:]}"
    elif cleaned.startswith('254') and len(cleaned) == 12:
        return cleaned
    elif (cleaned.startswith('7') or cleaned.startswith('1')) and len(cleaned) == 9:
        return f"254{cleaned}"
    
    return cleaned


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


# Public Homepage
def index(request):
    hero_slides = HeroSlide.objects.filter(category='hero', is_active=True).order_by('-created_at')
    if not hero_slides.exists():
        hero_slides = HeroSlide.objects.filter(is_active=True).order_by('-created_at')

    what_we_do = WhatWeDoContent.objects.first()
    experiences = Experience.objects.all().order_by('order')
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


# Custom Admin Page
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


def meet_the_tribe(request):
    team_members = TeamMember.objects.all().order_by('order')
    
    # Try fetching by page_name; fallback to first header if not found
    header = PageHeader.objects.filter(page_name='meet_the_tribe').first() or PageHeader.objects.first()
    
    return render(request, 'tours/meet_the_tribe.html', {
        'team_members': team_members,
        'header': header,
        'Experience': Experience,
    })


def gallery(request):
    photos = ExpeditionPhoto.objects.order_by("-pk")
    return render(request, "tours/gallery.html", {
        "photos": [
            {
                "image": p.image.url,
                "thumb": p.thumb.url if p.thumb else p.image.url,
            }
            for p in photos
        ],
    })

expedition_gallery = gallery


def blog_list(request):
    header = BlogHeader.objects.first()
    posts = BlogPost.objects.filter(is_published=True)
    categories = posts.values_list("category", flat=True).distinct()
    featured_post = posts.first() if posts.exists() else None
    grid_posts = posts[1:] if posts.count() > 1 else []

    return render(request, "tours/blog_list.html", {
        "header": header,
        "featured_post": featured_post,
        "posts": grid_posts,
        "categories": sorted(set(c for c in categories if c)),
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    related_posts = BlogPost.objects.filter(is_published=True).exclude(id=post.id)[:3]

    return render(request, "tours/blog_detail.html", {
        "post": post,
        "related_posts": related_posts,
    })


def shop_list(request):
    products = Product.objects.all()
    return render(request, 'tours/shop_list.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'tours/product_detail.html', {'product': product})



def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    variant = None
    variant_id = request.POST.get('variant_id')
    
    if product.variants.exists():
        if variant_id and variant_id != 'None':
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        else:
            variant = product.variants.filter(stock__gt=0).first()
            
        available_stock = variant.stock if variant else 0
    else:
        available_stock = product.stock

    if available_stock <= 0:
        return redirect('product_detail', product_id=product.id)

    cart.add(product=product, variant=variant, quantity=1)
    return redirect('cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    variant_id = request.GET.get('variant_id') or None
    if variant_id == 'None':
        variant_id = None
    cart.remove(product_id=product_id, variant_id=variant_id)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'tours/cart_detail.html', {'cart': cart})

def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')
    if variant_id == 'None':
        variant_id = None
        
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    action = request.POST.get('action') or request.GET.get('action')
    
    # Determine current quantity in cart
    cart_key = f"{product_id}_{variant_id}"
    current_qty = cart.cart.get(cart_key, {}).get('quantity', 1)

    if action == 'increase':
        max_stock = variant.stock if variant else product.stock
        if current_qty < max_stock:
            cart.add(product=product, variant=variant, quantity=1)
    elif action == 'decrease':
        if current_qty > 1:
            cart.add(product=product, variant=variant, quantity=-1)
        else:
            cart.remove(product_id=product_id, variant_id=variant_id)

    return redirect('cart_detail')

def guest_checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('shop_list')

    if request.method == 'POST':
        delivery_type = request.POST.get('delivery_type', 'home')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        payment_method = request.POST.get('payment_method')
        raw_phone = request.POST.get('phone')
        formatted_phone = format_phone_number(raw_phone)

        # 1. Create Pending Order
        order = Order.objects.create(
            email=email,
            phone=formatted_phone,
            full_name=full_name,
            delivery_type=delivery_type,
            address_line_1=request.POST.get('address_line_1', ''),
            address_line_2=request.POST.get('address_line_2', ''),
            city=request.POST.get('city', ''),
            country=request.POST.get('country', 'Kenya'),
            hotel_name=request.POST.get('hotel_name', ''),
            room_number=request.POST.get('room_number', ''),
            is_gift=bool(request.POST.get('is_gift')),
            gift_message=request.POST.get('gift_message', ''),
            total_amount=cart.get_total_price(),
            currency='USD',
            payment_status='pending'
        )

        # 2. Save Order Items and Reduce Stock
        for item in cart:
            prod = item.get('product')
            variant = item.get('variant') # Get the variant object from cart item
            qty = item.get('quantity', 1)
            
            # Reduce stock appropriately (Variant stock if it exists, otherwise product stock)
            if variant:
                variant.stock = max(0, variant.stock - qty)
                variant.save()
            elif hasattr(prod, 'stock') and prod.stock is not None:
                prod.stock = max(0, prod.stock - qty)
                prod.save()

            # Create OrderItem with both product and variant
            OrderItem.objects.create(
                order=order,
                product=prod,
                variant=variant,
                price=item['price'],
                quantity=qty
            )

        # 3. Send Confirmation Email
        
        tracking_url = request.build_absolute_uri(
            reverse('guest_order_tracking', kwargs={'token': order.tracking_token})
        )
        send_mail(
            subject=f"Your Maasai Souvenir Order #{order.id}",
            message=f"Thank you for your order! Track your shipment here:\n\n{tracking_url}",
            from_email='shop@yourdomain.com',
            recipient_list=[order.email],
            fail_silently=True,
        )

        # guest_checkout view (inside payment_method == 'mpesa')
        if payment_method == 'mpesa':
            exchange_rate = 130
            calculated_kes = int(float(order.total_amount) * exchange_rate)
            amount_in_kes = max(1, calculated_kes)  # Enforce minimum 1 KES

            stk_result = trigger_stk_push(
                phone=order.phone,
                amount=amount_in_kes,
                order_reference=order.id
            )

            if stk_result.get('success'):
                order.checkout_request_id = stk_result.get('checkout_request_id')
                order.save()

                messages.success(request, "M-Pesa payment prompt sent to your phone. Enter your PIN to complete.")
                cart.clear()
                return redirect('guest_order_tracking', token=order.tracking_token)
            else:
                # Mark order failed immediately if STK Push fails to trigger
                order.payment_status = 'failed'
                order.save()

                messages.error(request, f"M-Pesa prompt failed: {stk_result.get('message', 'Check your phone number and try again.')}")
                return redirect('guest_order_tracking', token=order.tracking_token)

        # Fallback redirect
        cart.clear()
        return redirect('guest_order_tracking', token=order.tracking_token)

    return render(request, 'tours/checkout.html', {'cart': cart})


def guest_order_tracking(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    return render(request, 'tours/order_tracking.html', {'order': order})


@csrf_exempt
def mpesa_callback(request):
    """Async webhook endpoint called by Safaricom Daraja API."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')

            try:
                order = Order.objects.get(checkout_request_id=checkout_request_id)
            except Order.DoesNotExist:
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Order not found'}, status=404)

            # ResultCode 0 = Successful Payment
            if result_code == 0:
                meta_data = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = None

                for item in meta_data:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value')

                order.payment_status = 'paid'
                order.mpesa_receipt_number = receipt_number
                order.save()
            else:
                order.payment_status = 'failed'
                order.save()

            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=400)


def check_payment_status(request, token):
    """API view for frontend AJAX polling."""
    order = get_object_or_404(Order, tracking_token=token)
    return JsonResponse({
        'payment_status': order.payment_status,
        'mpesa_receipt': order.mpesa_receipt_number or '',
    })
    

def retry_mpesa_payment(request, token):
    """Re-triggers M-Pesa STK push for a failed order."""
    order = get_object_or_404(Order, tracking_token=token)
    
    if request.method == 'POST':
        # Safely extract total cost attribute
        raw_total = getattr(order, 'total_cost', getattr(order, 'total_amount', 0))
        
        # Calculate amount in KES and enforce minimum 1 KES requirement
        exchange_rate = 130
        calculated_kes = int(float(raw_total) * exchange_rate)
        amount_in_kes = max(1, calculated_kes)

        stk_result = trigger_stk_push(
            phone=order.phone,
            amount=amount_in_kes,
            order_reference=order.id
        )

        if stk_result.get('success'):
            order.checkout_request_id = stk_result.get('checkout_request_id')
            order.payment_status = 'pending'  # Reset status so AJAX polling starts
            order.save()
            messages.success(request, "New M-Pesa payment prompt sent to your phone.")
        else:
            order.payment_status = 'failed'
            order.save()
            error_msg = stk_result.get('message', 'Failed to initiate M-Pesa payment.')
            messages.error(request, f"STK Push failed: {error_msg}")

    return redirect('guest_order_tracking', token=order.tracking_token)


def safari_inquiry_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        travelers = request.POST.get('travelers')
        experience = request.POST.get('experience')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        user_message = request.POST.get('message')

        # 1. Save inquiry to the database
        try:
            inquiry = SafariInquiry.objects.create(
                name=name,
                email=email,
                travelers=travelers,
                experience=experience,
                start_date=start_date,
                end_date=end_date,
                message=user_message
            )
        except Exception as e:
            messages.error(request, "There was an error saving your request. Please check your inputs.")
            return redirect('/#contact')

        # 2. Compose and send email to kaeloexpeditions@gmail.com
        subject = f"New Safari Inquiry from {name} - Kaelo Expeditions"
        body = (
            f"You have received a new safari inquiry from your website contact form.\n\n"
            f"--- Contact Details ---\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Number of Guests: {travelers}\n"
            f"Experience ID/Title: {experience}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n\n"
            f"--- Trip Notes ---\n"
            f"{user_message}\n"
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,  # Defaults to DEFAULT_FROM_EMAIL
                recipient_list=['kaeloexpeditions@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, "Your safari inquiry has been successfully sent! We will get back to you shortly.")
        except Exception as e:
            messages.warning(request, "Your inquiry was saved, but we encountered an issue sending the email notification. We will still review it shortly.")

    return redirect('/#contact')

