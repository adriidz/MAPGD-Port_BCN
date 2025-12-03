# Versión local de dashboard, sin AWS, leyendo JSON de /datos y vídeos de /runs/cars_video

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# --- CONFIG BÁSICA ---
st.set_page_config(page_title="Monitor de Tráfico", layout="wide")

DATA_DIR = "datos"
VIDEO_DIR = "runs/cars_video"


# --- CARGA DE DATOS ---

@st.cache_data
def load_events(data_dir: str = DATA_DIR) -> pd.DataFrame:
    data_path = Path(data_dir)
    if not data_path.exists():
        return pd.DataFrame()

    events = []
    for f in data_path.glob("event_*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                events.append(json.load(fh))
        except Exception:
            # Ignorar ficheros corruptos
            pass

    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)

    # Conversión de tipos
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        df["fecha"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")

    # Asegurar tipos de texto
    for col in ["camera_id", "video_file", "direction", "zone", "counter_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df


def get_video_path(video_file_name: str, base_dir: str = VIDEO_DIR) -> str | None:
    base = Path(base_dir)
    path = base / video_file_name
    if path.exists():
        return str(path)

    # Segundo intento: por si video_file trae ruta relativa distinta
    alt = Path(video_file_name)
    if alt.is_file():
        return str(alt)

    return None


# --- UI PRINCIPAL ---

st.title("🚗 Monitor de Tráfico (Demo Local)")

df_full = load_events()

if df_full.empty:
    st.info("No hay eventos todavía. Ejecuta `python main.py` para generar datos en la carpeta `datos/`.")
    st.stop()

# --- SIDEBAR: FILTROS ---

st.sidebar.header("Filtros")

df = df_full.copy()

# Filtro por cámara
if "camera_id" in df.columns:
    camaras = sorted(df["camera_id"].dropna().unique())
    cam_sel = st.sidebar.selectbox("Cámara (para vistas filtradas)", ["TODAS"] + camaras)
    if cam_sel != "TODAS":
        df = df[df["camera_id"] == cam_sel]
else:
    cam_sel = "N/A"
    st.sidebar.markdown("*No hay campo `camera_id` en los datos*")

# Filtro por rango de fechas (sobre df filtrado)
if "fecha" in df.columns and df["fecha"].notna().any():
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    rango = st.sidebar.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    if isinstance(rango, tuple) and len(rango) == 2:
        ini, fin = rango
        df = df[(df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin)]

st.sidebar.button("🔄 Refrescar datos", on_click=lambda: st.cache_data.clear())

st.sidebar.divider()

# Botón de descarga de CSV global (sin filtros)
st.sidebar.download_button(
    label="📥 Descargar CSV completo (todas cámaras)",
    data=df_full.to_csv(index=False).encode("utf-8"),
    file_name=f"eventos_completos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)

# Si tras filtros no queda nada
if df.empty:
    st.warning("No hay eventos que cumplan los filtros seleccionados.")
    st.stop()

# --- MÉTRICAS PRINCIPALES ---

st.subheader("Resumen general")

# Aforo GLOBAL (todas cámaras, sin aplicar filtro de cámara)
entradas_global = 0
salidas_global = 0
if "zone" in df_full.columns:
    entradas_global = int((df_full["zone"] == "entry").sum())
    salidas_global = int((df_full["zone"] == "exit").sum())
aforo_global = abs(entradas_global - salidas_global)

# Aforo CÁMARA (sobre df filtrado por cámara/fechas)
entradas_cam = 0
salidas_cam = 0
if "zone" in df.columns:
    entradas_cam = int((df["zone"] == "entry").sum())
    salidas_cam = int((df["zone"] == "exit").sum())
aforo_cam = abs(entradas_cam - salidas_cam)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total eventos (filtro actual)", len(df))

if "direction" in df.columns:
    fw = int((df["direction"] == "forward").sum())
    bw = int((df["direction"] == "backward").sum())
    col2.metric("Forward (↑)", fw)
    col3.metric("Backward (↓)", bw)
else:
    col2.metric("Forward (↑)", 0)
    col3.metric("Backward (↓)", 0)

col4.metric("Aforo GLOBAL (todas cámaras)", aforo_global)

# Aforo cámara (solo si una cámara concreta está seleccionada)
if cam_sel != "TODAS":
    st.info(f"Aforo para la cámara **{cam_sel}** (según filtros): {aforo_cam}")

st.markdown("---")

# --- TABS DE CONTENIDO ---

tab_resumen, tab_tiempo, tab_eventos, tab_video = st.tabs(
    ["📊 Resumen", "⏱️ Evolución temporal", "📋 Eventos", "🎥 Vídeo"]
)

# --- TAB: RESUMEN ---

with tab_resumen:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Conteo por dirección (filtro actual)")
        if "direction" in df.columns:
            st.bar_chart(df["direction"].value_counts())
        else:
            st.write("No hay campo `direction` en los datos.")

    with col_b:
        st.subheader("Eventos por vídeo (todas cámaras)")
        if "video_file" in df_full.columns:
            counts = (
                df_full["video_file"]
                .astype(str)
                .value_counts()
                .rename_axis("video_file")
                .reset_index(name="eventos")
            )
            st.dataframe(counts, use_container_width=True, height=250)
        else:
            st.write("No hay campo `video_file` en los datos.")

    # Aforo por cámara (métrica)
    if "camera_id" in df_full.columns and "zone" in df_full.columns:
        st.subheader("Aforo por cámara (entradas - salidas)")
        aforo_cam_df = (
            df_full[df_full["zone"].isin(["entry", "exit"])]
            .groupby(["camera_id", "zone"])
            .size()
            .unstack(fill_value=0)
        )
        aforo_cam_df["aforo"] = abs(aforo_cam_df.get("entry", 0) - aforo_cam_df.get("exit", 0))
        st.dataframe(aforo_cam_df, use_container_width=True, height=250)

# --- TAB: EVOLUCIÓN TEMPORAL ---

with tab_tiempo:
    st.subheader("Eventos a lo largo del tiempo (filtro actual)")

    if "fecha" in df.columns and df["fecha"].notna().any():
        df_tmp = df.set_index("fecha").sort_index()

        # --- Serie total de eventos (cada 45 segundos) ---
        serie_total = df_tmp.resample("45S").size()
        st.line_chart(serie_total, height=250)

        # --- Serie por dirección (si existe) ---
        if "direction" in df_tmp.columns:
            st.markdown("**Desglose por dirección (forward / backward)**")
            serie_dir = (
                df_tmp.groupby("direction")
                .resample("45S")
                .size()
                .unstack(level=0)
                .fillna(0)
            )
            st.line_chart(serie_dir, height=250)

        # --- Aforo temporal (entradas - salidas) para el filtro actual ---
        if "zone" in df_tmp.columns:
            st.markdown("**Aforo en el tiempo (entradas - salidas, filtro actual)**")

            entradas_t = (
                df_tmp[df_tmp["zone"] == "entry"]
                .resample("45S")
                .size()
                .rename("entradas")
            )
            salidas_t = (
                df_tmp[df_tmp["zone"] == "exit"]
                .resample("45S")
                .size()
                .rename("salidas")
            )

            aforo_df = pd.concat([entradas_t, salidas_t], axis=1).fillna(0)
            aforo_df["aforo_instantaneo"] = abs(aforo_df["entradas"] - aforo_df["salidas"])
            aforo_df["aforo_acumulado"] = aforo_df["aforo_instantaneo"].cumsum()

            st.line_chart(aforo_df[["aforo_acumulado"]], height=250)
        else:
            st.info("No hay columna `zone` (entry/exit), ejecuta el detector actualizado para calcular aforo.")
    else:
        st.write("No se puede generar serie temporal (no hay columna `fecha` válida).")

# --- TAB: EVENTOS (TABLA) ---

with tab_eventos:
    st.subheader("Tabla de eventos (filtro actual)")

    cols_pref = ["fecha", "timestamp", "direction", "track_id", "camera_id", "video_file", "zone", "counter_type"]
    cols_existentes = [c for c in cols_pref if c in df.columns]
    cols_otras = [c for c in df.columns if c not in cols_existentes]
    cols_final = cols_existentes + cols_otras

    df_sorted = df.sort_values("fecha", ascending=False) if "fecha" in df.columns else df
    st.dataframe(df_sorted[cols_final].head(500), use_container_width=True, height=450)

    st.download_button(
        "📥 Descargar CSV filtrado",
        data=df_sorted[cols_final].to_csv(index=False).encode("utf-8"),
        file_name=f"eventos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# --- TAB: VÍDEO ---

with tab_video:
    st.subheader("Revisión de vídeos")

    if "video_file" not in df_full.columns:
        st.info("Los eventos no incluyen `video_file`. Asegúrate de que el detector la esté guardando.")
    else:
        videos_unicos = sorted(df_full["video_file"].dropna().unique())
        if not videos_unicos:
            st.info("No hay vídeos asociados a los eventos.")
        else:
            video_sel = st.selectbox("Selecciona un vídeo", videos_unicos)

            df_video = df_full[df_full["video_file"] == video_sel]
            st.write(f"Eventos asociados a `{video_sel}`:")
            cols_pref_local = ["fecha", "timestamp", "direction", "track_id", "camera_id", "zone", "counter_type"]
            cols_exist_local = [c for c in cols_pref_local if c in df_video.columns]
            cols_otras_local = [c for c in df_video.columns if c not in cols_exist_local]
            cols_final_local = cols_exist_local + cols_otras_local

            if "fecha" in df_video.columns:
                df_video = df_video.sort_values("fecha", ascending=False)

            st.dataframe(
                df_video[cols_final_local].head(100),
                use_container_width=True,
                height=250,
            )

            path = get_video_path(video_sel)
            st.write(f"Ruta buscada para el vídeo: `{path or 'NO ENCONTRADO'}`")
            if path:
                st.video(path)
            else:
                st.error(
                    f"No se ha encontrado el fichero de vídeo.\n"
                    f"- Esperado en `{VIDEO_DIR}\\{video_sel}`\n"
                    f"- Verifica que el archivo existe físicamente en esa carpeta."
                )