from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse,HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Order, QRCode, MenuItem, ItemOption
import json
from django.contrib.auth.decorators import login_required

# @login_required
def dashboard(request):
    new_count = Order.objects.filter(status='NEW').count()
    delivered_count = Order.objects.filter(status='DELIVERED').count()
    context = {
        'new_count': new_count,
        'delivered_count': delivered_count
    }
    return render(request, 'adminDash/index.html', context)

def get_new_orders(request):
    status = request.GET.get('status', 'NEW')
    orders = Order.objects.filter(status=status).order_by('-created_at')
    return render(request, 'adminDash/order_list_partial.html', {'orders': orders})

def get_order_stats(request):
    new_count = Order.objects.filter(status='NEW').count()
    delivered_count = Order.objects.filter(status='DELIVERED').count()
    return JsonResponse({
        'new_count': new_count,
        'delivered_count': delivered_count
    })

@require_POST
@login_required
def mark_order_done(request, order_id):
    
    if not hasattr(request.user, 'canteenmanager'):
        return HttpResponseForbidden("User is neither a Canteen Manager nor authorized.")

    manager = request.user.canteenmanager


    canteen = manager.canteen

    order = get_object_or_404(Order, order_id=order_id,seat__lab__canteen=canteen)
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
def place_order(request):
    """
    Handles order submission from the user.
    """
    print(f"--- POST /place_order received from {request.META.get('REMOTE_ADDR')} ---")
    print(f"POST Data: {request.POST}")

     # Validate QR from session
    qr_id = request.session.get('qr_id')
    if not qr_id:
        return HttpResponse("Session expired or invalid QR. Please rescan.", status=400)

    qr_obj = get_object_or_404(QRCode, qr_id=qr_id, is_active=True)

     # Get selected item
    item_id = request.POST.get('item_id')
    option_id = request.POST.get('option_id')
    request_id = request.POST.get('request_id')

    # Idempotency Check
    if request_id:
        existing_order = Order.objects.filter(request_id=request_id).first()
        if existing_order:
            # Already created, redirect to success
            return redirect('order_success')
    
    if not item_id:
        return HttpResponse("Please select an item", status=400)
        
    item = get_object_or_404(MenuItem, id=item_id)
    option = None
    
    # Optional customization
    if option_id:
        option = get_object_or_404(ItemOption, id=option_id)
        # Validation: Option must belong to Item
        if option.menu_item != item:
             return HttpResponse("Invalid option for selected item", status=400)

    # Create Order
    Order.objects.create(
        seat=qr_obj.seat,
        item=item,
        option=option,
        status='NEW',
        request_id=request_id
    )
    return redirect('order_success')

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
