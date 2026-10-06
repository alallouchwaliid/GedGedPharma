from django.contrib import admin
from .models import Medicament, MouvementStock

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'dosage', 'stock_actuel', 'cout_sous_stockage', 'cout_surstockage')
    search_fields = ('nom',)

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'type_mouvement', 'quantite', 'date_mouvement', 'impact_financier')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('medicament__nom',) 