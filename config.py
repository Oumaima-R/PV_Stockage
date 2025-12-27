# config.py
# Configuration de l'application pour le Maroc

# ============================================================================
# PALETTE DE COULEURS
# ============================================================================
COLOR_PALETTE = {
    # Couleurs principales inspirées du Maroc
    "primary": "#C1272D",      # Rouge marocain (drapeau)
    "secondary": "#006233",    # Vert marocain (drapeau)
    "accent": "#F7DC6F",       # Or/sable du désert
    "neutral": "#5D4037",      # Brun terre/argile
    "success": "#27AE60",      # Vert palmier
    "warning": "#E67E22",      # Orange coucher de soleil
    "error": "#C0392B",        # Rouge terre cuite
    "background": "#FEF9E7",   # Jaune sable clair
    "text": "#2C3E50",         # Bleu nuit
    "card_bg": "#FFFFFF",      # Blanc cassé
    
    # Couleurs des scénarios
    "scenario_0": "#95A5A6",   # S0 - Gris neutre
    "scenario_1": "#F39C12",   # S1 - Orange soleil
    "scenario_2": "#3498DB",   # S2 - Bleu eau
    "scenario_3": "#2ECC71",   # S3 - Vert oasis
    "scenario_4": "#9B59B6",   # S4 - Violet montagne
}

# ============================================================================
# PARAMÈTRES PAR DÉFAUT (Adaptés au contexte marocain)
# ============================================================================
DEFAULT_PARAMS = {
    "annual_consumption": 4500,      # kWh/an (moyenne ménage marocain)
    "day_night_ratio": 0.65,         # 65% jour, 35% nuit (climat ensoleillé)
    "pv_coverage_target": 0.7,       # 70% de couverture PV (ensoleillement élevé)
    "performance_ratio": 0.78,       # PR du système (bon ensoleillement)
    "module_efficiency": 0.19,       # Rendement module
    "system_losses": 0.10,           # Pertes système
    "autonomy_hours": 6,             # Autonomie batterie
    "battery_tech": "lithium",       # Technologie batterie par défaut
    "currency": "MAD",               # Dirham marocain
    "electricity_price": 1.4,        # Prix moyen kWh en MAD (réseau ONEE)
    "injection_price": 0.8,          # Prix de rachat en MAD
}

# ============================================================================
# SPÉCIFICATIONS TECHNIQUES
# ============================================================================
TECH_SPECS = {
    "batteries": {
        "lithium": {
            "name": "Lithium-ion",
            "dod": 0.85,             # Depth of Discharge
            "efficiency": 0.95,      # Rendement charge/décharge
            "lifetime_cycles": 6000, # Durée de vie en cycles
            "cost_per_kwh": 3500,    # MAD/kWh (environ 350€)
            "maintenance_cost": 200, # MAD/an
            "replacement_years": 10, # Durée avant remplacement
            "temperature_range": "0-45°C", # Adapté au climat marocain
            "color": COLOR_PALETTE["scenario_3"],
            "icon": "🔋"
        },
        "lead_acid": {
            "name": "Plomb-acide",
            "dod": 0.5,
            "efficiency": 0.85,
            "lifetime_cycles": 1500,
            "cost_per_kwh": 1800,    # MAD/kWh (environ 180€)
            "maintenance_cost": 400, # MAD/an
            "replacement_years": 5,
            "temperature_range": "15-30°C",
            "color": COLOR_PALETTE["scenario_2"],
            "icon": "⚡"
        },
        "stationary": {
            "name": "Batterie stationnaire",
            "dod": 0.8,
            "efficiency": 0.92,
            "lifetime_cycles": 4000,
            "cost_per_kwh": 2800,    # MAD/kWh
            "maintenance_cost": 300, # MAD/an
            "replacement_years": 8,
            "temperature_range": "10-40°C",
            "color": "#8E44AD",
            "icon": "🏭"
        }
    },
    "pv_modules": {
        "monocrystalline": {
            "name": "Monocristallin",
            "efficiency_range": (0.18, 0.22),
            "efficiency_typical": 0.20,
            "power_per_module": 0.4,   # kWc/module
            "area_per_module": 1.8,    # m²/module
            "cost_per_kwp": 7000,      # MAD/kWc
            "lifetime_years": 25,
            "degradation": 0.005,      # %/an
            "temperature_coef": -0.004, # %/°C
            "color": "#2C3E50",
            "icon": "🔷"
        },
        "polycrystalline": {
            "name": "Polycristallin",
            "efficiency_range": (0.15, 0.18),
            "efficiency_typical": 0.16,
            "power_per_module": 0.35,  # kWc/module
            "area_per_module": 1.9,    # m²/module
            "cost_per_kwp": 5500,      # MAD/kWc
            "lifetime_years": 25,
            "degradation": 0.005,
            "temperature_coef": -0.0045,
            "color": "#3498DB",
            "icon": "🔶"
        },
        "thin_film": {
            "name": "Couche mince",
            "efficiency_range": (0.10, 0.13),
            "efficiency_typical": 0.11,
            "power_per_module": 0.3,   # kWc/module
            "area_per_module": 2.2,    # m²/module
            "cost_per_kwp": 4500,      # MAD/kWc
            "lifetime_years": 20,
            "degradation": 0.008,
            "temperature_coef": -0.002,
            "color": "#E74C3C",
            "icon": "📉"
        }
    },
    "inverters": {
        "string": {
            "name": "Onduleur string",
            "efficiency": 0.97,
            "cost_per_kw": 3000,       # MAD/kW
            "lifetime_years": 10,
            "icon": "🔌"
        },
        "micro": {
            "name": "Micro-onduleur",
            "efficiency": 0.96,
            "cost_per_kw": 4500,       # MAD/kW
            "lifetime_years": 15,
            "icon": "📱"
        },
        "hybrid": {
            "name": "Onduleur hybride",
            "efficiency": 0.95,
            "cost_per_kw": 5000,       # MAD/kW
            "lifetime_years": 10,
            "icon": "⚡"
        }
    }
}

# ============================================================================
# VILLES MAROCAINES AVEC IRRADIATION (kWh/m²/an)
# ============================================================================
CITIES_IRRADIATION = {
    # Source : NASA POWER, PVGIS, données solaires Maroc
    "Agadir": {
        "irradiation": 1850,
        "latitude": 30.4278,
        "longitude": -9.5981,
        "altitude": 23,
        "region": "Souss-Massa",
        "climate": "Méditerranéen",
        "avg_temp": 20.4,
        "sun_hours": 3000
    },
    "Marrakech": {
        "irradiation": 2050,
        "latitude": 31.6295,
        "longitude": -7.9811,
        "altitude": 466,
        "region": "Marrakech-Safi",
        "climate": "Semi-aride",
        "avg_temp": 19.6,
        "sun_hours": 3200
    },
    "Casablanca": {
        "irradiation": 1750,
        "latitude": 33.5731,
        "longitude": -7.5898,
        "altitude": 57,
        "region": "Casablanca-Settat",
        "climate": "Méditerranéen",
        "avg_temp": 18.5,
        "sun_hours": 2800
    },
    "Rabat": {
        "irradiation": 1700,
        "latitude": 34.0209,
        "longitude": -6.8416,
        "altitude": 75,
        "region": "Rabat-Salé-Kénitra",
        "climate": "Méditerranéen",
        "avg_temp": 17.8,
        "sun_hours": 2750
    },
    "Fès": {
        "irradiation": 1950,
        "latitude": 34.0181,
        "longitude": -5.0078,
        "altitude": 410,
        "region": "Fès-Meknès",
        "climate": "Méditerranéen continental",
        "avg_temp": 17.8,
        "sun_hours": 2900
    },
    "Tanger": {
        "irradiation": 1650,
        "latitude": 35.7595,
        "longitude": -5.8340,
        "altitude": 80,
        "region": "Tanger-Tétouan-Al Hoceïma",
        "climate": "Méditerranéen",
        "avg_temp": 18.2,
        "sun_hours": 2700
    },
    "Meknès": {
        "irradiation": 1900,
        "latitude": 33.8920,
        "longitude": -5.5541,
        "altitude": 549,
        "region": "Fès-Meknès",
        "climate": "Méditerranéen continental",
        "avg_temp": 17.2,
        "sun_hours": 2850
    },
    "Oujda": {
        "irradiation": 2000,
        "latitude": 34.6810,
        "longitude": -1.9076,
        "altitude": 470,
        "region": "Oriental",
        "climate": "Semi-aride",
        "avg_temp": 17.4,
        "sun_hours": 2950
    },
    "Laâyoune": {
        "irradiation": 2250,
        "latitude": 27.1500,
        "longitude": -13.2000,
        "altitude": 64,
        "region": "Laâyoune-Sakia El Hamra",
        "climate": "Désertique",
        "avg_temp": 21.5,
        "sun_hours": 3400
    },
    "Dakhla": {
        "irradiation": 2350,
        "latitude": 23.7141,
        "longitude": -15.9368,
        "altitude": 11,
        "region": "Dakhla-Oued Ed-Dahab",
        "climate": "Désertique",
        "avg_temp": 21.0,
        "sun_hours": 3500
    },
    "Essaouira": {
        "irradiation": 1800,
        "latitude": 31.5085,
        "longitude": -9.7595,
        "altitude": 10,
        "region": "Marrakech-Safi",
        "climate": "Méditerranéen océanique",
        "avg_temp": 18.5,
        "sun_hours": 2900
    },
    "Ifrane": {
        "irradiation": 1750,
        "latitude": 33.5333,
        "longitude": -5.1167,
        "altitude": 1665,
        "region": "Fès-Meknès",
        "climate": "Montagnard",
        "avg_temp": 11.4,
        "sun_hours": 2600
    },
    "Tétouan": {
        "irradiation": 1700,
        "latitude": 35.5889,
        "longitude": -5.3622,
        "altitude": 90,
        "region": "Tanger-Tétouan-Al Hoceïma",
        "climate": "Méditerranéen",
        "avg_temp": 18.0,
        "sun_hours": 2650
    },
    "Nador": {
        "irradiation": 1900,
        "latitude": 35.1686,
        "longitude": -2.9275,
        "altitude": 42,
        "region": "Oriental",
        "climate": "Méditerranéen",
        "avg_temp": 18.8,
        "sun_hours": 2850
    },
    "Kénitra": {
        "irradiation": 1750,
        "latitude": 34.2541,
        "longitude": -6.5890,
        "altitude": 26,
        "region": "Rabat-Salé-Kénitra",
        "climate": "Méditerranéen",
        "avg_temp": 18.1,
        "sun_hours": 2800
    }
}

# ============================================================================
# TARIFS ÉLECTRIQUES MAROC (ONEE - 2024)
# ============================================================================
ELECTRICITY_TARIFFS = {
    "residential_low": {        # Basse tension
        "blocks": [
            {"limit": 100, "price": 0.9017},    # MAD/kWh
            {"limit": 200, "price": 1.0732},
            {"limit": 300, "price": 1.3456},
            {"limit": 400, "price": 1.5687},
            {"limit": None, "price": 1.7829}
        ],
        "fixed_charge": 35.00,  # MAD/mois
    },
    "residential_medium": {     # Moyenne tension
        "blocks": [
            {"limit": 200, "price": 0.8567},
            {"limit": 500, "price": 1.0367},
            {"limit": 1000, "price": 1.2122},
            {"limit": None, "price": 1.3712}
        ],
        "fixed_charge": 120.00,
    },
    "injection_tariff": {       # Tarif de rachat
        "pv_under_20kw": 0.95,  # MAD/kWh pour PV < 20kW
        "pv_20_200kw": 0.90,    # MAD/kWh pour 20-200kW
        "pv_over_200kw": 0.85,  # MAD/kWh pour >200kW
    },
    "peak_hours": {
        "summer": ["18:00", "22:00"],
        "winter": ["18:00", "21:00"],
        "peak_price_multiplier": 1.5
    }
}

# ============================================================================
# SUBSIDES ET INCITATIONS MAROC
# ============================================================================
SUBSIDIES = {
    "energy_efficiency": {
        "name": "Programme d'Efficacité Énergétique",
        "subsidy_rate": 0.30,     # 30% de subvention
        "max_amount": 20000,      # MAD maximum
        "conditions": ["Résidentiel", "Système certifié"]
    },
    "solar_water_heater": {
        "name": "Chauffe-eau Solaire",
        "subsidy_rate": 0.40,     # 40% de subvention
        "max_amount": 15000,      # MAD maximum
    },
    "pv_installation": {
        "name": "Installation PV",
        "subsidy_rate": 0.20,     # 20% de subvention
        "max_amount": 30000,      # MAD maximum
        "conditions": ["Puissance ≤ 5kWc", "Autoconsommation"]
    },
    "battery_storage": {
        "name": "Stockage Énergétique",
        "subsidy_rate": 0.25,     # 25% de subvention
        "max_amount": 25000,      # MAD maximum
        "conditions": ["Coupled with PV", "Efficiency > 90%"]
    }
}

# ============================================================================
# PROFILS DE CONSOMMATION TYPIQUE MAROC
# ============================================================================
CONSUMPTION_PROFILES = {
    "urban_standard": {
        "name": "Ménage urbain standard",
        "annual_kwh": 4500,
        "day_night_ratio": 0.65,
        "peak_hours": ["19:00", "22:00"],
        "appliances": ["Climatisation", "Réfrigérateur", "TV", "Éclairage LED"]
    },
    "rural": {
        "name": "Ménage rural",
        "annual_kwh": 2500,
        "day_night_ratio": 0.60,
        "peak_hours": ["18:00", "21:00"],
        "appliances": ["Éclairage", "TV", "Petits appareils"]
    },
    "high_consumption": {
        "name": "Maison climatisée",
        "annual_kwh": 8000,
        "day_night_ratio": 0.70,
        "peak_hours": ["14:00", "23:00"],
        "appliances": ["Climatisation", "Chauffe-eau", "Électroménager"]
    },
    "eco": {
        "name": "Maison économe",
        "annual_kwh": 3000,
        "day_night_ratio": 0.60,
        "peak_hours": ["19:00", "21:00"],
        "appliances": ["Éclairage LED", "Électroménager A++"]
    }
}

# ============================================================================
# RÉGLEMENTATIONS ET NORMES MAROC
# ============================================================================
REGULATIONS = {
    "pv_installation": {
        "min_distance": 1.0,      # mètres des limites
        "max_height": 2.5,        # mètres de hauteur
        "structural_requirements": "Norme NM IEC 61215",
        "electrical_standards": "Norme NM CEI 60364"
    },
    "grid_connection": {
        "max_power_no_permit": 5, # kWc sans permis
        "injection_limit": 0.33,  # 33% de la puissance souscrite
        "protection_devices": ["Disjoncteur différentiel", "Parafoudre"]
    },
    "battery_storage": {
        "safety_standards": "Norme NM CEI 62619",
        "ventilation_required": True,
        "fire_protection": "Classe IP54 minimum"
    }
}

# ============================================================================
# CONSTANTES TECHNIQUES SPÉCIFIQUES MAROC
# ============================================================================
TECH_CONSTANTS = {
    "temperature_correction": {
        "reference_temp": 25,      # °C
        "temp_coef_power": -0.004, # %/°C
        "avg_ambient_temp": 20,    # °C moyen Maroc
        "module_temp_rise": 25,    # °C au-dessus de l'ambiant
    },
    "system_losses": {
        "soiling": 0.05,          # 5% salissure (poussière, sable)
        "shading": 0.03,          # 3% ombrage
        "wiring": 0.02,           # 2% câblage
        "mismatch": 0.02,         # 2% désadaptation
        "inverter": 0.03,         # 3% onduleur
        "total_typical": 0.15,    # 15% pertes totales typiques
    },
    "financial": {
        "inflation_rate": 0.02,   # 2% inflation
        "discount_rate": 0.05,    # 5% taux d'actualisation
        "project_lifetime": 25,   # ans
        "maintenance_rate": 0.01, # 1% du coût d'investissement/an
    }
}

# ============================================================================
# LABELS ET TRADUCTIONS (Français/Arabe)
# ============================================================================
LABELS = {
    "fr": {
        "app_name": "Suite de Dimensionnement PV+Batterie - Maroc",
        "app_slogan": "Optimisation Énergétique Intelligente pour le Maroc",
        "kwh": "kWh",
        "mad": "MAD",
        "years": "ans",
        "hours": "heures",
        "efficiency": "Rendement",
        "capacity": "Capacité",
        "production": "Production",
        "consumption": "Consommation",
        "savings": "Économies",
        "roi": "Retour sur investissement",
        "autonomy": "Autonomie",
        "coverage": "Couverture",
        "grid": "Réseau",
        "battery": "Batterie",
        "pv": "Photovoltaïque",
    },
    "ar": {
        "app_name": "سويت تحديد أبعاد الأنظمة الشمسية مع البطاريات - المغرب",
        "app_slogan": "التكيف الذكي للطاقة للمغرب",
        "kwh": "كيلوواط ساعة",
        "mad": "درهم",
        "years": "سنوات",
        "hours": "ساعات",
        "efficiency": "الكفاءة",
        "capacity": "السعة",
        "production": "الإنتاج",
        "consumption": "الاستهلاك",
        "savings": "التوفير",
        "roi": "العائد على الاستثمار",
        "autonomy": "الاستقلالية",
        "coverage": "التغطية",
        "grid": "الشبكة",
        "battery": "البطارية",
        "pv": "الطاقة الشمسية",
    }
}

# ============================================================================
# FONCTIONS UTILITAIRES SPÉCIFIQUES
# ============================================================================
def get_city_info(city_name):
    """Récupère les informations d'une ville marocaine"""
    return CITIES_IRRADIATION.get(city_name, {
        "irradiation": 1800,
        "latitude": 31.7917,
        "longitude": -7.0926,
        "region": "Non spécifiée",
        "climate": "Non spécifié"
    })

def calculate_irradiation_monthly(city_name):
    """Retourne l'irradiation mensuelle typique pour une ville"""
    # Valeurs approximatives en kWh/m²
    monthly_irradiation = {
        "Agadir": [120, 140, 170, 190, 210, 220, 220, 200, 180, 150, 130, 120],
        "Marrakech": [140, 150, 180, 200, 220, 230, 240, 220, 190, 160, 140, 130],
        "Casablanca": [110, 130, 160, 180, 200, 210, 210, 190, 160, 130, 110, 100],
        "Rabat": [105, 125, 155, 175, 195, 205, 205, 185, 155, 125, 105, 95],
        "Laâyoune": [160, 180, 210, 230, 240, 250, 250, 230, 200, 170, 150, 140],
    }
    
    return monthly_irradiation.get(city_name, [150] * 12)

def estimate_electricity_bill(consumption_kwh, tariff_type="residential_low"):
    """Estime la facture électrique selon les tarifs ONEE"""
    tariff = ELECTRICITY_TARIFFS[tariff_type]
    total = tariff["fixed_charge"] * 12  # Frais fixes annuels
    
    remaining = consumption_kwh
    previous_limit = 0
    
    for block in tariff["blocks"]:
        if block["limit"] is None:
            # Dernier bloc (consommation restante)
            total += remaining * block["price"]
            break
        
        block_consumption = min(remaining, block["limit"] - previous_limit)
        total += block_consumption * block["price"]
        remaining -= block_consumption
        previous_limit = block["limit"]
        
        if remaining <= 0:
            break
    
    return total

def calculate_subsidy_amount(investment_cost, subsidy_type="pv_installation"):
    """Calcule le montant de la subvention"""
    subsidy = SUBSIDIES.get(subsidy_type, {})
    rate = subsidy.get("subsidy_rate", 0)
    max_amount = subsidy.get("max_amount", 0)
    
    subsidy_amount = investment_cost * rate
    return min(subsidy_amount, max_amount)

# ============================================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================================
APP_CONFIG = {
    "default_language": "fr",
    "available_languages": ["fr", "ar", "en"],
    "currency_symbol": "MAD",
    "decimal_separator": ",",
    "thousands_separator": " ",
    "date_format": "%d/%m/%Y",
    "time_format": "%H:%M",
    "temperature_unit": "°C",
    "energy_unit": "kWh",
    "power_unit": "kW",
    "capacity_unit": "kWh",
}

# ============================================================================
# MESSAGES D'INFORMATION CONTEXTUELS
# ============================================================================
INFO_MESSAGES = {
    "high_irradiation": "⚠️ Fort ensoleillement : Prévoir un dimensionnement légèrement inférieur et une ventilation adéquate",
    "desert_areas": "🏜️ Zones désertiques : Nettoyage fréquent des modules nécessaire (poussière, sable)",
    "coastal_areas": "🌊 Zones côtières : Protection contre la corrosion saline recommandée",
    "mountain_areas": "⛰️ Zones montagneuses : Tenir compte des variations de température",
    "summer_consumption": "☀️ Consommation estivale élevée : Forte demande pour la climatisation",
    "grid_stability": "⚡ Stabilité réseau : Dans certaines zones rurales, considérer une autonomie plus importante",
}

print("✅ Configuration Maroc chargée avec succès")