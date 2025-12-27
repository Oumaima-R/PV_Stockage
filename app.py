# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configuration de la page
st.set_page_config(
    page_title="PV+Battery Dimensioning Suite",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dans app.py, modifiez la fonction load_css() :
def load_css():
    with open('style_maroc.css') as f:  # Changé ici
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Importer la configuration
try:
    from config import COLOR_PALETTE, DEFAULT_PARAMS, TECH_SPECS, CITIES_IRRADIATION
except:
    # Fallback si config.py n'existe pas
    COLOR_PALETTE = {
        "primary": "#1E3A8A",
        "secondary": "#10B981",
        "accent": "#F59E0B",
        "neutral": "#6B7280",
        "success": "#059669",
        "warning": "#D97706",
        "error": "#DC2626",
        "background": "#F8FAFC",
        "scenario_0": "#94A3B8",
        "scenario_1": "#F59E0B",
        "scenario_2": "#3B82F6",
        "scenario_3": "#10B981",
        "scenario_4": "#8B5CF6",
    }
    
    DEFAULT_PARAMS = {
        "annual_consumption": 4000,
        "day_night_ratio": 0.6,
        "pv_coverage_target": 0.6,
        "performance_ratio": 0.75,
        "module_efficiency": 0.18,
        "system_losses": 0.12,
        "autonomy_hours": 8,
        "battery_tech": "lithium",
    }
    
    TECH_SPECS = {
        "batteries": {
            "lithium": {
                "name": "Lithium-ion",
                "dod": 0.85,
                "efficiency": 0.95,
                "lifetime_cycles": 6000,
                "cost_per_kwh": 400,
                "color": "#10B981"
            },
            "lead_acid": {
                "name": "Plomb-acide",
                "dod": 0.5,
                "efficiency": 0.85,
                "lifetime_cycles": 1500,
                "cost_per_kwh": 200,
                "color": "#3B82F6"
            }
        }
    }
    
    CITIES_IRRADIATION = {
        "Paris": 1150,
        "Lyon": 1250,
        "Marseille": 1550,
        "Toulouse": 1400,
        "Bordeaux": 1300,
    }

# ============================================================================
# FONCTIONS DE CALCUL
# ============================================================================

def calculate_daily_consumption(annual_consumption):
    """Calcule la consommation journalière"""
    return annual_consumption / 365

def calculate_average_power(daily_consumption):
    """Calcule la puissance moyenne"""
    return daily_consumption / 24

def calculate_pv_power(annual_consumption, coverage_target, irradiation, 
                      performance_ratio, module_efficiency, system_losses):
    """Calcule la puissance PV nécessaire"""
    energy_needed = annual_consumption * coverage_target
    system_efficiency = performance_ratio * module_efficiency * (1 - system_losses)
    pv_power_kwp = energy_needed / (irradiation * system_efficiency)
    return pv_power_kwp

def calculate_annual_pv_production(pv_power_kwp, irradiation, 
                                 performance_ratio, system_losses):
    """Calcule la production annuelle PV"""
    return pv_power_kwp * irradiation * performance_ratio * (1 - system_losses)

def calculate_battery_capacity(night_consumption, autonomy_hours, dod):
    """Calcule la capacité de batterie nécessaire"""
    usable_capacity = night_consumption * (autonomy_hours / 24)
    nominal_capacity = usable_capacity / dod
    return nominal_capacity

def calculate_scenario_indicators(scenario_name, params, pv_power, battery_capacity):
    """Calcule les indicateurs pour un scénario donné"""
    
    annual_consumption = params["annual_consumption"]
    day_night_ratio = params["day_night_ratio"]
    pv_production = params.get("pv_production", 0)
    battery_tech = params.get("battery_tech")
    
    # Consommations jour/nuit
    day_consumption = annual_consumption * day_night_ratio
    night_consumption = annual_consumption * (1 - day_night_ratio)
    
    # Initialisation des indicateurs
    indicators = {
        "scenario": scenario_name,
        "pv_production": 0,
        "energy_stored": 0,
        "energy_discharged": 0,
        "grid_import": 0,
        "grid_export": 0,
        "energy_losses": 0,
        "self_consumption_rate": 0,
        "coverage_rate": 0,
        "grid_reduction": 0,
        "autonomy_hours": 0,
    }
    
    # Scénario S0: Réseau seul
    if scenario_name == "S0":
        indicators["grid_import"] = annual_consumption
        indicators["coverage_rate"] = 0
        indicators["grid_reduction"] = 0
    
    # Scénario S1: PV seul
    elif scenario_name == "S1":
        pv_prod = pv_production
        # Production utilisée directement
        direct_use = min(pv_prod, day_consumption)
        surplus = pv_prod - direct_use
        
        indicators["pv_production"] = pv_prod
        indicators["grid_import"] = annual_consumption - direct_use
        indicators["grid_export"] = surplus * 0.8  # 80% exporté, 20% perdu
        indicators["energy_losses"] = surplus * 0.2
        
        if pv_prod > 0:
            indicators["self_consumption_rate"] = (direct_use / pv_prod) * 100
            indicators["coverage_rate"] = (direct_use / annual_consumption) * 100
            indicators["grid_reduction"] = ((annual_consumption - indicators["grid_import"]) / annual_consumption) * 100
    
    # Scénario S2/S3: PV + Batterie
    elif scenario_name in ["S2", "S3"]:
        pv_prod = pv_production
        battery_specs = TECH_SPECS["batteries"][battery_tech]
        
        # Production PV
        direct_use = min(pv_prod, day_consumption)
        surplus = pv_prod - direct_use
        
        # Stockage batterie
        battery_efficiency = battery_specs["efficiency"]
        max_storage = battery_capacity * battery_specs["dod"] if battery_capacity > 0 else 0
        
        energy_to_store = min(surplus, max_storage)
        energy_stored = energy_to_store * battery_efficiency
        energy_discharged = min(energy_stored, night_consumption) * battery_efficiency
        
        # Calculs finaux
        indicators["pv_production"] = pv_prod
        indicators["energy_stored"] = energy_stored
        indicators["energy_discharged"] = energy_discharged
        indicators["grid_import"] = max(0, annual_consumption - direct_use - energy_discharged)
        indicators["grid_export"] = max(0, surplus - energy_to_store) * 0.8
        indicators["energy_losses"] = (surplus - energy_to_store) * 0.2 + energy_stored * (1 - battery_efficiency)
        
        if pv_prod > 0:
            indicators["self_consumption_rate"] = ((direct_use + energy_to_store) / pv_prod) * 100
            indicators["coverage_rate"] = ((direct_use + energy_discharged) / annual_consumption) * 100
            indicators["grid_reduction"] = ((annual_consumption - indicators["grid_import"]) / annual_consumption) * 100
            indicators["autonomy_hours"] = (battery_capacity * battery_specs["dod"] / (night_consumption / 365 * 24)) if night_consumption > 0 else 0
    
    # Scénario S4: Optimisé (meilleur entre S2 et S3)
    elif scenario_name == "S4":
        # Pour l'exemple, on prend le meilleur des scénarios S2 et S3
        # Dans une version complète, on optimiserait les paramètres
        s2_indicators = calculate_scenario_indicators("S2", params, pv_power, battery_capacity)
        s3_indicators = calculate_scenario_indicators("S3", params, pv_power, battery_capacity)
        
        # Prendre le scénario avec la plus grande réduction réseau
        if s3_indicators["grid_reduction"] >= s2_indicators["grid_reduction"]:
            indicators = s3_indicators.copy()
            indicators["scenario"] = "S4"
            indicators["recommended_tech"] = "Lithium-ion"
        else:
            indicators = s2_indicators.copy()
            indicators["scenario"] = "S4"
            indicators["recommended_tech"] = "Plomb-acide"
    
    return indicators

def calculate_multicriteria_score(indicators):
    """Calcule un score multicritère pour un scénario"""
    weights = {
        "grid_reduction": 0.40,
        "self_consumption_rate": 0.30,
        "coverage_rate": 0.20,
        "cost_efficiency": 0.10  # Calculé séparément
    }
    
    # Normalisation des indicateurs (0-100)
    normalized = {}
    
    for key in ["grid_reduction", "self_consumption_rate", "coverage_rate"]:
        value = indicators.get(key, 0)
        normalized[key] = min(max(value, 0), 100)  # Déjà en pourcentage
    
    # Score coût (inversé - plus c'est bas, mieux c'est)
    # Estimation simplifiée du coût
    pv_cost = indicators.get("pv_power", 0) * 800  # €/kWc
    battery_cost = indicators.get("battery_capacity", 0) * 300  # €/kWh moyen
    total_cost = pv_cost + battery_cost
    
    # Normalisation coût (0-100, 100 = meilleur/moins cher)
    max_cost = 20000  # Coût maximum de référence
    normalized["cost_efficiency"] = max(0, 100 - (total_cost / max_cost * 100))
    
    # Calcul score pondéré
    score = sum(normalized[key] * weights[key] for key in weights.keys())
    
    return {
        "score": round(score, 1),
        "breakdown": normalized,
        "total_cost": round(total_cost, 0)
    }

# ============================================================================
# FONCTIONS DE VISUALISATION
# ============================================================================

def create_energy_balance_chart(scenarios_data):
    """Crée un graphique de bilan énergétique empilé"""
    
    scenarios = [s["scenario"] for s in scenarios_data]
    
    # Préparation des données pour chaque scénario
    categories = ["Autoconsommation", "Batterie", "Réseau", "Export", "Pertes"]
    colors = [COLOR_PALETTE["accent"], COLOR_PALETTE["secondary"], 
              COLOR_PALETTE["neutral"], "#60A5FA", COLOR_PALETTE["warning"]]
    
    fig = go.Figure()
    
    for i, category in enumerate(categories):
        values = []
        for scenario in scenarios_data:
            if category == "Autoconsommation":
                val = scenario.get("pv_production", 0) * (scenario.get("self_consumption_rate", 0) / 100)
            elif category == "Batterie":
                val = scenario.get("energy_discharged", 0)
            elif category == "Réseau":
                val = scenario.get("grid_import", 0)
            elif category == "Export":
                val = scenario.get("grid_export", 0)
            elif category == "Pertes":
                val = scenario.get("energy_losses", 0)
            values.append(val)
        
        fig.add_trace(go.Bar(
            name=category,
            x=scenarios,
            y=values,
            marker_color=colors[i],
            text=[f"{v:.0f}" for v in values],
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Bilan Énergétique par Scénario (kWh/an)",
        barmode='stack',
        xaxis_title="Scénarios",
        yaxis_title="Énergie (kWh/an)",
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Roboto, sans-serif"),
        height=500
    )
    
    return fig

def create_indicators_comparison_chart(scenarios_data):
    """Crée un graphique de comparaison des indicateurs clés"""
    
    scenarios = [s["scenario"] for s in scenarios_data]
    indicators = ["grid_reduction", "self_consumption_rate", "coverage_rate"]
    indicator_names = ["Réduction Réseau", "Autoconsommation", "Couverture"]
    
    fig = go.Figure()
    
    scenario_colors = {
        "S0": COLOR_PALETTE["scenario_0"],
        "S1": COLOR_PALETTE["scenario_1"],
        "S2": COLOR_PALETTE["scenario_2"],
        "S3": COLOR_PALETTE["scenario_3"],
        "S4": COLOR_PALETTE["scenario_4"],
    }
    
    for i, scenario in enumerate(scenarios):
        values = [scenarios_data[i].get(ind, 0) for ind in indicators]
        
        fig.add_trace(go.Bar(
            name=scenario,
            x=indicator_names,
            y=values,
            marker_color=scenario_colors.get(scenario, COLOR_PALETTE["neutral"]),
            text=[f"{v:.1f}%" for v in values],
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Comparaison des Indicateurs Clés (%)",
        barmode='group',
        xaxis_title="Indicateurs",
        yaxis_title="Valeur (%)",
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Roboto, sans-serif"),
        height=500
    )
    
    return fig

def create_radar_chart(scenarios_data):
    """Crée un graphique radar multicritère"""
    
    categories = ['Réduction Réseau', 'Autoconsommation', 'Couverture', 'Coût-efficacité', 'Autonomie']
    
    fig = go.Figure()
    
    scenario_colors = {
        "S0": COLOR_PALETTE["scenario_0"],
        "S1": COLOR_PALETTE["scenario_1"],
        "S2": COLOR_PALETTE["scenario_2"],
        "S3": COLOR_PALETTE["scenario_3"],
        "S4": COLOR_PALETTE["scenario_4"],
    }
    
    for scenario_dict in scenarios_data:
        scenario = scenario_dict["scenario"]
        
        # Calcul des valeurs normalisées (0-100)
        values = [
            scenario_dict.get("grid_reduction", 0),
            scenario_dict.get("self_consumption_rate", 0),
            scenario_dict.get("coverage_rate", 0),
            100 - min(scenario_dict.get("grid_import", 0) / 100, 100),  # Coût-efficacité simplifié
            min(scenario_dict.get("autonomy_hours", 0) * 10, 100)  # Autonomie normalisée
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=scenario,
            line_color=scenario_colors.get(scenario, COLOR_PALETTE["neutral"]),
            opacity=0.7
        ))
    
    fig.update_layout(
        title="Analyse Multicritère des Scénarios",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=500
    )
    
    return fig

def create_daily_profile_chart(params):
    """Crée un graphique du profil journalier de consommation"""
    
    # Profil horaire simulé
    hours = list(range(24))
    
    # Consommation de base
    daily_consumption = params["annual_consumption"] / 365
    hourly_base = [daily_consumption / 24] * 24
    
    # Ajout de pics (matin et soir)
    morning_peak = [1.5 if 7 <= h <= 9 else 1.0 for h in hours]
    evening_peak = [2.0 if 18 <= h <= 21 else 1.0 for h in hours]
    
    hourly_consumption = [base * morn * eve for base, morn, eve in zip(hourly_base, morning_peak, evening_peak)]
    
    # Production PV (en journée)
    pv_production = [0.3 * max(0, np.sin((h-6)*np.pi/12)) for h in hours]
    pv_production = [p * daily_consumption * 0.6 for p in pv_production]  # Ajustement
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=hourly_consumption,
        mode='lines',
        name='Consommation',
        line=dict(color=COLOR_PALETTE["primary"], width=3),
        fill='tozeroy',
        fillcolor='rgba(30, 58, 138, 0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=pv_production,
        mode='lines',
        name='Production PV',
        line=dict(color=COLOR_PALETTE["accent"], width=3, dash='dash'),
        fill='tozeroy',
        fillcolor='rgba(245, 158, 11, 0.1)'
    ))
    
    fig.update_layout(
        title="Profil Journalier Type (Consommation vs Production)",
        xaxis_title="Heure de la journée",
        yaxis_title="Puissance (kW)",
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Roboto, sans-serif"),
        height=400
    )
    
    return fig

# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================

def generate_pdf_report(params, scenarios_data, recommendations):
    """Génère un rapport PDF"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor(COLOR_PALETTE["primary"]),
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor(COLOR_PALETTE["primary"]),
        spaceAfter=12
    )
    
    # Contenu du rapport
    content = []
    
    # Titre
    content.append(Paragraph("Rapport de Dimensionnement PV avec Stockage", title_style))
    content.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    content.append(Spacer(1, 30))
    
    # Paramètres du projet
    content.append(Paragraph("1. Paramètres du Projet", heading_style))
    
    params_table_data = [
        ["Paramètre", "Valeur"],
        ["Consommation annuelle", f"{params['annual_consumption']} kWh"],
        ["Répartition jour/nuit", f"{params['day_night_ratio']*100:.0f}% / {(1-params['day_night_ratio'])*100:.0f}%"],
        ["Objectif couverture PV", f"{params['pv_coverage_target']*100:.0f}%"],
        ["Ville sélectionnée", params.get('selected_city', 'Paris')],
        ["Irradiation annuelle", f"{params.get('irradiation', 1200)} kWh/m²"],
        ["Technologie batterie", params.get('battery_tech_display', 'Lithium-ion')],
    ]
    
    params_table = Table(params_table_data)
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_PALETTE["primary"])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    content.append(params_table)
    content.append(Spacer(1, 30))
    
    # Résultats des scénarios
    content.append(Paragraph("2. Résultats par Scénario", heading_style))
    
    # Préparation des données pour le tableau
    scenario_headers = ["Scénario", "Prod. PV (kWh)", "Import Réseau (kWh)", 
                       "Autocon. (%)", "Couverture (%)", "Réduct. (%)"]
    
    scenario_rows = [scenario_headers]
    
    for scenario in scenarios_data:
        row = [
            scenario["scenario"],
            f"{scenario.get('pv_production', 0):.0f}",
            f"{scenario.get('grid_import', 0):.0f}",
            f"{scenario.get('self_consumption_rate', 0):.1f}",
            f"{scenario.get('coverage_rate', 0):.1f}",
            f"{scenario.get('grid_reduction', 0):.1f}",
        ]
        scenario_rows.append(row)
    
    scenario_table = Table(scenario_rows)
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_PALETTE["primary"])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    content.append(scenario_table)
    content.append(Spacer(1, 30))
    
    # Recommandations
    content.append(Paragraph("3. Recommandations", heading_style))
    
    if recommendations:
        best_scenario = recommendations["best_scenario"]
        justification = recommendations["justification"]
        
        content.append(Paragraph(f"Scénario recommandé : {best_scenario}", styles['Heading3']))
        content.append(Paragraph("Justification :", styles['Normal']))
        
        for point in justification.split('\n'):
            if point.strip():
                content.append(Paragraph(f"• {point}", styles['Normal']))
    
    # Génération du PDF
    doc.build(content)
    
    buffer.seek(0)
    return buffer

def export_to_excel(scenarios_data, params):
    """Exporte les résultats vers Excel"""
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Feuille 1: Résultats détaillés
        results_df = pd.DataFrame(scenarios_data)
        results_df.to_excel(writer, sheet_name='Résultats', index=False)
        
        # Feuille 2: Paramètres
        params_df = pd.DataFrame([params])
        params_df.to_excel(writer, sheet_name='Paramètres', index=False)
        
        # Feuille 3: Synthèse
        summary_data = []
        for scenario in scenarios_data:
            summary_data.append({
                "Scénario": scenario["scenario"],
                "Production PV (kWh)": scenario.get("pv_production", 0),
                "Import Réseau (kWh)": scenario.get("grid_import", 0),
                "Autoconsommation (%)": scenario.get("self_consumption_rate", 0),
                "Couverture (%)": scenario.get("coverage_rate", 0),
                "Réduction Réseau (%)": scenario.get("grid_reduction", 0),
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Synthèse', index=False)
    
    buffer.seek(0)
    return buffer

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

def main():
    # Header
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, {COLOR_PALETTE["primary"]} 0%, {COLOR_PALETTE["secondary"]} 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🔋 PV+Battery Dimensioning Suite</h1>
        <p style='color: white; opacity: 0.9; margin: 0.5rem 0 0 0;'>Optimisation énergétique intelligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de l'état de session
    if 'params' not in st.session_state:
        st.session_state.params = DEFAULT_PARAMS.copy()
        st.session_state.params['selected_city'] = "Paris"
        st.session_state.params['irradiation'] = CITIES_IRRADIATION["Paris"]
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")
        
        # Onglets dans la sidebar
        tab1, tab2, tab3 = st.tabs(["📊 Consommation", "☀️ PV", "🔋 Batterie"])
        
        with tab1:
            st.session_state.params['annual_consumption'] = st.slider(
                "Consommation annuelle (kWh)",
                min_value=1000,
                max_value=15000,
                value=int(st.session_state.params['annual_consumption']),
                step=500,
                help="Consommation électrique annuelle du logement"
            )
            
            st.session_state.params['day_night_ratio'] = st.slider(
                "Consommation de jour (%)",
                min_value=0,
                max_value=100,
                value=int(st.session_state.params['day_night_ratio'] * 100),
                step=5,
                help="Pourcentage de la consommation qui a lieu en journée"
            ) / 100
            
            # Affichage des calculs
            daily_cons = calculate_daily_consumption(st.session_state.params['annual_consumption'])
            avg_power = calculate_average_power(daily_cons)
            
            st.markdown(f"""
            <div class='custom-card'>
                <h4>📈 Calculs Automatiques</h4>
                <p><strong>Consommation journalière:</strong> {daily_cons:.1f} kWh/j</p>
                <p><strong>Puissance moyenne:</strong> {avg_power:.2f} kW</p>
                <p><strong>Consommation nuit:</strong> {st.session_state.params['annual_consumption'] * (1-st.session_state.params['day_night_ratio']):.0f} kWh/an</p>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            # Sélection de la ville
            selected_city = st.selectbox(
                "Ville",
                options=list(CITIES_IRRADIATION.keys()),
                index=list(CITIES_IRRADIATION.keys()).index(st.session_state.params.get('selected_city', 'Paris'))
            )
            st.session_state.params['selected_city'] = selected_city
            st.session_state.params['irradiation'] = CITIES_IRRADIATION[selected_city]
            
            st.markdown(f"**Irradiation annuelle:** {CITIES_IRRADIATION[selected_city]} kWh/m²")
            
            st.session_state.params['pv_coverage_target'] = st.slider(
                "Objectif couverture PV (%)",
                min_value=0,
                max_value=100,
                value=int(st.session_state.params['pv_coverage_target'] * 100),
                step=5,
                help="Pourcentage de la consommation à couvrir par le PV"
            ) / 100
            
            st.session_state.params['performance_ratio'] = st.slider(
                "Performance Ratio",
                min_value=0.65,
                max_value=0.85,
                value=float(st.session_state.params['performance_ratio']),
                step=0.01,
                help="Efficacité globale du système PV"
            )
            
            st.session_state.params['module_efficiency'] = st.slider(
                "Rendement module (%)",
                min_value=15,
                max_value=22,
                value=int(st.session_state.params['module_efficiency'] * 100),
                step=1,
            ) / 100
        
        with tab3:
            battery_tech = st.radio(
                "Technologie batterie",
                options=["lithium", "lead_acid"],
                format_func=lambda x: "Lithium-ion" if x == "lithium" else "Plomb-acide",
                index=0 if st.session_state.params.get('battery_tech') == "lithium" else 1
            )
            st.session_state.params['battery_tech'] = battery_tech
            st.session_state.params['battery_tech_display'] = "Lithium-ion" if battery_tech == "lithium" else "Plomb-acide"
            
            st.session_state.params['autonomy_hours'] = st.slider(
                "Autonomie souhaitée (heures)",
                min_value=2,
                max_value=24,
                value=int(st.session_state.params['autonomy_hours']),
                step=2,
                help="Autonomie de la batterie pour la consommation nocturne"
            )
            
            # Affichage spécifications batterie
            battery_specs = TECH_SPECS["batteries"][battery_tech]
            st.markdown(f"""
            <div class='custom-card'>
                <h4>🔧 Spécifications {battery_specs['name']}</h4>
                <p><strong>Depth of Discharge:</strong> {battery_specs['dod']*100:.0f}%</p>
                <p><strong>Rendement:</strong> {battery_specs['efficiency']*100:.0f}%</p>
                <p><strong>Durée de vie:</strong> {battery_specs['lifetime_cycles']} cycles</p>
                <p><strong>Coût estimé:</strong> {battery_specs['cost_per_kwh']} €/kWh</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Bouton de simulation
        st.markdown("---")
        if st.button("🚀 Lancer la Simulation", type="primary", use_container_width=True):
            st.session_state['run_simulation'] = True
        else:
            st.session_state['run_simulation'] = False
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{st.session_state.params['annual_consumption']:,}</div>
            <div class='kpi-label'>Consommation annuelle</div>
            <small>kWh/an</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        coverage_kwh = st.session_state.params['annual_consumption'] * st.session_state.params['pv_coverage_target']
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{coverage_kwh:.0f}</div>
            <div class='kpi-label'>Objectif couverture PV</div>
            <small>kWh/an</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-value'>{st.session_state.params['autonomy_hours']}</div>
            <div class='kpi-label'>Autonomie batterie</div>
            <small>heures</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Calculs de dimensionnement
    if 'run_simulation' in st.session_state and st.session_state['run_simulation']:
        
        with st.spinner('Calculs en cours...'):
            time.sleep(0.5)  # Simulation de calcul
            
            # Calculs PV
            pv_power = calculate_pv_power(
                st.session_state.params['annual_consumption'],
                st.session_state.params['pv_coverage_target'],
                st.session_state.params['irradiation'],
                st.session_state.params['performance_ratio'],
                st.session_state.params['module_efficiency'],
                st.session_state.params.get('system_losses', 0.12)
            )
            
            pv_production = calculate_annual_pv_production(
                pv_power,
                st.session_state.params['irradiation'],
                st.session_state.params['performance_ratio'],
                st.session_state.params.get('system_losses', 0.12)
            )
            
            st.session_state.params['pv_power'] = pv_power
            st.session_state.params['pv_production'] = pv_production
            
            # Calculs batterie
            night_consumption = st.session_state.params['annual_consumption'] * (1 - st.session_state.params['day_night_ratio'])
            battery_specs = TECH_SPECS["batteries"][st.session_state.params['battery_tech']]
            
            battery_capacity = calculate_battery_capacity(
                night_consumption / 365,  # Consommation nocturne journalière
                st.session_state.params['autonomy_hours'],
                battery_specs['dod']
            )
            
            st.session_state.params['battery_capacity'] = battery_capacity
            
            # Simulation des scénarios
            scenarios = ["S0", "S1", "S2", "S3", "S4"]
            scenarios_data = []
            
            for scenario in scenarios:
                params_copy = st.session_state.params.copy()
                
                # Pour S2 et S3, on ajuste la technologie batterie
                if scenario == "S2":
                    params_copy['battery_tech'] = "lead_acid"
                    params_copy['battery_tech_display'] = "Plomb-acide"
                elif scenario == "S3":
                    params_copy['battery_tech'] = "lithium"
                    params_copy['battery_tech_display'] = "Lithium-ion"
                
                indicators = calculate_scenario_indicators(
                    scenario, 
                    params_copy, 
                    pv_power, 
                    battery_capacity if scenario in ["S2", "S3", "S4"] else 0
                )
                
                # Ajout des scores multicritères
                score_data = calculate_multicriteria_score(indicators)
                indicators.update(score_data)
                
                scenarios_data.append(indicators)
            
            st.session_state['scenarios_data'] = scenarios_data
            
            # Trouver le meilleur scénario
            best_scenario = max(scenarios_data[1:], key=lambda x: x['score'])  # Exclure S0
            worst_scenario = min(scenarios_data[1:], key=lambda x: x['score'])
            
            # Préparation des recommandations
            recommendations = {
                "best_scenario": best_scenario["scenario"],
                "best_score": best_scenario["score"],
                "worst_scenario": worst_scenario["scenario"],
                "justification": f"""
                Le scénario {best_scenario["scenario"]} obtient le score multicritère le plus élevé ({best_scenario["score"]}/100).
                
                Principaux atouts :
                • Réduction du réseau : {best_scenario.get("grid_reduction", 0):.1f}%
                • Taux d'autoconsommation : {best_scenario.get("self_consumption_rate", 0):.1f}%
                • Couverture énergétique : {best_scenario.get("coverage_rate", 0):.1f}%
                
                Comparé au scénario de référence (S0), il permet de réduire l'import réseau de {best_scenario.get("grid_reduction", 0):.1f}%.
                """
            }
            
            st.session_state['recommendations'] = recommendations
        
        # Affichage des résultats
        st.success("✅ Simulation terminée !")
        
        # Onglets de résultats
        tab_results, tab_analysis, tab_export = st.tabs(["📊 Résultats", "📈 Analyse", "📥 Export"])
        
        with tab_results:
            # Graphique du profil journalier
            st.plotly_chart(create_daily_profile_chart(st.session_state.params), use_container_width=True)
            
            # Tableau des résultats
            st.markdown("### 📋 Tableau Comparatif des Scénarios")
            
            display_df = pd.DataFrame(st.session_state['scenarios_data'])
            display_columns = ["scenario", "pv_production", "grid_import", "energy_stored", 
                             "self_consumption_rate", "coverage_rate", "grid_reduction", "score"]
            
            display_df = display_df[display_columns]
            display_df.columns = ["Scénario", "Prod. PV (kWh)", "Import Réseau (kWh)", 
                                "Énergie Stockée (kWh)", "Autocon. (%)", "Couverture (%)", 
                                "Réduct. (%)", "Score"]
            
            # Formatage
            for col in ["Prod. PV (kWh)", "Import Réseau (kWh)", "Énergie Stockée (kWh)"]:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.0f}")
            
            for col in ["Autocon. (%)", "Couverture (%)", "Réduct. (%)", "Score"]:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Résumé dimensionnement
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class='custom-card'>
                    <h3>☀️ Dimensionnement PV</h3>
                    <p><strong>Puissance nécessaire:</strong> {pv_power:.2f} kWc</p>
                    <p><strong>Puissance installée recommandée:</strong> {np.ceil(pv_power):.0f} kWc</p>
                    <p><strong>Production estimée:</strong> {pv_production:.0f} kWh/an</p>
                    <p><strong>Surface nécessaire:</strong> {pv_power * 6:.0f} m²</p>
                    <p><strong>Nombre de modules (400W):</strong> {int(np.ceil(pv_power / 0.4))}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='custom-card'>
                    <h3>🔋 Dimensionnement Batterie</h3>
                    <p><strong>Technologie:</strong> {st.session_state.params['battery_tech_display']}</p>
                    <p><strong>Capacité nécessaire:</strong> {battery_capacity:.1f} kWh</p>
                    <p><strong>Capacité commerciale:</strong> {np.ceil(battery_capacity):.0f} kWh</p>
                    <p><strong>Énergie utilisable:</strong> {battery_capacity * battery_specs['dod']:.1f} kWh</p>
                    <p><strong>Coût estimé:</strong> {battery_capacity * battery_specs['cost_per_kwh']:.0f} €</p>
                    <p><strong>Autonomie:</strong> {st.session_state.params['autonomy_hours']} heures</p>
                </div>
                """, unsafe_allow_html=True)
        
        with tab_analysis:
            # Graphiques
            st.plotly_chart(create_energy_balance_chart(st.session_state['scenarios_data']), use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_indicators_comparison_chart(st.session_state['scenarios_data']), use_container_width=True)
            
            with col2:
                st.plotly_chart(create_radar_chart(st.session_state['scenarios_data']), use_container_width=True)
            
            # Recommandations détaillées
            st.markdown("### 🏆 Recommandation")
            
            if 'recommendations' in st.session_state:
                rec = st.session_state['recommendations']
                
                st.markdown(f"""
                <div class='custom-card' style='border-left: 6px solid {COLOR_PALETTE["success"]};'>
                    <h3>🎯 Scénario Recommandé : {rec['best_scenario']}</h3>
                    <p><strong>Score multicritère :</strong> {rec['best_score']}/100</p>
                    <p>{rec['justification']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Comparaison détaillée
                st.markdown("#### 📊 Comparaison Détaillée")
                
                best_scenario_data = next(s for s in st.session_state['scenarios_data'] if s['scenario'] == rec['best_scenario'])
                worst_scenario_data = next(s for s in st.session_state['scenarios_data'] if s['scenario'] == rec['worst_scenario'])
                
                comparison_data = {
                    "Indicateur": ["Réduction réseau", "Autoconsommation", "Couverture", "Score multicritère"],
                    rec['best_scenario']: [
                        f"{best_scenario_data.get('grid_reduction', 0):.1f}%",
                        f"{best_scenario_data.get('self_consumption_rate', 0):.1f}%",
                        f"{best_scenario_data.get('coverage_rate', 0):.1f}%",
                        f"{best_scenario_data.get('score', 0):.1f}/100"
                    ],
                    rec['worst_scenario']: [
                        f"{worst_scenario_data.get('grid_reduction', 0):.1f}%",
                        f"{worst_scenario_data.get('self_consumption_rate', 0):.1f}%",
                        f"{worst_scenario_data.get('coverage_rate', 0):.1f}%",
                        f"{worst_scenario_data.get('score', 0):.1f}/100"
                    ]
                }
                
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
        
        with tab_export:
            st.markdown("### 📤 Export des Résultats")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Générer Rapport PDF", use_container_width=True):
                    pdf_buffer = generate_pdf_report(
                        st.session_state.params,
                        st.session_state['scenarios_data'],
                        st.session_state.get('recommendations', {})
                    )
                    
                    st.download_button(
                        label="⬇️ Télécharger PDF",
                        data=pdf_buffer,
                        file_name=f"rapport_pv_batterie_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("📊 Exporter vers Excel", use_container_width=True):
                    excel_buffer = export_to_excel(
                        st.session_state['scenarios_data'],
                        st.session_state.params
                    )
                    
                    st.download_button(
                        label="⬇️ Télécharger Excel",
                        data=excel_buffer,
                        file_name=f"donnees_pv_batterie_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("📋 Exporter Configuration JSON", use_container_width=True):
                    export_data = {
                        "parameters": st.session_state.params,
                        "scenarios": st.session_state['scenarios_data'],
                        "recommendations": st.session_state.get('recommendations', {}),
                        "metadata": {
                            "export_date": datetime.now().isoformat(),
                            "application": "PV+Battery Dimensioning Suite v1.0"
                        }
                    }
                    
                    json_str = json.dumps(export_data, indent=2, default=str)
                    
                    st.download_button(
                        label="⬇️ Télécharger JSON",
                        data=json_str,
                        file_name=f"configuration_pv_batterie_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            # Aperçu des données exportées
            st.markdown("#### 👁️ Aperçu des Données")
            
            with st.expander("Voir les données brutes"):
                st.json(st.session_state.params)
                
                st.markdown("##### Données des scénarios")
                st.dataframe(pd.DataFrame(st.session_state['scenarios_data']), use_container_width=True)
    
    else:
        # Page d'accueil avant simulation
        st.markdown("""
        <div class='custom-card' style='text-align: center; padding: 3rem;'>
            <h2 style='color: #1E3A8A;'>🚀 Bienvenue dans le PV+Battery Dimensioning Suite</h2>
            <p style='font-size: 1.2rem; color: #6B7280; margin: 2rem 0;'>
                Configurez vos paramètres dans la sidebar, puis cliquez sur <strong>"Lancer la Simulation"</strong> pour commencer l'analyse.
            </p>
            
            <div style='display: flex; justify-content: center; gap: 2rem; margin: 2rem 0;'>
                <div style='text-align: center;'>
                    <div style='font-size: 3rem;'>☀️</div>
                    <h4>Dimensionnement PV</h4>
                    <p>Calculez la puissance nécessaire en fonction de votre consommation et localisation</p>
                </div>
                
                <div style='text-align: center;'>
                    <div style='font-size: 3rem;'>🔋</div>
                    <h4>Dimensionnement Batterie</h4>
                    <p>Déterminez la capacité de stockage optimale pour votre autonomie souhaitée</p>
                </div>
                
                <div style='text-align: center;'>
                    <div style='font-size: 3rem;'>📊</div>
                    <h4>Analyse Multicritère</h4>
                    <p>Comparez 5 scénarios et obtenez des recommandations personnalisées</p>
                </div>
            </div>
            
            <div style='margin-top: 3rem;'>
                <h4>🎯 Scénarios Simulés</h4>
                <div style='display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;'>
                    <span class='scenario-badge s0'>S0: Réseau seul</span>
                    <span class='scenario-badge s1'>S1: PV seul</span>
                    <span class='scenario-badge s2'>S2: PV + Pb-acide</span>
                    <span class='scenario-badge s3'>S3: PV + Li-ion</span>
                    <span class='scenario-badge s4'>S4: Optimisé</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Graphique d'exemple
        st.plotly_chart(create_daily_profile_chart(DEFAULT_PARAMS), use_container_width=True)

if __name__ == "__main__":
    main()