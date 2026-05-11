import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import hashlib
import hmac
from pathlib import Path
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Simulador PayZen", page_icon="💳", layout="wide")

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

USERS = {
    "comercial": {
        "name": "Comercial PayZen",
        "password_hash": "4d56be48304187c35b8616564f71980f17b78381ed4c27ff7b957656ca808be2"
    },
    "director": {
        "name": "Director",
        "password_hash": "ae12bd8f5543f2f2d6844dfa694fdb5570687f347d36c95be20a8ff5efa9c263"
    }
}


def check_password(username, password):
    username = username.strip().lower()
    if username not in USERS:
        return False
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(password_hash, USERS[username]["password_hash"])


def login_screen():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0F172A 45%, #082F49 100%);
        color: white;
    }
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .login-title {font-size: 48px;font-weight: 900;color: white;text-align: center;margin-top: 80px;}
    .login-subtitle {font-size: 20px;color: #CBD5E1;text-align: center;margin-bottom: 30px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-title">💳 Calculadora Comercial PayZen</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Acceso interno Globalinvest Advisors</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")
            if submitted:
                if check_password(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username.strip().lower()
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrecta")


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# ---------------------------------------------------
# FUNCIONES GENERALES
# ---------------------------------------------------

def h(code):
    st.markdown(code, unsafe_allow_html=True)


def money(value):
    return f"${value:,.0f}".replace(",", ".")


def number_fmt(value):
    return f"{value:,.0f}".replace(",", ".")


def percent(value):
    return f"{value:.2f}%"


def clean_number(value):
    try:
        return int(str(value).replace(".", "").replace(",", "").strip())
    except Exception:
        return None


def tarifa_adicional_por_rango(tx_adicionales):
    if tx_adicionales <= 0:
        return 0
    if tx_adicionales <= 500:
        return 506
    elif tx_adicionales <= 1000:
        return 440
    elif tx_adicionales <= 5000:
        return 385
    elif tx_adicionales <= 10000:
        return 363
    return 319


def tarifa_breb_payzen(tx_breb, r1, r2, r3):
    if tx_breb <= 0:
        return 0
    if tx_breb <= 10000:
        return r1
    elif tx_breb <= 100000:
        return r2
    return r3


def calcular_escenario(
    nombre,
    tx_tarjeta,
    tx_pse,
    tx_breb,
    ticket,
    fijo_actual_tarjeta,
    porcentaje_actual_tarjeta,
    porcentaje_banco_tarjeta,
    costo_pse_actual,
    costo_pse_payzen,
    costo_breb_actual,
    breb_r1,
    breb_r2,
    breb_r3,
    plan_mensual,
    tx_incluidas,
):
    tx_total = tx_tarjeta + tx_pse + tx_breb

    costo_actual_tarjeta = tx_tarjeta * (fijo_actual_tarjeta + (ticket * porcentaje_actual_tarjeta / 100))
    costo_actual_pse = tx_pse * costo_pse_actual
    costo_actual_breb = tx_breb * costo_breb_actual
    costo_actual_total = costo_actual_tarjeta + costo_actual_pse + costo_actual_breb

    tx_adicionales = max(tx_total - tx_incluidas, 0)
    tarifa_adicional = tarifa_adicional_por_rango(tx_adicionales)
    costo_tx_adicionales = tx_adicionales * tarifa_adicional

    costo_payzen_tarjeta = ticket * tx_tarjeta * porcentaje_banco_tarjeta / 100
    costo_payzen_pse = tx_pse * costo_pse_payzen
    tarifa_breb = tarifa_breb_payzen(tx_breb, breb_r1, breb_r2, breb_r3)
    costo_payzen_breb = tx_breb * tarifa_breb

    costo_payzen_total = (
        plan_mensual
        + costo_tx_adicionales
        + costo_payzen_tarjeta
        + costo_payzen_pse
        + costo_payzen_breb
    )

    ahorro = costo_actual_total - costo_payzen_total
    ahorro_anual = ahorro * 12
    ahorro_pct = (ahorro / costo_actual_total * 100) if costo_actual_total > 0 else 0
    payzen_pct = (costo_payzen_total / costo_actual_total * 100) if costo_actual_total > 0 else 0

    return {
        "Escenario": nombre,
        "Tx tarjeta": tx_tarjeta,
        "Tx PSE": tx_pse,
        "Tx Bre-B": tx_breb,
        "Transacciones": tx_total,
        "Pasarela actual": costo_actual_total,
        "Actual tarjeta": costo_actual_tarjeta,
        "Actual PSE": costo_actual_pse,
        "Actual Bre-B": costo_actual_breb,
        "PayZen": costo_payzen_total,
        "PayZen tarjeta": costo_payzen_tarjeta,
        "PayZen PSE": costo_payzen_pse,
        "PayZen Bre-B": costo_payzen_breb,
        "Mensualidad PayZen": plan_mensual,
        "Ahorro mensual": ahorro,
        "Ahorro anual": ahorro_anual,
        "PayZen %": payzen_pct,
        "Ahorro %": ahorro_pct,
        "Tx adicionales": tx_adicionales,
        "Tarifa adicional": tarifa_adicional,
        "Costo adicionales": costo_tx_adicionales,
        "Tarifa Bre-B PayZen": tarifa_breb,
    }


def distribuir_transacciones(tx_total, base_tarjeta, base_pse, base_breb):
    base_total = base_tarjeta + base_pse + base_breb
    if base_total <= 0:
        return 0, 0, 0

    tx_tarjeta = round(tx_total * base_tarjeta / base_total)
    tx_pse = round(tx_total * base_pse / base_total)
    tx_breb = tx_total - tx_tarjeta - tx_pse
    return max(tx_tarjeta, 0), max(tx_pse, 0), max(tx_breb, 0)


def grafica_base(fig, titulo_y="COP", altura=560):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=15),
        yaxis_title=titulo_y,
        legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="center", x=0.5, font=dict(color="white", size=15)),
        margin=dict(t=90, b=45, l=45, r=45),
        height=altura,
        hovermode="x unified",
    )
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.18)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    return fig


def buscar_logo():
    posibles = [
        Path("Logo_Globalinvest_PayZen.png"),
        Path("logo.png"),
        Path("Logo_Globalinvest_PayZen.jpg"),
        Path("logo.jpg"),
    ]
    for p in posibles:
        if p.exists():
            return p
    return None


DISCLAIMER = (
    "Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión "
    "y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no "
    "constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones "
    "comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos "
    "de terceros o modificaciones acordadas entre las partes."
)


def crear_pdf_resumen(df_pdf, plan, plan_mensual, tx_incluidas, creacion_tienda, logo_path):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    except ImportError:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Normal"], fontSize=11, leading=14, alignment=TA_LEFT, spaceAfter=8)
    small_style = ParagraphStyle("small", parent=styles["Normal"], fontSize=7, leading=8, alignment=TA_LEFT)
    center_style = ParagraphStyle("center", parent=styles["Normal"], fontSize=8, leading=10, alignment=TA_CENTER)

    elements = []

    header_data = [[Paragraph("PLAN ACTUAL CON COSTOS ACTUALES VS EL PLAN QUE PUEDES ESCOGER CON NOSOTROS", title_style), ""]]
    if logo_path and logo_path.exists():
        header_data[0][1] = Image(str(logo_path), width=1.25 * inch, height=0.55 * inch)
    header = Table(header_data, colWidths=[8.1 * inch, 1.7 * inch])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    elements.append(header)

    comparativo = [["Escenario", "Transacciones", "Pasarela actual", "PayZen", "Ahorro mensual", "Ahorro anual", "% ahorro"]]
    for _, r in df_pdf.iterrows():
        comparativo.append([
            r["Escenario"],
            number_fmt(r["Transacciones"]),
            money(r["Pasarela actual"]),
            money(r["PayZen"]),
            money(r["Ahorro mensual"]),
            money(r["Ahorro anual"]),
            percent(r["Ahorro %"]),
        ])

    table = Table(comparativo, repeatRows=1, colWidths=[1.65 * inch, 1.15 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch, 0.9 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D7E8F5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("AHORRO MENSUAL Y ANUAL QUE TIENES AL ESCOGER NUESTRA PASARELA PAYZEN", title_style))
    ahorro_data = [["Escenario", "Ahorro mensual", "Ahorro anual", "% ahorro"]]
    for _, r in df_pdf.iterrows():
        ahorro_data.append([r["Escenario"], money(r["Ahorro mensual"]), money(r["Ahorro anual"]), percent(r["Ahorro %"])])
    ahorro_table = Table(ahorro_data, repeatRows=1, colWidths=[2.5 * inch, 2.0 * inch, 2.0 * inch, 1.2 * inch])
    ahorro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D8FE1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#EAF6FF")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    elements.append(ahorro_table)
    elements.append(Spacer(1, 10))

    plan_txt = f"Plan seleccionado: {plan} | Mensualidad: {money(plan_mensual)} | Tx incluidas: {number_fmt(tx_incluidas)} | Creación tienda: {money(creacion_tienda)} | Fecha: {datetime.now().strftime('%Y-%m-%d')}"
    elements.append(Paragraph(plan_txt, center_style))
    elements.append(Spacer(1, 7))
    elements.append(Paragraph(DISCLAIMER, small_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------
# ESTILOS
# ---------------------------------------------------

h("""
<style>
.stApp {background: linear-gradient(135deg, #020617 0%, #0F172A 45%, #082F49 100%); color: white;}
[data-testid="stHeader"] {background: rgba(0,0,0,0); height: 0rem;}
.block-container {padding-top: 0.8rem; padding-bottom: 2rem; max-width: 1450px;}
section[data-testid="stSidebar"] {background-color: #E5E7EB;}
.title {font-size: 50px; font-weight: 900; color: white; line-height: 1.1; margin-top: 8px;}
.subtitle {color: #CBD5E1; font-size: 21px; margin-bottom: 38px;}
.section-title {font-size: 32px; font-weight: 900; color: white; margin-top: 36px; margin-bottom: 22px;}
.card, .card-plan, .card-compare, .card-saving {border-radius: 24px; padding: 26px; box-shadow: 0px 8px 30px rgba(0,0,0,0.30); border: 1px solid rgba(255,255,255,0.10);}
.card {background: rgba(255,255,255,0.06); min-height: 230px;}
.card-plan {background: linear-gradient(135deg, #2563EB, #06B6D4); min-height: 230px;}
.card-compare {background: rgba(255,255,255,0.06); min-height: 390px;}
.card-saving {background: linear-gradient(135deg, #2563EB, #06B6D4); min-height: 330px;}
.label {color: #CBD5E1; text-transform: uppercase; letter-spacing: 1px; font-size: 13px; font-weight: 800;}
.label-white {color: white; text-transform: uppercase; letter-spacing: 1px; font-size: 13px; font-weight: 800;}
.big-number {font-size: 38px; font-weight: 900; color: #38BDF8; margin-top: 16px; line-height: 1.15;}
.big-number-white {font-size: 38px; font-weight: 900; color: white; margin-top: 16px; line-height: 1.15;}
.big-number-orange {font-size: 38px; font-weight: 900; color: #F97316; margin-top: 16px; line-height: 1.15;}
.big-number-green {font-size: 38px; font-weight: 900; color: #22C55E; margin-top: 16px; line-height: 1.15;}
.orange-inline {color: #F97316; font-size: 38px; font-weight: 900; margin-top: 2px; line-height: 1.15;}
.plus-inline {color: white; font-size: 34px; font-weight: 900; margin-top: 2px; line-height: 1.15;}
.small-text {color: #CBD5E1; font-size: 16px; line-height: 1.55;}
.small-text-white {color: white; font-size: 16px; line-height: 1.55;}
.actual-label {color: #F97316; font-size: 20px; font-weight: 900; margin-top: 22px;}
.payzen-label {color: #38BDF8; font-size: 20px; font-weight: 900; margin-top: 22px;}
.annual-text {color: white; font-size: 23px; font-weight: 900; margin-top: 18px; line-height: 1.4;}
.percent-text {color: white; font-size: 38px; font-weight: 900; margin-top: 14px;}
.channel-pill {display:inline-block; background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.28); color:#BAE6FD; padding:6px 10px; border-radius:999px; font-size:13px; font-weight:800; margin:4px 6px 0 0;}
.math-box {background: rgba(15,23,42,0.90); border: 1px solid rgba(148,163,184,0.22); border-radius: 18px; padding: 22px; margin-top: 12px; margin-bottom: 16px;}
.math-title {color: #38BDF8; font-size: 22px; font-weight: 900; margin-bottom: 14px;}
.math-line {color: white; font-size: 19px; line-height: 1.65; font-weight: 600;}
.math-result {color: #38BDF8; font-size: 27px; font-weight: 900; margin-top: 12px;}
.math-result-orange {color: #F97316; font-size: 27px; font-weight: 900; margin-top: 12px;}
.disclaimer {font-size: 11px; color: #CBD5E1; line-height: 1.45; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.10); padding: 14px 16px; border-radius: 14px; margin-top: 22px;}
div[data-testid="stExpander"] {background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10); border-radius: 16px;}
div[data-testid="stExpander"] details summary {color: #38BDF8 !important; font-weight: 800; font-size: 18px;}
div[data-testid="stExpander"] details[open] summary {color: #38BDF8 !important; background: rgba(56,189,248,0.10) !important;}
</style>
""")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:
    current_user = st.session_state.get("username", "")
    st.success(f"Sesión activa: {USERS.get(current_user, {'name': 'Usuario'})['name']}")
    if st.button("Cerrar sesión"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.header("⚙️ Parámetros base")
    ticket_promedio = st.number_input("Ticket promedio tarjeta", min_value=0, value=60000, step=10000)

    st.divider()
    st.subheader("Canales de pago")
    usar_tarjeta = st.checkbox("Tarjeta crédito / débito", value=True)
    usar_pse = st.checkbox("PSE", value=False)
    usar_breb = st.checkbox("Bre-B", value=False)

    st.caption("Las transacciones incluidas del plan se calculan sobre la suma de los canales activos.")

    tx_tarjeta_actual = 0
    tx_pse_actual = 0
    tx_breb_actual = 0

    if usar_tarjeta:
        st.markdown("**Tarjeta crédito / débito**")
        tx_tarjeta_actual = st.number_input("Transacciones tarjeta", min_value=0, value=350, step=50)
        costo_fijo_actual = st.number_input("Costo fijo actual por tx tarjeta", min_value=0, value=750, step=50)
        porcentaje_actual = st.number_input("% actual pasarela tarjeta", min_value=0.0, value=2.90, step=0.10)
        porcentaje_banco = st.number_input("% adquirencia banco tarjeta PayZen", min_value=0.0, value=1.84, step=0.01)
    else:
        costo_fijo_actual = 0
        porcentaje_actual = 0.0
        porcentaje_banco = 0.0

    if usar_pse:
        st.markdown("**PSE**")
        tx_pse_actual = st.number_input("Transacciones PSE", min_value=0, value=100, step=50)
        costo_pse_actual = st.number_input("Costo PSE actual por tx", min_value=0, value=400, step=50)
        costo_pse_payzen = st.number_input("Costo PSE PayZen por tx", min_value=0, value=400, step=50)
    else:
        costo_pse_actual = 0
        costo_pse_payzen = 0

    if usar_breb:
        st.markdown("**Bre-B**")
        tx_breb_actual = st.number_input("Transacciones Bre-B", min_value=0, value=0, step=50)
        costo_breb_actual = st.number_input("Costo Bre-B actual por tx", min_value=0, value=600, step=50)
        st.caption("Tarifa Bre-B PayZen editable por rango")
        breb_r1 = st.number_input("Bre-B PayZen 1 - 10.000 tx", min_value=0, value=600, step=50)
        breb_r2 = st.number_input("Bre-B PayZen 10.001 - 100.000 tx", min_value=0, value=550, step=50)
        breb_r3 = st.number_input("Bre-B PayZen 100.001 en adelante", min_value=0, value=500, step=50)
    else:
        costo_breb_actual = 0
        breb_r1 = 0
        breb_r2 = 0
        breb_r3 = 0

    st.divider()
    st.subheader("Plan PayZen")
    plan = st.selectbox("Selecciona el plan", ["PayZen Pro", "PayZen Basic"])

    st.divider()
    tx_total_actual = tx_tarjeta_actual + tx_pse_actual + tx_breb_actual
    proyecciones_texto = st.text_area(
        "Proyecciones de transacciones totales",
        value="2000\n3000",
        help="La proyección total se distribuye según la mezcla actual de canales. Ejemplo: si hoy 70% es tarjeta y 30% es PSE, la proyección conserva esa proporción."
    )

# ---------------------------------------------------
# PLANES
# ---------------------------------------------------

if plan == "PayZen Pro":
    plan_mensual = 340000
    tx_incluidas = 500
    creacion_tienda = 755500
else:
    plan_mensual = 126500
    tx_incluidas = 100
    creacion_tienda = 319000

# ---------------------------------------------------
# PROYECCIONES Y CÁLCULOS
# ---------------------------------------------------

proyecciones = []
texto_limpio = proyecciones_texto.replace(",", "\n")
for linea in texto_limpio.splitlines():
    numero = clean_number(linea)
    if numero is not None and numero > 0:
        proyecciones.append(numero)
proyecciones = list(dict.fromkeys(proyecciones))

escenarios_tx = [("Actual", tx_tarjeta_actual, tx_pse_actual, tx_breb_actual)]
for tx_total in proyecciones:
    p_tarjeta, p_pse, p_breb = distribuir_transacciones(tx_total, tx_tarjeta_actual, tx_pse_actual, tx_breb_actual)
    escenarios_tx.append((f"Proyección {number_fmt(tx_total)} tx", p_tarjeta, p_pse, p_breb))

resultados = []
for nombre, tx_tarjeta, tx_pse, tx_breb in escenarios_tx:
    resultados.append(calcular_escenario(
        nombre,
        tx_tarjeta,
        tx_pse,
        tx_breb,
        ticket_promedio,
        costo_fijo_actual,
        porcentaje_actual,
        porcentaje_banco,
        costo_pse_actual,
        costo_pse_payzen,
        costo_breb_actual,
        breb_r1,
        breb_r2,
        breb_r3,
        plan_mensual,
        tx_incluidas,
    ))

df = pd.DataFrame(resultados)

# ---------------------------------------------------
# HEADER CON LOGO
# ---------------------------------------------------

logo_path = buscar_logo()
col_title, col_logo = st.columns([4, 1])
with col_title:
    h('<div class="title">💳 Simulador Comercial PayZen Basic / Pro</div>')
    h('<div class="subtitle">Comparativo de costos por canal entre pasarela actual vs PayZen</div>')
with col_logo:
    if logo_path:
        st.image(str(logo_path), use_container_width=True)

# ---------------------------------------------------
# PARÁMETROS BASE
# ---------------------------------------------------

h('<div class="section-title">📌 Parámetros base</div>')

c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    h('<div class="card">'
      '<div class="label">Ticket promedio tarjeta</div>'
      f'<div class="big-number">{money(ticket_promedio)}</div>'
      '<br><div class="small-text">Valor promedio usado para tarjeta crédito / débito.</div>'
      '</div>')

with c2:
    canales = []
    if usar_tarjeta:
        canales.append(f"Tarjeta: {number_fmt(tx_tarjeta_actual)}")
    if usar_pse:
        canales.append(f"PSE: {number_fmt(tx_pse_actual)}")
    if usar_breb:
        canales.append(f"Bre-B: {number_fmt(tx_breb_actual)}")
    canales_html = "".join([f'<span class="channel-pill">{c}</span>' for c in canales]) or '<span class="channel-pill">Sin canales activos</span>'
    h('<div class="card">'
      '<div class="label">Transacciones actuales</div>'
      f'<div class="big-number">{number_fmt(tx_total_actual)}</div>'
      f'<div>{canales_html}</div>'
      '</div>')

with c3:
    if usar_tarjeta:
        h('<div class="card">'
          '<div class="label">Pasarela actual tarjeta</div>'
          f'<div class="big-number-orange">{money(costo_fijo_actual)} <span class="plus-inline">+</span></div>'
          f'<div class="orange-inline">{percent(porcentaje_actual)}</div>'
          '<div class="small-text">por transacción</div>'
          '</div>')
    else:
        h('<div class="card">'
          '<div class="label">Pasarela actual tarjeta</div>'
          '<div class="big-number-orange">No aplica</div>'
          '<div class="small-text">Canal tarjeta desactivado.</div>'
          '</div>')

with c4:
    h('<div class="card-plan">'
      '<div class="label-white">Plan seleccionado</div>'
      f'<div class="big-number-white">{plan}</div>'
      f'<br><div class="small-text-white">Mensualidad: <b>{money(plan_mensual)}</b></div>'
      f'<div class="small-text-white">Tx incluidas: <b>{number_fmt(tx_incluidas)}</b></div>'
      f'<div class="small-text-white">Creación tienda: <b>{money(creacion_tienda)}</b></div>'
      '</div>')

# ---------------------------------------------------
# COMPARATIVO DE COSTOS
# ---------------------------------------------------

h('<div class="section-title">📊 Comparativo de costos</div>')

for start in range(0, len(df), 3):
    cols = st.columns(3, gap="large")
    for pos, (_, row) in enumerate(df.iloc[start:start + 3].iterrows()):
        with cols[pos]:
            h('<div class="card-compare">'
              f'<div class="label">{row["Escenario"]}</div>'
              f'<div class="small-text">Total tx: <b>{number_fmt(row["Transacciones"])}</b></div>'
              f'<div class="small-text">Tarjeta: {number_fmt(row["Tx tarjeta"])} | PSE: {number_fmt(row["Tx PSE"])} | Bre-B: {number_fmt(row["Tx Bre-B"])}</div>'
              f'<div class="actual-label">Pasarela actual</div>'
              f'<div class="big-number-orange">{money(row["Pasarela actual"])}</div>'
              f'<div class="small-text">Tarjeta: {money(row["Actual tarjeta"])}<br>PSE: {money(row["Actual PSE"])}<br>Bre-B: {money(row["Actual Bre-B"])}</div>'
              f'<div class="payzen-label">PayZen</div>'
              f'<div class="big-number">{money(row["PayZen"])}</div>'
              f'<div class="small-text">Mensualidad + adicionales: {money(row["Mensualidad PayZen"] + row["Costo adicionales"])}<br>Tarjeta: {money(row["PayZen tarjeta"])} | PSE: {money(row["PayZen PSE"])} | Bre-B: {money(row["PayZen Bre-B"])}</div>'
              f'<br><div class="small-text">Diferencia mensual estimada: <b>{money(row["Ahorro mensual"])}</b></div>'
              '</div>')

# ---------------------------------------------------
# AHORRO ESTIMADO
# ---------------------------------------------------

h('<div class="section-title">💰 Ahorro estimado</div>')

for start in range(0, len(df), 3):
    cols = st.columns(3, gap="large")
    for pos, (_, row) in enumerate(df.iloc[start:start + 3].iterrows()):
        with cols[pos]:
            h('<div class="card-saving">'
              f'<div class="label-white">{row["Escenario"]}</div>'
              f'<div class="big-number-white">{money(row["Ahorro mensual"])}</div>'
              '<div class="small-text-white">Ahorro mensual estimado</div>'
              f'<div class="annual-text">Ahorro anual: {money(row["Ahorro anual"])}</div>'
              '<br><div class="small-text-white">Si hoy pagas el 100% con tu pasarela actual, con PayZen ahorrarías:</div>'
              f'<div class="percent-text">{percent(row["Ahorro %"])}</div>'
              f'<div class="small-text-white">Costo PayZen frente al costo actual: <b>{percent(row["PayZen %"])}</b>.</div>'
              '</div>')

# ---------------------------------------------------
# BOTÓN PDF
# ---------------------------------------------------

h('<div class="section-title">🧾 Resumen comercial PDF</div>')
pdf_bytes = crear_pdf_resumen(df, plan, plan_mensual, tx_incluidas, creacion_tienda, logo_path)
if pdf_bytes is None:
    st.warning("Para generar PDF debes agregar reportlab en requirements.txt")
else:
    st.download_button(
        label="📥 Descargar resumen PDF",
        data=pdf_bytes,
        file_name=f"Resumen_Comercial_PayZen_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# ---------------------------------------------------
# GRÁFICA BARRAS
# ---------------------------------------------------

h('<div class="section-title">📈 Pasarela actual vs PayZen</div>')
fig = go.Figure()
fig.add_trace(go.Bar(x=df["Escenario"], y=df["Pasarela actual"], name="Pasarela actual", text=[money(v) for v in df["Pasarela actual"]], textposition="outside", marker_color="#F97316"))
fig.add_trace(go.Bar(x=df["Escenario"], y=df["PayZen"], name="PayZen", text=[money(v) for v in df["PayZen"]], textposition="outside", marker_color="#06B6D4"))
max_y = max(df["Pasarela actual"].max(), df["PayZen"].max()) if len(df) else 0
fig.update_layout(barmode="group", yaxis=dict(range=[0, max_y * 1.22 if max_y else 1]))
fig = grafica_base(fig, titulo_y="Costo mensual COP", altura=560)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# GRÁFICA LÍNEA
# ---------------------------------------------------

h('<div class="section-title">📉 Evolución del costo mensual</div>')
fig_line = go.Figure()
fig_line.add_trace(go.Scatter(
    x=df["Escenario"], y=df["Pasarela actual"], name="Pasarela actual", mode="lines+markers",
    line=dict(width=4, color="#F97316"), marker=dict(size=12, color="#F97316"),
    customdata=df[["Ahorro mensual", "Ahorro %", "PayZen"]],
    hovertemplate="<b>%{x}</b><br>Pasarela actual: $%{y:,.0f}<br>PayZen: $%{customdata[2]:,.0f}<br>Ahorro mensual: $%{customdata[0]:,.0f}<br>Ahorro porcentual: %{customdata[1]:.2f}%<extra></extra>"
))
fig_line.add_trace(go.Scatter(
    x=df["Escenario"], y=df["PayZen"], name="PayZen", mode="lines+markers",
    line=dict(width=4, color="#06B6D4"), marker=dict(size=12, color="#06B6D4"),
    customdata=df[["Ahorro mensual", "Ahorro %", "Pasarela actual"]],
    hovertemplate="<b>%{x}</b><br>PayZen: $%{y:,.0f}<br>Pasarela actual: $%{customdata[2]:,.0f}<br>Ahorro mensual: $%{customdata[0]:,.0f}<br>Ahorro porcentual: %{customdata[1]:.2f}%<extra></extra>"
))
fig_line = grafica_base(fig_line, titulo_y="Costo mensual COP", altura=560)
st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------
# DETALLE MATEMÁTICO
# ---------------------------------------------------

h('<div class="section-title">🧮 Detalle matemático</div>')

for row in resultados:
    titulo_expander = f"Ver cálculo de {row['Escenario']} - {number_fmt(row['Transacciones'])} tx"
    with st.expander(titulo_expander):
        h('<div class="math-box">'
          '<div class="math-title">Pasarela actual</div>'
          f'<div class="math-line">Tarjeta: {number_fmt(row["Tx tarjeta"])} × ({money(costo_fijo_actual)} + ({percent(porcentaje_actual)} × {money(ticket_promedio)})) = {money(row["Actual tarjeta"])}</div>'
          f'<div class="math-line">PSE: {number_fmt(row["Tx PSE"])} × {money(costo_pse_actual)} = {money(row["Actual PSE"])}</div>'
          f'<div class="math-line">Bre-B: {number_fmt(row["Tx Bre-B"])} × {money(costo_breb_actual)} = {money(row["Actual Bre-B"])}</div>'
          f'<div class="math-result-orange">Total actual = {money(row["Pasarela actual"])}</div>'
          '</div>')

        h('<div class="math-box">'
          '<div class="math-title">PayZen</div>'
          f'<div class="math-line">Mensualidad: {money(plan_mensual)}</div>'
          f'<div class="math-line">Tx adicionales: {number_fmt(row["Tx adicionales"])} × {money(row["Tarifa adicional"])} = {money(row["Costo adicionales"])}</div>'
          f'<div class="math-line">Tarjeta: {money(ticket_promedio)} × {number_fmt(row["Tx tarjeta"])} × {percent(porcentaje_banco)} = {money(row["PayZen tarjeta"])}</div>'
          f'<div class="math-line">PSE: {number_fmt(row["Tx PSE"])} × {money(costo_pse_payzen)} = {money(row["PayZen PSE"])}</div>'
          f'<div class="math-line">Bre-B: {number_fmt(row["Tx Bre-B"])} × {money(row["Tarifa Bre-B PayZen"])} = {money(row["PayZen Bre-B"])}</div>'
          f'<div class="math-result">Total PayZen = {money(row["PayZen"])}</div>'
          '</div>')

        h('<div class="math-box">'
          '<div class="math-title">Ahorro</div>'
          f'<div class="math-line">{money(row["Pasarela actual"])} - {money(row["PayZen"])}</div>'
          f'<div class="math-result">Ahorro mensual: {money(row["Ahorro mensual"])}</div>'
          f'<div class="math-result">Ahorro anual: {money(row["Ahorro anual"])}</div>'
          f'<div class="math-line">Porcentaje de ahorro: <b>{percent(row["Ahorro %"])}</b></div>'
          '</div>')

# ---------------------------------------------------
# TABLA RESUMEN
# ---------------------------------------------------

h('<div class="section-title">📋 Tabla resumen</div>')
df_mostrar = df.copy()
columnas_dinero = [
    "Pasarela actual", "Actual tarjeta", "Actual PSE", "Actual Bre-B", "PayZen", "PayZen tarjeta", "PayZen PSE", "PayZen Bre-B",
    "Mensualidad PayZen", "Ahorro mensual", "Ahorro anual", "Costo adicionales", "Tarifa adicional", "Tarifa Bre-B PayZen"
]
for col in columnas_dinero:
    df_mostrar[col] = df_mostrar[col].apply(money)
df_mostrar["PayZen %"] = df_mostrar["PayZen %"].apply(percent)
df_mostrar["Ahorro %"] = df_mostrar["Ahorro %"].apply(percent)
for col in ["Transacciones", "Tx tarjeta", "Tx PSE", "Tx Bre-B", "Tx adicionales"]:
    df_mostrar[col] = df_mostrar[col].apply(number_fmt)
st.dataframe(df_mostrar, use_container_width=True)

h(f'<div class="disclaimer">{DISCLAIMER}</div>')
