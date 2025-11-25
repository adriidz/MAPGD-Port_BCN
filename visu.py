import streamlit as st
import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key

# --- CONFIGURACIÓN DE CREDENCIALES (CÓPIALAS DE AWS ACADEMY) ---
# IMPORTANTE: Estas claves cambian cada vez que reinicias el laboratorio.
# poner claves whatsapp aqui

TABLE_NAME = 'RegistroTrafico'
BUCKET_NAME = 'videos-trafic-mapgd' # Asegúrate de poner TU nombre de bucket

st.set_page_config(page_title="Dashboard Tráfico", layout="wide")

# --- CONEXIÓN AWS (CON CREDENCIALES EXPLÍCITAS) ---
# Aquí es donde fallaba: ahora le pasamos las claves directamente
try:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
    table = dynamodb.Table(TABLE_NAME)

    s3_client = boto3.client(
        's3',
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
except Exception as e:
    st.error(f"Error de conexión con AWS. Revisa tus credenciales: {e}")
    st.stop()

# --- FUNCIONES ---
def get_data(camera_id):
    try:
        response = table.scan(
            FilterExpression=Key('camera_id').eq(camera_id)
        )
        items = response['Items']
        return pd.DataFrame(items)
    except Exception as e:
        st.error(f"Error leyendo DynamoDB: {e}")
        return pd.DataFrame()

def get_video_url(bucket, key):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=3600
        )
        return url
    except Exception as e:
        return None

# --- INTERFAZ ---
st.title("🚗 Monitor de Tráfico Cloud")

# 1. Sidebar de controles
st.sidebar.header("Filtros")
camara = st.sidebar.selectbox("Selecciona Cámara", ["camara_1", "camara_2"])

# 2. Cargar datos
if st.button("Refrescar Datos"):
    st.cache_data.clear()

df = get_data(camara)

if not df.empty:
    # Convertir tipos
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_numeric(df['timestamp'])
    
    # Convertir ISO date a objeto datetime real
    if 'iso_date' in df.columns:
        df['fecha'] = pd.to_datetime(df['iso_date'])
    
    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Vehículos", len(df))
    
    if 'direction' in df.columns:
        fw = len(df[df['direction'] == 'forward'])
        bw = len(df[df['direction'] == 'backward'])
        col2.metric("Dirección Forward", fw)
        col3.metric("Dirección Backward", bw)

    # --- GRÁFICOS ---
    st.subheader("Actividad Temporal")
    if 'fecha' in df.columns and 'direction' in df.columns:
        # Gráfico simple de barras por dirección
        st.bar_chart(df['direction'].value_counts())

    # --- VISUALIZADOR DE VÍDEO ---
    st.divider()
    st.subheader("Evidence Locker (Vídeos)")
    
    if 'video_file' in df.columns:
        # Filtramos valores nulos o vacíos por si acaso
        videos_disponibles = df['video_file'].dropna().unique()
        
        if len(videos_disponibles) > 0:
            video_seleccionado = st.selectbox("Selecciona una grabación asociada:", videos_disponibles)
            
            if video_seleccionado:
                st.write(f"Reproduciendo: {video_seleccionado}")
                # Intentamos generar la URL
                video_url = get_video_url(BUCKET_NAME, video_seleccionado)
                if video_url:
                    st.video(video_url)
                else:
                    st.error("No se pudo generar el enlace del vídeo.")
        else:
            st.info("Hay datos de tráfico, pero no tienen vídeos asociados todavía.")
    else:
        st.warning("Tus datos en DynamoDB no tienen la columna 'video_file'. Asegúrate de haber ejecutado el detector nuevo.")

else:
    st.info("No hay datos para esta cámara todavía o no se pudieron cargar.")