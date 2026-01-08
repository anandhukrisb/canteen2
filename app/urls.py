from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('get_new_orders/', views.get_new_orders, name='get_new_orders'),
    path('get_order_stats/', views.get_order_stats, name='get_order_stats'),
    path('mark_order_done/<uuid:order_id>/', views.mark_order_done, name='mark_order_done'),
    path('scan/<uuid:qr_id>/', views.scan_qr, name='scan_qr'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_success/', views.order_success, name='order_success'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )