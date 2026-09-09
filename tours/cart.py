# tours/cart.py
from decimal import Decimal
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('guest_cart')
        if not cart:
            cart = self.session['guest_cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price_usd)}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove_single(self, product):
        """Decrements product quantity by 1. Removes item if quantity reaches 0."""
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] -= 1
            if self.cart[product_id]['quantity'] <= 0:
                del self.cart[product_id]
            self.save()

    def remove(self, product):
        """Completely removes the product from the cart."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True


    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        # Map products by string ID for quick lookup
        product_map = {str(product.id): product for product in products}
        
        for product_id, item in self.cart.items():
            if product_id in product_map:
                item_copy = item.copy()
                item_copy['product'] = product_map[product_id]
                item_copy['price'] = Decimal(item_copy['price'])
                item_copy['total_price'] = item_copy['price'] * item_copy['quantity']
                yield item_copy
            

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        if 'guest_cart' in self.session:
            del self.session['guest_cart']
            self.save()