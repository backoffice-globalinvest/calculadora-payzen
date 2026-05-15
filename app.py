import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import hashlib
import hmac
from io import BytesIO

from reportlab.lib.pagesizes import letter, landscape
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
    },
    "desarrollo": {
        "name": "Desarrollo",
        "password_hash": "c648919311c73fc5f855e3bdf3b163e6443adfda670352d5f5fadbe9ddf12b1a"
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

def h(code_html):
    st.markdown(code_html, unsafe_allow_html=True)


def money(value):
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except Exception:
        return "$0"


def number_fmt(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "0"


def percent(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "0.00%"


def clean_number(value):
    try:
        return int(str(value).replace(".", "").replace(",", "").strip())
    except Exception:
        return None


PAYZEN_PLANS = {
    "PayZen Basic 100 tx": {
        "mensualidad": 126500,
        "tx_incluidas": 100,
        "creacion_tienda": 319000,
        "tx_adicional": 505
    },
    "PayZen Pro 500 tx": {
        "mensualidad": 324500,
        "tx_incluidas": 500,
        "creacion_tienda": 755500,
        "tx_adicional": 440
    },
    "PayZen Pro 5.000 tx": {
        "mensualidad": 1925000,
        "tx_incluidas": 5000,
        "creacion_tienda": 755500,
        "tx_adicional": 385
    },
    "PayZen Pro 10.000 tx": {
        "mensualidad": 3492500,
        "tx_incluidas": 10000,
        "creacion_tienda": 755500,
        "tx_adicional": 349
    },
    "PayZen Pro 15.000 tx": {
        "mensualidad": 3445000,
        "tx_incluidas": 15000,
        "creacion_tienda": 755500,
        "tx_adicional": 297
    },
    "PayZen Pro 25.000 tx": {
        "mensualidad": 7232500,
        "tx_incluidas": 25000,
        "creacion_tienda": 755500,
        "tx_adicional": 289
    },
    "PayZen Pro 50.000 tx": {
        "mensualidad": 14179000,
        "tx_incluidas": 50000,
        "creacion_tienda": 755500,
        "tx_adicional": 284
    },
    "PayZen Pro 100.000 tx": {
        "mensualidad": 27225000,
        "tx_incluidas": 100000,
        "creacion_tienda": 755500,
        "tx_adicional": 272
    },
    "PayZen Pro 200.000 tx": {
        "mensualidad": 52800000,
        "tx_incluidas": 200000,
        "creacion_tienda": 755500,
        "tx_adicional": 264
    },
}


def calcular_pasarela_actual(ticket_tc, ticket_pse, ticket_breb, tx_tc, tx_pse, tx_breb, fijo_actual, pct_actual):
    costo_tc = tx_tc * (fijo_actual + (ticket_tc * pct_actual / 100))
    costo_pse = tx_pse * (fijo_actual + (ticket_pse * pct_actual / 100))
    costo_breb = tx_breb * (fijo_actual + (ticket_breb * pct_actual / 100))
    total = costo_tc + costo_pse + costo_breb
    return costo_tc, costo_pse, costo_breb, total


def calcular_costos_canales(ticket_tc, ticket_pse, ticket_breb, tx_tc, tx_pse, tx_breb, fijo_actual, pct_actual,
                            pct_banco_tc, plan_mensual, tx_incluidas, tx_adicional_unitario,
                            costo_pse_payzen, costo_breb_payzen):
    total_tx = tx_tc + tx_pse + tx_breb

    costo_actual_tc, costo_actual_pse, costo_actual_breb, costo_actual_total = calcular_pasarela_actual(
        ticket_tc, ticket_pse, ticket_breb, tx_tc, tx_pse, tx_breb, fijo_actual, pct_actual
    )

    tx_adicionales = max(total_tx - tx_incluidas, 0)
    costo_tx_adicionales = tx_adicionales * tx_adicional_unitario
    costo_banco_tc = ticket_tc * tx_tc * pct_banco_tc / 100
    costo_payzen_pse = tx_pse * costo_pse_payzen
    costo_payzen_breb = tx_breb * costo_breb_payzen

    total_adquirencia = costo_banco_tc + costo_payzen_pse + costo_payzen_breb
    total_payzen_gateway = plan_mensual + costo_tx_adicionales
    payzen_total = total_payzen_gateway + total_adquirencia

    return {
        "total_tx": total_tx,
        "costo_actual_total": costo_actual_total,
        "costo_actual_tc": costo_actual_tc,
        "costo_actual_pse": costo_actual_pse,
        "costo_actual_breb": costo_actual_breb,
        "tx_adicionales": tx_adicionales,
        "tarifa_adicional": tx_adicional_unitario,
        "costo_tx_adicionales": costo_tx_adicionales,
        "plan_mensual": plan_mensual,
        "total_payzen_gateway": total_payzen_gateway,
        "costo_banco": costo_banco_tc,
        "costo_payzen_pse": costo_payzen_pse,
        "costo_payzen_breb": costo_payzen_breb,
        "total_adquirencia": total_adquirencia,
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
        tx_tc_actual = st.number_input("Transacciones TC", min_value=0, value=2000, step=50) if activar_tc else 0
        tx_pse_actual = st.number_input("Transacciones PSE", min_value=0, value=200, step=50) if activar_pse else 0
        tx_breb_actual = st.number_input("Transacciones Bre-B", min_value=0, value=10, step=10) if activar_breb else 0

        total_transacciones_base = tx_tc_actual + tx_pse_actual + tx_breb_actual

        pct_tc = (tx_tc_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0
        pct_pse = (tx_pse_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0
        pct_breb = (tx_breb_actual / total_transacciones_base * 100) if total_transacciones_base > 0 else 0

    else:
        total_transacciones_base = st.number_input("Total transacciones", min_value=0, value=2210, step=100)

        pct_tc = st.number_input("% Tarjetas", min_value=0.0, max_value=100.0, value=90.50, step=0.10) if activar_tc else 0.0
        pct_pse = st.number_input("% PSE", min_value=0.0, max_value=100.0, value=9.05, step=0.10) if activar_pse else 0.0
        pct_breb = st.number_input("% Bre-B", min_value=0.0, max_value=100.0, value=0.45, step=0.10) if activar_breb else 0.0

        suma_pct = pct_tc + pct_pse + pct_breb

        if total_transacciones_base > 0 and abs(suma_pct - 100) > 0.01:
            st.warning(f"Los porcentajes activos suman {suma_pct:.2f}%. Lo ideal es que sumen 100%.")

        tx_tc_actual = int(round(total_transacciones_base * pct_tc / 100)) if activar_tc else 0
        tx_pse_actual = int(round(total_transacciones_base * pct_pse / 100)) if activar_pse else 0
        tx_breb_actual = int(round(total_transacciones_base * pct_breb / 100)) if activar_breb else 0

        diferencia = total_transacciones_base - (tx_tc_actual + tx_pse_actual + tx_breb_actual)
        if activar_breb:
            tx_breb_actual += diferencia
        elif activar_pse:
            tx_pse_actual += diferencia
        elif activar_tc:
            tx_tc_actual += diferencia

    st.caption(
        f"Distribución calculada: TC {number_fmt(tx_tc_actual)} | "
        f"PSE {number_fmt(tx_pse_actual)} | Bre-B {number_fmt(tx_breb_actual)} | "
        f"Total {number_fmt(tx_tc_actual + tx_pse_actual + tx_breb_actual)}"
    )

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
        ticket_pse = st.number_input("Ticket promedio PSE", min_value=0, value=60000, step=10000)
        ticket_breb = st.number_input("Ticket promedio Bre-B", min_value=0, value=60000, step=10000)
        ticket_promedio = ticket_tc

    st.divider()
    st.subheader("Pasarela actual")

    costo_fijo_actual = st.number_input("Costo fijo actual por transacción", min_value=0, value=750, step=50)
    porcentaje_actual = st.number_input("% actual de la pasarela", min_value=0.0, value=2.90, step=0.10)

    st.caption("Modelo agregador: porcentaje + fijo por transacción, aplicado a todos los métodos activos.")

    st.divider()
    st.subheader("Costos adquirencia / procesamiento")

    porcentaje_banco = st.number_input("% adquirencia banco TC", min_value=0.0, value=1.84, step=0.01) if activar_tc else 0.0
    costo_pse_payzen = st.number_input("Costo PSE por tx", min_value=0, value=400, step=50) if activar_pse else 0
    costo_breb_payzen = st.number_input("Costo Bre-B por tx", min_value=0, value=600, step=50) if activar_breb else 0

    st.divider()
    st.subheader("Plan PayZen")

    plan = st.selectbox("Selecciona el plan", list(PAYZEN_PLANS.keys()), index=1)

    st.divider()

    proyecciones_texto = st.text_area(
        "Proyecciones de transacciones totales",
        value="3000\n5000",
        help="Escribe el total de transacciones proyectadas por línea. La app mantendrá la distribución por canal."
    )


# ---------------------------------------------------
# PLANES
# ---------------------------------------------------

plan_info = PAYZEN_PLANS[plan]
plan_mensual = plan_info["mensualidad"]
tx_incluidas = plan_info["tx_incluidas"]
creacion_tienda = plan_info["creacion_tienda"]
tx_adicional_unitario = plan_info["tx_adicional"]


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
        tx_adicional_unitario,
        costo_pse_payzen,
        costo_breb_payzen
    )

    costo_actual_total = canales["costo_actual_total"]
    payzen_total = canales["payzen_total"]

    ahorro = costo_actual_total - payzen_total
    ahorro_anual = ahorro * 12
    ahorro_pct = (ahorro / costo_actual_total * 100) if costo_actual_total > 0 else 0

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
        "Costo actual TC": canales["costo_actual_tc"],
        "Costo actual PSE": canales["costo_actual_pse"],
        "Costo actual Bre-B": canales["costo_actual_breb"],
        "PayZen": payzen_total,
        "Ahorro mensual": ahorro,
        "Ahorro anual": ahorro_anual,
        "Ahorro %": ahorro_pct,
        "Tx adicionales": canales["tx_adicionales"],
        "Tarifa adicional": canales["tarifa_adicional"],
        "Costo adicionales": canales["costo_tx_adicionales"],
        "Costo plan": canales["plan_mensual"],
        "Total PayZen Gateway": canales["total_payzen_gateway"],
        "Costo banco TC": canales["costo_banco"],
        "Costo PSE PayZen": canales["costo_payzen_pse"],
        "Costo Bre-B PayZen": canales["costo_payzen_breb"],
        "Total adquirencia": canales["total_adquirencia"]
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
        f'<div class="small-text-white">Tx adicional: <b>{money(tx_adicional_unitario)}</b></div>'
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
                f'<div class="payzen-label">PayZen + adquirencia</div>'
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
                f'<br><div class="small-text-white">Ahorro estimado frente al modelo agregador actual:</div>'
                f'<div class="percent-text">{percent(row["Ahorro %"])}</div>'
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
    name="PayZen + adquirencia",
    text=[money(v) for v in df["PayZen"]],
    textposition="outside",
    marker_color="#06B6D4"
))

max_y = max(df["Pasarela actual"].max(), df["PayZen"].max()) if len(df) else 0
fig.update_layout(barmode="group", yaxis=dict(range=[0, max_y * 1.22 if max_y > 0 else 1]))
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
        "PayZen + adquirencia: $%{customdata[2]:,.0f}<br>"
        "Ahorro mensual: $%{customdata[0]:,.0f}<br>"
        "Ahorro porcentual: %{customdata[1]:.2f}%"
        "<extra></extra>"
    )
))

fig_line.add_trace(go.Scatter(
    x=df["Escenario"],
    y=df["PayZen"],
    name="PayZen + adquirencia",
    mode="lines+markers",
    line=dict(width=4, color="#06B6D4"),
    marker=dict(size=12, color="#06B6D4"),
    customdata=df[["Ahorro mensual", "Ahorro %", "Pasarela actual"]],
    hovertemplate=(
        "<b>%{x}</b><br>"
        "PayZen + adquirencia: $%{y:,.0f}<br>"
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
        h(
            '<div class="math-box">'
            '<div class="math-title">Pasarela actual / modelo agregador</div>'
            f'<div class="math-line">Total: {number_fmt(row["Transacciones"])} × ({percent(porcentaje_actual)} × ticket + {money(costo_fijo_actual)})</div>'
            f'<div class="math-result-orange">= {money(row["Pasarela actual"])}</div>'
            '</div>'
        )

        h(
            '<div class="math-box">'
            '<div class="math-title">PayZen Gateway</div>'
            f'<div class="math-line">Mensualidad {money(row["Costo plan"])} + '
            f'({number_fmt(row["Tx adicionales"])} tx adicionales × {money(row["Tarifa adicional"])})</div>'
            f'<div class="math-result">= {money(row["Total PayZen Gateway"])}</div>'
            '</div>'
        )

        h(
            '<div class="math-box">'
            '<div class="math-title">Adquirencia / costos por método</div>'
            f'<div class="math-line">TC: {money(row["Costo banco TC"])} | PSE: {money(row["Costo PSE PayZen"])} | Bre-B: {money(row["Costo Bre-B PayZen"])}</div>'
            f'<div class="math-result">= {money(row["Total adquirencia"])}</div>'
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
# PDF RESUMEN COMERCILA JULI
# ---------------------------------------------------

DISCLAIMER = """
Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos de terceros o modificaciones acordadas entre las partes.
"""


def paragraph_cell(text, style):
    return Paragraph(str(text), style)


def generar_pdf_Comercial(df_pdf):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=28,
        leftMargin=28,
        topMargin=10,
        bottomMargin=18
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCenter",
        parent=styles["Title"],
        alignment=1,
        fontSize=22,
        leading=26,
        spaceAfter=4
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=10,
        leading=12,
        spaceBefore=2,
        spaceAfter=2,
        textColor=colors.black
    )

    small_style = ParagraphStyle(
        "SmallDisclaimer",
        parent=styles["BodyText"],
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#111827"),
        alignment=0
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["BodyText"],
        fontSize=7,
        leading=8.5,
        textColor=colors.black
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell,
        alignment=1
    )

    table_cell_right = ParagraphStyle(
        "TableCellRight",
        parent=table_cell,
        alignment=2
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=table_cell,
        fontName="Helvetica-Bold",
        alignment=1,
        textColor=colors.black
    )

    story = []

    try:
        logo = Image("Logo_Globalinvest_PayZen.png", width=1.80 * inch, height=0.55 * inch)
    except Exception:
        logo = Paragraph("", table_cell)

    titulo_pdf = Paragraph("Resumen Comercial PayZen", title_style)

    encabezado_pdf = Table(
        [[logo, titulo_pdf]],
        colWidths=[1.65 * inch, 8.20 * inch]
        )

    encabezado_pdf.hAlign = "LEFT"

    encabezado_pdf.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    story.append(encabezado_pdf)
    story.append(Spacer(1, 4))

    first = df_pdf.iloc[0]

    total_tx = first["Transacciones"]
    total_methods = max(total_tx, 1)

    pct_tc_pdf = (first["TC"] / total_methods * 100) if total_methods > 0 else 0
    pct_pse_pdf = (first["PSE"] / total_methods * 100) if total_methods > 0 else 0
    pct_breb_pdf = (first["Bre-B"] / total_methods * 100) if total_methods > 0 else 0
    pct_total_pdf = pct_tc_pdf + pct_pse_pdf + pct_breb_pdf

    # 1. INFORMACIÓN OPERATIVA INICIAL

    story.append(Paragraph("Información Operativa Inicial", section_style))

    # Tabla 1: Valor inicial
    info_resumen_data = [
        [
        Paragraph(
            '<font color="white"><b>Valores Iniciales</b></font>',
            table_header
        ),
        ""
        ],
        [
            paragraph_cell("Volumen", table_cell),
            paragraph_cell(number_fmt(total_tx), table_cell_right)
        ],
        [
            paragraph_cell("Ticket Promedio", table_cell),
            paragraph_cell(money(ticket_promedio), table_cell_right)
        ],
    ]

    info_resumen_table = Table(
        info_resumen_data,
        colWidths=[2.25 * inch, 1.00 * inch]
    )

    info_resumen_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#3A3A3D")),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
        ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (1, 0), "CENTER"),

        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#9CA3AF")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#9CA3AF")),

        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    # Tabla 2: Métodos de pago escogidos
    metodos_data = [
        [
            Paragraph('<font color="white"><b>Métodos de pago escogidos</b></font>', table_header),
            Paragraph('<font color="white"><b>Número de transacciones</b></font>', table_header),
            Paragraph('<font color="white"><b>% Transaccional</b></font>', table_header)
        ],
        [
            paragraph_cell("Tarjeta Crédito / Tarjeta Débito", table_cell),
            paragraph_cell(number_fmt(first["TC"]), table_cell_right),
            paragraph_cell(percent(pct_tc_pdf), table_cell_right)
        ],
        [
            paragraph_cell("PSE", table_cell),
            paragraph_cell(number_fmt(first["PSE"]), table_cell_right),
            paragraph_cell(percent(pct_pse_pdf), table_cell_right)
        ],
        [
            paragraph_cell("Bre-B", table_cell),
            paragraph_cell(number_fmt(first["Bre-B"]), table_cell_right),
            paragraph_cell(percent(pct_breb_pdf), table_cell_right)
        ],
        [
            Paragraph("<b>Total</b>", table_cell),
            Paragraph(f"<b>{number_fmt(total_tx)}</b>", table_cell_right),
            Paragraph(f"<b>{percent(pct_total_pdf)}</b>", table_cell_right)
        ],
    ]

    metodos_table = Table(
        metodos_data,
        colWidths=[2.45 * inch, 1.35 * inch, 1.15 * inch]
    )

    metodos_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#9CA3AF")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3A3A3D")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#9CA3AF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    # Unir las dos tablas lado a lado
    tablas_operativas = Table(
        [[info_resumen_table, metodos_table]],
        colWidths=[3.35 * inch, 5.20 * inch]
    )

    tablas_operativas.hAlign = "LEFT"

    tablas_operativas.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(tablas_operativas)
    story.append(Spacer(1, 8))
    
    # 2. COSTOS PASARELA ACTUAL

    story.append(Paragraph(
        '<font color="#111827"><b>Costos Pasarela Actual</b></font>',
        section_style
    ))

    modelo_actual = f"{percent(porcentaje_actual)} + {money(costo_fijo_actual)}"

    actual_data = [
        [
            Paragraph('<font color="white"><b>Costos Pasarela Actual</b></font>', table_header),
            Paragraph('<font color="white"><b>MODELO AGREGADOR</b></font>', table_header)
        ],
        [
            paragraph_cell("Plan actual", table_cell),
            paragraph_cell(modelo_actual, table_cell_right)
        ],
        [
            paragraph_cell("Ticket Promedio", table_cell),
            paragraph_cell(money(ticket_promedio), table_cell_right)
        ],
        [
            paragraph_cell("Volumen (Número de transacciones)", table_cell),
            paragraph_cell(number_fmt(total_tx), table_cell_right)
        ],
        [
            Paragraph("<b>Costo Total pasarela agregadora</b>", table_cell),
            Paragraph(f"<b>{money(first['Pasarela actual'])}</b>", table_cell_right)
        ],
    ]

    actual_table = Table(
        actual_data,
        colWidths=[2.45 * inch, 1.45 * inch]
    )

    actual_table.hAlign = "LEFT"

    actual_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#BFC5D2")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#EA7A2F")),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EA7A2F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 4), (-1, 4), colors.black),

        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#FDE7D7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),

        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(actual_table)
    story.append(Spacer(1, 8))

    # 3. COSTOS PAYZEN Y COSTOS ADQUIRENTE LADO A LADO

    story.append(Paragraph(
        '<font color="#111827"><b>Costos PayZen + Costos Adquirientes</b></font>',
        section_style
    ))

    payzen_data = [
        [
            Paragraph('<font color="white"><b>Costos PayZen</b></font>', table_header),
            Paragraph('<font color="white"><b>MODELO GATEWAY</b></font>', table_header)
        ],
        [paragraph_cell("Ticket Promedio", table_cell), paragraph_cell(money(ticket_promedio), table_cell_right)],
        [paragraph_cell("Volumen (Número de transacciones)", table_cell), paragraph_cell(number_fmt(total_tx), table_cell_right)],
        [paragraph_cell("Costo de la transacción Adicional", table_cell), paragraph_cell(money(first["Tarifa adicional"]), table_cell_right)],
        [paragraph_cell("Cantidad de transacciones Adicionales", table_cell), paragraph_cell(number_fmt(first["Tx adicionales"]), table_cell_right)],
        [paragraph_cell("Costo total de las transacciones Adicionales", table_cell), paragraph_cell(money(first["Costo adicionales"]), table_cell_right)],
        [paragraph_cell(f"Costo del Plan Escogido {plan}", table_cell), paragraph_cell(money(first["Costo plan"]), table_cell_right)],
        [paragraph_cell("Total Costo PayZen", table_header), paragraph_cell(money(first["Total PayZen Gateway"]), table_cell_right)],
    ]

    payzen_table = Table(
        payzen_data,
        colWidths=[2.55 * inch, 1.28 * inch]
    )

    payzen_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#A7B7D8")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#2563EB")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    total_payzen_data = [
        [
            paragraph_cell("Total PayZen + Total Adquirientes", table_header),
            paragraph_cell(money(first["PayZen"]), table_cell_right)
        ]
    ]

    total_payzen_table = Table(
        total_payzen_data,
        colWidths=[2.55 * inch, 1.28 * inch]
    )

    total_payzen_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#A7B7D8")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#2563EB")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    payzen_bloque = Table(
        [
            [payzen_table],
            [Spacer(1, 6)],
            [total_payzen_table],
        ],
        colWidths=[3.95 * inch]
    )

    payzen_bloque.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    adquirente_data = [
        [
            Paragraph('<font color="white"><b>Costos Adquiriente</b></font>', table_header),
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph('<font color="white"><b>Método de pago</b></font>', table_header),
            Paragraph('<font color="white"><b>Valor</b></font>', table_header),
            Paragraph('<font color="white"><b>Número de transacciones</b></font>', table_header),
            Paragraph('<font color="white"><b>Ticket promedio</b></font>', table_header),
            Paragraph('<font color="white"><b>Total Adquiriente</b></font>', table_header)
        ],
        [
            paragraph_cell("Tarjeta Crédito / Tarjeta Débito", table_cell),
            paragraph_cell(percent(porcentaje_banco), table_cell_right),
            paragraph_cell(number_fmt(first["TC"]), table_cell_right),
            paragraph_cell(money(first["Ticket TC"]), table_cell_right),
            paragraph_cell(money(first["Costo banco TC"]), table_cell_right)
        ],
        [
            paragraph_cell("PSE", table_cell),
            paragraph_cell(money(costo_pse_payzen), table_cell_right),
            paragraph_cell(number_fmt(first["PSE"]), table_cell_right),
            paragraph_cell("N/A", table_cell_center),
            paragraph_cell(money(first["Costo PSE PayZen"]), table_cell_right)
        ],
        [
            paragraph_cell("Bre-B", table_cell),
            paragraph_cell(money(costo_breb_payzen), table_cell_right),
            paragraph_cell(number_fmt(first["Bre-B"]), table_cell_right),
            paragraph_cell("N/A", table_cell_center),
            paragraph_cell(money(first["Costo Bre-B PayZen"]), table_cell_right)
        ],
        [
            paragraph_cell("Total de los Adquirientes", table_header),
            "",
            "",
            "",
            paragraph_cell(money(first["Total adquirencia"]), table_cell_right)
        ],
    ]

    adquirente_table = Table(
        adquirente_data,
        colWidths=[1.75 * inch, 0.72 * inch, 1.18 * inch, 0.95 * inch, 1.15 * inch]
    )

    adquirente_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#A7B7D8")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#2563EB")),
        ("SPAN", (0, 0), (4, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
        ("BACKGROUND", (3, 5), (4, 5), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME", (3, 5), (4, 5), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (4, 0), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (0, 5), (3, 5)),
        ("ALIGN", (0, 5), (3, 5), "CENTER"),
        ("BACKGROUND", (0, 5), (4, 5), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0, 5), (4, 5), "Helvetica-Bold"),
    ]))

    combined_tables = Table(
        [[payzen_bloque, adquirente_table]],
        colWidths=[3.95 * inch, 5.85 * inch]
    )

    combined_tables.hAlign = "LEFT"

    combined_tables.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(combined_tables)
    story.append(Spacer(1, 2))
    
    # 4. AHORRO ESTIMADO

    story.append(Paragraph("Ahorro estimado con PayZen", section_style))

    ahorro_data = [
        [Paragraph('<font color="white"><b>Indicador</b></font>', table_header), Paragraph('<font color="white"><b>Resultado</b></font>', table_header)],
        [paragraph_cell("Ahorro mensual", table_cell), paragraph_cell(money(first["Ahorro mensual"]), table_cell_right)],
        [paragraph_cell("Ahorro anual", table_cell), paragraph_cell(money(first["Ahorro anual"]), table_cell_right)],
        [paragraph_cell("Ahorro porcentual", table_cell), paragraph_cell(percent(first["Ahorro %"]), table_cell_right)],
    ]

    ahorro_table = Table(ahorro_data, colWidths=[2.45 * inch, 1.45 * inch])

    ahorro_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#A7B7D8")),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#047857")),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#047857")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECFDF5")),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ahorro_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(DISCLAIMER, small_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ---------------------------------------------------
# PDF EJECUTIVO - CEDRIC 
# ---------------------------------------------------

def generar_pdf_ejecutivo(df_pdf):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=34,
        leftMargin=34,
        topMargin=16,
        bottomMargin=18
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleExecutive",
        parent=styles["Title"],
        fontSize=22,
        leading=25,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "SubtitleExecutive",
        parent=styles["BodyText"],
        fontSize=9,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8
    )

    section_style = ParagraphStyle(
        "SectionExecutive",
        parent=styles["Heading2"],
        fontSize=9.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4,
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        "ExecutiveCell",
        parent=styles["BodyText"],
        fontSize=7.6,
        leading=9.2,
        textColor=colors.HexColor("#111827")
    )

    table_cell_right = ParagraphStyle(
        "ExecutiveCellRight",
        parent=table_cell,
        alignment=2
    )

    table_header = ParagraphStyle(
        "ExecutiveHeader",
        parent=table_cell,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=1
    )

    total_style = ParagraphStyle(
        "ExecutiveTotal",
        parent=table_cell,
        fontName="Helvetica-Bold",
        fontSize=8.4,
        leading=10,
        textColor=colors.white
    )

    total_style_right = ParagraphStyle(
        "ExecutiveTotalRight",
        parent=total_style,
        alignment=2
    )

    ahorro_style = ParagraphStyle(
        "AhorroStyle",
        parent=table_cell,
        fontName="Helvetica-Bold",
        fontSize=8.4,
        leading=10,
        textColor=colors.HexColor("#047857"),
        alignment=2
    )

    disclaimer_style = ParagraphStyle(
        "DisclaimerExecutive",
        parent=styles["BodyText"],
        fontSize=6,
        leading=7,
        textColor=colors.HexColor("#6B7280"),
        alignment=0
    )

    conclusion_style = ParagraphStyle(
        "Conclusion",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
        alignment=0
    )

    def make_table(data, col_widths, header_color="#2563EB", total_last=False, grid_color="#CBD5E1"):
        table = Table(data, colWidths=col_widths)
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.30, colors.HexColor(grid_color)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if total_last:
            style_cmds.extend([
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ])
        table.setStyle(TableStyle(style_cmds))
        return table

    story = []
    first = df_pdf.iloc[0]
    total_tx = first["Transacciones"]
    modelo_actual = f"{percent(porcentaje_actual)} + {money(costo_fijo_actual)}"

    try:
        logo = Image("Logo_Globalinvest_PayZen.png", width=1.70 * inch, height=0.52 * inch)
    except Exception:
        logo = Paragraph("", table_cell)

    header_table = Table(
        [[logo, Paragraph("Resumen Ejecutivo PayZen", title_style)]],
        colWidths=[1.7 * inch, 7.5 * inch]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(header_table)
    story.append(Paragraph("Análisis comparativo de costos transaccionales", subtitle_style))
    story.append(Spacer(1, 5))

    # ---------------------------------------------------
    # TABLA 1 - DATOS INICIALES
    # ---------------------------------------------------

    datos_iniciales_data = [
        [
            Paragraph('<font color="white"><b>Datos iniciales del escenario</b></font>', table_header),
            ""
        ],
        [
            Paragraph('<font color="white"><b>Concepto</b></font>', table_header),
            Paragraph('<font color="white"><b>Valor</b></font>', table_header)
        ],
        [
            Paragraph("Ticket promedio", table_cell),
            Paragraph(money(ticket_promedio), table_cell_right)
        ],
        [
            Paragraph("Número de transacciones", table_cell),
            Paragraph(number_fmt(total_tx), table_cell_right)
        ],
    ]

    datos_iniciales_table = Table(
        datos_iniciales_data,
        colWidths=[4.8 * inch, 2.4 * inch]
    )

    datos_iniciales_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#4B5563")),
        ("BACKGROUND", (0, 1), (1, 1), colors.HexColor("#9CA3AF")),
        ("TEXTCOLOR", (0, 0), (1, 1), colors.white),
        ("ALIGN", (0, 0), (1, 1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    story.append(datos_iniciales_table)
    story.append(Spacer(1, 7))

    # ---------------------------------------------------
    # TABLA 2 - MODELO ACTUAL
    # ---------------------------------------------------
    modelo_actual_data = [
        [
            Paragraph('<font color="white"><b>Costos Pasarela Actual</b></font>', table_header),
            ""
        ],
        [
            Paragraph("Plan actual", table_cell),
            Paragraph(modelo_actual, table_cell_right)
        ],
        [
            Paragraph("<b>Costo total pasarela agregadora</b>", total_style),
            Paragraph(f"<b>{money(first['Pasarela actual'])}</b>", total_style_right)
        ],
    ]

    modelo_actual_table = Table(
        modelo_actual_data,
        colWidths=[4.8 * inch, 2.4 * inch]
    )

    modelo_actual_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),

        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#FF7A1A")),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
        ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),

        ("BACKGROUND", (0, 2), (1, 2), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 2), (1, 2), colors.white),
        ("FONTNAME", (0, 2), (1, 2), "Helvetica-Bold"),

        ("ALIGN", (0, 0), (1, 0), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),

        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#EA7A2F")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    story.append(modelo_actual_table)
    story.append(Spacer(1, 7))


    # ---------------------------------------------------
    # TABLA 3 - MODELO PAYZEN
    # ---------------------------------------------------
    modelo_payzen_data = [
            [
                Paragraph('<font color="white"><b>Modelo PayZen</b></font>', table_header),
                ""
            ],
            [
                Paragraph("Plan seleccionado PayZen", table_cell),
                Paragraph(plan, table_cell_right)
            ],
            [
                Paragraph("Costo PayZen", table_cell),
                Paragraph(money(first["Costo plan"]), table_cell_right)
            ],
            [
                Paragraph("Costo transacción adicional PayZen", table_cell),
                Paragraph(money(first["Tarifa adicional"]), table_cell_right)
            ],
            [
                Paragraph("Costo total transacciones adicionales PayZen", table_cell),
                Paragraph(money(first["Costo adicionales"]), table_cell_right)
            ],
            [
                Paragraph("Costo total PayZen", table_cell),
                Paragraph(money(first["Total PayZen Gateway"]), table_cell_right)
            ],
            [
                Paragraph("Costo adquirientes", table_cell),
                Paragraph(money(first["Total adquirencia"]), table_cell_right)
            ],
            [
                Paragraph("<b>Total PayZen + adquirientes</b>", total_style),
                Paragraph(f"<b>{money(first['PayZen'])}</b>", total_style_right)
            ],
        ]

    modelo_payzen_table = Table(
            modelo_payzen_data,
            colWidths=[4.8 * inch, 2.4 * inch]
        )

    modelo_payzen_table.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),

            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#0955F9")),
            ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
            ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),

            ("BACKGROUND", (0, 7), (1, 7), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 7), (1, 7), colors.white),
            ("FONTNAME", (0, 7), (1, 7), "Helvetica-Bold"),

            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),

            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#0096FF")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))

    story.append(modelo_payzen_table)
    story.append(Spacer(1, 7))


    # ---------------------------------------------------
    # TABLA 5 - AHORRO ESTIMADO
    # ---------------------------------------------------
    
    ahorro_data = [
        [Paragraph('<font color="white"><b>Indicador</b></font>', table_header), Paragraph('<font color="white"><b>Resultado</b></font>', table_header)],
        [Paragraph("Ahorro mensual", table_cell), Paragraph(money(first["Ahorro mensual"]), ahorro_style)],
        [Paragraph("Ahorro anual", table_cell), Paragraph(money(first["Ahorro anual"]), ahorro_style)],
        [Paragraph("Ahorro porcentual", table_cell), Paragraph(percent(first["Ahorro %"]), ahorro_style)],
    ]
    ahorro_table = make_table(ahorro_data, [4.8 * inch, 2.4 * inch], header_color="#16A34A", grid_color="#BBF7D0")
    ahorro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F0FDF4")),
    ]))
    story.append(ahorro_table)
    story.append(Spacer(1, 7))

    #-------------------------------------------------
    #CONCLUSION 
    #-------------------------------------------------

    conclusion = (
        "Con base en el escenario analizado, la propuesta PayZen permite "
        f"una reducción estimada del {percent(first['Ahorro %'])} "
        "en costos transaccionales mensuales frente al modelo agregador actual."
    )
    story.append(Paragraph(conclusion, conclusion_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(DISCLAIMER, disclaimer_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


st.download_button(
    label="📄 PDF Comercial para Cliente",
    data=generar_pdf_Comercial(df),
    file_name="Resumen_Comercial_PayZen.pdf",
    mime="application/pdf"
)

st.download_button(
    label="📄 PDF Ejecutivo",
    data=generar_pdf_ejecutivo(df),
    file_name="Resumen_Ejecutivo_PayZen.pdf",
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
    "Costo actual TC",
    "Costo actual PSE",
    "Costo actual Bre-B",
    "PayZen",
    "Ahorro mensual",
    "Ahorro anual",
    "Costo adicionales",
    "Costo plan",
    "Total PayZen Gateway",
    "Costo banco TC",
    "Costo PSE PayZen",
    "Costo Bre-B PayZen",
    "Total adquirencia",
    "Ticket TC",
    "Ticket PSE",
    "Ticket Bre-B",
    "Tarifa adicional",
]

for col in columnas_dinero:
    df_mostrar[col] = df_mostrar[col].apply(money)

df_mostrar["Ahorro %"] = df_mostrar["Ahorro %"].apply(percent)
df_mostrar["Transacciones"] = df_mostrar["Transacciones"].apply(number_fmt)
df_mostrar["Tx adicionales"] = df_mostrar["Tx adicionales"].apply(number_fmt)

st.dataframe(df_mostrar, use_container_width=True)
