import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import hashlib
import hmac
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.flowables import Image
from reportlab.lib.units import inch
from io import BytesIO

st.set_page_config(
    page_title="Calculadora Comercial PayZen",
    page_icon="💳",
    layout="wide"
)

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

    return hmac.compare_digest(
        password_hash,
        USERS[username]["password_hash"]
    )

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
        font-size: 64px;
        font-weight: 900;
        color: white;
        text-align: center;
        margin-top: 80px;
    }

    .login-subtitle {
        font-size: 22px;
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
        min-width: 110px !important;
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

    st.markdown(
        '<div class="login-title">💳 Calculadora Comercial PayZen</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">Acceso interno Globalinvest Advisors</div>',
        unsafe_allow_html=True
    )

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

def money(v):
    return f"${v:,.0f}".replace(",", ".")

def percent(v):
    return f"{v:.2f}%"

def number_fmt(v):
    return f"{v:,.0f}".replace(",", ".")

def tarifa_adicional(tx):
    if tx <= 0:
        return 0
    if tx <= 500:
        return 506
    elif tx <= 1000:
        return 440
    elif tx <= 5000:
        return 385
    elif tx <= 10000:
        return 363
    return 319

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617 0%, #0F172A 45%, #082F49 100%);
}

.title-main {
    font-size: 54px;
    font-weight: 900;
    color: white;
    margin-top: 15px;
}

.subtitle-main {
    color: #CBD5E1;
    font-size: 20px;
    margin-bottom: 30px;
}

.section-title {
    font-size: 32px;
    color: white;
    font-weight: 900;
    margin-top: 35px;
    margin-bottom: 25px;
}

.card {
    background: rgba(255,255,255,0.06);
    border-radius: 24px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.10);
    min-height: 220px;
}

.card-blue {
    background: linear-gradient(135deg, #2563EB, #06B6D4);
    border-radius: 24px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.10);
    min-height: 220px;
}

.label {
    color: #CBD5E1;
    font-size: 14px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.big-number {
    color: #38BDF8;
    font-size: 42px;
    font-weight: 900;
    margin-top: 10px;
}

.big-number-orange {
    color: #F97316;
    font-size: 42px;
    font-weight: 900;
    margin-top: 10px;
}

.big-number-green {
    color: #22C55E;
    font-size: 42px;
    font-weight: 900;
    margin-top: 10px;
}

.small-text {
    color: #CBD5E1;
    font-size: 16px;
    margin-top: 15px;
    line-height: 1.5;
}

.disclaimer {
    color: rgba(255,255,255,0.60);
    font-size: 11px;
    line-height: 1.5;
    margin-top: 30px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    current_user = st.session_state.get("username", "")

    st.success(
        f"Sesión activa: {USERS.get(current_user, {'name':'Usuario'})['name']}"
    )

    if st.button("Cerrar sesión"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.header("⚙️ Parámetros")

    ticket = st.number_input(
        "Ticket promedio TC",
        value=60000,
        step=10000
    )

    plan = st.selectbox(
        "Plan PayZen",
        ["PayZen Pro", "PayZen Basic"]
    )

    if plan == "PayZen Pro":
        mensualidad = 340000
        incluidas = 500
    else:
        mensualidad = 126500
        incluidas = 100

    st.divider()

    st.subheader("Tarjetas crédito / débito")

    activar_tc = st.checkbox(
        "Activar Tarjetas",
        value=True
    )

    if activar_tc:
        tx_tc = st.number_input(
            "Transacciones TC",
            value=350
        )

        costo_fijo_actual_tc = st.number_input(
            "Costo fijo actual TC",
            value=750
        )

        porcentaje_actual_tc = st.number_input(
            "% actual TC",
            value=2.90
        )

        porcentaje_banco_tc = st.number_input(
            "% adquirencia banco TC",
            value=1.84
        )
    else:
        tx_tc = 0
        costo_fijo_actual_tc = 0
        porcentaje_actual_tc = 0
        porcentaje_banco_tc = 0

    st.divider()

    st.subheader("PSE")

    activar_pse = st.checkbox(
        "Activar PSE",
        value=False
    )

    if activar_pse:
        tx_pse = st.number_input(
            "Transacciones PSE",
            value=100
        )

        costo_actual_pse = st.number_input(
            "Costo actual PSE por tx",
            value=700
        )

        costo_payzen_pse = st.number_input(
            "Costo PayZen PSE por tx",
            value=400
        )
    else:
        tx_pse = 0
        costo_actual_pse = 0
        costo_payzen_pse = 0

    st.divider()

    st.subheader("Bre-B")

    activar_breb = st.checkbox(
        "Activar Bre-B",
        value=False
    )

    if activar_breb:
        tx_breb = st.number_input(
            "Transacciones Bre-B",
            value=100
        )

        costo_actual_breb = st.number_input(
            "Costo actual Bre-B por tx",
            value=700
        )

        costo_payzen_breb = st.number_input(
            "Costo PayZen Bre-B por tx",
            value=600
        )
    else:
        tx_breb = 0
        costo_actual_breb = 0
        costo_payzen_breb = 0

costo_actual_tc = (
    tx_tc *
    (
        costo_fijo_actual_tc +
        (ticket * porcentaje_actual_tc / 100)
    )
)

costo_actual_pse_total = tx_pse * costo_actual_pse
costo_actual_breb_total = tx_breb * costo_actual_breb

costo_total_actual = (
    costo_actual_tc +
    costo_actual_pse_total +
    costo_actual_breb_total
)

tx_totales = tx_tc + tx_pse + tx_breb

tx_adicionales = max(
    tx_totales - incluidas,
    0
)

tarifa_extra = tarifa_adicional(tx_adicionales)
costo_adicionales = tx_adicionales * tarifa_extra

costo_tc_payzen = (
    ticket *
    tx_tc *
    porcentaje_banco_tc / 100
)

costo_pse_payzen_total = tx_pse * costo_payzen_pse
costo_breb_payzen_total = tx_breb * costo_payzen_breb

costo_total_payzen = (
    mensualidad +
    costo_adicionales +
    costo_tc_payzen +
    costo_pse_payzen_total +
    costo_breb_payzen_total
)

ahorro = costo_total_actual - costo_total_payzen
ahorro_anual = ahorro * 12

col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.image(
        "Logo_Globalinvest_PayZen.png",
        width=180
    )

with col_title:
    st.markdown(
        '<div class="title-main">💳 Calculadora Comercial PayZen</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle-main">Comparativo comercial de costos</div>',
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="section-title">📊 Comparativo comercial</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)

with c1:
    st.markdown(
        f'''
        <div class="card">
            <div class="label">Pasarela actual</div>
            <div class="big-number-orange">${number_fmt(int(costo_fijo_actual_tc))} +</div>
            <div class="big-number-orange">{percent(porcentaje_actual_tc)}</div>
            <div class="small-text">por transacción</div>
            <br>
            <div class="small-text">
                Total actual:
                <b>{money(costo_total_actual)}</b>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f'''
        <div class="card-blue">
            <div class="label">Plan seleccionado</div>
            <div class="big-number">{plan}</div>
            <div class="small-text">
                Mensualidad:
                <b>{money(mensualidad)}</b>
            </div>
            <div class="small-text">
                Tx incluidas:
                <b>{number_fmt(incluidas)}</b>
            </div>
            <br>
            <div class="small-text">
                Total PayZen:
                <b>{money(costo_total_payzen)}</b>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="section-title">💰 Ahorro estimado</div>',
    unsafe_allow_html=True
)

c3, c4 = st.columns(2)

with c3:
    st.markdown(
        f'''
        <div class="card">
            <div class="label">Ahorro mensual</div>
            <div class="big-number-green">{money(ahorro)}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f'''
        <div class="card">
            <div class="label">Ahorro anual</div>
            <div class="big-number-green">{money(ahorro_anual)}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

def generar_pdf():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()
    story = []

    try:
        img = Image(
            "Logo_Globalinvest_PayZen.png",
            width=2.5*inch,
            height=1*inch
        )
        story.append(img)
    except:
        pass

    story.append(Spacer(1, 12))

    title = Paragraph(
        "Resumen Comercial PayZen",
        styles['Title']
    )

    story.append(title)
    story.append(Spacer(1, 20))

    data = [
        ["Concepto", "Valor"],
        ["Costo actual", money(costo_total_actual)],
        ["Costo PayZen", money(costo_total_payzen)],
        ["Ahorro mensual", money(ahorro)],
        ["Ahorro anual", money(ahorro_anual)],
    ]

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))

    story.append(table)
    story.append(Spacer(1, 25))

    disclaimer = Paragraph(
        """
        Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos de terceros o modificaciones acordadas entre las partes.
        """,
        styles['BodyText']
    )

    story.append(disclaimer)
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf

pdf_file = generar_pdf()

st.download_button(
    label="📄 Descargar resumen PDF",
    data=pdf_file,
    file_name="Resumen_Comercial_PayZen.pdf",
    mime="application/pdf"
)

st.markdown(
    """
    <div class="disclaimer">
    Esta proyección comercial se realiza con base en la información suministrada por el cliente durante la reunión y/o en los datos actuales compartidos para efectos de análisis. Los valores presentados son estimaciones y no constituyen una oferta definitiva ni vinculante. Las tarifas podrán estar sujetas a validación, condiciones comerciales finales, cambios en políticas de adquirencia, ajustes operativos, incrementos anuales, IPC, costos de terceros o modificaciones acordadas entre las partes.
    </div>
    """,
    unsafe_allow_html=True
)