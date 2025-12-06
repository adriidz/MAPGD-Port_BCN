# Versión local de dashboard, sin AWS, leyendo JSON de /datos y vídeos de /runs/cars_video

import json
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px
import streamlit as st

# --- CONFIG BÁSICA ---
st.set_page_config(page_title="Monitor de Tráfico", page_icon="🚦", layout="wide")

DATA_DIR = "datos"
from pathlib import Path
import os

print("PWD:", os.getcwd())
print("DATA_DIR absolute:", Path(DATA_DIR).resolve())
print("DATA_DIR exists?:", Path(DATA_DIR).exists())
VIDEO_DIR = "runs/cars_video"

CUSTOM_STYLE = dedent(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;600&display=swap');
    :root {
        --bg: #0b1224;
        --panel: rgba(255, 255, 255, 0.04);
        --text: #e8edf7;
        --muted: #9fb0d5;
        --accent: #8ef8c2;
        --accent-2: #7bc5ff;
        --shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
        --radius: 16px;
    }
    .stApp {
        background: radial-gradient(circle at 20% 20%, #13203d 0, #0b1224 35%, #080d1a 100%);
        color: var(--text);
        font-family: "DM Sans", "Space Grotesk", sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: var(--text);
        font-family: "Space Grotesk", "DM Sans", sans-serif;
        letter-spacing: -0.02em;
    }
    .block-container { padding-top: 3.5rem; }
    [data-testid="stSidebar"] {
        background: #0c1326;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] * { color: var(--text); }
    .hero {
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        padding: 1.25rem 1.5rem;
        border-radius: var(--radius);
        border: 1px solid rgba(255, 255, 255, 0.05);
        background: linear-gradient(120deg, rgba(142, 248, 194, 0.12), rgba(123, 197, 255, 0.12));
        box-shadow: var(--shadow);
    }
    .hero .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--accent);
        font-size: 0.75rem;
        margin-bottom: 0.35rem;
    }
    .hero h1 { margin: 0.1rem 0 0.45rem; font-size: 2.2rem; }
    .hero p { margin: 0; color: var(--muted); max-width: 820px; }
    .pill-row { margin-top: 0.9rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .pill {
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        color: var(--text);
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .metric-card {
        background: var(--panel);
        border-radius: var(--radius);
        padding: 1rem 1.15rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: var(--shadow);
        height: 100%;
    }
    .metric-label { font-size: 0.95rem; color: var(--muted); margin-bottom: 0.1rem; }
    .metric-value { font-size: 1.9rem; font-weight: 700; color: var(--text); }
    .metric-caption { font-size: 0.9rem; color: var(--accent-2); margin-top: 0.1rem; }
    .section-title { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; margin: 1.2rem 0 0.4rem; }
    .soft-card {
        background: var(--panel);
        border-radius: var(--radius);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 0.85rem 1rem;
    }
    .divider {
        height: 1px;
        margin: 1.2rem 0 0.8rem;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.22), transparent);
    }
    [data-testid="stTabs"] [role="tablist"] { gap: 0.4rem; border: none; }
    [data-testid="stTabs"] [role="tab"] {
        background: rgba(255, 255, 255, 0.04);
        color: var(--text);
        border-radius: 12px;
        padding: 0.35rem 0.85rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(120deg, rgba(142, 248, 194, 0.18), rgba(123, 197, 255, 0.16));
        color: var(--text);
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    [data-testid="stDataFrame"] {
        background: var(--panel);
        border-radius: var(--radius);
        padding: 0.2rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: var(--shadow);
    }
    </style>
    """
)

st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)


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
    """
    Intenta localizar el vídeo aunque en los JSON venga con ruta parcial o absoluta.
    """
    base = Path(base_dir)

    # 1) Si el JSON ya trae una ruta válida, úsala tal cual
    candidate = Path(video_file_name)
    if candidate.is_file():
        return str(candidate)

    # 2) Probar solo con el nombre del fichero dentro de VIDEO_DIR
    name_only = Path(video_file_name).name
    direct = base / name_only
    if direct.is_file():
        return str(direct)

    # 3) Buscar recursivamente en VIDEO_DIR por nombre
    for p in base.rglob(name_only):
        if p.is_file():
            return str(p)

    return None


def metric_card(title: str, value: str | int | float, caption: str = "") -> None:
    st.markdown(
        dedent(
            f"""
            <div class="metric-card">
                <div class="metric-label">{title}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-caption">{caption}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

# --- UI PRINCIPAL ---

df_full = load_events()

st.markdown(
    dedent(
        """
        <div class="hero">
            <div class="eyebrow">Monitor en tiempo real</div>
            <h1>Tráfico urbano con visión por computador</h1>
            <p>Seguimiento continuo de eventos, aforo y vídeos asociados. Pensado para demos con cliente: limpio, visual y enfocado en negocio.</p>
            <div class="pill-row">
                <span class="pill">Datos locales (JSON)</span>
                <span class="pill">Vídeo sincronizado</span>
                <span class="pill">Filtros instantáneos</span>
            </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

if df_full.empty:
    st.info("No hay eventos todavía. Ejecuta `python main.py` para generar datos en la carpeta `datos/`.")
    st.stop()

# --- SIDEBAR: FILTROS ---

st.sidebar.header("🎛️ Panel de filtros")
st.sidebar.caption("Filtra en tiempo real sin recargar la sesión.")

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

st.markdown('<div class="section-title">Resumen ejecutivo</div>', unsafe_allow_html=True)

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

with col1:
    metric_card("Eventos (filtro actual)", f"{len(df):,}".replace(",", "."), "Procesados desde JSON locales")

if "direction" in df.columns:
    fw = int((df["direction"] == "forward").sum())
    bw = int((df["direction"] == "backward").sum())
else:
    fw = 0
    bw = 0

with col2:
    metric_card("Forward (↑)", fw, "Tráfico hacia delante")
with col3:
    metric_card("Backward (↓)", bw, "Tráfico en sentido contrario")
with col4:
    metric_card("Aforo global", aforo_global, "Entradas vs salidas (todas cámaras)")

if cam_sel != "TODAS":
    st.markdown(
        dedent(
            f"""
            <div class="soft-card">
                <strong>Cámara activa:</strong> {cam_sel} · Aforo bajo filtros:
                <span style="color: var(--accent)">{aforo_cam}</span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# --- TABS DE CONTENIDO ---

st.markdown('<div class="section-title">Panel de análisis</div>', unsafe_allow_html=True)
st.caption("Explora métricas, series temporales, tablas y clips de vídeo en un mismo lugar.")

tab_resumen, tab_tiempo, tab_eventos, tab_video = st.tabs(
    ["📊 Resumen", "⏱️ Evolución temporal", "📋 Eventos", "🎥 Vídeo"]
)

# --- TAB: RESUMEN ---

with tab_resumen:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Conteo por dirección (filtro actual)")
        if "direction" in df.columns:
            dir_counts = df["direction"].value_counts().reset_index()
            dir_counts.columns = ["direction", "count"]
            fig_bar = px.bar(
                dir_counts,
                x="direction",
                y="count",
                color="direction",
                color_discrete_map={
                    "forward": "#7bc5ff",
                    "backward": "#8ef8c2",
                },
            )
            fig_bar.update_layout(
                height=280,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e8edf7",
                showlegend=False,
                xaxis_title="",
                yaxis_title="Eventos",
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
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
        serie_total_df = serie_total.reset_index()
        serie_total_df.columns = ["fecha", "eventos"]
        fig_total = px.line(
            serie_total_df,
            x="fecha",
            y="eventos",
            line_shape="spline",
            color_discrete_sequence=["#7bc5ff"],
        )
        fig_total.update_layout(
            height=250,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e8edf7",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_total, use_container_width=True)

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
            serie_dir_df = serie_dir.reset_index()
            serie_dir_melt = serie_dir_df.melt(
                id_vars="fecha",
                var_name="direction",
                value_name="eventos",
            )
            fig_dir = px.line(
                serie_dir_melt,
                x="fecha",
                y="eventos",
                color="direction",
                line_shape="spline",
                color_discrete_map={
                    "forward": "#7bc5ff",
                    "backward": "#8ef8c2",
                },
            )
            fig_dir.update_layout(
                height=250,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e8edf7",
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig_dir, use_container_width=True)

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

            aforo_plot = aforo_df[["aforo_acumulado"]].reset_index()
            aforo_plot.columns = ["fecha", "aforo_acumulado"]
            fig_aforo = px.line(
                aforo_plot,
                x="fecha",
                y="aforo_acumulado",
                line_shape="spline",
                color_discrete_sequence=["#8ef8c2"],
            )
            fig_aforo.update_layout(
                height=250,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e8edf7",
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig_aforo, use_container_width=True)
        else:
            st.info("No hay columna `zone` (entry/exit), ejecuta el detector actualizado para calcular aforo.")

        # --- Aforo por cámara en el tiempo (solo cuando cam_sel = TODAS) ---
        if cam_sel == "TODAS" and "zone" in df_tmp.columns and "camera_id" in df_tmp.columns:
            st.markdown("**Aforo por cámara en el tiempo (todas las cámaras)**")

            # Nos quedamos solo con eventos de entrada/salida
            df_aforo_cam = df_tmp[df_tmp["zone"].isin(["entry", "exit"])].copy()

            # Contamos entradas y salidas por cámara y ventana temporal
            entradas_cam_t = (
                df_aforo_cam[df_aforo_cam["zone"] == "entry"]
                .groupby("camera_id")
                .resample("45S")
                .size()
                .rename("entradas")
            )
            salidas_cam_t = (
                df_aforo_cam[df_aforo_cam["zone"] == "exit"]
                .groupby("camera_id")
                .resample("45S")
                .size()
                .rename("salidas")
            )

            aforo_cam_t = pd.concat([entradas_cam_t, salidas_cam_t], axis=1).fillna(0)
            aforo_cam_t["aforo_instantaneo"] = (aforo_cam_t["entradas"] - aforo_cam_t["salidas"]).abs()

            # Acumulado por cámara
            aforo_cam_t["aforo_acumulado"] = (
                aforo_cam_t.groupby("camera_id")["aforo_instantaneo"].cumsum()
            )

            aforo_cam_plot = aforo_cam_t["aforo_acumulado"].reset_index()
            aforo_cam_plot.columns = ["camera_id", "fecha", "aforo_acumulado"]

            fig_aforo_cam = px.line(
                aforo_cam_plot,
                x="fecha",
                y="aforo_acumulado",
                color="camera_id",
                line_shape="spline",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_aforo_cam.update_layout(
                height=280,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e8edf7",
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                legend_title_text="Cámara",
            )
            st.plotly_chart(fig_aforo_cam, use_container_width=True)
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
        df_videos = df_full[df_full["video_file"].notna()].copy()
        df_videos["video_name"] = df_videos["video_file"].astype(str).apply(lambda p: Path(p).name)

        # Solo vídeos con sufijo _web y que existan físicamente
        def is_valid_web(name: str) -> bool:
            if not name.endswith(".mp4"):
                return False
            if "_web" not in name:
                return False
            return (Path(VIDEO_DIR) / name).is_file()

        valid_names = sorted({n for n in df_videos["video_name"].unique() if is_valid_web(n)})

        if not valid_names:
            st.info("No hay vídeos compatibles (formato web) encontrados en la carpeta de salida.")
        else:
            video_sel = st.selectbox("Selecciona un vídeo", valid_names)

            df_video = df_videos[df_videos["video_name"] == video_sel]

            st.write(f"Eventos asociados a `{video_sel}`:")
            cols_pref_local = ["fecha", "timestamp", "direction", "track_id", "camera_id", "zone", "counter_type", "video_file"]
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
                with st.container():
                    st.video(path)
                    st.markdown(
                        """
                        <style>
                        video {
                            max-height: 420px !important;
                            max-width: 80% !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.error(
                    f"No se ha encontrado el fichero de vídeo compatible.\n"
                    f"- Buscado `{video_sel}` dentro de `{VIDEO_DIR}`.\n"
                    f"- Asegúrate de que ffmpeg ha generado la versión _web."
                )