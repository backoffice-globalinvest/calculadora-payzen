import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import hashlib
import hmac
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Calculadora Comercial PayZen",
    layout="wide"
)

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

USERS = {
    "comercial": {
        "password": hashlib.sha256("payzen2026".encode()).hexdigest()
    },
    "director": {
        "password": hashlib.sha256("global2026".encode()).hexdigest()
    }
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""

def verify_user(username, password):

    username = username.strip().lower()

    if username in USERS:

        hashed_input = hashlib.sha256(
            password.encode()
        ).hexdigest()

        return hmac.compare_digest(
            hashed_input,
            USERS[username]["password"]
        )

    return False

# ---------------------------------------------------
# CSS
# ---------------------------------------------------

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
}

h1, h2, h3 {
    color: white !important;
}

[data-testid="stSidebar"] {
    background: #e5e7eb;
}

.card {
    background: rgba(255,255,255,0.06);
    padding: 25px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
}

.card-payzen {
    background: linear-gradient(135deg,#2563eb,#06b6d4);
    padding: 25px;
    border-radius: 20px;
}

.card-current {
    background: rgba(255,255,255,0.06);
    padding: 25px;
    border-radius: 20px;
}

.green {
    color: #22c55e;
}

.orange {
    color: #fb923c;
}

.small-text {
    font-size: 11px;
    color: #d1d5db;
}

button[kind="primary"] {
    background: #374151 !important;
    color: #60a5fa !important;
    border-radius: 10px !important;
}

label {
    color: #0ea5e9 !important;
    font-weight: 600 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------

if not st.session_state["authenticated"]:

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <h1 style='text-align:center;'>
    💳 Calculadora Comercial PayZen
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h3 style='text-align:center;color:#cbd5e1;'>
    Acceso interno Globalinvest Advisors
    </h3>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        username = st.text_input("Usuario")
        password = st.text_input(
            "Contraseña",
            type="password"
        )

        if st.button("Ingresar"):

            if verify_user(username, password):

                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()

            else:
                st.error("Usuario o contraseña incorrectos")

    st.stop()

# ---------------------------------------------------
# FORMATOS
# ---------------------------------------------------

def money(x):
    return f"${x:,.0f}".replace(",", ".")

def percent(x):
    return f"{x:.2f}%"

def number_fmt(x):
    return f"{x:,.0f}".replace(",", ".")

# ---------------------------------------------------
# PLANES
# ---------------------------------------------------

PLANES = {
    "PayZen Basic": {
        "mensualidad": 126500,
        "incluidas": 100,
        "setup": 319000
    },
    "PayZen Pro": {
        "mensualidad": 340000,
        "incluidas": 500,
        "setup": 755500
    }
}

# ---------------------------------------------------
# COSTO TX ADICIONAL
# ---------------------------------------------------

def costo_tx_adicional(tx):

    if tx <= 500:
        return 506

    elif tx <= 1000:
        return 440

    elif tx <= 5000:
        return 385

    elif tx <= 10000:
        return 363

    return 319

# ---------------------------------------------------
# COSTO PASARELA ACTUAL
# ---------------------------------------------------

def calcular_pasarela_actual(
    ticket,
    tx,
    fijo,
    porcentaje
):

    variable = ticket * porcentaje / 100

    total_por_tx = fijo + variable

    total = tx * total_por_tx

    return total, total_por_tx, variable

# ---------------------------------------------------
# COSTO BRE-B
# ---------------------------------------------------

def calcular_breb(
    tx,
    r1_ini,
    r1_fin,
    r1_valor,
    r2_ini,
    r2_fin,
    r2_valor,
    r3_ini,
    r3_fin,
    r3_valor
):

    if tx >= r1_ini and tx <= r1_fin:
        return tx * r1_valor

    elif tx >= r2_ini and tx <= r2_fin:
        return tx * r2_valor

    return tx * r3_valor

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.success(
        f"Sesión activa: {st.session_state['username'].title()}"
    )

    if st.button("Cerrar sesión"):

        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.header("⚙️ Parámetros")

    # ---------------------------------------------------
    # DISTRIBUCIÓN
    # ---------------------------------------------------

    st.subheader("Distribución de transacciones")

    modo_transacciones = st.radio(
        "¿Cómo quieres ingresar las transacciones?",
        [
            "Por número de transacciones",
            "Por porcentaje sobre total"
        ]
    )

    activar_tc = st.checkbox(
        "Activar Tarjetas crédito / débito",
        value=True
    )

    activar_pse = st.checkbox(
        "Activar PSE",
        value=True
    )

    activar_breb = st.checkbox(
        "Activar Bre-B",
        value=False
    )

    if activar_tc:
        tx_tc_actual = st.number_input(
            "Transacciones TC",
            min_value=0,
            value=350
        )
    else:
        tx_tc_actual = 0

    if activar_pse:
        tx_pse_actual = st.number_input(
            "Transacciones PSE",
            min_value=0,
            value=0
        )
    else:
        tx_pse_actual = 0

    if activar_breb:
        tx_breb_actual = st.number_input(
            "Transacciones Bre-B",
            min_value=0,
            value=0
        )
    else:
        tx_breb_actual = 0

    total_tx = (
        tx_tc_actual
        + tx_pse_actual
        + tx_breb_actual
    )

    st.divider()

    # ---------------------------------------------------
    # TICKETS
    # ---------------------------------------------------

    st.subheader("Ticket promedio")

    modo_ticket = st.radio(
        "Modo ticket",
        [
            "Un solo ticket para todos",
            "Ticket por canal"
        ]
    )

    if modo_ticket == "Un solo ticket para todos":

        ticket_general = st.number_input(
            "Ticket promedio general",
            min_value=0,
            value=60000
        )

        ticket_tc = ticket_general
        ticket_pse = ticket_general
        ticket_breb = ticket_general

    else:

        ticket_tc = st.number_input(
            "Ticket promedio TC",
            min_value=0,
            value=60000
        )

        ticket_pse = st.number_input(
            "Ticket promedio PSE",
            min_value=0,
            value=40000
        )

        ticket_breb = st.number_input(
            "Ticket promedio Bre-B",
            min_value=0,
            value=40000
        )

    st.divider()

    # ---------------------------------------------------
    # PASARELA ACTUAL
    # ---------------------------------------------------

    st.subheader("Pasarela actual")

    costo_fijo_actual = st.number_input(
        "Costo fijo actual por transacción",
        min_value=0,
        value=750
    )

    porcentaje_actual = st.number_input(
        "% actual de la pasarela",
        min_value=0.0,
        value=2.90
    )

    st.divider()

    # ---------------------------------------------------
    # ADQUIRENCIA
    # ---------------------------------------------------

    st.subheader("Costos adquirencia / procesamiento")

    porcentaje_banco = st.number_input(
        "% adquirencia banco TC",
        min_value=0.0,
        value=1.84
    )

    costo_pse_payzen = st.number_input(
        "Costo PSE PayZen por tx",
        min_value=0,
        value=400
    )

    st.divider()

    # ---------------------------------------------------
    # BRE-B
    # ---------------------------------------------------

    st.subheader("Rangos Bre-B PayZen")

    breb_r1_ini = st.number_input(
        "Rango 1 inicial",
        value=1
    )

    breb_r1_fin = st.number_input(
        "Rango 1 final",
        value=10000
    )

    breb_r1_valor = st.number_input(
        "Valor rango 1",
        value=600
    )

    breb_r2_ini = st.number_input(
        "Rango 2 inicial",
        value=10001
    )

    breb_r2_fin = st.number_input(
        "Rango 2 final",
        value=100000
    )

    breb_r2_valor = st.number_input(
        "Valor rango 2",
        value=550
    )

    breb_r3_ini = st.number_input(
        "Rango 3 inicial",
        value=100001
    )

    breb_r3_fin = st.number_input(
        "Rango 3 final",
        value=999999
    )

    breb_r3_valor = st.number_input(
        "Valor rango 3",
        value=500
    )

    st.divider()

    # ---------------------------------------------------
    # PLAN
    # ---------------------------------------------------

    st.subheader("Plan PayZen")

    plan = st.selectbox(
        "Selecciona el plan",
        list(PLANES.keys())
    )

# ---------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------

datos_plan = PLANES[plan]

mensualidad = datos_plan["mensualidad"]
incluidas = datos_plan["incluidas"]

# actual

costo_actual_total, _, _ = calcular_pasarela_actual(
    ticket_tc,
    total_tx,
    costo_fijo_actual,
    porcentaje_actual
)

# adicionales

tx_adicionales = max(
    total_tx - incluidas,
    0
)

valor_tx_extra = costo_tx_adicional(
    total_tx
)

costo_extra = tx_adicionales * valor_tx_extra

# tc

costo_tc_payzen = (
    ticket_tc
    * tx_tc_actual
    * porcentaje_banco
    / 100
)

# pse

costo_pse_total = (
    tx_pse_actual
    * costo_pse_payzen
)

# breb

costo_breb_total = calcular_breb(
    tx_breb_actual,
    breb_r1_ini,
    breb_r1_fin,
    breb_r1_valor,
    breb_r2_ini,
    breb_r2_fin,
    breb_r2_valor,
    breb_r3_ini,
    breb_r3_fin,
    breb_r3_valor
)

# total payzen

costo_payzen_total = (
    mensualidad
    + costo_extra
    + costo_tc_payzen
    + costo_pse_total
    + costo_breb_total
)

ahorro = costo_actual_total - costo_payzen_total
ahorro_anual = ahorro * 12

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

st.title("📊 Comparativo comercial")

# ---------------------------------------------------
# CARDS
# ---------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    st.markdown(f"""
    <div class='card-current'>
        <h5>PASARELA ACTUAL</h5>
        <h1 class='orange'>
        ${number_fmt(costo_fijo_actual)} +
        </h1>
        <h1 class='orange'>
        {percent(porcentaje_actual)}
        </h1>
        <p>por transacción</p>
        <br>
        <b>Total actual: {money(costo_actual_total)}</b>
    </div>
    """, unsafe_allow_html=True)

with col2:

    st.markdown(f"""
    <div class='card-payzen'>
        <h5>PLAN SELECCIONADO</h5>
        <h1>{plan}</h1>

        <p>Mensualidad: {money(mensualidad)}</p>
        <p>Tx incluidas: {incluidas}</p>

        <br>

        <b>Total PayZen: {money(costo_payzen_total)}</b>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# AHORRO
# ---------------------------------------------------

st.markdown("<br>", unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:

    st.markdown(f"""
    <div class='card'>
        <h5>AHORRO MENSUAL</h5>
        <h1 class='green'>{money(ahorro)}</h1>
    </div>
    """, unsafe_allow_html=True)

with col4:

    st.markdown(f"""
    <div class='card'>
        <h5>AHORRO ANUAL</h5>
        <h1 class='green'>{money(ahorro_anual)}</h1>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# GRÁFICA
# ---------------------------------------------------

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=["Pasarela actual", "PayZen"],
        y=[costo_actual_total, costo_payzen_total]
    )
)

fig.update_layout(
    height=450,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white')
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ---------------------------------------------------
# TABLA
# ---------------------------------------------------

st.subheader("Resumen")

df = pd.DataFrame({
    "Concepto": [
        "Costo actual",
        "Costo PayZen",
        "Ahorro mensual",
        "Ahorro anual"
    ],
    "Valor": [
        money(costo_actual_total),
        money(costo_payzen_total),
        money(ahorro),
        money(ahorro_anual)
    ]
})

st.dataframe(
    df,
    use_container_width=True
)

# ---------------------------------------------------
# PDF
# ---------------------------------------------------

def generar_pdf():

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(
        Paragraph(
            "Resumen Comercial PayZen",
            styles["Heading1"]
        )
    )

    elementos.append(Spacer(1, 20))

    data = [
        ["Concepto", "Valor"],
        ["Costo actual", money(costo_actual_total)],
        ["Costo PayZen", money(costo_payzen_total)],
        ["Ahorro mensual", money(ahorro)],
        ["Ahorro anual", money(ahorro_anual)]
    ]

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elementos.append(table)

    elementos.append(Spacer(1, 20))

    disclaimer = """
    Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante.
    """

    elementos.append(
        Paragraph(
            disclaimer,
            styles["BodyText"]
        )
    )

    doc.build(elementos)

    buffer.seek(0)

    return buffer

pdf = generar_pdf()

st.download_button(
    "📄 Descargar resumen PDF",
    data=pdf,
    file_name="resumen_payzen.pdf",
    mime="application/pdf"
)

# ---------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------

st.markdown("""
<p class='small-text'>
Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos de terceros o modificaciones acordadas entre las partes.
</p>
""", unsafe_allow_html=True)