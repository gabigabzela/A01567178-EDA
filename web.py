import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Robos - Chihuahua",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('robos_tot_final.csv')
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    return df

df = load_data()

# Sidebar - Filtros
st.sidebar.title("🔍 Filtros")
st.sidebar.markdown("---")

# Página principal
page = st.sidebar.radio(
    "Selecciona una vista:",
    ["📈 Dashboard Principal", "🔍 Análisis por Tipo", "🗺️ Mapa", "🔮 Predicciones"]
)

st.sidebar.markdown("---")

tipos_robo = st.sidebar.multiselect(
    "Tipo de Robo",
    options=sorted(df['TIPO'].unique()),
    default=sorted(df['TIPO'].unique())
)

años = st.sidebar.slider(
    "Rango de Años",
    min_value=int(df['AÑO'].min()),
    max_value=int(df['AÑO'].max()),
    value=(int(df['AÑO'].min()), int(df['AÑO'].max()))
)

# Filtrar datos
df_filtrado = df[
    (df['TIPO'].isin(tipos_robo)) &
    (df['AÑO'] >= años[0]) &
    (df['AÑO'] <= años[1])
]

# Cargar archivos de predicciones
@st.cache_data
def load_prediction_data():
    import json
    
    pred_data = {}
    metricas = {}
    
    try:
        pred_data['negocio'] = pd.read_csv('exportados/Robos a negocios/top_10_prediccion_robos_negocios_enero.csv')
    except:
        pred_data['negocio'] = None
    
    try:
        pred_data['vehiculo'] = pd.read_csv('exportados/Robos de vehiculos/top_10_prediccion_robos_vehiculos_enero.csv')
    except:
        pred_data['vehiculo'] = None
    
    try:
        pred_data['casa'] = pd.read_csv('exportados/Robos a casa habitacion/top_10_prediccion_robos_casa_habitacion_enero.csv')
    except:
        pred_data['casa'] = None
    
    try:
        with open('metricas_modelos.json', 'r') as f:
            metricas = json.load(f)
    except:
        metricas = {}
    
    return pred_data, metricas

# Función para obtener coordenadas de cuadrantes
@st.cache_data
def get_cuadrante_coords():
    """Obtiene las coordenadas promedio de cada cuadrante del dataset"""
    df_full = load_data()
    coords = df_full.groupby('CUADRANTE')[['LATITUD', 'LONGITUD']].mean().reset_index()
    return coords

pred_data, metricas_modelos = load_prediction_data()
cuadrante_coords = get_cuadrante_coords()

# ==================== PÁGINA PRINCIPAL ====================
if page == "📈 Dashboard Principal":
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>📊 Dashboard de Robos en Chihuahua</h1>
            <p>Análisis integral de delitos por robo (2015-2024)</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Período:** {años[0]} - {años[1]} | **Registros analizados:** {len(df_filtrado):,}")
    st.divider()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🔴 Total de Robos",
            f"{len(df_filtrado):,}"
        )
    
    with col2:
        robos_violentos = len(df_filtrado[df_filtrado['VIOLENCIA'] == 'SI'])
        porcentaje = (robos_violentos / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.metric(
            "⚠️ Robos Violentos",
            f"{robos_violentos:,}",
            f"{porcentaje:.1f}%"
        )
    
    with col3:
        distritos = df_filtrado['DISTRITO'].nunique()
        st.metric(
            "📍 Distritos Afectados",
            distritos
        )
    
    with col4:
        cuadrantes = df_filtrado['CUADRANTE'].nunique()
        st.metric(
            "📌 Cuadrantes",
            cuadrantes
        )
    
    st.divider()
    
    # Row 1: Gráficos principales
    st.subheader("📊 Visión General")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Robos por Tipo")
        tipo_counts = df_filtrado['TIPO'].value_counts()
        fig_tipo = px.bar(
            x=tipo_counts.values,
            y=tipo_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Tipo de Robo'},
            color=tipo_counts.values,
            color_continuous_scale='Viridis'
        )
        fig_tipo.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    with col2:
        st.markdown("### ⚠️ Distribución de Violencia")
        violencia_counts = df_filtrado['VIOLENCIA'].value_counts()
        colors_violencia = ['#FF6B6B' if x == 'SI' else '#4ECDC4' for x in violencia_counts.index]
        fig_violencia = px.pie(
            values=violencia_counts.values,
            names=violencia_counts.index,
            color_discrete_sequence=colors_violencia
        )
        fig_violencia.update_traces(labels=['Con Violencia' if x == 'SI' else 'Sin Violencia' 
                                             for x in violencia_counts.index])
        fig_violencia.update_layout(height=400)
        st.plotly_chart(fig_violencia, use_container_width=True)
    
    st.divider()
    
    # Row 2: Tendencias temporales
    st.subheader("📅 Análisis Temporal")
    robos_por_año = df_filtrado.groupby('AÑO').size()
    robos_por_mes = df_filtrado.groupby('MES').size()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_año = px.line(
            x=robos_por_año.index,
            y=robos_por_año.values,
            markers=True,
            labels={'x': 'Año', 'y': 'Cantidad de Robos'},
            title="Evolución Anual"
        )
        fig_año.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_año, use_container_width=True)
    
    with col2:
        fig_mes = px.bar(
            x=robos_por_mes.index,
            y=robos_por_mes.values,
            labels={'x': 'Mes', 'y': 'Cantidad de Robos'},
            title="Distribución Mensual (Promedio Histórico)",
            color=robos_por_mes.values,
            color_continuous_scale='Viridis'
        )
        fig_mes.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_mes, use_container_width=True)
    
    st.divider()
    
    # Row 3: Distribución geográfica
    st.subheader("🗺️ Análisis Geográfico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Top 10 Distritos")
        distritos_counts = df_filtrado['DISTRITO'].value_counts().head(10)
        fig_distritos = px.bar(
            x=distritos_counts.values,
            y=distritos_counts.index,
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Distrito'},
            color=distritos_counts.values,
            color_continuous_scale='Blues'
        )
        fig_distritos.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_distritos, use_container_width=True)
    
    with col2:
        st.markdown("### Top 10 Cuadrantes")
        cuadrantes_counts = df_filtrado['CUADRANTE'].value_counts().head(10)
        fig_cuadrantes = px.bar(
            x=cuadrantes_counts.values,
            y=cuadrantes_counts.index.astype(str),
            orientation='h',
            labels={'x': 'Cantidad', 'y': 'Cuadrante'},
            color=cuadrantes_counts.values,
            color_continuous_scale='Reds'
        )
        fig_cuadrantes.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_cuadrantes, use_container_width=True)
    
    st.divider()
    
    # Row 4: Estadísticas adicionales
    st.subheader("📊 Estadísticas Clave")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estacion_counts = df_filtrado['ESTACION'].value_counts()
        fig_estacion = px.pie(
            values=estacion_counts.values,
            names=estacion_counts.index,
            title="Robos por Estación"
        )
        fig_estacion.update_layout(height=350)
        st.plotly_chart(fig_estacion, use_container_width=True)
    
    with col2:
        # Año con mayor incidencia
        año_max = df_filtrado.groupby('AÑO').size().idxmax()
        robos_año_max = df_filtrado.groupby('AÑO').size().max()
        st.info(f"**Año con mayor incidencia:** {int(año_max)} con {robos_año_max:,} robos")
        
        # Mes con mayor incidencia
        mes_max = df_filtrado.groupby('MES').size().idxmax()
        robos_mes_max = df_filtrado.groupby('MES').size().max()
        st.success(f"**Mes más peligroso:** Mes {int(mes_max)} con {robos_mes_max:,} robos")
        
        # Distrito más afectado
        distrito_max = df_filtrado['DISTRITO'].value_counts().index[0]
        robos_distrito_max = df_filtrado['DISTRITO'].value_counts().max()
        st.warning(f"**Distrito más afectado:** {distrito_max} con {robos_distrito_max:,} robos")
    
    with col3:
        # Tasa de violencia por tipo
        st.markdown("#### Tasa de Violencia por Tipo")
        for tipo in tipos_robo:
            df_tipo = df_filtrado[df_filtrado['TIPO'] == tipo]
            if len(df_tipo) > 0:
                tasa_violencia = (len(df_tipo[df_tipo['VIOLENCIA'] == 'SI']) / len(df_tipo) * 100)
                st.metric(tipo.replace('ROBO ', ''), f"{tasa_violencia:.1f}%")

# ==================== PÁGINA ANÁLISIS POR TIPO ====================
elif page == "🔍 Análisis por Tipo":
    st.title("🔍 Análisis Detallado por Tipo de Robo")
    st.markdown(f"**Período:** {años[0]} - {años[1]} | **Registros:** {len(df_filtrado):,}")
    st.divider()
    
    # Crear tabs dinámicamente
    tabs = st.tabs([f"🔍 {tipo}" for tipo in tipos_robo])
    
    for idx, tipo in enumerate(tipos_robo):
        with tabs[idx]:
            df_tipo = df_filtrado[df_filtrado['TIPO'] == tipo]
            
            if len(df_tipo) > 0:
                # Métricas principales del tipo de robo
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total",
                        f"{len(df_tipo):,}"
                    )
                
                with col2:
                    violentos = len(df_tipo[df_tipo['VIOLENCIA'] == 'SI'])
                    pct = (violentos / len(df_tipo) * 100) if len(df_tipo) > 0 else 0
                    st.metric(
                        "Violentos",
                        f"{violentos:,}",
                        f"{pct:.1f}%"
                    )
                
                with col3:
                    top_distrito = df_tipo['DISTRITO'].value_counts().index[0] if len(df_tipo) > 0 else 'N/A'
                    st.metric(
                        "Distrito Top",
                        top_distrito
                    )
                
                with col4:
                    año_pico = df_tipo.groupby('AÑO').size().idxmax() if len(df_tipo) > 0 else 'N/A'
                    st.metric(
                        "Año Pico",
                        int(año_pico)
                    )
                
                st.divider()
                
                # Gráficos para este tipo de robo
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Tendencia por Año")
                    robos_año_tipo = df_tipo.groupby('AÑO').size()
                    fig_año_tipo = px.line(
                        x=robos_año_tipo.index,
                        y=robos_año_tipo.values,
                        markers=True,
                        labels={'x': 'Año', 'y': 'Cantidad'},
                    )
                    fig_año_tipo.update_layout(height=350, template='plotly_white')
                    st.plotly_chart(fig_año_tipo, use_container_width=True)
                
                with col2:
                    st.subheader("Distribución por Mes")
                    robos_mes_tipo = df_tipo.groupby('MES').size()
                    fig_mes_tipo = px.bar(
                        x=robos_mes_tipo.index,
                        y=robos_mes_tipo.values,
                        labels={'x': 'Mes', 'y': 'Cantidad'},
                        color=robos_mes_tipo.values,
                        color_continuous_scale='Viridis'
                    )
                    fig_mes_tipo.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_mes_tipo, use_container_width=True)
                
                st.divider()
                
                # Top distritos y cuadrantes
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Top 10 Distritos")
                    distritos_tipo = df_tipo['DISTRITO'].value_counts().head(10)
                    fig_dist_tipo = px.bar(
                        x=distritos_tipo.values,
                        y=distritos_tipo.index,
                        orientation='h',
                        labels={'x': 'Cantidad', 'y': 'Distrito'},
                        color=distritos_tipo.values,
                        color_continuous_scale='Blues'
                    )
                    fig_dist_tipo.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_dist_tipo, use_container_width=True)
                
                with col2:
                    st.subheader("Top 10 Cuadrantes")
                    cuadrantes_tipo = df_tipo['CUADRANTE'].value_counts().head(10)
                    fig_cuad_tipo = px.bar(
                        x=cuadrantes_tipo.values,
                        y=cuadrantes_tipo.index.astype(str),
                        orientation='h',
                        labels={'x': 'Cantidad', 'y': 'Cuadrante'},
                        color=cuadrantes_tipo.values,
                        color_continuous_scale='Reds'
                    )
                    fig_cuad_tipo.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_cuad_tipo, use_container_width=True)
                
                st.divider()
                
                # Violencia y estaciones
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Violencia en Robos")
                    violencia_tipo = df_tipo['VIOLENCIA'].value_counts()
                    colors_vio = ['#FF6B6B' if x == 'SI' else '#4ECDC4' for x in violencia_tipo.index]
                    fig_vio_tipo = px.pie(
                        values=violencia_tipo.values,
                        names=violencia_tipo.index,
                        color_discrete_sequence=colors_vio
                    )
                    fig_vio_tipo.update_traces(labels=['Con Violencia' if x == 'SI' else 'Sin Violencia' 
                                                        for x in violencia_tipo.index])
                    fig_vio_tipo.update_layout(height=350)
                    st.plotly_chart(fig_vio_tipo, use_container_width=True)
                
                with col2:
                    st.subheader("Distribución por Estación")
                    estacion_tipo = df_tipo['ESTACION'].value_counts()
                    fig_estacion = px.bar(
                        x=estacion_tipo.index,
                        y=estacion_tipo.values,
                        labels={'x': 'Estación', 'y': 'Cantidad'},
                        color=estacion_tipo.values,
                        color_continuous_scale='Plasma'
                    )
                    fig_estacion.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_estacion, use_container_width=True)
            else:
                st.info(f"No hay datos disponibles para {tipo} en el rango seleccionado.")

# ==================== PÁGINA MAPA ====================
elif page == "🗺️ Mapa":
    st.title("🗺️ Visualización Geográfica de Robos")
    st.markdown(f"**Período:** {años[0]} - {años[1]}")
    st.divider()
    
    if len(df_filtrado[df_filtrado['LATITUD'].notna() & df_filtrado['LONGITUD'].notna()]) > 0:
        # Preparar datos para el mapa
        df_mapa = df_filtrado[df_filtrado['LATITUD'].notna() & df_filtrado['LONGITUD'].notna()].copy()
        
        st.subheader(f"📍 Total de puntos en el mapa: {len(df_mapa):,}")
        
        # Crear mapa con colores por distrito
        fig_scatter = px.scatter_mapbox(
            df_mapa,
            lat='LATITUD',
            lon='LONGITUD',
            color='DISTRITO',
            hover_data=['TIPO', 'VIOLENCIA', 'FECHA', 'DISTRITO'],
            zoom=10,
            height=700,
            title="Ubicación de Robos en Chihuahua (Coloreado por Distrito)"
        )
        fig_scatter.update_layout(
            mapbox_style='open-street-map',
            margin={"r": 0, "t": 30, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.divider()
        
        # Densidad por tipo de robo
        st.subheader("🎯 Densidad de Robos por Tipo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'ROBO A CASA HABITACION' in df_mapa['TIPO'].values:
                df_casa = df_mapa[df_mapa['TIPO'] == 'ROBO A CASA HABITACION']
                fig_casa = px.density_mapbox(
                    df_casa,
                    lat='LATITUD',
                    lon='LONGITUD',
                    zoom=10,
                    height=400,
                    title="Robos a Casa Habitación"
                )
                fig_casa.update_layout(mapbox_style='open-street-map')
                st.plotly_chart(fig_casa, use_container_width=True)
        
        with col2:
            if 'ROBO A NEGOCIO' in df_mapa['TIPO'].values:
                df_negocio = df_mapa[df_mapa['TIPO'] == 'ROBO A NEGOCIO']
                fig_negocio = px.density_mapbox(
                    df_negocio,
                    lat='LATITUD',
                    lon='LONGITUD',
                    zoom=10,
                    height=400,
                    title="Robos a Negocio"
                )
                fig_negocio.update_layout(mapbox_style='open-street-map')
                st.plotly_chart(fig_negocio, use_container_width=True)
        
        with col3:
            if 'ROBO DE VEHICULO' in df_mapa['TIPO'].values:
                df_vehiculo = df_mapa[df_mapa['TIPO'] == 'ROBO DE VEHICULO']
                fig_vehiculo = px.density_mapbox(
                    df_vehiculo,
                    lat='LATITUD',
                    lon='LONGITUD',
                    zoom=10,
                    height=400,
                    title="Robos de Vehículo"
                )
                fig_vehiculo.update_layout(mapbox_style='open-street-map')
                st.plotly_chart(fig_vehiculo, use_container_width=True)
    else:
        st.warning("No hay datos geográficos disponibles para el rango seleccionado.")

# ==================== PÁGINA PREDICCIONES ====================
elif page == "🔮 Predicciones":
    st.title("🔮 Predicciones de Robos por Modelo")
    st.markdown("**Modelos entrenados con Redes Neuronales para predicción de robos mensuales por cuadrante**")
    st.divider()
    
    # Crear tabs para cada tipo de robo
    tab_negocio, tab_vehiculo, tab_casa = st.tabs([
        "🏪 Robos a Negocio",
        "🚗 Robos de Vehículo", 
        "🏠 Robos a Casa Habitación"
    ])
    
    # TAB 1: ROBOS A NEGOCIO
    with tab_negocio:
        st.subheader("📊 Predicción - Robos a Negocios")
        if pred_data['negocio'] is not None and len(pred_data['negocio']) > 0:
            df_pred_neg = pred_data['negocio']
            
            # Obtener métricas
            r2_neg = metricas_modelos.get('negocio', {}).get('enero', {}).get('r2', 'N/A')
            mae_neg = metricas_modelos.get('negocio', {}).get('enero', {}).get('mae', 'N/A')
            
            # Mostrar información del modelo
            col1, col2, col3 = st.columns(3)
            with col1:
                if r2_neg != 'N/A':
                    st.metric("R² Score", f"{r2_neg:.4f}")
                else:
                    st.metric("R² Score", r2_neg)
            
            with col2:
                if mae_neg != 'N/A':
                    st.metric("MAE", f"{mae_neg:.4f}")
                else:
                    st.metric("MAE", mae_neg)
            
            with col3:
                st.metric("Total Cuadrantes", len(df_pred_neg))
            
            st.divider()
            
            # Mostrar tabla de predicciones
            st.subheader("Top 10 Cuadrantes - Predicciones")
            df_display = df_pred_neg.head(10).copy()
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de predicciones
            fig_pred_neg = px.bar(
                df_display.head(10),
                x=df_display.columns[1] if len(df_display.columns) > 1 else df_display.columns[0],
                y=df_display.columns[0],
                orientation='h',
                title="Top 10 Cuadrantes por Predicción de Robos a Negocio"
            )
            st.plotly_chart(fig_pred_neg, use_container_width=True)
        else:
            st.info("No hay datos de predicción disponibles para Robos a Negocio")
    
    # TAB 2: ROBOS DE VEHÍCULO
    with tab_vehiculo:
        st.subheader("📊 Predicción - Robos de Vehículos")
        if pred_data['vehiculo'] is not None and len(pred_data['vehiculo']) > 0:
            df_pred_veh = pred_data['vehiculo']
            
            # Obtener métricas
            r2_veh = metricas_modelos.get('vehiculo', {}).get('enero', {}).get('r2', 'N/A')
            mae_veh = metricas_modelos.get('vehiculo', {}).get('enero', {}).get('mae', 'N/A')
            
            # Mostrar información del modelo
            col1, col2, col3 = st.columns(3)
            with col1:
                if r2_veh != 'N/A':
                    st.metric("R² Score", f"{r2_veh:.4f}")
                else:
                    st.metric("R² Score", r2_veh)
            
            with col2:
                if mae_veh != 'N/A':
                    st.metric("MAE", f"{mae_veh:.4f}")
                else:
                    st.metric("MAE", mae_veh)
            
            with col3:
                st.metric("Total Cuadrantes", len(df_pred_veh))
            
            st.divider()
            
            # Mostrar tabla de predicciones
            st.subheader("Top 10 Cuadrantes - Predicciones")
            df_display = df_pred_veh.head(10).copy()
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de predicciones
            fig_pred_veh = px.bar(
                df_display.head(10),
                x=df_display.columns[1] if len(df_display.columns) > 1 else df_display.columns[0],
                y=df_display.columns[0],
                orientation='h',
                title="Top 10 Cuadrantes por Predicción de Robos de Vehículos"
            )
            st.plotly_chart(fig_pred_veh, use_container_width=True)
        else:
            st.info("No hay datos de predicción disponibles para Robos de Vehículos")
    
    # TAB 3: ROBOS A CASA HABITACIÓN
    with tab_casa:
        st.subheader("📊 Predicción - Robos a Casa Habitación")
        if pred_data['casa'] is not None and len(pred_data['casa']) > 0:
            df_pred_casa = pred_data['casa']
            
            # Obtener métricas
            r2_casa = metricas_modelos.get('casa', {}).get('enero', {}).get('r2', 'N/A')
            mae_casa = metricas_modelos.get('casa', {}).get('enero', {}).get('mae', 'N/A')
            
            # Mostrar información del modelo
            col1, col2, col3 = st.columns(3)
            with col1:
                if r2_casa != 'N/A':
                    st.metric("R² Score", f"{r2_casa:.4f}")
                else:
                    st.metric("R² Score", r2_casa)
            
            with col2:
                if mae_casa != 'N/A':
                    st.metric("MAE", f"{mae_casa:.4f}")
                else:
                    st.metric("MAE", mae_casa)
            
            with col3:
                st.metric("Total Cuadrantes", len(df_pred_casa))
            
            st.divider()
            
            # Mapa de predicciones
            st.subheader("🗺️ Mapa de Predicciones - Casa Habitación (TODOS los cuadrantes)")
            
            # Unir predicciones con coordenadas - TODOS los datos, no solo top 10
            df_pred_mapa = df_pred_casa.merge(cuadrante_coords, left_on='CUADRANTE', right_on='CUADRANTE', how='left')
            df_pred_mapa = df_pred_mapa.dropna(subset=['LATITUD', 'LONGITUD'])
            
            if len(df_pred_mapa) > 0:
                # Crear mapa con Plotly
                fig_mapa_pred = px.scatter_mapbox(
                    df_pred_mapa,
                    lat='LATITUD',
                    lon='LONGITUD',
                    size='PREDICCION_ROBOS_MES_N',
                    color='PREDICCION_ROBOS_MES_N',
                    hover_data={'CUADRANTE': True, 'PREDICCION_ROBOS_MES_N': ':.2f', 'LATITUD': False, 'LONGITUD': False},
                    color_continuous_scale='Reds',
                    zoom=10,
                    height=500,
                    title="Predicciones de Robos a Casa Habitación - Todos los cuadrantes (Tamaño y color = Cantidad de robos predichos)"
                )
                fig_mapa_pred.update_layout(
                    mapbox_style='open-street-map',
                    margin={"r": 0, "t": 30, "l": 0, "b": 0}
                )
                st.plotly_chart(fig_mapa_pred, use_container_width=True)
                
                st.info(f"📍 Se muestran {len(df_pred_mapa)} cuadrantes con predicciones en el mapa. El tamaño y color de los puntos representa la cantidad de robos predichos.")
            else:
                st.warning("No hay datos geográficos disponibles para mostrar el mapa.")
            
            st.divider()
            
            # Mostrar tabla de predicciones
            st.subheader("Top 10 Cuadrantes - Predicciones")
            df_display = df_pred_casa.head(10).copy()
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de predicciones
            fig_pred_casa = px.bar(
                df_display.head(10),
                x=df_display.columns[1] if len(df_display.columns) > 1 else df_display.columns[0],
                y=df_display.columns[0],
                orientation='h',
                title="Top 10 Cuadrantes por Predicción de Robos a Casa Habitación"
            )
            st.plotly_chart(fig_pred_casa, use_container_width=True)
        else:
            st.info("No hay datos de predicción disponibles para Robos a Casa Habitación")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    <p><strong>Dashboard de Análisis de Robos - Chihuahua</strong></p>
    <p>Datos: 2015-2024 | Actualizado: Noviembre 2025</p>
</div>
""", unsafe_allow_html=True)
