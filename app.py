import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import hashlib
import hmac
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    .login-title {
        font-size: 48px;
        font-weight: 900;
        color: white;
        text-align: center;
        margin-top: 80px;
    }
    .login-subtitle {
        font-size: 20px;
        color: #CBD5E1;
        text-align: center;
        margin-bottom: 30px;
    }
.stTextInput label {
        color: #38BDF8 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    .stFormSubmitButton button {
        background: #374151 !important;
        color: #38BDF8 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(56,189,248,0.50) !important;
        font-weight: 800 !important;
        padding: 10px 28px !important;
        min-width: 120px !important;
    }

    .stFormSubmitButton button:hover {
        background: #4B5563 !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(56,189,248,0.90) !important;
    }

    .stFormSubmitButton button p {
        color: #38BDF8 !important;
        font-weight: 800 !important;
    }
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
    except:
        return None

def tarifa_adicional_por_plan(tx_adicionales, tarifa_adicional_plan):
    if tx_adicionales <= 0:
        return 0
    return tarifa_adicional_plan

def calcular_pasarela_actual(ticket, tx, fijo, porcentaje):
    variable_unitaria = ticket * porcentaje / 100
    costo_por_tx = fijo + variable_unitaria
    total = tx * costo_por_tx
    return total, costo_por_tx, variable_unitaria

def calcular_payzen(ticket, tx, plan_mensual, tx_incluidas, porcentaje_banco, tarifa_adicional_plan):
    tx_adicionales = max(tx - tx_incluidas, 0)
    tarifa_adicional = tarifa_adicional_por_plan(tx_adicionales, tarifa_adicional_plan)
    costo_tx_adicionales = tx_adicionales * tarifa_adicional
    costo_banco = ticket * tx * porcentaje_banco / 100
    total = plan_mensual + costo_tx_adicionales + costo_banco

    return {
        "tx_adicionales": tx_adicionales,
        "tarifa_adicional": tarifa_adicional,
        "costo_tx_adicionales": costo_tx_adicionales,
        "costo_banco": costo_banco,
        "total": total
    }

def tarifa_por_rango_breb(tx, r1_ini, r1_fin, r1_tarifa, r2_ini, r2_fin, r2_tarifa, r3_ini, r3_fin, r3_tarifa):
    if tx <= 0:
        return 0

    if r1_ini <= tx <= r1_fin:
        return r1_tarifa

    if r2_ini <= tx <= r2_fin:
        return r2_tarifa

    if r3_ini <= tx <= r3_fin:
        return r3_tarifa

    return r3_tarifa

def calcular_costos_canales(ticket_tc, ticket_pse, ticket_breb, tx_tc, tx_pse, tx_breb, fijo_tc, pct_actual_tc, pct_banco_tc,
                            plan_mensual, tx_incluidas, tarifa_adicional_plan, costo_pse_payzen,
                            breb_r1_ini, breb_r1_fin, breb_r1_tarifa,
                            breb_r2_ini, breb_r2_fin, breb_r2_tarifa,
                            breb_r3_ini, breb_r3_fin, breb_r3_tarifa):
    total_tx = tx_tc + tx_pse + tx_breb

    # Competencia / pasarela actual:
    # Se aplica el esquema global informado por el cliente: fijo + porcentaje.
    # No se suma un costo PSE ni Bre-B aparte porque usualmente el cliente entrega una tarifa "full".
    costo_actual_tc, costo_actual_por_tx, variable_actual = calcular_pasarela_actual(
        ticket_tc, tx_tc, fijo_tc, pct_actual_tc
    )

    costo_actual_pse, _, _ = calcular_pasarela_actual(
        ticket_pse, tx_pse, fijo_tc, pct_actual_tc
    )

    costo_actual_breb, _, _ = calcular_pasarela_actual(
        ticket_breb, tx_breb, fijo_tc, pct_actual_tc
    )

    costo_actual_total = costo_actual_tc + costo_actual_pse + costo_actual_breb

    # PayZen:
    # Mensualidad + transacciones adicionales sobre el total de canales + adquirencia/costos por canal.
    tx_adicionales = max(total_tx - tx_incluidas, 0)
    tarifa_adicional = tarifa_adicional_por_plan(tx_adicionales, tarifa_adicional_plan)
    costo_tx_adicionales = tx_adicionales * tarifa_adicional

    costo_banco_tc = ticket_tc * tx_tc * pct_banco_tc / 100
    costo_payzen_pse = tx_pse * costo_pse_payzen

    tarifa_breb_payzen = tarifa_por_rango_breb(
        tx_breb,
        breb_r1_ini,
        breb_r1_fin,
        breb_r1_tarifa,
        breb_r2_ini,
        breb_r2_fin,
        breb_r2_tarifa,
        breb_r3_ini,
        breb_r3_fin,
        breb_r3_tarifa
    )
    costo_payzen_breb = tx_breb * tarifa_breb_payzen

    payzen_total = (
        plan_mensual
        + costo_tx_adicionales
        + costo_banco_tc
        + costo_payzen_pse
        + costo_payzen_breb
    )

    return {
        "total_tx": total_tx,
        "costo_actual_total": costo_actual_total,
        "costo_actual_tc": costo_actual_tc,
        "costo_actual_pse": costo_actual_pse,
        "costo_actual_breb": costo_actual_breb,
        "costo_actual_por_tx": costo_actual_por_tx,
        "variable_actual": variable_actual,
        "tx_adicionales": tx_adicionales,
        "tarifa_adicional": tarifa_adicional,
        "costo_tx_adicionales": costo_tx_adicionales,
        "costo_banco": costo_banco_tc,
        "costo_payzen_pse": costo_payzen_pse,
        "tarifa_breb_payzen": tarifa_breb_payzen,
        "costo_payzen_breb": costo_payzen_breb,
        "payzen_total": payzen_total
    }

def grafica_base(fig, titulo_y="COP", altura=560):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=15),
        yaxis_title=titulo_y,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.10,
            xanchor="center",
            x=0.5,
            font=dict(color="white", size=15)
        ),
        margin=dict(t=90, b=45, l=45, r=45),
        height=altura,
        hovermode="x unified"
    )
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.18)")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    return fig

# ---------------------------------------------------
# ESTILOS
# ---------------------------------------------------

h("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617 0%, #0F172A 45%, #082F49 100%);
    color: white;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
    height: 0rem;
}

.block-container {
    padding-top: 0.8rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background-color: #E5E7EB;
}

.title {
    font-size: 54px;
    font-weight: 900;
    color: white;
    line-height: 1.1;
    margin-top: 8px;
}

.subtitle {
    color: #CBD5E1;
    font-size: 21px;
    margin-bottom: 45px;
}

.section-title {
    font-size: 34px;
    font-weight: 900;
    color: white;
    margin-top: 38px;
    margin-bottom: 24px;
}

.card, .card-plan, .card-compare, .card-saving, .growth-card {
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.30);
    border: 1px solid rgba(255,255,255,0.10);
}

.card {
    background: rgba(255,255,255,0.06);
    min-height: 230px;
}

.card-plan {
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    min-height: 230px;
}

.card-compare {
    background: rgba(255,255,255,0.06);
    min-height: 360px;
}

.card-saving {
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    min-height: 360px;
}

.growth-card {
    background: rgba(255,255,255,0.06);
    min-height: 190px;
}

.label {
    color: #CBD5E1;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 13px;
    font-weight: 800;
}

.label-white {
    color: white;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 13px;
    font-weight: 800;
}

.big-number {
    font-size: 38px;
    font-weight: 900;
    color: #38BDF8;
    margin-top: 16px;
    line-height: 1.15;
}

.big-number-white {
    font-size: 38px;
    font-weight: 900;
    color: white;
    margin-top: 16px;
    line-height: 1.15;
}

.big-number-orange {
    font-size: 38px;
    font-weight: 900;
    color: #F97316;
    margin-top: 16px;
    line-height: 1.15;
}

.big-number-green {
    font-size: 38px;
    font-weight: 900;
    color: #22C55E;
    margin-top: 16px;
    line-height: 1.15;
}

.orange-inline {
    color: #F97316;
    font-size: 38px;
    font-weight: 900;
    margin-top: 4px;
    line-height: 1.15;
}

.small-text {
    color: #CBD5E1;
    font-size: 16px;
    line-height: 1.55;
}

.small-text-white {
    color: white;
    font-size: 16px;
    line-height: 1.55;
}

.actual-label {
    color: #F97316;
    font-size: 20px;
    font-weight: 900;
    margin-top: 26px;
}

.payzen-label {
    color: #38BDF8;
    font-size: 20px;
    font-weight: 900;
    margin-top: 26px;
}

.annual-text {
    color: white;
    font-size: 23px;
    font-weight: 900;
    margin-top: 18px;
    line-height: 1.4;
}

.percent-text {
    color: white;
    font-size: 38px;
    font-weight: 900;
    margin-top: 14px;
}

.math-box {
    background: rgba(15,23,42,0.90);
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 18px;
    padding: 22px;
    margin-top: 12px;
    margin-bottom: 16px;
}

.math-title {
    color: #38BDF8;
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 14px;
}

.math-line {
    color: white;
    font-size: 20px;
    line-height: 1.65;
    font-weight: 600;
}

.math-result {
    color: #38BDF8;
    font-size: 28px;
    font-weight: 900;
    margin-top: 12px;
}

.math-result-orange {
    color: #F97316;
    font-size: 28px;
    font-weight: 900;
    margin-top: 12px;
}

div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
}

div[data-testid="stExpander"] details summary {
    color: #38BDF8 !important;
    font-weight: 800;
    font-size: 18px;
}

div[data-testid="stExpander"] details[open] summary {
    color: #38BDF8 !important;
    background: rgba(56,189,248,0.10) !important;
}

.disclaimer {
    color: rgba(255,255,255,0.62);
    font-size: 11px;
    line-height: 1.45;
    margin-top: 22px;
    margin-bottom: 10px;
}

.stDownloadButton button {
    background: #374151 !important;
    color: #38BDF8 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(56,189,248,0.45) !important;
    font-weight: 800 !important;
}
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

    st.header("⚙️ Parámetros")

    # ---------------------------------------------------
    # DISTRIBUCIÓN DE TRANSACCIONES
    # ---------------------------------------------------

    st.subheader("Distribución de transacciones")

    modo_transacciones = st.radio(
        "¿Cómo quieres ingresar las transacciones?",
        ["Por número de transacciones", "Por porcentaje sobre total"],
        horizontal=False
    )

    activar_tc = st.checkbox("Activar Tarjetas crédito / débito", value=True)
    activar_pse = st.checkbox("Activar PSE", value=False)
    activar_breb = st.checkbox("Activar Bre-B", value=False)

    if modo_transacciones == "Por número de transacciones":
        if activar_tc:
            tx_tc_actual = st.number_input("Transacciones TC", min_value=0, value=350, step=50)
        else:
            tx_tc_actual = 0

        if activar_pse:
            tx_pse_actual = st.number_input("Transacciones PSE", min_value=0, value=0, step=50)
        else:
            tx_pse_actual = 0

        if activar_breb:
            tx_breb_actual = st.number_input("Transacciones Bre-B", min_value=0, value=0, step=50)
        else:
            tx_breb_actual = 0

        total_transacciones_base = tx_tc_actual + tx_pse_actual + tx_breb_actual

        pct_tc = (tx_tc_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0
        pct_pse = (tx_pse_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0
        pct_breb = (tx_breb_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0

    else:
        total_transacciones_base = st.number_input("Total transacciones", min_value=0, value=4000, step=100)

        if activar_tc:
            pct_tc = st.number_input("% Tarjetas", min_value=0.0, max_value=100.0, value=30.0, step=1.0)
        else:
            pct_tc = 0.0

        if activar_pse:
            pct_pse = st.number_input("% PSE", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
        else:
            pct_pse = 0.0

        if activar_breb:
            pct_breb = st.number_input("% Bre-B", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        else:
            pct_breb = 0.0

        suma_pct = pct_tc + pct_pse + pct_breb

        if total_transacciones_base > 0 and abs(suma_pct - 100) > 0.01:
            st.warning(f"Los porcentajes activos suman {suma_pct:.2f}%. Lo ideal es que sumen 100%.")

        tx_tc_actual = int(round(total_transacciones_base * pct_tc / 100)) if activar_tc else 0
        tx_pse_actual = int(round(total_transacciones_base * pct_pse / 100)) if activar_pse else 0
        tx_breb_actual = max(total_transacciones_base - tx_tc_actual - tx_pse_actual, 0) if activar_breb else int(round(total_transacciones_base * pct_breb / 100))

    st.caption(
        f"Distribución calculada: TC {number_fmt(tx_tc_actual)} | "
        f"PSE {number_fmt(tx_pse_actual)} | Bre-B {number_fmt(tx_breb_actual)} | "
        f"Total {number_fmt(tx_tc_actual + tx_pse_actual + tx_breb_actual)}"
    )

    # ---------------------------------------------------
    # TICKET PROMEDIO
    # ---------------------------------------------------

    st.divider()
    st.subheader("Ticket promedio")

    modo_ticket = st.radio(
        "¿Cómo quieres manejar el ticket promedio?",
        ["Un solo ticket para todos los canales", "Ticket diferente por canal"],
        horizontal=False
    )

    if modo_ticket == "Un solo ticket para todos los canales":
        ticket_promedio = st.number_input("Ticket promedio general", min_value=0, value=60000, step=10000)
        ticket_tc = ticket_promedio
        ticket_pse = ticket_promedio
        ticket_breb = ticket_promedio
    else:
        ticket_tc = st.number_input("Ticket promedio TC", min_value=0, value=60000, step=10000)
        ticket_pse = st.number_input("Ticket promedio PSE", min_value=0, value=40000, step=10000)
        ticket_breb = st.number_input("Ticket promedio Bre-B", min_value=0, value=40000, step=10000)
        ticket_promedio = ticket_tc

    # ---------------------------------------------------
    # PASARELA ACTUAL
    # ---------------------------------------------------

    st.divider()
    st.subheader("Pasarela actual")

    costo_fijo_actual = st.number_input("Costo fijo actual por transacción", min_value=0, value=750, step=50)
    porcentaje_actual = st.number_input("% actual de la pasarela", min_value=0.0, value=2.90, step=0.10)

    st.caption("La pasarela actual se calcula con el esquema global: fijo + porcentaje aplicado al total de canales activos.")

    # ---------------------------------------------------
    # COSTOS ADQUIRENCIA / PROCESAMIENTO
    # ---------------------------------------------------

    st.divider()
    st.subheader("Costos adquirencia / procesamiento")

    if activar_tc:
        porcentaje_banco = st.number_input("% adquirencia banco TC", min_value=0.0, value=1.84, step=0.01)
    else:
        porcentaje_banco = 0.0

    if activar_pse:
        costo_pse_payzen = st.number_input("Costo PSE PayZen por tx", min_value=0, value=400, step=50)
    else:
        costo_pse_payzen = 0

    if activar_breb:
        st.divider()
        st.subheader("Rangos Bre-B PayZen")
        st.caption("Rangos editables según la negociación con cada cliente.")

        st.markdown("**Rango 1**")
        breb_r1_ini = st.number_input("Rango 1 inicial", min_value=0, value=1, step=1000)
        breb_r1_fin = st.number_input("Rango 1 final", min_value=breb_r1_ini, value=10000, step=1000)
        breb_r1_tarifa = st.number_input("Valor rango 1", min_value=0, value=600, step=50)

        st.markdown("**Rango 2**")
        breb_r2_ini = st.number_input("Rango 2 inicial", min_value=0, value=10001, step=1000)
        breb_r2_fin = st.number_input("Rango 2 final", min_value=breb_r2_ini, value=100000, step=5000)
        breb_r2_tarifa = st.number_input("Valor rango 2", min_value=0, value=550, step=50)

        st.markdown("**Rango 3**")
        breb_r3_ini = st.number_input("Rango 3 inicial", min_value=0, value=100001, step=10000)
        breb_r3_fin = st.number_input("Rango 3 final", min_value=breb_r3_ini, value=999999999, step=10000)
        breb_r3_tarifa = st.number_input("Valor rango 3", min_value=0, value=500, step=50)
    else:
        breb_r1_ini = 1
        breb_r1_fin = 10000
        breb_r1_tarifa = 600
        breb_r2_ini = 10001
        breb_r2_fin = 100000
        breb_r2_tarifa = 550
        breb_r3_ini = 100001
        breb_r3_fin = 999999999
        breb_r3_tarifa = 500

    # ---------------------------------------------------
    # PLAN PAYZEN
    # ---------------------------------------------------

    st.divider()
    st.subheader("Plan PayZen")

    PLANES_PAYZEN = {
        "PayZen Basic 100 tx": {"mensualidad": 126500, "tx_incluidas": 100, "tarifa_adicional": 505, "creacion_tienda": 319000},
        "PayZen Pro 500 tx": {"mensualidad": 324500, "tx_incluidas": 500, "tarifa_adicional": 440, "creacion_tienda": 755500},
        "PayZen Pro 5.000 tx": {"mensualidad": 1925000, "tx_incluidas": 5000, "tarifa_adicional": 385, "creacion_tienda": 755500},
        "PayZen Pro 10.000 tx": {"mensualidad": 3492500, "tx_incluidas": 10000, "tarifa_adicional": 349, "creacion_tienda": 755500},
        "PayZen Pro 15.000 tx": {"mensualidad": 3445000, "tx_incluidas": 15000, "tarifa_adicional": 297, "creacion_tienda": 755500},
        "PayZen Pro 25.000 tx": {"mensualidad": 7232500, "tx_incluidas": 25000, "tarifa_adicional": 289, "creacion_tienda": 755500},
        "PayZen Pro 50.000 tx": {"mensualidad": 14179000, "tx_incluidas": 50000, "tarifa_adicional": 284, "creacion_tienda": 755500},
        "PayZen Pro 100.000 tx": {"mensualidad": 27225000, "tx_incluidas": 100000, "tarifa_adicional": 272, "creacion_tienda": 755500},
        "PayZen Pro 200.000 tx": {"mensualidad": 52800000, "tx_incluidas": 200000, "tarifa_adicional": 264, "creacion_tienda": 755500},
    }

    plan = st.selectbox("Selecciona el plan", list(PLANES_PAYZEN.keys()), index=1)

    # ---------------------------------------------------
    # PROYECCIONES
    # ---------------------------------------------------

    st.divider()

    proyecciones_texto = st.text_area(
        "Proyecciones de transacciones totales",
        value="2000\n3000",
        help="Escribe el total de transacciones proyectadas por línea. La app mantendrá la distribución por canal."
    )


# ---------------------------------------------------
# PLANES
# ---------------------------------------------------

# Diccionario de planes definido en el sidebar.
# Cada plan tiene su propia mensualidad, transacciones incluidas y tarifa fija por transacción adicional.
plan_config = PLANES_PAYZEN[plan]
plan_mensual = plan_config["mensualidad"]
tx_incluidas = plan_config["tx_incluidas"]
tarifa_adicional_plan = plan_config["tarifa_adicional"]
creacion_tienda = plan_config["creacion_tienda"]

# ---------------------------------------------------
# PROYECCIONES
# ---------------------------------------------------

proyecciones = []
texto_limpio = proyecciones_texto.replace(",", "\n")

for linea in texto_limpio.splitlines():
    numero = clean_number(linea)
    if numero is not None and numero > 0:
        proyecciones.append(numero)

proyecciones = list(dict.fromkeys(proyecciones))

total_tx_base = tx_tc_actual + tx_pse_actual + tx_breb_actual

escenarios = [("Actual", total_tx_base)]

for tx in proyecciones:
    escenarios.append((f"Proyección {number_fmt(tx)} tx", tx))

# ---------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------

resultados = []

tx_base_canales = max(tx_tc_actual + tx_pse_actual + tx_breb_actual, 1)

def distribuir_transacciones(total_tx):
    if total_tx <= 0:
        return 0, 0, 0

    if modo_transacciones == "Por porcentaje sobre total":
        tc = int(round(total_tx * pct_tc / 100)) if activar_tc else 0
        pse = int(round(total_tx * pct_pse / 100)) if activar_pse else 0
        breb = int(round(total_tx * pct_breb / 100)) if activar_breb else 0

        diferencia = total_tx - (tc + pse + breb)

        if activar_breb:
            breb += diferencia
        elif activar_pse:
            pse += diferencia
        elif activar_tc:
            tc += diferencia

        return max(tc, 0), max(pse, 0), max(breb, 0)

    ratio_tc = tx_tc_actual / tx_base_canales
    ratio_pse = tx_pse_actual / tx_base_canales
    ratio_breb = tx_breb_actual / tx_base_canales

    tc = int(round(total_tx * ratio_tc)) if activar_tc else 0
    pse = int(round(total_tx * ratio_pse)) if activar_pse else 0
    breb = int(round(total_tx * ratio_breb)) if activar_breb else 0

    diferencia = total_tx - (tc + pse + breb)

    if activar_breb:
        breb += diferencia
    elif activar_pse:
        pse += diferencia
    elif activar_tc:
        tc += diferencia

    return max(tc, 0), max(pse, 0), max(breb, 0)

for nombre, tx in escenarios:
    if nombre == "Actual":
        tx_tc_calc = tx_tc_actual
        tx_pse_calc = tx_pse_actual
        tx_breb_calc = tx_breb_actual
    else:
        tx_tc_calc, tx_pse_calc, tx_breb_calc = distribuir_transacciones(tx)

    canales = calcular_costos_canales(
        ticket_tc,
        ticket_pse,
        ticket_breb,
        tx_tc_calc,
        tx_pse_calc,
        tx_breb_calc,
        costo_fijo_actual,
        porcentaje_actual,
        porcentaje_banco,
        plan_mensual,
        tx_incluidas,
        tarifa_adicional_plan,
        costo_pse_payzen,
        breb_r1_ini,
        breb_r1_fin,
        breb_r1_tarifa,
        breb_r2_ini,
        breb_r2_fin,
        breb_r2_tarifa,
        breb_r3_ini,
        breb_r3_fin,
        breb_r3_tarifa
    )

    costo_actual_total = canales["costo_actual_total"]
    payzen_total = canales["payzen_total"]

    ahorro = costo_actual_total - payzen_total
    ahorro_anual = ahorro * 12
    ahorro_pct = (ahorro / costo_actual_total * 100) if costo_actual_total > 0 else 0
    payzen_pct = (payzen_total / costo_actual_total * 100) if costo_actual_total > 0 else 0

    resultados.append({
        "Escenario": nombre,
        "Transacciones": canales["total_tx"],
        "TC": tx_tc_calc,
        "PSE": tx_pse_calc,
        "Bre-B": tx_breb_calc,
        "Ticket TC": ticket_tc,
        "Ticket PSE": ticket_pse,
        "Ticket Bre-B": ticket_breb,
        "Pasarela actual": costo_actual_total,
        "Costo actual por tx": canales["costo_actual_por_tx"],
        "Variable actual por tx": canales["variable_actual"],
        "PayZen": payzen_total,
        "Ahorro mensual": ahorro,
        "Ahorro anual": ahorro_anual,
        "PayZen %": payzen_pct,
        "Ahorro %": ahorro_pct,
        "Tx adicionales": canales["tx_adicionales"],
        "Tarifa adicional": canales["tarifa_adicional"],
        "Costo adicionales": canales["costo_tx_adicionales"],
        "Costo banco": canales["costo_banco"],
        "Costo PSE actual": canales["costo_actual_pse"],
        "Costo PSE PayZen": canales["costo_payzen_pse"],
        "Costo Bre-B actual": canales["costo_actual_breb"],
        "Costo Bre-B PayZen": canales["costo_payzen_breb"],
        "Tarifa Bre-B PayZen": canales["tarifa_breb_payzen"]
    })

df = pd.DataFrame(resultados)

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------

header_col1, header_col2 = st.columns([1, 5], gap="large")

with header_col1:
    try:
        st.image("Logo_Globalinvest_PayZen.png", width=180)
    except Exception:
        st.markdown("")

with header_col2:
    h('<div class="title">💳 Simulador Comercial PayZen Basic / Pro</div>')
    h('<div class="subtitle">Comparativo de costos entre pasarela actual vs PayZen</div>')

# ---------------------------------------------------
# PARÁMETROS BASE
# ---------------------------------------------------

h('<div class="section-title">📌 Parámetros base</div>')

c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    h(
        '<div class="card">'
        f'<div class="label">Ticket promedio</div>'
        f'<div class="big-number">{money(ticket_promedio)}</div>'
        f'<br><div class="small-text">Valor promedio por transacción.</div>'
        '</div>'
    )

with c2:
    h(
        '<div class="card">'
        f'<div class="label">Transacciones actuales</div>'
        f'<div class="big-number">{number_fmt(total_tx_base)}</div>'
        f'<br><div class="small-text">Escenario base del cliente.</div>'
        '</div>'
    )

with c3:
    h(
        '<div class="card">'
        f'<div class="label">Pasarela actual</div>'
        f'<div class="big-number-orange">{money(costo_fijo_actual)}</div>'
        f'<div class="orange-inline">{percent(porcentaje_actual)}</div>'
        f'<div class="small-text">por transacción</div>'
        '</div>'
    )

with c4:
    h(
        '<div class="card-plan">'
        f'<div class="label-white">Plan seleccionado</div>'
        f'<div class="big-number-white">{plan}</div>'
        f'<br><div class="small-text-white">Mensualidad: <b>{money(plan_mensual)}</b></div>'
        f'<div class="small-text-white">Tx incluidas: <b>{number_fmt(tx_incluidas)}</b></div>'
        f'<div class="small-text-white">Tx adicional: <b>{money(tarifa_adicional_plan)}</b></div>'
        f'<div class="small-text-white">Creación tienda: <b>{money(creacion_tienda)}</b></div>'
        '</div>'
    )

# ---------------------------------------------------
# COMPARATIVO DE COSTOS
# ---------------------------------------------------

h('<div class="section-title">📊 Comparativo de costos</div>')

for start in range(0, len(df), 3):
    cols = st.columns(3, gap="large")

    for pos, (_, row) in enumerate(df.iloc[start:start + 3].iterrows()):
        with cols[pos]:
            h(
                '<div class="card-compare">'
                f'<div class="label">{row["Escenario"]}</div>'
                f'<div class="small-text">Transacciones: <b>{number_fmt(row["Transacciones"])}</b></div>'
                f'<div class="actual-label">Pasarela actual</div>'
                f'<div class="big-number-orange">{money(row["Pasarela actual"])}</div>'
                f'<div class="payzen-label">PayZen</div>'
                f'<div class="big-number">{money(row["PayZen"])}</div>'
                f'<br><div class="small-text">Diferencia mensual estimada: <b>{money(row["Ahorro mensual"])}</b></div>'
                '</div>'
            )

# ---------------------------------------------------
# AHORRO ESTIMADO
# ---------------------------------------------------

h('<div class="section-title">💰 Ahorro estimado</div>')

for start in range(0, len(df), 3):
    cols = st.columns(3, gap="large")

    for pos, (_, row) in enumerate(df.iloc[start:start + 3].iterrows()):
        with cols[pos]:
            h(
                '<div class="card-saving">'
                f'<div class="label-white">{row["Escenario"]}</div>'
                f'<div class="big-number-white">{money(row["Ahorro mensual"])}</div>'
                f'<div class="small-text-white">Ahorro mensual estimado</div>'
                f'<div class="annual-text">Ahorro anual: {money(row["Ahorro anual"])}</div>'
                f'<br><div class="small-text-white">Si hoy pagas el 100% con tu pasarela actual, con PayZen ahorrarías:</div>'
                f'<div class="percent-text">{percent(row["Ahorro %"])}</div>'
                f'<div class="small-text-white">Costo PayZen frente al costo actual: <b>{percent(row["PayZen %"])}</b>.</div>'
                '</div>'
            )

# ---------------------------------------------------
# GRÁFICA BARRAS
# ---------------------------------------------------

h('<div class="section-title">📈 Pasarela actual vs PayZen</div>')

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df["Escenario"],
    y=df["Pasarela actual"],
    name="Pasarela actual",
    text=[money(v) for v in df["Pasarela actual"]],
    textposition="outside",
    marker_color="#F97316"
))

fig.add_trace(go.Bar(
    x=df["Escenario"],
    y=df["PayZen"],
    name="PayZen",
    text=[money(v) for v in df["PayZen"]],
    textposition="outside",
    marker_color="#06B6D4"
))

max_y = max(df["Pasarela actual"].max(), df["PayZen"].max())

fig.update_layout(
    barmode="group",
    yaxis=dict(range=[0, max_y * 1.22])
)

fig = grafica_base(fig, titulo_y="Costo mensual COP", altura=560)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# GRÁFICA LÍNEA
# ---------------------------------------------------

h('<div class="section-title">📉 Evolución del costo mensual</div>')

fig_line = go.Figure()

fig_line.add_trace(go.Scatter(
    x=df["Escenario"],
    y=df["Pasarela actual"],
    name="Pasarela actual",
    mode="lines+markers",
    line=dict(width=4, color="#F97316"),
    marker=dict(size=12, color="#F97316"),
    customdata=df[["Ahorro mensual", "Ahorro %", "PayZen"]],
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Pasarela actual: $%{y:,.0f}<br>"
        "PayZen: $%{customdata[2]:,.0f}<br>"
        "Ahorro mensual: $%{customdata[0]:,.0f}<br>"
        "Ahorro porcentual: %{customdata[1]:.2f}%"
        "<extra></extra>"
    )
))

fig_line.add_trace(go.Scatter(
    x=df["Escenario"],
    y=df["PayZen"],
    name="PayZen",
    mode="lines+markers",
    line=dict(width=4, color="#06B6D4"),
    marker=dict(size=12, color="#06B6D4"),
    customdata=df[["Ahorro mensual", "Ahorro %", "Pasarela actual"]],
    hovertemplate=(
        "<b>%{x}</b><br>"
        "PayZen: $%{y:,.0f}<br>"
        "Pasarela actual: $%{customdata[2]:,.0f}<br>"
        "Ahorro mensual: $%{customdata[0]:,.0f}<br>"
        "Ahorro porcentual: %{customdata[1]:.2f}%"
        "<extra></extra>"
    )
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
        tx = row["Transacciones"]
        variable_actual = row["Variable actual por tx"]
        costo_banco_payzen = row["Costo banco"]

        h(
            '<div class="math-box">'
            '<div class="math-title">Pasarela actual</div>'
            f'<div class="math-line">{number_fmt(tx)} × ({money(costo_fijo_actual)} + ({percent(porcentaje_actual)} × ticket por canal))</div>'
            f'<div class="math-line">{number_fmt(tx)} × ({money(costo_fijo_actual)} + {money(variable_actual)})</div>'
            f'<div class="math-result-orange">= {money(row["Pasarela actual"])}</div>'
            '</div>'
        )

        if row["Tx adicionales"] > 0:
            linea_adicionales = f"+ ({number_fmt(row['Tx adicionales'])} × {money(row['Tarifa adicional'])})"
            calculo_adicionales = f"+ {money(row['Costo adicionales'])}"
        else:
            linea_adicionales = "+ $0 transacciones adicionales"
            calculo_adicionales = "+ $0"

        h(
            '<div class="math-box">'
            '<div class="math-title">PayZen</div>'
            f'<div class="math-line">{money(plan_mensual)} {linea_adicionales} + ({money(ticket_promedio)} × {number_fmt(tx)} × {percent(porcentaje_banco)})</div>'
            f'<div class="math-line">{money(plan_mensual)} {calculo_adicionales} + TC banco {money(costo_banco_payzen)} + PSE {money(row.get("Costo PSE PayZen", 0))} + Bre-B {money(row.get("Costo Bre-B PayZen", 0))}</div>'
            f'<div class="math-result">= {money(row["PayZen"])}</div>'
            '</div>'
        )

        h(
            '<div class="math-box">'
            '<div class="math-title">Ahorro</div>'
            f'<div class="math-line">{money(row["Pasarela actual"])} - {money(row["PayZen"])}</div>'
            f'<div class="math-result">Ahorro mensual: {money(row["Ahorro mensual"])}</div>'
            f'<div class="math-result">Ahorro anual: {money(row["Ahorro anual"])}</div>'
            f'<div class="math-line">Porcentaje de ahorro: <b>{percent(row["Ahorro %"])}</b></div>'
            '</div>'
        )


# ---------------------------------------------------
# PDF RESUMEN
# ---------------------------------------------------

DISCLAIMER = """
Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos de terceros o modificaciones acordadas entre las partes.
"""

def generar_pdf_resumen(df_pdf):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=28, bottomMargin=24)
    styles = getSampleStyleSheet()

    small_style = ParagraphStyle(
        "SmallDisclaimer",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#4B5563")
    )

    story = []

    try:
        story.append(Image("Logo_Globalinvest_PayZen.png", width=2.6*inch, height=0.9*inch))
    except Exception:
        pass

    story.append(Spacer(1, 8))
    story.append(Paragraph("Resumen Comercial PayZen", styles["Title"]))
    story.append(Spacer(1, 12))

    first = df_pdf.iloc[0]
    resumen_data = [
        ["Concepto", "Valor"],
        ["Plan seleccionado", plan],
        ["Total transacciones", number_fmt(first["Transacciones"])],
        ["Costo actual", money(first["Pasarela actual"])],
        ["Costo PayZen", money(first["PayZen"])],
        ["Ahorro mensual", money(first["Ahorro mensual"])],
        ["Ahorro anual", money(first["Ahorro anual"])],
        ["Ahorro porcentual", percent(first["Ahorro %"])],
    ]

    resumen_table = Table(resumen_data, colWidths=[2.4*inch, 3.5*inch])
    resumen_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
    ]))
    story.append(resumen_table)

    story.append(Spacer(1, 12))

    canales_data = [
        ["Canal", "Transacciones", "Costo actual", "Costo PayZen"],
        ["Tarjetas", number_fmt(first.get("TC", 0)), money(first["Pasarela actual"] - first.get("Costo PSE actual", 0) - first.get("Costo Bre-B actual", 0)), money(first["Costo banco"])],
        ["PSE", number_fmt(first.get("PSE", 0)), money(first.get("Costo PSE actual", 0)), money(first.get("Costo PSE PayZen", 0))],
        ["Bre-B", number_fmt(first.get("Bre-B", 0)), money(first.get("Costo Bre-B actual", 0)), money(first.get("Costo Bre-B PayZen", 0))],
        ["Plan + tx adicionales", "", "", money(plan_mensual + first["Costo adicionales"])],
    ]

    canales_table = Table(canales_data, colWidths=[1.6*inch, 1.3*inch, 1.5*inch, 1.5*inch])
    canales_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,0), 7),
    ]))
    story.append(canales_table)

    story.append(Spacer(1, 12))
    story.append(Paragraph(DISCLAIMER, small_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

st.download_button(
    label="📄 Descargar resumen PDF",
    data=generar_pdf_resumen(df),
    file_name="Resumen_Comercial_PayZen.pdf",
    mime="application/pdf"
)

h(f'<div class="disclaimer">{DISCLAIMER}</div>')


# ---------------------------------------------------
# TABLA RESUMEN
# ---------------------------------------------------

h('<div class="section-title">📋 Tabla resumen</div>')

df_mostrar = df.copy()

columnas_dinero = [
    "Pasarela actual",
    "PayZen",
    "Ahorro mensual",
    "Ahorro anual",
    "Costo adicionales",
    "Costo banco",
    "Costo actual por tx",
    "Variable actual por tx",
    "Ticket TC",
    "Ticket PSE",
    "Ticket Bre-B",
    "Costo PSE actual",
    "Costo PSE PayZen",
    "Costo Bre-B actual",
    "Costo Bre-B PayZen",
    "Tarifa Bre-B PayZen"
]

for col in columnas_dinero:
    df_mostrar[col] = df_mostrar[col].apply(money)

df_mostrar["PayZen %"] = df_mostrar["PayZen %"].apply(percent)
df_mostrar["Ahorro %"] = df_mostrar["Ahorro %"].apply(percent)
df_mostrar["Tarifa adicional"] = df_mostrar["Tarifa adicional"].apply(money)
df_mostrar["Transacciones"] = df_mostrar["Transacciones"].apply(number_fmt)
df_mostrar["Tx adicionales"] = df_mostrar["Tx adicionales"].apply(number_fmt)

st.dataframe(df_mostrar, use_container_width=True)