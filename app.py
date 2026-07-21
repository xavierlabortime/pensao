import streamlit as st

st.set_page_config(page_title="Calculadora de Pensão", layout="centered")

st.title("🧮 Calculadora de Pensão Alimentícia")
st.caption("Informe os dados do empregado e veja o cálculo completo")

def calcular_inss(salario: float) -> float:
    faixas = [
        (1518.00, 0.075),
        (2793.88, 0.09),
        (4190.83, 0.12),
        (8157.41, 0.14),
    ]
    inss = 0.0
    resto = salario
    teto_anterior = 0.0
    for teto, aliquota in faixas:
        if resto <= 0:
            break
        faixa_atual = min(resto, teto - teto_anterior)
        inss += faixa_atual * aliquota
        resto -= faixa_atual
        teto_anterior = teto
    return round(min(inss, 8157.41 * 0.14), 2)

def calcular_irrf(salario: float, dependentes: int = 0) -> float:
    deducao_dependente = 189.59
    base_irrf = salario - dependentes * deducao_dependente
    faixas = [
        (2259.20, 0.0, 0.0),
        (2826.65, 0.075, 169.44),
        (3751.05, 0.15, 381.44),
        (4664.68, 0.225, 662.77),
        (float("inf"), 0.275, 896.00),
    ]
    for teto, aliquota, deducao in faixas:
        if base_irrf <= teto:
            valor = base_irrf * aliquota - deducao
            return round(max(valor, 0), 2)
    return 0.0

def calcular_pensao(salario, dependentes, percentual):
    inss = calcular_inss(salario)
    irrf = calcular_irrf(salario, dependentes)
    base_liquida = salario - inss - irrf
    valor_pensao = base_liquida * (percentual / 100)
    return {
        "salario_bruto": salario,
        "inss": inss,
        "irrf": irrf,
        "base_liquida": round(base_liquida, 2),
        "percentual": percentual,
        "valor_pensao": round(valor_pensao, 2),
    }

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        salario = st.number_input(
            "Salário bruto (R$)", min_value=0.0, step=100.0, format="%.2f",
            help="Valor base sobre o qual a pensão será calculada",
        )
        dependentes = st.number_input(
            "Nº de dependentes", min_value=0, step=1,
            help="Quantidade de dependentes legais para dedução do IRRF",
        )
    with col2:
        percentual = st.number_input(
            "Percentual da pensão (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
            help="Percentual definido judicialmente (ex: 30 para 30%)",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        desconsiderar_inss = st.checkbox("Desconsiderar INSS no cálculo", value=False)
        desconsiderar_irrf = st.checkbox("Desconsiderar IRRF no cálculo", value=False)

    calcular = st.button("🔢 Efetuar calculo da pensão", type="primary", use_container_width=True)

if calcular and salario > 0:
    resultado = calcular_pensao(salario, dependentes, percentual)
    if desconsiderar_inss:
        resultado["inss"] = 0.0
    if desconsiderar_irrf:
        resultado["irrf"] = 0.0
    base_liquida = salario - resultado["inss"] - resultado["irrf"]
    resultado["base_liquida"] = round(base_liquida, 2)
    resultado["valor_pensao"] = round(base_liquida * (percentual / 100), 2)

    st.divider()
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Salário bruto", f"R$ {resultado['salario_bruto']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col_res2.metric("Base líquida", f"R$ {resultado['base_liquida']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col_res3.metric("Percentual aplicado", f"{resultado['percentual']:.1f}%")

    st.divider()
    col_d1, col_d2 = st.columns(2)
    col_d1.metric("INSS", f"R$ {resultado['inss']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col_d2.metric("IRRF", f"R$ {resultado['irrf']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.divider()
    st.success(
        f"### 💰 Valor da pensão a descontar: **R$ {resultado['valor_pensao']:,.2f}**"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

    with st.expander("📋 Demonstrativo completo"):
        st.markdown(
            f"""
            | Item | Valor |
            |---|---:|
            | Salário bruto | R$ {resultado['salario_bruto']:,.2f} |
            | (-) INSS | R$ {resultado['inss']:,.2f} |
            | (-) IRRF | R$ {resultado['irrf']:,.2f} |
            | **= Base de cálculo** | **R$ {resultado['base_liquida']:,.2f}** |
            | × Percentual | {resultado['percentual']:.1f}% |
            | **= Pensão** | **R$ {resultado['valor_pensao']:,.2f}** |
            """
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
elif calcular:
    st.warning("Informe um salário bruto maior que zero.")
