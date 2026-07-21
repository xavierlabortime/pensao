import streamlit as st

st.set_page_config(page_title="Calculadora de Pensão", layout="centered")

st.title("🧮 Calculadora de Pensão Alimentícia")
st.caption("Tabelas INSS e IRRF 2026 atualizadas — cálculo iterativo pensão × IRRF")

def calcular_inss(salario: float) -> float:
    """Tabela INSS 2026 — alíquotas progressivas com dedução"""
    faixas = [
        (1621.00, 0.075, 0.00),
        (2902.84, 0.09, 24.32),
        (4354.27, 0.12, 111.40),
        (8475.55, 0.14, 198.49),
    ]

    for teto, aliquota, deducao in faixas:
        if salario <= teto:
            return round(salario * aliquota - deducao, 2)

    # Acima do teto máximo
    return round(8475.55 * 0.14 - 198.49, 2)

def calcular_irrf_puro(base_irrf: float) -> float:
    """Calcula o IRRF pela tabela progressiva (sem redutor)"""
    faixas = [
        (2428.80, 0.0, 0.00),
        (2826.65, 0.075, 182.16),
        (3751.05, 0.15, 394.16),
        (4664.68, 0.225, 675.49),
        (float("inf"), 0.275, 908.73),
    ]

    for teto, aliquota, deducao in faixas:
        if base_irrf <= teto:
            return round(base_irrf * aliquota - deducao, 2)

    return 0.0

def aplicar_redutor_adicional(irrf_sem_redutor: float, rendimentos_tributaveis: float) -> float:
    """
    Aplica o redutor adicional do IRRF 2026 (Lei 15.270/2025).
    - Até R$ 5.000: redução de até R$ 312,89 (zera o IRRF)
    - R$ 5.000,01 a R$ 7.350: redução decrescente linear
    - Acima de R$ 7.350: sem redução
    """
    if rendimentos_tributaveis <= 5000.0:
        redutor = min(irrf_sem_redutor, 312.89)
        return round(irrf_sem_redutor - redutor, 2)

    elif rendimentos_tributaveis <= 7350.0:
        # Fórmula: Redutor = 978,61 - (0,133145 × rendimentos_tributáveis)
        redutor = 978.61 - (0.133145 * rendimentos_tributaveis)
        redutor = max(redutor, 0)
        return round(max(irrf_sem_redutor - redutor, 0), 2)

    else:
        return irrf_sem_redutor

def calcular_irrf_completo(base_irrf: float, rendimentos_tributaveis: float) -> float:
    """Calcula IRRF completo: tabela progressiva + redutor adicional"""
    irrf_sem_redutor = calcular_irrf_puro(base_irrf)
    return aplicar_redutor_adicional(irrf_sem_redutor, rendimentos_tributaveis)

def calcular_pensao_com_loop(
    salario_bruto: float,
    dependentes: int,
    percentual: float,
    considerar_inss: bool = True,
    considerar_irrf: bool = True,
    max_iteracoes: int = 50,
    tolerancia: float = 0.01,
) -> dict:
    """
    Cálculo iterativo com loop pensão × IRRF:
    - A pensão é dedutível do IRRF (base do IRRF = salário - INSS - dependentes - pensão)
    - O IRRF reduz a base da pensão
    - Esses valores são interdependentes → precisa iterar até convergir
    """
    inss = calcular_inss(salario_bruto) if considerar_inss else 0.0

    # Estimativa inicial (sem pensão nem IRRF)
    valor_pensao = 0.0
    irrf = 0.0

    for i in range(max_iteracoes):
        # Calcula base do IRRF considerando pensão como dedução
        base_irrf = salario_bruto - inss - (dependentes * 189.59) - valor_pensao
        base_irrf = max(base_irrf, 0)

        # Os rendimentos tributáveis para o redutor são o salário bruto
        # (sem deduções) conforme esclarecimento da Receita Federal
        rendimentos_trib = salario_bruto

        if considerar_irrf:
            irrf_novo = calcular_irrf_completo(base_irrf, rendimentos_trib)
        else:
            irrf_novo = 0.0

        # Base líquida = salário - INSS - IRRF
        base_liquida = salario_bruto - inss - irrf_novo
        novo_valor_pensao = round(base_liquida * (percentual / 100), 2)

        # Verifica convergência
        diff_pensao = abs(novo_valor_pensao - valor_pensao)
        diff_irrf = abs(irrf_novo - irrf)

        valor_pensao = novo_valor_pensao
        irrf = irrf_novo

        if diff_pensao < tolerancia and diff_irrf < tolerancia:
            break

    base_irrf_final = salario_bruto - inss - (dependentes * 189.59) - valor_pensao
    base_irrf_final = max(base_irrf_final, 0)

    return {
        "salario_bruto": round(salario_bruto, 2),
        "inss": inss,
        "dependentes": dependentes,
        "deducao_dependentes": round(dependentes * 189.59, 2),
        "base_irrf": round(base_irrf_final, 2),
        "irrf": irrf,
        "base_liquida": round(salario_bruto - inss - irrf, 2),
        "percentual": percentual,
        "valor_pensao": valor_pensao,
        "iteracoes": i + 1,
    }

# --- Interface ---

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        salario = st.number_input(
            "Salário bruto (R$)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            help="Valor base sobre o qual a pensão será calculada",
        )
        dependentes = st.number_input(
            "Nº de dependentes",
            min_value=0,
            step=1,
            help="Quantidade de dependentes legais para dedução do IRRF",
        )

    with col2:
        percentual = st.number_input(
            "Percentual da pensão (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            format="%.1f",
            help="Percentual definido judicialmente (ex: 30 para 30%)",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        considerar_inss = st.checkbox("Considerar INSS no cálculo", value=True)
        considerar_irrf = st.checkbox("Considerar IRRF no cálculo", value=True)

    calcular = st.button("🔢 Calcular pensão", type="primary", use_container_width=True)

if calcular and salario > 0:
    resultado = calcular_pensao_com_loop(
        salario, dependentes, percentual,
        considerar_inss=considerar_inss,
        considerar_irrf=considerar_irrf,
    )

    st.divider()

    # Métricas principais
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric(
        "Salário bruto",
        f"R$ {resultado['salario_bruto']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    col_r2.metric(
        "Base líquida (p/ pensão)",
        f"R$ {resultado['base_liquida']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    col_r3.metric(
        "Percentual",
        f"{resultado['percentual']:.1f}%"
    )

    st.divider()

    # Descontos
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric(
        "INSS",
        f"R$ {resultado['inss']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta="Desconsiderado" if not considerar_inss else "",
        delta_color="off",
    )
    col_d2.metric(
        "IRRF",
        f"R$ {resultado['irrf']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta="Desconsiderado" if not considerar_irrf else "",
        delta_color="off",
    )
    col_d3.metric(
        "Dedução dependentes",
        f"R$ {resultado['deducao_dependentes']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    st.divider()

    # Resultado principal
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
            | (-) Dedução dependentes ({dependentes}) | R$ {resultado['deducao_dependentes']:,.2f} |
            | (-) Pensão | R$ {resultado['valor_pensao']:,.2f} |
            | **= Base de cálculo IRRF** | **R$ {resultado['base_irrf']:,.2f}** |
            | (-) IRRF (com redutor 2026) | R$ {resultado['irrf']:,.2f} |
            | **= Base líquida para pensão** | **R$ {resultado['base_liquida']:,.2f}** |
            | × Percentual | {resultado['percentual']:.1f}% |
            | **= Pensão calculada** | **R$ {resultado['valor_pensao']:,.2f}** |
            """
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )

        st.caption(f"🔄 Cálculo convergiu em {resultado['iteracoes']} iteração(ões)")

elif calcular:
    st.warning("Informe um salário bruto maior que zero.")
