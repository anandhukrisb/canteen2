from . import views
from django.urls import path

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('get_new_orders/', views.get_new_orders, name='get_new_orders'),
    path('get_order_stats/', views.get_order_stats, name='get_order_stats'),
    path('mark_order_done/<uuid:order_id>/', views.mark_order_done, name='mark_order_done'),
    path('scan/<uuid:qr_id>/', views.scan_qr, name='scan_qr'),
    path('place_order/<uuid:qr_id>/', views.place_order, name='place_order'),
]