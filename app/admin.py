# admin.py
from django.contrib import admin
from .models import *
from .utils.qr import generate_qr

@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ('name', 'active_manager', 'is_active')
    list_editable = ('active_manager', 'is_active')

admin.site.register(Lab)
admin.site.register(Seat)
admin.site.register(MenuItem)
admin.site.register(Order)
admin.site.register(ItemOption)
admin.site.register(CanteenManager)


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('seat', 'qr_id', 'is_active')
    actions = ['generate_qr_codes']
    actions_on_top = True
    actions_on_bottom = True

    @admin.action(description="Generate QR codes for selected seats")
    def generate_qr_codes(self, request, queryset):
        count = 0
        for qr in queryset:
            generate_qr(qr)
            count += 1

        self.message_user(
            request,
            f"{count} QR code(s) generated successfully."
        )
