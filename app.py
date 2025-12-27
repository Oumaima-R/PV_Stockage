# app.py - Version corrigée pour le Maroc
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
import sys
import os

# ============================================================================
# CONFIGURATION INITIALE
# ============================================================================
st.set_page_config(
    page_title="PV+Battery Dimensioning Suite - Maroc",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger la configuration Maroc
try:
    from config import COLOR_PALETTE, DEFAULT_PARAMS, TECH_SPECS, CITIES_IRRADIATION
    print("✅ Configuration Maroc chargée")
except ImportError as e:
    st.error(f"❌ Erreur de configuration: {e}")
    st.stop()

# ============================================================================
# CSS PERSONNALISÉ POUR MAROC
# ============================================================================
def load_css():
    css = """
    <style>
    :root {
        --primary-red: #C1272D;
        --primary-green: #006233;
        --gold-accent: #F7DC6F;
        --earth-brown: #5D4037;
        --sand-yellow: #FEF9E7;
        --night-blue: #2C3E50;
    }
    
    .stApp {
        background: var(--sand-yellow);
    }
    
    .morocco-header {
        background: linear-gradient(90deg, var(--primary-red) 0%, var(--primary-green) 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .morocco-header h1 {
        color: white;
        margin: 0;
    }
    
    .morocco-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
    }
    
    .kpi-card {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        border-left: 4px solid var(--primary-green);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--primary-red);
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: var(--earth-brown);
        text-transform: uppercase;
    }
    
    .scenario-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .s0 { background-color: #94A3B8; }
    .s1 { background-color: #F59E0B; }
    .s2 { background-color: #3B82F6; }
    .s3 { background-color: #10B981; }
    .s4 { background-color: #8B5CF6; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# ============================================================================
# FONCTIONS DE CALCUL (MÊMES QUE PRÉCÉDENT)
# ============================================================================
def calculate_daily_consumption(annual_consumption):
    return annual_consumption / 365

def calculate_average_power(daily_consumption):
    return daily_consumption / 24

def calculate_pv_power(annual_consumption, coverage_target, irradiation, 
                      performance_ratio, module_efficiency, system_losses):
    energy_needed = annual_consumption * coverage_target
    system_efficiency = performance_ratio * module_efficiency * (1 - system_losses)
    pv_power_kwp = energy_needed / (irradiation * system_efficiency)
    return pv_power_kwp

def calculate_annual_pv_production(pv_power_kwp, irradiation, 
                                 performance_ratio, system_losses):
    return pv_power_kwp * irradiation * performance_ratio * (1 - system_losses)

def calculate_battery_capacity(night_consumption, autonomy_hours, dod):
    usable_capacity = night_consumption * (autonomy_hours / 24)
    nominal_capacity = usable_capacity / dod
    return nominal_capacity

def calculate_scenario_indicators(scenario_name, params, pv_power, battery_capacity):
    annual_consumption = params["annual_consumption"]
    day_night_ratio = params["day_night_ratio"]
    pv_production = params.get("pv_production", 0)
    battery_tech = params.get("battery_tech")
    
    day_consumption = annual_consumption * day_night_ratio
    night_consumption = annual_consumption * (1 - day_night_ratio)
    
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
    
    if scenario_name == "S0":
        indicators["grid_import"] = annual_consumption
        indicators["coverage_rate"] = 0
        indicators["grid_reduction"] = 0
    
    elif scenario_name == "S1":
        pv_prod = pv_production
        direct_use = min(pv_prod, day_consumption)
        surplus = pv_prod - direct_use
        
        indicators["pv_production"] = pv_prod
        indicators["grid_import"] = annual_consumption - direct_use
        indicators["grid_export"] = surplus * 0.8
        indicators["energy_losses"] = surplus * 0.2
        
        if pv_prod > 0:
            indicators["self_consumption_rate"] = (direct_use / pv_prod) * 100
            indicators["coverage_rate"] = (direct_use / annual_consumption) * 100
            indicators["grid_reduction"] = ((annual_consumption - indicators["grid_import"]) / annual_consumption) * 100
    
    elif scenario_name in ["S2", "S3"]:
        pv_prod = pv_production
        battery_specs = TECH_SPECS["batteries"][battery_tech]
        
        direct_use = min(pv_prod, day_consumption)
        surplus = pv_prod - direct_use
        
        battery_efficiency = battery_specs["efficiency"]
        max_storage = battery_capacity * battery_specs["dod"] if battery_capacity > 0 else 0
        
        energy_to_store = min(surplus, max_storage)
        energy_stored = energy_to_store * battery_efficiency
        energy_discharged = min(energy_stored, night_consumption) * battery_efficiency
        
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
    
    elif scenario_name == "S4":
        s2_params = params.copy()
        s2_params['battery_tech'] = 'lead_acid'
        s2_indicators = calculate_scenario_indicators("S2", s2_params, pv_power, battery_capacity)
        
        s3_params = params.copy()
        s3_params['battery_tech'] = 'lithium'
        s3_indicators = calculate_scenario_indicators("S3", s3_params, pv_power, battery_capacity)
        
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
    weights = {
        "grid_reduction": 0.40,
        "self_consumption_rate": 0.30,
        "coverage_rate": 0.20,
        "cost_efficiency": 0.10
    }
    
    normalized = {}
    
    for key in ["grid_reduction", "self_consumption_rate", "coverage_rate"]:
        value = indicators.get(key, 0)
        normalized[key] = min(max(value, 0), 100)
    
    pv_cost = indicators.get("pv_power", 0) * 7000  # MAD/kWc pour Maroc
    battery_cost = indicators.get("battery_capacity", 0) * 3000  # MAD/kWh moyen
    total_cost = pv_cost + battery_cost
    
    max_cost = 50000  # Coût maximum de référence pour Maroc
    normalized["cost_efficiency"] = max(0, 100 - (total_cost / max_cost * 100))
    
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
    scenarios = [s["scenario"] for s in scenarios_data]
    
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
        height=500
    )
    
    return fig

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    # Header Maroc
    st.markdown(f"""
    <div class='morocco-header'>
        <h1>🔋 PV+Battery Dimensioning Suite - Maroc 🇲🇦</h1>
        <p>Optimisation énergétique intelligente pour le contexte marocain</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de session avec valeurs Maroc par défaut
    if 'params' not in st.session_state:
        st.session_state.params = DEFAULT_PARAMS.copy()
        
        # CORRECTION ICI : Utiliser une ville marocaine par défaut
        default_city = "Marrakech"  # Ville par défaut pour le Maroc
        if default_city in CITIES_IRRADIATION:
            st.session_state.params['selected_city'] = default_city
            st.session_state.params['irradiation'] = CITIES_IRRADIATION[default_city]["irradiation"]
        else:
            # Prendre la première ville disponible
            first_city = list(CITIES_IRRADIATION.keys())[0]
            st.session_state.params['selected_city'] = first_city
            st.session_state.params['irradiation'] = CITIES_IRRADIATION[first_city]["irradiation"]
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres - Maroc")
        
        tab1, tab2, tab3 = st.tabs(["📊 Consommation", "☀️ PV", "🔋 Batterie"])
        
        with tab1:
            st.session_state.params['annual_consumption'] = st.slider(
                "Consommation annuelle (kWh)",
                min_value=1000,
                max_value=15000,
                value=int(st.session_state.params['annual_consumption']),
                step=500,
                help="Consommation électrique annuelle typique au Maroc: 4000-8000 kWh"
            )
            
            st.session_state.params['day_night_ratio'] = st.slider(
                "Consommation de jour (%)",
                min_value=0,
                max_value=100,
                value=int(st.session_state.params['day_night_ratio'] * 100),
                step=5,
                help="Pourcentage de la consommation qui a lieu en journée (60-70% typique)"
            ) / 100
            
            daily_cons = calculate_daily_consumption(st.session_state.params['annual_consumption'])
            avg_power = calculate_average_power(daily_cons)
            
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid {COLOR_PALETTE["primary"]};'>
                <h4 style='margin-top: 0;'>📈 Calculs Automatiques</h4>
                <p><strong>Consommation journalière:</strong> {daily_cons:.1f} kWh/j</p>
                <p><strong>Puissance moyenne:</strong> {avg_power:.2f} kW</p>
                <p><strong>Consommation nuit:</strong> {st.session_state.params['annual_consumption'] * (1-st.session_state.params['day_night_ratio']):.0f} kWh/an</p>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            # CORRECTION ICI : Gestion sécurisée de l'index
            city_keys = list(CITIES_IRRADIATION.keys())
            current_city = st.session_state.params.get('selected_city', city_keys[0])
            
            # Trouver l'index de la ville actuelle
            try:
                current_index = city_keys.index(current_city)
            except ValueError:
                current_index = 0  # Fallback au premier index
            
            selected_city = st.selectbox(
                "Ville marocaine",
                options=city_keys,
                index=current_index,
                help="Sélectionnez votre ville pour l'irradiation solaire"
            )
            
            st.session_state.params['selected_city'] = selected_city
            st.session_state.params['irradiation'] = CITIES_IRRADIATION[selected_city]["irradiation"]
            
            # Afficher les informations de la ville
            city_info = CITIES_IRRADIATION[selected_city]
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                <p><strong>📍 {selected_city}</strong></p>
                <p><strong>Irradiation:</strong> {city_info['irradiation']} kWh/m²</p>
                <p><strong>Région:</strong> {city_info['region']}</p>
                <p><strong>Climat:</strong> {city_info['climate']}</p>
                <p><strong>Heures soleil:</strong> {city_info['sun_hours']} h/an</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.params['pv_coverage_target'] = st.slider(
                "Objectif couverture PV (%)",
                min_value=0,
                max_value=100,
                value=int(st.session_state.params['pv_coverage_target'] * 100),
                step=5,
                help="Pourcentage de la consommation à couvrir par le PV (60-80% recommandé)"
            ) / 100
            
            st.session_state.params['performance_ratio'] = st.slider(
                "Performance Ratio",
                min_value=0.65,
                max_value=0.85,
                value=float(st.session_state.params['performance_ratio']),
                step=0.01,
                help="Efficacité globale du système PV (0.75-0.80 pour Maroc)"
            )
            
            st.session_state.params['module_efficiency'] = st.slider(
                "Rendement module (%)",
                min_value=15,
                max_value=22,
                value=int(st.session_state.params['module_efficiency'] * 100),
                step=1,
                help="Rendement des panneaux PV (18-20% pour monocristallin)"
            ) / 100
        
        with tab3:
            battery_tech_options = {
                "lithium": "Lithium-ion",
                "lead_acid": "Plomb-acide"
            }
            
            current_tech = st.session_state.params.get('battery_tech', 'lithium')
            battery_tech = st.radio(
                "Technologie batterie",
                options=list(battery_tech_options.keys()),
                format_func=lambda x: battery_tech_options[x],
                index=0 if current_tech == "lithium" else 1,
                help="Lithium-ion: meilleure durée de vie. Plomb-acide: plus économique"
            )
            
            st.session_state.params['battery_tech'] = battery_tech
            st.session_state.params['battery_tech_display'] = battery_tech_options[battery_tech]
            
            st.session_state.params['autonomy_hours'] = st.slider(
                "Autonomie souhaitée (heures)",
                min_value=2,
                max_value=24,
                value=int(st.session_state.params['autonomy_hours']),
                step=2,
                help="Autonomie de la batterie pour la consommation nocturne (6-12h recommandé)"
            )
            
            battery_specs = TECH_SPECS["batteries"][battery_tech]
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px;'>
                <h4 style='margin-top: 0;'>🔧 Spécifications {battery_specs['name']}</h4>
                <p><strong>Depth of Discharge:</strong> {battery_specs['dod']*100:.0f}%</p>
                <p><strong>Rendement:</strong> {battery_specs['efficiency']*100:.0f}%</p>
                <p><strong>Durée de vie:</strong> {battery_specs['lifetime_cycles']} cycles</p>
                <p><strong>Coût estimé:</strong> {battery_specs['cost_per_kwh']:,} MAD/kWh</p>
                <p><strong>Température:</strong> {battery_specs['temperature_range']}</p>
            </div>
            """, unsafe_allow_html=True)
        
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
    
    # Simulation
    if 'run_simulation' in st.session_state and st.session_state['run_simulation']:
        with st.spinner('Calculs en cours...'):
            time.sleep(0.5)
            
            # Calculs PV
            pv_power = calculate_pv_power(
                st.session_state.params['annual_consumption'],
                st.session_state.params['pv_coverage_target'],
                st.session_state.params['irradiation'],
                st.session_state.params['performance_ratio'],
                st.session_state.params['module_efficiency'],
                0.12  # Pertes système par défaut
            )
            
            pv_production = calculate_annual_pv_production(
                pv_power,
                st.session_state.params['irradiation'],
                st.session_state.params['performance_ratio'],
                0.12
            )
            
            st.session_state.params['pv_power'] = pv_power
            st.session_state.params['pv_production'] = pv_production
            
            # Calculs batterie
            night_consumption = st.session_state.params['annual_consumption'] * (1 - st.session_state.params['day_night_ratio'])
            battery_specs = TECH_SPECS["batteries"][st.session_state.params['battery_tech']]
            
            battery_capacity = calculate_battery_capacity(
                night_consumption / 365,
                st.session_state.params['autonomy_hours'],
                battery_specs['dod']
            )
            
            st.session_state.params['battery_capacity'] = battery_capacity
            
            # Simulation des scénarios
            scenarios = ["S0", "S1", "S2", "S3", "S4"]
            scenarios_data = []
            
            for scenario in scenarios:
                params_copy = st.session_state.params.copy()
                
                if scenario == "S2":
                    params_copy['battery_tech'] = "lead_acid"
                    params_copy['battery_tech_display'] = "Plomb-acide"
                elif scenario == "S3":
                    params_copy['battery_tech'] = "lithium"
                    params_copy['battery_tech_display'] = "Lithium-ion"
                elif scenario == "S4":
                    # Pour S4, on garde la technologie par défaut pour le calcul initial
                    pass
                
                indicators = calculate_scenario_indicators(
                    scenario, 
                    params_copy, 
                    pv_power, 
                    battery_capacity if scenario in ["S2", "S3", "S4"] else 0
                )
                
                score_data = calculate_multicriteria_score(indicators)
                indicators.update(score_data)
                
                scenarios_data.append(indicators)
            
            st.session_state['scenarios_data'] = scenarios_data
            
            # Trouver le meilleur scénario
            best_scenario = max(scenarios_data[1:], key=lambda x: x['score'])
            worst_scenario = min(scenarios_data[1:], key=lambda x: x['score'])
            
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
                <div style='background: white; padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd;'>
                    <h3 style='color: {COLOR_PALETTE["primary"]};'>☀️ Dimensionnement PV</h3>
                    <p><strong>Puissance nécessaire:</strong> {pv_power:.2f} kWc</p>
                    <p><strong>Puissance installée recommandée:</strong> {np.ceil(pv_power):.0f} kWc</p>
                    <p><strong>Production estimée:</strong> {pv_production:.0f} kWh/an</p>
                    <p><strong>Surface nécessaire:</strong> {pv_power * 6:.0f} m²</p>
                    <p><strong>Nombre de modules (400W):</strong> {int(np.ceil(pv_power / 0.4))}</p>
                    <p><strong>Coût estimé:</strong> {pv_power * 7000:.0f} MAD</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style='background: white; padding: 1.5rem; border-radius: 10px; border: 1px solid #ddd;'>
                    <h3 style='color: {COLOR_PALETTE["primary"]};'>🔋 Dimensionnement Batterie</h3>
                    <p><strong>Technologie:</strong> {st.session_state.params['battery_tech_display']}</p>
                    <p><strong>Capacité nécessaire:</strong> {battery_capacity:.1f} kWh</p>
                    <p><strong>Capacité commerciale:</strong> {np.ceil(battery_capacity):.0f} kWh</p>
                    <p><strong>Énergie utilisable:</strong> {battery_capacity * battery_specs['dod']:.1f} kWh</p>
                    <p><strong>Coût estimé:</strong> {battery_capacity * battery_specs['cost_per_kwh']:.0f} MAD</p>
                    <p><strong>Autonomie:</strong> {st.session_state.params['autonomy_hours']} heures</p>
                    <p><strong>Durée de vie:</strong> {battery_specs['replacement_years']} ans</p>
                </div>
                """, unsafe_allow_html=True)
        
        with tab_analysis:
            # Graphiques
            st.plotly_chart(create_energy_balance_chart(st.session_state['scenarios_data']), 
                          use_container_width=True)
            
            # Recommandations
            if 'recommendations' in st.session_state:
                rec = st.session_state['recommendations']
                
                st.markdown(f"""
                <div style='background: #E8F5E9; padding: 1.5rem; border-radius: 10px; border-left: 6px solid {COLOR_PALETTE["success"]};'>
                    <h3 style='color: {COLOR_PALETTE["primary"]}; margin-top: 0;'>🎯 Scénario Recommandé : {rec['best_scenario']}</h3>
                    <p><strong>Score multicritère :</strong> {rec['best_score']}/100</p>
                    <p style='white-space: pre-line;'>{rec['justification']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with tab_export:
            st.markdown("### 📤 Export des Résultats")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Générer Résumé", use_container_width=True):
                    # Création d'un résumé simple
                    summary = f"""
                    RAPPORT DE SIMULATION - PV+Battery Suite Maroc
                    ===============================================
                    
                    Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    Ville: {st.session_state.params['selected_city']}
                    
                    PARAMÈTRES
                    ----------
                    Consommation annuelle: {st.session_state.params['annual_consumption']} kWh
                    Objectif couverture PV: {st.session_state.params['pv_coverage_target']*100:.0f}%
                    Technologie batterie: {st.session_state.params['battery_tech_display']}
                    Autonomie: {st.session_state.params['autonomy_hours']} heures
                    
                    RÉSULTATS
                    ---------
                    Puissance PV nécessaire: {pv_power:.2f} kWc
                    Production PV estimée: {pv_production:.0f} kWh/an
                    Capacité batterie: {battery_capacity:.1f} kWh
                    
                    SCÉNARIO RECOMMANDÉ
                    -------------------
                    {rec['best_scenario']} (Score: {rec['best_score']}/100)
                    """
                    
                    st.download_button(
                        label="⬇️ Télécharger Résumé (TXT)",
                        data=summary,
                        file_name=f"resume_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("📊 Exporter Données JSON", use_container_width=True):
                    export_data = {
                        "parameters": st.session_state.params,
                        "scenarios": st.session_state['scenarios_data'],
                        "recommendations": st.session_state.get('recommendations', {}),
                        "metadata": {
                            "export_date": datetime.now().isoformat(),
                            "application": "PV+Battery Dimensioning Suite Maroc v1.0"
                        }
                    }
                    
                    json_str = json.dumps(export_data, indent=2, default=str)
                    
                    st.download_button(
                        label="⬇️ Télécharger JSON",
                        data=json_str,
                        file_name=f"donnees_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
    
    else:
        # Page d'accueil avant simulation
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h2 style='color: #C1272D;'>🚀 Bienvenue dans PV+Battery Dimensioning Suite - Maroc</h2>
            <p style='font-size: 1.2rem; color: #5D4037; margin: 2rem 0;'>
                Configurez vos paramètres dans la sidebar, puis cliquez sur <strong>"Lancer la Simulation"</strong> pour commencer l'analyse.
            </p>
            
            <div style='display: flex; justify-content: center; gap: 2rem; margin: 2rem 0; flex-wrap: wrap;'>
                <div style='text-align: center; max-width: 200px;'>
                    <div style='font-size: 3rem;'>☀️</div>
                    <h4>Dimensionnement PV</h4>
                    <p>Calculez la puissance nécessaire en fonction de votre localisation au Maroc</p>
                </div>
                
                <div style='text-align: center; max-width: 200px;'>
                    <div style='font-size: 3rem;'>🔋</div>
                    <h4>Dimensionnement Batterie</h4>
                    <p>Déterminez la capacité de stockage optimale pour votre autonomie souhaitée</p>
                </div>
                
                <div style='text-align: center; max-width: 200px;'>
                    <div style='font-size: 3rem;'>📊</div>
                    <h4>Analyse Multicritère</h4>
                    <p>Comparez 5 scénarios et obtenez des recommandations personnalisées</p>
                </div>
            </div>
            
            <div style='margin-top: 3rem;'>
                <h4>🎯 Scénarios Simulés</h4>
                <div style='display: flex; justify-content: center; gap: 1rem; margin: 1rem 0; flex-wrap: wrap;'>
                    <span class='scenario-badge s0'>S0: Réseau seul</span>
                    <span class='scenario-badge s1'>S1: PV seul</span>
                    <span class='scenario-badge s2'>S2: PV + Pb-acide</span>
                    <span class='scenario-badge s3'>S3: PV + Li-ion</span>
                    <span class='scenario-badge s4'>S4: Optimisé</span>
                </div>
            </div>
            
            <div style='margin-top: 3rem; padding: 1.5rem; background: #F0F7FF; border-radius: 8px;'>
                <h4>🏜️ Spécifique au Maroc</h4>
                <p>Données d'irradiation pour 15 villes marocaines, tarifs ONEE, subventions gouvernementales</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Une erreur est survenue: {str(e)}")
        st.info("💡 Vérifiez que tous les fichiers de configuration sont présents.")
        
        # Affichage d'information de débogage (seulement en développement)
        if os.getenv('ENVIRONMENT') == 'development':
            with st.expander("Informations de débogage"):
                st.write("Erreur détaillée:", str(e))
                st.write("Villes disponibles:", list(CITIES_IRRADIATION.keys())[:5])
