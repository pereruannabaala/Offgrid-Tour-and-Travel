from .cart import Cart

def cart_context(request):
 
    cart = Cart(request)
    total_items = sum(item['quantity'] for item in cart)
    return {
        'cart': cart,
        'cart_item_count': total_items,
    }