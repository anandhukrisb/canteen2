
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings') # Assumption: project name might vary, but usually it's passed in shell
import sys
sys.path.append(os.getcwd())

# Initialize Django
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from app.models import Canteen, Lab, Seat, MenuItem, Order
from app.views import get_new_orders, get_order_stats

def run_verification():
    print("--- Starting Dashboard Verification ---")

    # 1. Setup Data
    username = 'test_manager_v1'
    password = 'password123'
    
    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.save()
    
    print(f"User: {user.username}")

    canteen, created = Canteen.objects.get_or_create(name="Test Canteen V1")
    canteen.active_manager = user
    canteen.save()
    
    print(f"Canteen: {canteen.name} assigned to {canteen.active_manager.username}")

    lab, _ = Lab.objects.get_or_create(name="Test Lab V1", canteen=canteen)
    seat, _ = Seat.objects.get_or_create(lab=lab, seat_number="A1")
    item, _ = MenuItem.objects.get_or_create(canteen=canteen, name="Test Burger")
    
    # Clear existing orders for clean test
    Order.objects.filter(seat=seat).delete()

    # Create NEW order
    order = Order.objects.create(seat=seat, item=item, status='NEW')
    print(f"Created Order: {order}")

    # 2. Test get_new_orders
    factory = RequestFactory()
    request = factory.get('/get_new_orders/')
    request.user = user # Simulate login

    print("\nTesting get_new_orders...")
    response = get_new_orders(request)
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        # Check if order text is in response
        if item.name in content and "Test Lab V1" in content:
            print("SUCCESS: Order found in response HTML.")
        else:
            print("FAILURE: Order NOT found in response HTML.")
            print("Content preview:", content[:500])
    else:
        print(f"FAILURE: Status code {response.status_code}")

    # 3. Test get_order_stats
    print("\nTesting get_order_stats...")
    req_stats = factory.get('/get_order_stats/')
    req_stats.user = user
    
    resp_stats = get_order_stats(req_stats)
    if resp_stats.status_code == 200:
        import json
        data = json.loads(resp_stats.content)
        print(f"Stats: {data}")
        if data['new_count'] >= 1:
             print("SUCCESS: Stats reflect new order.")
        else:
             print("FAILURE: Stats count is wrong.")
    else:
        print(f"FAILURE: Stats status code {resp_stats.status_code}")

if __name__ == '__main__':
    try:
        run_verification()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
