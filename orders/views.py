from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreatForm
from caart.cart import Cart
from .tasks import order_created
from django.urls import reverse


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreatForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            cart.clear()
            order_created.delay(order.id)

            request.session['order_id'] = order.id

            return redirect(reverse('payments:process'))
    else:
        form = OrderCreatForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})
