from django.db import models
from django.utils import timezone

class Medicament(models.Model):
    nom = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actuel = models.IntegerField(default=0) # Représente S_{i,p}
    
    # Nouveaux champs pour calculer le Ratio Critique (CR_p)
    cout_sous_stockage = models.DecimalField(max_digits=10, decimal_places=2, default=50.00, help_text="Marge perdue + impact santé (C_u)")
    cout_surstockage = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, help_text="Prix d'achat + stockage + risque (C_o)")

    def __str__(self):
        return f"{self.nom} {self.dosage}"

class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Réception Fournisseur'),
        ('SORTIE', 'Vente Client'),
    ]
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField()
    date_mouvement = models.DateTimeField(default=timezone.now)
    impact_financier = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calcul de l'impact et mise à jour du stock automatique
        if self.type_mouvement == 'SORTIE':
            self.impact_financier = self.medicament.prix_unitaire * self.quantite
        else:
            self.impact_financier = -(self.medicament.prix_unitaire * self.quantite)

        if not self.pk:
            if self.type_mouvement == 'ENTREE':
                self.medicament.stock_actuel += self.quantite
            elif self.type_mouvement == 'SORTIE':
                self.medicament.stock_actuel -= self.quantite
            self.medicament.save()

        super().save(*args, **kwargs)