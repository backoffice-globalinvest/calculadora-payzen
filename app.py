import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador PayZen", page_icon="💳", layout="wide")

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

def calcular_pasarela_actual(ticket, tx, fijo, porcentaje):
    variable_unitaria = ticket * porcentaje / 100
    costo_por_tx = fijo + variable_unitaria
    total = tx * costo_por_tx
    return total, costo_por_tx, variable_unitaria

def calcular_payzen(ticket, tx, plan_mensual, tx_incluidas, porcentaje_banco):
    tx_adicionales = max(tx - tx_incluidas, 0)
    tarifa_adicional = tarifa_adicional_por_rango(tx_adicionales)
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

def grafica_torta(labels, values, colors, title):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textfont=dict(color="white", size=15),
                hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>"
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(color="white", size=22)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.08,
            xanchor="center",
            x=0.5,
            font=dict(color="white", size=14)
        ),
        margin=dict(t=70, b=80, l=20, r=20),
        height=470
    )

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

.card, .card-plan, .card-compare, .card-saving, .chart-card {
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

.chart-card {
    background: rgba(255,255,255,0.045);
    min-height: 560px;
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
</style>
""")

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------

h('<div class="title">💳 Simulador Comercial PayZen Basic / Pro</div>')
h('<div class="subtitle">Comparativo de costos entre pasarela actual vs PayZen</div>')

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:
    st.header("⚙️ Parámetros base")

    ticket_promedio = st.number_input("Ticket promedio", min_value=0, value=60000, step=10000)
    tx_actuales = st.number_input("Cantidad de transacciones actuales", min_value=0, value=350, step=50)

    proyecciones_texto = st.text_area(
        "Proyecciones de transacciones",
        value="2000\n3000",
        help="Escribe una proyección por línea. También puedes separar con comas."
    )

    st.divider()
    st.subheader("Pasarela actual")

    costo_fijo_actual = st.number_input("Costo fijo actual por transacción", min_value=0, value=750, step=50)
    porcentaje_actual = st.number_input("% actual de la pasarela", min_value=0.0, value=2.90, step=0.10)

    st.divider()
    st.subheader("Plan PayZen")

    plan = st.selectbox("Selecciona el plan", ["PayZen Pro", "PayZen Basic"])
    porcentaje_banco = st.number_input("% adquirencia banco", min_value=0.0, value=1.84, step=0.01)

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
# PROYECCIONES
# ---------------------------------------------------

proyecciones = []
texto_limpio = proyecciones_texto.replace(",", "\n")

for linea in texto_limpio.splitlines():
    numero = clean_number(linea)
    if numero is not None and numero > 0:
        proyecciones.append(numero)

proyecciones = list(dict.fromkeys(proyecciones))

escenarios = [("Actual", tx_actuales)]

for tx in proyecciones:
    escenarios.append((f"Proyección {number_fmt(tx)} tx", tx))

# ---------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------

resultados = []

for nombre, tx in escenarios:
    costo_actual_total, costo_actual_por_tx, variable_actual = calcular_pasarela_actual(
        ticket_promedio,
        tx,
        costo_fijo_actual,
        porcentaje_actual
    )

    payzen = calcular_payzen(
        ticket_promedio,
        tx,
        plan_mensual,
        tx_incluidas,
        porcentaje_banco
    )

    ahorro = costo_actual_total - payzen["total"]
    ahorro_anual = ahorro * 12
    ahorro_pct = (ahorro / costo_actual_total * 100) if costo_actual_total > 0 else 0
    payzen_pct = (payzen["total"] / costo_actual_total * 100) if costo_actual_total > 0 else 0

    resultados.append({
        "Escenario": nombre,
        "Transacciones": tx,
        "Pasarela actual": costo_actual_total,
        "Costo actual por tx": costo_actual_por_tx,
        "Variable actual por tx": variable_actual,
        "PayZen": payzen["total"],
        "Ahorro mensual": ahorro,
        "Ahorro anual": ahorro_anual,
        "PayZen %": payzen_pct,
        "Ahorro %": ahorro_pct,
        "Tx adicionales": payzen["tx_adicionales"],
        "Tarifa adicional": payzen["tarifa_adicional"],
        "Costo adicionales": payzen["costo_tx_adicionales"],
        "Costo banco": payzen["costo_banco"]
    })

df = pd.DataFrame(resultados)

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
        f'<div class="big-number">{number_fmt(tx_actuales)}</div>'
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
# TORTAS MENSUAL Y ANUAL
# ---------------------------------------------------

h('<div class="section-title">🥧 Distribución de costos y ahorro</div>')

escenario_torta = st.selectbox(
    "Selecciona el escenario para ver la distribución mensual y anual",
    df["Escenario"]
)

row_torta = df[df["Escenario"] == escenario_torta].iloc[0]

actual_mensual = row_torta["Pasarela actual"]
payzen_mensual = row_torta["PayZen"]
ahorro_mensual = row_torta["Ahorro mensual"]

actual_anual = actual_mensual * 12
payzen_anual = payzen_mensual * 12
ahorro_anual = ahorro_mensual * 12

costo_evitado_mensual = max(ahorro_mensual, 0)
costo_evitado_anual = max(ahorro_anual, 0)

col_pie_1, col_pie_2 = st.columns(2, gap="large")

with col_pie_1:
    h(
        '<div class="chart-card">'
        f'<div class="label">Escenario seleccionado</div>'
        f'<div class="big-number">{escenario_torta}</div>'
        f'<div class="small-text">Comparación mensual entre el costo PayZen y el ahorro estimado frente a la pasarela actual.</div>'
        '</div>'
    )

    fig_pie_mensual = grafica_torta(
        labels=["Costo con PayZen", "Ahorro mensual"],
        values=[payzen_mensual, costo_evitado_mensual],
        colors=["#06B6D4", "#22C55E"],
        title="Distribución mensual"
    )

    st.plotly_chart(fig_pie_mensual, use_container_width=True)

with col_pie_2:
    h(
        '<div class="chart-card">'
        f'<div class="label">Resumen anual</div>'
        f'<div class="big-number-white">{money(actual_anual)}</div>'
        f'<div class="small-text">Costo anual estimado si el cliente continúa con la pasarela actual.</div>'
        '</div>'
    )

    fig_pie_anual = grafica_torta(
        labels=["Costo anual PayZen", "Ahorro anual"],
        values=[payzen_anual, costo_evitado_anual],
        colors=["#06B6D4", "#22C55E"],
        title="Distribución anual"
    )

    st.plotly_chart(fig_pie_anual, use_container_width=True)

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
            f'<div class="math-line">{number_fmt(tx)} × ({money(costo_fijo_actual)} + ({percent(porcentaje_actual)} × {money(ticket_promedio)}))</div>'
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
            f'<div class="math-line">{money(plan_mensual)} {calculo_adicionales} + {money(costo_banco_payzen)}</div>'
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
    "Variable actual por tx"
]

for col in columnas_dinero:
    df_mostrar[col] = df_mostrar[col].apply(money)

df_mostrar["PayZen %"] = df_mostrar["PayZen %"].apply(percent)
df_mostrar["Ahorro %"] = df_mostrar["Ahorro %"].apply(percent)
df_mostrar["Tarifa adicional"] = df_mostrar["Tarifa adicional"].apply(money)
df_mostrar["Transacciones"] = df_mostrar["Transacciones"].apply(number_fmt)
df_mostrar["Tx adicionales"] = df_mostrar["Tx adicionales"].apply(number_fmt)

st.dataframe(df_mostrar, use_container_width=True)
