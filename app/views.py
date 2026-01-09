from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse,HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Order, QRCode, MenuItem, ItemOption, Canteen
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import qrcode
from io import BytesIO
from django.urls import reverse

@login_required
def dashboard(request):
    # Get all canteens managed by this user
    my_canteens = Canteen.objects.filter(active_manager=request.user)
    
    new_count = Order.objects.filter(status='NEW', seat__lab__canteen__in=my_canteens).count()
    delivered_count = Order.objects.filter(status='DELIVERED', seat__lab__canteen__in=my_canteens).count()
    context = {
        'new_count': new_count,
        'delivered_count': delivered_count
    }
    return render(request, 'adminDash/index.html', context)

def get_new_orders(request):
    status = request.GET.get('status', 'NEW')
    # Filter by user's assigned canteens
    my_canteens = Canteen.objects.filter(active_manager=request.user)
    orders = Order.objects.filter(status=status, seat__lab__canteen__in=my_canteens).order_by('-created_at')
    return render(request, 'adminDash/order_list_partial.html', {'orders': orders})

def get_order_stats(request):
    my_canteens = Canteen.objects.filter(active_manager=request.user)
    new_count = Order.objects.filter(status='NEW', seat__lab__canteen__in=my_canteens).count()
    delivered_count = Order.objects.filter(status='DELIVERED', seat__lab__canteen__in=my_canteens).count()
    return JsonResponse({
        'new_count': new_count,
        'delivered_count': delivered_count
    })

@require_POST
@login_required
def mark_order_done(request, order_id):
    
    # Verify user manages the canteen for this order
    order = get_object_or_404(Order, order_id=order_id)
    if order.seat.lab.canteen.active_manager != request.user:
         return HttpResponseForbidden("You are not the active manager for this order's canteen.")

    order.status = 'DELIVERED'
    order.save()
    return JsonResponse({'status': 'success'})


def scan_qr(request, qr_id):
    print(request.user)
    # Validate QR code
    qr_obj = get_object_or_404(QRCode, qr_id=qr_id, is_active=True)

    # Store QR in session for persistence
    request.session['qr_id'] = str(qr_id)


    # Get seat, lab and canteen
    seat = qr_obj.seat
    canteen = seat.lab.canteen

    # Fetch menu only from this canteen
    menu_items = MenuItem.objects.filter(canteen=canteen, is_available=True).prefetch_related('options')
    
    # Serialize for frontend JS
    items_data = []

    #loop       
    for item in menu_items:
        options_list = []
        if item.options.exists():
            opts = [opt.name for opt in item.options.all()]

            pass

        item_opts = []
        for opt in item.options.all():
            item_opts.append({'id': opt.id, 'name': opt.name})
            
        customizations = []
        if item_opts:
            customizations.append({
                'id': 'main_option', # Single group
                'label': 'Options',
                'options': item_opts # List of {id, name}
            })

        items_data.append({
            'id': item.id,
            'name': item.name,
            'image': 'https://placehold.co/400x300?text=' + item.name.replace(' ', '+'), # Placeholder
            'customizations': customizations
        })
    
    context = {
        'qr_id': qr_id,
        'canteen': canteen,
        'seat': seat,
        'menu_items_json': json.dumps(items_data),
        'menu_items': menu_items # Keep for fallback or debugging
    }
    return render(request, 'userHome/index.html', context)


@require_POST
def place_order(request, qr_id):
    """
    Handles order submission via standard HTML Form POST.
    User must be authenticated.
    """
    # Validate QR
    qr_obj = get_object_or_404(QRCode, qr_id=qr_id, is_active=True)

    # Get selected item
    item_id = request.POST.get('item_id')
    option_id = request.POST.get('option_id')
    # request_id = request.POST.get('request_id') # Optional: Use if you implement idempotency with hidden field

    if not item_id:
        # In a real app, you might render the page again with an error message
        return HttpResponse("Error: Item not selected", status=400)

    item = get_object_or_404(MenuItem, id=item_id)
    option = None

    if option_id:
        option = get_object_or_404(ItemOption, id=option_id)
        if option.menu_item != item:
            return HttpResponse("Error: Invalid option", status=400)

    # Create order
    Order.objects.create(
        seat=qr_obj.seat,
        item=item,
        option=option,
        status='NEW',
        # request_id=request_id 
    )
    
    # Store QR ID in session so order_success knows context if needed
    request.session['qr_id'] = str(qr_id)

    return redirect('order_success')
@never_cache
def order_success(request):
    qr_id = request.session.get('qr_id')
    context = {}
    if qr_id:
        try:
            qr_obj = QRCode.objects.get(qr_id=qr_id)
            context['seat'] = qr_obj.seat
            context['qr_id'] = qr_id
        except QRCode.DoesNotExist:
            pass
            
    return render(request, 'order_success.html', context)


def serve_qr_code(request, qr_id):
    """
    Generates a QR code image on the fly.
    Uses request.build_absolute_uri() to ensure the current host/IP is used.
    """
    qr_obj = get_object_or_404(QRCode, qr_id=qr_id)
    
    # Dynamically build the URL for the scan view
    # This uses the host from the current request (e.g. 192.168.x.x or domain.com)
    scan_url = request.build_absolute_uri(reverse('scan_qr', args=[qr_id]))
    
    # Generate QR code
    qr = qrcode.make(scan_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")
