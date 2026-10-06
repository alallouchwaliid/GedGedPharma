from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('historique/', views.historique, name='historique'),
    path('parametres/', views.parametres, name='parametres'),
    path('profil/', views.profil, name='profil'), # Add this line
    path('export-csv/', views.export_csv, name='export_csv'), # Add this line
    path('export/bon/', views.export_bon, name='export_bon'),
]