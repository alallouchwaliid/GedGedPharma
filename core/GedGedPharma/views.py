from django.shortcuts import render

import math
import statistics
import csv
from datetime import timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from .models import Medicament, MouvementStock
import math
import statistics
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from .models import Medicament, MouvementStock

import math
import statistics
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from .models import Medicament, MouvementStock

def index(request):
    # Récupérer tous les médicaments de la base de données
    medicaments = Medicament.objects.all()
    
    # Paramètres globaux de l'algorithme (Inputs)
    T = 7       # Délai d'approvisionnement (en jours)
    Z = 1.65    # Facteur de confiance pour 95% de disponibilité
    
    # Initialisation des compteurs pour les KPIs (en haut du Dashboard)
    table_data = []
    ruptures_count = 0
    total_commandes = 0
    pertes_evitees = 0
    
    today = timezone.now().date()
    
    for med in medicaments:
        ventes_journalieres = []
        
        # 1. Analyse de l'historique sur 60 jours (2 mois exacts)
        for i in range(60):
            day = today - timedelta(days=i)
            total_vendu = MouvementStock.objects.filter(
                medicament=med, 
                type_mouvement='SORTIE', 
                date_mouvement__date=day
            ).aggregate(Sum('quantite'))['quantite__sum'] or 0
            
            ventes_journalieres.append(total_vendu)
        
        # 2. Calcul des paramètres statistiques (D et Sigma)
        demande_moyenne = statistics.mean(ventes_journalieres) if ventes_journalieres else 0
        ecart_type = statistics.stdev(ventes_journalieres) if len(ventes_journalieres) > 1 else 0
            
        # 3. Calcul du Stock de Sécurité (SS) et du Besoin Net (B)
        stock_securite = math.ceil(Z * ecart_type * math.sqrt(T))
        stock_actuel = med.stock_actuel
        
        besoin_net = math.ceil((demande_moyenne * T) + stock_securite - stock_actuel)
        besoin_net_arrondi = max(0, besoin_net) # On ne commande jamais une quantité négative
        
        # 4. Logique des statuts d'alerte et calcul des pertes financières évitées
        if stock_actuel <= stock_securite * 0.5:
            statut = "Commander d'urgence"
            badge_class = "bg-red-100 text-red-700"
            ruptures_count += 1
            # Urgence : on ajoute la marge perdue (C_u) fois le besoin net
            pertes_evitees += (besoin_net_arrondi * float(med.cout_sous_stockage))
            
        elif stock_actuel <= stock_securite:
            statut = "Préparer commande"
            badge_class = "bg-yellow-100 text-yellow-700"
            # Prévention : on ajoute la marge sauvée
            pertes_evitees += (besoin_net_arrondi * float(med.cout_sous_stockage))
            
        else:
            statut = "Stock Optimal"
            badge_class = "bg-emerald-100 text-emerald-700"
            # Tout va bien, aucune perte à éviter pour l'instant
            
        total_commandes += besoin_net_arrondi
        
        # 5. Préparation des données pour l'affichage (Tableau et Graphiques éventuels)
        historique_7j = ventes_journalieres[:7]
        historique_7j.reverse() # Remettre dans l'ordre chronologique (J-6 jusqu'à Aujourd'hui)
        
        # Calcul du Ratio Critique (CR_p) au cas où vous en auriez besoin
        cu = float(med.cout_sous_stockage)
        co = float(med.cout_surstockage)
        ratio_critique = cu / (cu + co) if (cu + co) > 0 else 0
        
        table_data.append({
            'nom': med.nom,
            'stock_actuel': stock_actuel,
            'stock_securite': stock_securite,
            'besoin_net': besoin_net_arrondi,
            'statut': statut,
            'badge_class': badge_class,
            'historique': historique_7j,
            'ratio_critique': round(ratio_critique, 2)
        })
        ordre_priorite = {
        "Commander d'urgence": 1,
        "Préparer commande": 2,
        "Stock Optimal": 3
    }
    
    table_data = sorted(table_data, key=lambda x: (ordre_priorite.get(x['statut'], 4), -x['besoin_net']))
    # Envoi de toutes les données compilées vers le template HTML
    context = {
        'table_data': table_data,
        'ruptures_count': ruptures_count,
        'total_commandes': total_commandes,
        # Formatage avec des espaces pour les milliers (ex: 4 250)
        'pertes_evitees': f"{pertes_evitees:,.0f}".replace(',', ' '), 
        'date_today': today.strftime("%d %B %Y")
    }
    
    return render(request, 'index.html', context)


# (Gardez vos fonctions historique(), export_csv() et export_bon() telles qu'elles étaient)
from .models import MouvementStock

import json
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from .models import MouvementStock, Medicament

def historique(request):
    # Récupérer tous les mouvements du plus récent au plus ancien
    mouvements = MouvementStock.objects.all().order_by('-date_mouvement')
    
    # Préparer les données pour le graphique des 7 derniers jours
    today = timezone.now().date()
    labels_jours = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels_jours.append(d.strftime("%d %b"))
        
    # On prend les 2 principaux médicaments pour tracer les courbes du graphique
    medicaments_top = Medicament.objects.all()[:2]
    
    datasets_chart = []
    colors = ['#10b981', '#3b82f6']
    border_dashes = [[], [5, 5]]
    
    for index, med in enumerate(medicaments_top):
        data_ventes = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            total = MouvementStock.objects.filter(
                medicament=med, 
                type_mouvement='SORTIE', 
                date_mouvement__date=day
            ).aggregate(Sum('quantite'))['quantite__sum'] or 0
            data_ventes.append(total)
            
        datasets_chart.append({
            'label': f"{med.nom} {med.dosage}",
            'data': data_ventes,
            'borderColor': colors[index % len(colors)],
            'backgroundColor': 'rgba(16, 185, 129, 0.1)' if index == 0 else 'transparent',
            'borderWidth': 2,
            'borderDash': border_dashes[index % len(border_dashes)],
            'tension': 0.4,
            'fill': (index == 0),
            'pointRadius': 3
        })

    context = {
        'mouvements': mouvements,
        'labels_jours': json.dumps(labels_jours),
        'datasets_chart': json.dumps(datasets_chart),
    }
    return render(request, 'historique.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages

def parametres(request):
    if request.method == 'POST':
        # Vous pouvez récupérer et sauvegarder les valeurs ici si vous utilisez un modèle de configuration, 
        # ou simplement afficher un message de succès pour le hackathon.
        nom_pharmacie = request.POST.get('nom_pharmacie', 'Pharmacie Centrale')
        ville = request.POST.get('ville', 'Ben Guerir')
        telephone = request.POST.get('telephone', '+212 5 24 12 34 56')
        taux_service = request.POST.get('taux_service', 'Équilibré (95%)')
        delai = request.POST.get('delai', '2')
        
        messages.success(request, "Paramètres enregistrés avec succès !")
        return redirect('parametres')

    context = {
        'nom_pharmacie': 'Pharmacie Centrale',
        'ville': 'Ben Guerir',
        'telephone': '+212 5 24 12 34 56',
        'delai': 7, # Aligné avec votre délai par défaut de l'algorithme (T=7)
    }
    return render(request, 'parametres.html', context)
def profil(request):
    context = {
        'nom_complet': 'Dr. Walid Alallouch',
        'role': 'Pharmacien Titulaire',
        'pharmacie': 'Pharmacie Centrale',
        'ville': 'Ben Guerir',
        'telephone': '+212 6 00 00 00 00',
        'email': 'walid.alallouch@emines.um6p.ma',
    }
    return render(request, 'profil.html', context)




import csv
from django.http import HttpResponse
from .models import MouvementStock

def export_csv(request):
    # Configuration de la réponse HTTP pour télécharger un fichier CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="historique_mouvements.csv"'
    
    # Ajout du BOM UTF-8 pour un affichage correct des accents sous Excel
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    
    # En-têtes des colonnes
    writer.writerow(['Date', 'Medicament', 'Dosage', 'Type de Mouvement', 'Quantite'])
    
    # Récupération de tous les mouvements réels de la base de données
    mouvements = MouvementStock.objects.all().order_by('-date_mouvement')
    
    for m in mouvements:
        writer.writerow([
            m.date_mouvement.strftime('%d/%m/%Y %H:%M'),
            m.medicament.nom,
            m.medicament.dosage,
            m.type_mouvement,
            m.quantite
        ])
        
    return response


import csv
import math
import statistics
from datetime import timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum
from .models import Medicament, MouvementStock

def export_bon(request):
    # En-tête de la réponse HTTP pour télécharger le fichier texte
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="bon_de_commande_fournisseur.txt"'
    
    response.write("==================================================\n")
    response.write("          GEDGED PHARMA - BON DE COMMANDE         \n")
    response.write("          Réapprovisionnement Intelligent         \n")
    response.write(f"          Date : {timezone.now().strftime('%d/%m/%Y')}                    \n")
    response.write("==================================================\n\n")
    response.write(f"{'STATUT':<12} | {'MÉDICAMENT':<15} | {'DOSAGE':<8} | {'COMMANDE'}\n")
    response.write("-" * 54 + "\n")
    
    medicaments = Medicament.objects.all()
    T = 7       
    Z = 1.65    
    today = timezone.now().date()
    
    items_commande = []
    total_boites = 0
    
    for med in medicaments:
        ventes_journalieres = []
        for i in range(60):
            day = today - timedelta(days=i)
            total_vendu = MouvementStock.objects.filter(
                medicament=med, type_mouvement='SORTIE', date_mouvement__date=day
            ).aggregate(Sum('quantite'))['quantite__sum'] or 0
            ventes_journalieres.append(total_vendu)
        
        demande_moyenne = statistics.mean(ventes_journalieres) if ventes_journalieres else 0
        ecart_type = statistics.stdev(ventes_journalieres) if len(ventes_journalieres) > 1 else 0
        
        stock_securite = math.ceil(Z * ecart_type * math.sqrt(T))
        stock_actuel = med.stock_actuel
        
        besoin_net = math.ceil((demande_moyenne * T) + stock_securite - stock_actuel)
        besoin_net_arrondi = max(0, besoin_net)
        
        # Attribution des statuts et des priorités strictes :
        # 1. ROUGE (Urgence) -> Priorité 1
        # 2. JAUNE (Préparation) -> Priorité 2
        # 3. VERT (Stock Optimal / Besoin = 0) -> Priorité 3
        if stock_actuel <= stock_securite * 0.5:
            statut_texte = "ROUGE"
            priorite_val = 1
        elif stock_actuel <= stock_securite:
            statut_texte = "JAUNE"
            priorite_val = 2
        else:
            statut_texte = "VERT"
            priorite_val = 3
                
        items_commande.append({
            'priorite': priorite_val,
            'statut': statut_texte,
            'nom': med.nom,
            'dosage': med.dosage,
            'quantite': besoin_net_arrondi
        })

    # Tri strict : d'abord Rouge (1), puis Jaune (2), puis Vert (3)
    items_commande = sorted(items_commande, key=lambda x: x['priorite'])
    
    # Écriture dans le fichier texte généré
    for item in items_commande:
        response.write(f"[{item['statut']:<5}]       | {item['nom']:<15} | {item['dosage']:<8} | {item['quantite']} boîtes\n")
        # On ne compte que les boîtes rouges et jaunes dans le total de la commande fournisseur
        if item['statut'] in ["ROUGE", "JAUNE"]:
            total_boites += item['quantite']

    response.write("-" * 54 + "\n")
    response.write(f"TOTAL DES BOÎTES À COMMANDER : {total_boites}\n")
    response.write("==================================================\n")
    response.write("Cachet et Signature du Pharmacien :\n\n\n")
    
    return response