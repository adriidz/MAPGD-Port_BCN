# Versió local del quadre de comandament, sense AWS, llegint JSON de /datos i vídeos de /runs/cars_video

import json
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px
import streamlit as st

# --- CONFIGURACIÓ BÀSICA ---
st.set_page_config(page_title="Monitor de trànsit", page_icon=None, layout="wide")

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
        margin-bottom: 0.45rem;
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


# --- CÀRREGA DE DADES ---

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
            # Ignorar fitxers corruptes
            pass

    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)

    # Conversió de tipus
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        df["fecha"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")

    # Assegurar tipus de text
    for col in ["camera_id", "video_file", "direction", "zone", "counter_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df


def get_video_path(video_file_name: str, base_dir: str = VIDEO_DIR) -> str | None:
    base = Path(base_dir)
    candidate = Path(video_file_name)
    if candidate.is_file():
        return str(candidate)
    name_only = Path(video_file_name).name
    direct = base / name_only
    if direct.is_file():
        return str(direct)
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
            <div class="eyebrow">Monitor en temps real</div>
            <h1>Sistema de monitorització Intel·ligent D’accessos</h1>
            <p>Supervisió contínua del flux de vehicles, ocupació i esdeveniments associats a partir de dades de vídeo.</p>
            <div class="pill-row">
                <span class="pill">Dades locals (JSON)</span>
                <span class="pill">Vídeo sincronitzat</span>
                <span class="pill">Filtres configurables</span>
            </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

if df_full.empty:
    st.info("Encara no hi ha esdeveniments. Executa `python main.py` per generar dades a la carpeta `datos/`.")
    st.stop()

# --- BARRA LATERAL: FILTRES ---

st.sidebar.header("Panell de filtres")
st.sidebar.caption("Ajusta els filtres sense recarregar la sessió.")

df = df_full.copy()

if "camera_id" in df.columns:
    camaras = sorted(df["camera_id"].dropna().unique())
    cam_sel = st.sidebar.selectbox("Càmera (per a vistes filtrades)", ["TOTES"] + camaras)
    if cam_sel != "TOTES":
        df = df[df["camera_id"] == cam_sel]
else:
    cam_sel = "N/A"
    st.sidebar.markdown("*No hi ha el camp `camera_id` a les dades*")

if "fecha" in df.columns and df["fecha"].notna().any():
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    rango = st.sidebar.date_input(
        "Rang de dates",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    if isinstance(rango, tuple) and len(rango) == 2:
        ini, fin = rango
        df = df[(df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin)]

st.sidebar.button("Refresca les dades", on_click=lambda: st.cache_data.clear())
st.sidebar.divider()

st.sidebar.download_button(
    label="Descarrega CSV complet (totes les càmeres)",
    data=df_full.to_csv(index=False).encode("utf-8"),
    file_name=f"esdeveniments_complets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)

if df.empty:
    st.warning("No hi ha esdeveniments que compleixin els filtres seleccionats.")
    st.stop()

# --- MÈTRIQUES PRINCIPALS ---

st.markdown('<div class="section-title">Resum executiu</div>', unsafe_allow_html=True)

entradas_global = 0
salidas_global = 0
if "zone" in df_full.columns:
    entradas_global = int((df_full["zone"] == "entry").sum())
    salidas_global = int((df_full["zone"] == "exit").sum())
aforo_global = abs(entradas_global - salidas_global)

entradas_cam = 0
salidas_cam = 0
if "zone" in df.columns:
    entradas_cam = int((df["zone"] == "entry").sum())
    salidas_cam = int((df["zone"] == "exit").sum())
aforo_cam = abs(entradas_cam - salidas_cam)

col1, col2, col3, col4 = st.columns(4)

with col1:
    metric_card("Esdeveniments (filtres actuals)", f"{len(df):,}".replace(",", "."), "Processats des de fitxers JSON locals")

if "direction" in df.columns:
    fw = int((df["direction"] == "forward").sum())
    bw = int((df["direction"] == "backward").sum())
else:
    fw = 0
    bw = 0

with col2:
    metric_card("Forward", fw, "Trànsit en sentit forward")
with col3:
    metric_card("Backward", bw, "Trànsit en sentit contrari")
with col4:
    metric_card("Ocupació global", aforo_global, "Entrades davant de sortides (totes les càmeres)")

if cam_sel != "TOTES":
    st.markdown(
        dedent(
            f"""
            <div class="soft-card" style="margin-top: 0.75rem;">
                <strong>Càmera activa:</strong> {cam_sel} · Ocupació amb filtres:
                <span style="color: var(--accent)">{aforo_cam}</span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# --- PESTANYES DE CONTINGUT ---

st.markdown('<div class="section-title">Panell d\'anàlisi</div>', unsafe_allow_html=True)
st.caption("Explora mètriques agregades, sèries temporals, taules d'esdeveniments i vídeos associats.")

tab_resumen, tab_tiempo, tab_eventos, tab_video = st.tabs(
    ["Resum", "Evolució temporal", "Esdeveniments", "Vídeo"]
)

# --- PESTANYA: RESUM ---

with tab_resumen:
    # Ocupació per càmera en el temps (totes les càmeres)
    if "fecha" in df.columns and df["fecha"].notna().any() and "zone" in df.columns and "camera_id" in df.columns:
        df_tmp_res = df.set_index("fecha").sort_index()
        st.subheader("Ocupació per càmera en el temps (totes les càmeres)")

        df_aforo_cam = df_tmp_res[df_tmp_res["zone"].isin(["entry", "exit"])].copy()

        entradas_cam_t = (
            df_aforo_cam[df_aforo_cam["zone"] == "entry"]
            .groupby("camera_id")
            .resample("45S")
            .size()
            .rename("entrades")
        )
        salidas_cam_t = (
            df_aforo_cam[df_aforo_cam["zone"] == "exit"]
            .groupby("camera_id")
            .resample("45S")
            .size()
            .rename("sortides")
        )

        aforo_cam_t = pd.concat([entradas_cam_t, salidas_cam_t], axis=1).fillna(0)
        aforo_cam_t["aforament_instantani"] = (aforo_cam_t["entrades"] - aforo_cam_t["sortides"]).abs()
        aforo_cam_t["aforament_acumulat"] = (
            aforo_cam_t.groupby("camera_id")["aforament_instantani"].cumsum()
        )

        aforo_cam_plot = aforo_cam_t["aforament_acumulat"].reset_index()
        aforo_cam_plot.columns = ["camera_id", "fecha", "aforament_acumulat"]

        fig_aforo_cam_res = px.line(
            aforo_cam_plot,
            x="fecha",
            y="aforament_acumulat",
            color="camera_id",
            line_shape="spline",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_aforo_cam_res.update_layout(
            height=280,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e8edf7",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            legend_title_text="Càmera",
        )
        st.plotly_chart(fig_aforo_cam_res, use_container_width=True)
    else:
        st.info("No es pot calcular l'ocupació per càmera en el temps (manca `fecha`, `zone` o `camera_id`).")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Esdeveniments per vídeo (totes les càmeres)")
        if "video_file" in df_full.columns:
            counts = (
                df_full["video_file"]
                .astype(str)
                .value_counts()
                .rename_axis("video_file")
                .reset_index(name="esdeveniments")
            )
            st.dataframe(counts, use_container_width=True, height=250)
        else:
            st.write("No hi ha el camp `video_file` a les dades.")

    with col_b:
        st.subheader("Ocupació per càmera (entrades - sortides)")
        if "camera_id" in df_full.columns and "zone" in df_full.columns:
            aforo_cam_df = (
                df_full[df_full["zone"].isin(["entry", "exit"])]
                .groupby(["camera_id", "zone"])
                .size()
                .unstack(fill_value=0)
            )
            aforo_cam_df["aforament"] = abs(aforo_cam_df.get("entry", 0) - aforo_cam_df.get("exit", 0))
            st.dataframe(aforo_cam_df, use_container_width=True, height=250)
        else:
            st.write("No hi ha prou informació per calcular l'ocupació per càmera.")

# --- PESTANYA: EVOLUCIÓ TEMPORAL ---

with tab_tiempo:
    st.subheader("Esdeveniments al llarg del temps (filtres actuals)")

    if "fecha" in df.columns and df["fecha"].notna().any():
        df_tmp = df.set_index("fecha").sort_index()

        # Esdeveniments totals
        serie_total = df_tmp.resample("45S").size()
        serie_total_df = serie_total.reset_index()
        serie_total_df.columns = ["fecha", "esdeveniments"]
        fig_total = px.line(
            serie_total_df,
            x="fecha",
            y="esdeveniments",
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

        # Desglossament per direcció
        if "direction" in df_tmp.columns:
            st.subheader("Desglossament per direcció (entrada / sortida)")
            df_tmp["direcció"] = df_tmp["direction"].map(
                {"forward": "entrada", "backward": "sortida"}
                ).fillna(df_tmp["direction"])
            serie_dir = (
                df_tmp.groupby("direcció")
                .resample("45S")
                .size()
                .unstack(level=0)
                .fillna(0)
            )
            serie_dir_df = serie_dir.reset_index()
            serie_dir_melt = serie_dir_df.melt(
                id_vars="fecha",
                var_name="direcció",
                value_name="esdeveniments",
            )
            fig_dir = px.line(
                serie_dir_melt,
                x="fecha",
                y="esdeveniments",
                color="direcció",
                line_shape="spline",
                color_discrete_map={
                    "entrada": "#7bc5ff",
                    "sortida": "#8ef8c2",
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

        # Ocupació en el temps (entrades - sortides, filtres actuals)
        if "zone" in df_tmp.columns:
            st.subheader("Ocupació en el temps (entrades - sortides, filtres actuals)")

            entradas_t = (
                df_tmp[df_tmp["zone"] == "entry"]
                .resample("45S")
                .size()
                .rename("entrades")
            )
            salidas_t = (
                df_tmp[df_tmp["zone"] == "exit"]
                .resample("45S")
                .size()
                .rename("sortides")
            )

            aforo_df = pd.concat([entradas_t, salidas_t], axis=1).fillna(0)
            aforo_df["aforament_instantani"] = abs(aforo_df["entrades"] - aforo_df["sortides"])
            aforo_df["aforament_acumulat"] = aforo_df["aforament_instantani"].cumsum()

            aforo_plot = aforo_df[["aforament_acumulat"]].reset_index()
            aforo_plot.columns = ["fecha", "aforament_acumulat"]
            fig_aforo = px.line(
                aforo_plot,
                x="fecha",
                y="aforament_acumulat",
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
            st.info("No hi ha la columna `zone` (entry/exit), executa el detector actualitzat per calcular l'ocupació.")
    else:
        st.write("No es pot generar la sèrie temporal (no hi ha una columna `fecha` vàlida).")

# --- PESTANYA: ESDEVENIMENTS (TAULA) ---

with tab_eventos:
    st.subheader("Taula d'esdeveniments (filtres actuals)")

    cols_pref = ["fecha", "timestamp", "direction", "track_id", "camera_id", "video_file", "zone", "counter_type"]
    cols_existentes = [c for c in cols_pref if c in df.columns]
    cols_otras = [c for c in df.columns if c not in cols_existentes]
    cols_final = cols_existentes + cols_otras

    df_sorted = df.sort_values("fecha", ascending=False) if "fecha" in df.columns else df
    st.dataframe(df_sorted[cols_final].head(500), use_container_width=True, height=450)

    st.download_button(
        "Descarrega CSV filtrat",
        data=df_sorted[cols_final].to_csv(index=False).encode("utf-8"),
        file_name=f"esdeveniments_filtrats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# --- PESTANYA: VÍDEO ---

with tab_video:
    st.subheader("Revisió de vídeos")

    if "video_file" not in df_full.columns:
        st.info("Els esdeveniments no inclouen `video_file`. Assegura't que el detector el desi.")
    else:
        df_videos = df_full[df_full["video_file"].notna()].copy()
        df_videos["video_name"] = df_videos["video_file"].astype(str).apply(lambda p: Path(p).name)

        def is_valid_web(name: str) -> bool:
            if not name.endswith(".mp4"):
                return False
            if "_web" not in name:
                return False
            return (Path(VIDEO_DIR) / name).is_file()

        valid_names = sorted({n for n in df_videos["video_name"].unique() if is_valid_web(n)})

        if not valid_names:
            st.info("No s'han trobat vídeos compatibles (format web) a la carpeta de sortida.")
        else:
            video_sel = st.selectbox("Selecciona un vídeo", valid_names)

            path = get_video_path(video_sel)
            st.write(f"Ruta cercada per al vídeo: `{path or 'NO TROBAT'}`")
            if path:
                with st.container():
                    st.video(path)
                    st.markdown(
                        """
                        <style>
                        video {
                            max-height: 720px !important;
                            max-width: 100% !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.error(
                    f"No s'ha trobat el fitxer de vídeo compatible.\n"
                    f"- Cercat `{video_sel}` dins de `{VIDEO_DIR}`.\n"
                    f"- Assegura't que ffmpeg ha generat la versió _web."
                )