import streamlit as st

st.set_page_config(page_title="Calculadora de Pensão", layout="centered")

st.title("🧮 Calculadora de Pensão Alimentícia")
st.caption("Tabelas INSS e IRRF 2026 — cálculo iterativo pensão × IRRF")

def calcular_inss(salario: float) -> float:
    """Tabela INSS 2026 — alíquotas progressivas"""
    faixas = [
        (1621.00, 0.075, 0.00),
        (2902.84, 0.09, 24.32),
        (4354.27, 0.12, 111.40),
        (8475.55, 0.14, 198.49),
    ]

    for teto, aliquota, deducao in faixas:
        if salario <= teto:
            return round(salario * aliquota - deducao, 2)

    return round(8475.55 * 0.14 - 198.49, 2)

def calcular_irrf_puro(base_irrf: float) -> float:
    """IRRF pela tabela progressiva 2026"""
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

def aplicar_redutor_adicional(irrf_sem_redutor: float, rendimentos: float) -> float:
    """Redutor adicional IRRF 2026 (Lei 15.270/2025)"""
    if rendimentos <= 5000.0:
        redutor = min(irrf_sem_redutor, 312.89)
        return round(irrf_sem_redutor - redutor, 2)
    elif rendimentos <= 7350.0:
        redutor = 978.61 - (0.133145 * rendimentos)
        redutor = max(redutor, 0)
        return round(max(irrf_sem_redutor - redutor, 0), 2)
    else:
        return irrf_sem_redutor

def calcular_pensao_com_loop(
    base_irrf: float,
    base_pensao: float,
    dependentes: int,
    percentual: float,
    previdencia_privada: float = 0.0,
    considerar_inss: bool = True,
    considerar_irrf: bool = True,
    max_iteracoes: int = 50,
    tolerancia: float = 0.01,
) -> dict:
    """
    Cálculo iterativo com duas bases independentes:
    - Base IRRF: rendimentos tributáveis
    - Base Pensão: apenas rendimentos sobre os quais incide a pensão
    - Previdência Privada (PGBL): dedutível da base do IRRF
    """

    inss = calcular_inss(base_irrf) if considerar_inss else 0.0

    valor_pensao = 0.0
    irrf = 0.0

    for i in range(max_iteracoes):
        # Base do IRRF = base IRRF - INSS - (dependentes × 189,59) - previdência - pensão
        base_irrf_calc = (
            base_irrf
            - inss
            - (dependentes * 189.59)
            - previdencia_privada
            - valor_pensao
        )
        base_irrf_calc = max(base_irrf_calc, 0)

        if considerar_irrf:
            irrf_novo = calcular_irrf_puro(base_irrf_calc)
            irrf_novo = aplicar_redutor_adicional(irrf_novo, base_irrf)
        else:
            irrf_novo = 0.0

        # Pensão = (base pensão - INSS - IRRF) × percentual
        base_liquida_pensao = base_pensao - inss - irrf_novo
        novo_valor_pensao = round(base_liquida_pensao * (percentual / 100), 2)

        diff_pensao = abs(novo_valor_pensao - valor_pensao)
        diff_irrf = abs(irrf_novo - irrf)

        valor_pensao = novo_valor_pensao
        irrf = irrf_novo

        if diff_pensao < tolerancia and diff_irrf < tolerancia:
            break

    base_irrf_final = (
        base_irrf
        - inss
        - (dependentes * 189.59)
        - previdencia_privada
        - valor_pensao
    )
    base_irrf_final = max(base_irrf_final, 0)

    return {
        "base_irrf": round(base_irrf, 2),
        "base_pensao": round(base_pensao, 2),
        "inss": inss,
        "dependentes": dependentes,
        "deducao_dependentes": round(dependentes * 189.59, 2),
        "previdencia_privada": round(previdencia_privada, 2),
        "base_irrf_calculo": round(base_irrf_final, 2),
        "irrf": irrf,
        "base_liquida_pensao": round(base_pensao - inss - irrf, 2),
        "percentual": percentual,
        "valor_pensao": valor_pensao,
        "iteracoes": i + 1,
    }

# --- Interface ---

with st.container():
    st.subheader("📌 Bases de cálculo")

    col1, col2 = st.columns(2)

    with col1:
        base_irrf = st.number_input(
            "Base para INSS e IRRF (R$)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            help="Total dos rendimentos tributáveis: salário + médias + 1/3 férias + HE",
        )

    with col2:
        base_pensao = st.number_input(
            "Base para Pensão (R$)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            help="Apenas os rendimentos sobre os quais incide a pensão",
        )

    st.divider()

    st.subheader("📌 Deduções do IRRF")

    col3, col4 = st.columns(2)

    with col3:
        dependentes = st.number_input(
            "Nº de dependentes",
            min_value=0,
            step=1,
            help="R$ 189,59 cada para dedução do IRRF",
        )
        considerar_inss = st.checkbox("Considerar INSS no cálculo", value=True)

    with col4:
        previdencia_privada = st.number_input(
            "Previdência Privada (PGBL) - R$",
            min_value=0.0,
            step=50.0,
            format="%.2f",
            help="Valor pago de previdência privada no mês (dedutível do IRRF)",
        )
        considerar_irrf = st.checkbox("Considerar IRRF no cálculo", value=True)

    col5, col6 = st.columns([1, 1])
    with col5:
        percentual = st.number_input(
            "Percentual da pensão (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            format="%.1f",
        )

    calcular = st.button("🔢 Calcular pensão", type="primary", use_container_width=True)

# --- Resultados ---

if calcular and base_irrf > 0 and base_pensao > 0:
    resultado = calcular_pensao_com_loop(
        base_irrf, base_pensao, dependentes, percentual,
        previdencia_privada=previdencia_privada,
        considerar_inss=considerar_inss,
        considerar_irrf=considerar_irrf,
    )

    st.divider()
    st.subheader("📊 Resultado")

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric(
        "Base IRRF",
        f"R$ {resultado['base_irrf']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    col_r2.metric(
        "Base
