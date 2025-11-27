import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import warnings

# Configuración de página (debe ser la primera llamada a Streamlit)
st.set_page_config(
    page_title="Dashboard de Predicción y Análisis de Robos en Chihuahua",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def load_data(file_path):
    """Carga y limpia los datos de robos."""
    warnings.filterwarnings('ignore')
    
    try:
        # Asumiendo que el archivo está en el mismo directorio
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Error: El archivo '{file_path}' no se encontró.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Conversión y Limpieza Esencial
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    df.dropna(subset=['FECHA', 'LATITUD', 'LONGITUD'], inplace=True)
    
    # Ingeniería de Features para Análisis
    df['FECHA_MES'] = df['FECHA'].dt.to_period('M').astype(str)
    df['HORA_CLEAN'] = df['HORA'].replace(99, np.nan).astype('Int64')
    df['VIOLENCIA'] = df['VIOLENCIA'].str.strip().str.upper()
    df.loc[~df['VIOLENCIA'].isin(['SI', 'NO']), 'VIOLENCIA'] = 'DESCONOCIDA'
    
    # Tablas Agregadas para Visualización
    df_mensual = df.groupby(['FECHA_MES', 'TIPO']).size().reset_index(name='Total Robos')
    df_mensual['FECHA_MES'] = pd.to_datetime(df_mensual['FECHA_MES'])

    df_coords = df.groupby('CUADRANTE').agg(
        LATITUD_AVG=('LATITUD', 'mean'),
        LONGITUD_AVG=('LONGITUD', 'mean'),
        DISTRITO=('DISTRITO', lambda x: x.mode()[0]) # Obtener el distrito más común
    ).reset_index()

    return df, df_mensual, df_coords

# 2. FUNCIÓN DE CREACIÓN DE GRÁFICOS (Plotly)
def create_figures(df, df_mensual):
    """Genera las visualizaciones interactivas de Plotly."""
    
    # --- GRÁFICA 1: TENDENCIA TEMPORAL (Insight: Evolución y Estacionalidad) ---
    fig_tendencia = px.line(
        df_mensual, 
        x='FECHA_MES', 
        y='Total Robos', 
        color='TIPO',
        title='📉 Evolución Mensual del Total de Robos (2015-2025)',
        labels={'FECHA_MES': 'Fecha', 'Total Robos': 'Conteo de Robos'},
        template='plotly_white'
    )
    fig_tendencia.update_xaxes(dtick="M12", tickformat="%Y")
    fig_tendencia.update_layout(hovermode="x unified")
    
    # --- GRÁFICA 2: TIPO Y VIOLENCIA (Insight: Perfil de Riesgo Operacional) ---
    df_tipo_violencia = df.groupby(['TIPO', 'VIOLENCIA']).size().reset_index(name='Conteo')
    fig_tipo_violencia = px.bar(
        df_tipo_violencia, 
        x='TIPO', 
        y='Conteo', 
        color='VIOLENCIA', 
        title='🔪 Distribución de Robos por Tipo y Violencia',
        labels={'TIPO': 'Tipo de Robo', 'Conteo': 'Número de Incidentes'},
        color_discrete_map={'SI': 'red', 'NO': 'blue', 'DESCONOCIDA': 'gray'},
        template='plotly_white'
    )
    fig_tipo_violencia.update_layout(xaxis={'categoryorder':'total descending'})

    # --- GRÁFICA 3: DISTRIBUCIÓN HORARIA (Insight: Optimización de Vigilancia) ---
    df_horaria = df.dropna(subset=['HORA_CLEAN'])
    df_horaria['HORA_CLEAN'] = df_horaria['HORA_CLEAN'].astype(int)
    fig_horaria = px.histogram(
        df_horaria, 
        x='HORA_CLEAN',
        color='TIPO',
        nbins=24, 
        title='⏰ Distribución Horaria de los Robos (Hora conocida)',
        labels={'HORA_CLEAN': 'Hora del Día (0-23)', 'count': 'Frecuencia de Robos'},
        template='plotly_white'
    )
    # fig_horaria.update_traces(marker_color='#F08080')
    fig_horaria.update_layout(xaxis={'tickmode': 'linear', 'dtick': 1})
    
    return fig_tendencia, fig_tipo_violencia, fig_horaria

# 3. FUNCIÓN DE MAPA DE PREDICCIÓN (Insight: Zonas Calientes Futuras)
def create_prediction_map(df_coords, df_predicciones):
    """Combina coordenadas y predicciones para generar el mapa de zonas de riesgo."""
    
    # Unir las predicciones con las coordenadas promedio por cuadrante
    df_mapa_pred = pd.merge(df_predicciones, df_coords, on='CUADRANTE', how='inner')
    
    # Generar el Mapa de Calor Predictivo (Plotly Scatter Mapbox)
    fig_mapa_predictivo = px.scatter_mapbox(
        df_mapa_pred, 
        lat="LATITUD_AVG", 
        lon="LONGITUD_AVG", 
        color="PREDICCION_ROBOS", 
        size="PREDICCION_ROBOS",
        color_continuous_scale=px.colors.sequential.Reds, # Escala de calor para riesgo
        hover_name="DISTRITO",
        hover_data={'PREDICCION_ROBOS': True, 'CUADRANTE': True, 'LATITUD_AVG': False},
        zoom=10, 
        title="🔥 Mapa de Calor Predictivo por Cuadrante (Próximo Mes)",
        template='plotly_dark'
    )

    fig_mapa_predictivo.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    
    return fig_mapa_predictivo, df_mapa_pred

# ==============================================================================
# ESTRUCTURA DEL DASHBOARD EN STREAMLIT
# ==============================================================================

# Cargar los datos al inicio
df, df_mensual, df_coords = load_data('robos_tot_final.csv')

# Solo correr si los datos se cargaron correctamente
if not df.empty:

    st.title("Sistema de Inteligencia Criminal: Análisis y Predicción de Robos en Chihuahua")
    st.markdown("---")

    # --- PUNTOS CLAVE (KPIs) ---
    col1, col2, col3 = st.columns(3)
    
    total_robos = df.shape[0]
    robos_mensuales_prom = df_mensual['Total Robos'].mean()
    tipo_mas_frecuente = df['TIPO'].mode()[0]

    col1.metric("Total de Robos (2015-2025)", f"{total_robos:,}")
    col2.metric("Robos Mensuales Promedio", f"{robos_mensuales_prom:.0f}")
    col3.metric("Tipo de Robo Dominante", tipo_mas_frecuente)
    
    st.markdown("---")

    # Generar Figuras de Análisis Descriptivo
    fig_tendencia, fig_tipo_violencia, fig_horaria = create_figures(df, df_mensual)

    # --- SECCIÓN 1: ANÁLISIS TEMPORAL E INSIGHTS ---
    st.header("1. Análisis Histórico y Tendencias (Punto 4)")
    st.plotly_chart(fig_tendencia, use_container_width=True)
    st.markdown(f"""
        **Insight Clave:** Identifica los picos de crisis (p. ej., {df_mensual.iloc[df_mensual['Total Robos'].idxmax()]['FECHA_MES']}) y los periodos de relativa calma.
        Usa la interactividad para evaluar si la tasa de crecimiento es positiva o negativa.
    """)

    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Perfil del Delito por Tipo y Violencia")
        st.plotly_chart(fig_tipo_violencia, use_container_width=True)
        st.markdown(f"**Insight:** **{tipo_mas_frecuente}** es el más frecuente. Usa esta gráfica para comparar la proporción 'SI' (Violencia) vs 'NO' y dirigir recursos de reacción vs prevención.")
    
    with col5:
        st.subheader("Horas Críticas de Incidencia")
        st.plotly_chart(fig_horaria, use_container_width=True)
        hora_pico = df['HORA_CLEAN'].mode()[0]
        st.markdown(f"**Insight:** La hora pico de actividad delictiva (conocida) es alrededor de las **{hora_pico} hrs**. Esto es fundamental para la optimización de los patrullajes.")
    
    st.markdown("---")
    
    # --- SECCIÓN 2: PREDICCIÓN Y ASIGNACIÓN DE RECURSOS (Punto 5 & 6) ---
    st.header("2. Predicción: Zonas de Riesgo Futuro (Punto 5 y 6)")
    st.sidebar.title("Carga de Predicciones")
    
    uploaded_file = st.sidebar.file_uploader(
        "Sube tu tabla de predicciones (CSV). Debe tener las columnas: CUADRANTE, PREDICCION_ROBOS_MES_N", 
        type=["csv"]
    )
    
    if uploaded_file is not None:
        try:
            df_predicciones = pd.read_csv(uploaded_file)
            
            # Validación de columnas
            required_cols = ['CUADRANTE', 'PREDICCION_ROBOS_MES_N']
            if not all(col in df_predicciones.columns for col in required_cols):
                st.sidebar.error("El archivo CSV debe contener las columnas 'CUADRANTE' y 'PREDICCION_ROBOS_MES_N'.")
            else:
                # Generar mapa predictivo
                fig_mapa_predictivo, df_mapa_pred = create_prediction_map(df_coords, df_predicciones)
                
                st.plotly_chart(fig_mapa_predictivo, use_container_width=True)
                
                # Insights del Mapa de Predicción
                top_cuadrantes = df_mapa_pred.sort_values(by='PREDICCION_ROBOS_MES_N', ascending=False).head(5)
                
                st.markdown(f"""
                    **Insight de Predicción (Toma de Decisiones):** El mapa identifica claramente los **cuadrantes con la mayor demanda de recursos** para el próximo mes.
                    - **Cuadrantes de Máximo Riesgo (Top 3):** {top_cuadrantes['CUADRANTE'].iloc[0]}, {top_cuadrantes['CUADRANTE'].iloc[1]} y {top_cuadrantes['CUADRANTE'].iloc[2]}.
                    - Estos cuadrantes, ubicados principalmente en el distrito **{top_cuadrantes['DISTRITO'].mode()[0]}**, deben ser el foco de patrullaje intensivo.
                """)
                
                st.subheader("Tabla de Predicciones Detallada")
                st.dataframe(df_mapa_pred[['CUADRANTE', 'DISTRITO', 'PREDICCION_ROBOS_MES_N']].sort_values(by='PREDICCION_ROBOS_MES_N', ascending=False), use_container_width=True)

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo de predicciones: {e}")
            
    else:
        st.info("Sube tu archivo de predicciones en la barra lateral para visualizar el mapa de zonas de riesgo futuro (Punto 5).")