from django.conf import settings

from .cart import Cart


def cart_context(request):
    if not settings.SHOP_ENABLED:
        return {'shop_enabled': False, 'cart_item_count': 0}

    cart = Cart(request)
    total_items = sum(item['quantity'] for item in cart)
    return {
        'shop_enabled': True,
        'cart': cart,
        'cart_item_count': total_items,
    }
