# PV+Battery Dimensioning Suite

Application web interactive pour le dimensionnement et l'analyse de systèmes photovoltaïques résidentiels avec stockage électrochimique.

## 🚀 Fonctionnalités

### 📐 Dimensionnement Intelligent
- **Analyse consommation** : Saisie de la consommation annuelle, répartition jour/nuit
- **Dimensionnement PV** : Calcul de la puissance nécessaire en fonction de la localisation
- **Dimensionnement batterie** : Choix de technologie (Li-ion, Plomb-acide), calcul de capacité

### 📊 Simulation Multi-Scénarios
5 scénarios prédéfinis :
- **S0** : Réseau seul (référence)
- **S1** : PV seul sans stockage
- **S2** : PV + Batterie Plomb-acide
- **S3** : PV + Batterie Lithium-ion
- **S4** : Configuration optimisée

### 📈 Indicateurs Énergétiques
Pour chaque scénario :
- Énergie produite par le PV (kWh)
- Énergie stockée/déstockée
- Énergie importée du réseau
- Taux d'autoconsommation (%)
- Taux de couverture (%)
- Réduction de l'appel réseau (%)

### 🎨 Visualisations Avancées
- Histogrammes comparatifs
- Courbes de performance
- Diagramme radar multicritère
- Graphique du profil journalier

### 🏆 Analyse et Recommandation
- Score multicritère personnalisable
- Classement automatique des scénarios
- Recommandation détaillée avec justification

### 📥 Export des Résultats
- Rapport PDF professionnel
- Fichier Excel avec données brutes
- Configuration JSON
- Données CSV

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip

### Installation
1. Cloner le dépôt :
```bash
git clone <repository-url>
cd pv_battery_suite