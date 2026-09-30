from decimal import Decimal
from django.conf import settings
from .models import Product, ProductVariant

class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, variant=None, quantity=1, override_quantity=False):
        """
        Add a product or its specific variant to the cart, or update its quantity.
        We use a unique cart key to separate base products from specific variants 
        (e.g., product_id_variant_id).
        """
        product_id = str(product.id)
        variant_id = str(variant.id) if variant else 'None'
        cart_key = f"{product_id}_{variant_id}"

        if cart_key not in self.cart:
            price = variant.get_price_usd() if variant else product.price_usd
            self.cart[cart_key] = {
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
                'quantity': 0,
                'price': str(price),
            }

        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity
        
        self.save()

    def save(self):
        # Mark the session as "modified" to ensure it gets saved/persisted
        self.session.modified = True

    def remove(self, product_id, variant_id=None):
        """Remove a product or variant from the cart."""
        cart_key = f"{product_id}_{variant_id}" if variant_id else f"{product_id}_None"
        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()

    def __iter__(self):
        """Iterate over the items in the cart and safely fetch products from the database."""
        cart_keys = list(self.cart.keys())
        for cart_key in cart_keys:
            item_data = self.cart[cart_key].copy()
            
            try:
                product = Product.objects.get(id=item_data['product_id'])
            except Product.DoesNotExist:
                # Clean out stale items if the product was deleted from the database
                del self.cart[cart_key]
                self.save()
                continue

            item_data['product'] = product
            
            # Check if it has a variant
            if item_data['variant_id']:
                try:
                    variant = ProductVariant.objects.get(id=item_data['variant_id'])
                    item_data['variant'] = variant
                    item_data['name_display'] = f"{product.name} ({variant.name})"
                    item_data['image'] = variant.image if variant.image else product.image
                except ProductVariant.DoesNotExist:
                    item_data['variant_id'] = None
                    item_data['name_display'] = product.name
                    item_data['image'] = product.image
            else:
                item_data['name_display'] = product.name
                item_data['image'] = product.image

            item_data['price'] = Decimal(item_data['price'])
            item_data['total_price'] = item_data['price'] * item_data['quantity']
            yield item_data

    def __len__(self):
        """Count all items in the cart safely."""
        total = 0
        for cart_key, item_data in list(self.cart.items()):
            if Product.objects.filter(id=item_data['product_id']).exists():
                total += item_data['quantity']
            else:
                del self.cart[cart_key]
                self.save()
        return total

    def get_total_price(self):
        """Calculate total price for all valid items in the cart."""
        return sum(Decimal(item['price']) * item['quantity'] for item in self)

    def clear(self):
        """Remove cart from session."""
        del self.session[settings.CART_SESSION_ID]
        self.save()