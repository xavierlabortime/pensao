import streamlit as st

st.set_page_config(page_title="Calculadora de Pensão", layout="centered")

st.title("🧮 Pensão Alimentícia")
st.caption("Tabelas INSS e IRRF 2026 — cálculo iterativo pensão x IRRF")

def calcular_inss(salario: float) -> float:
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

def aplicar_redutor(irrf_sem_redutor: float, rendimentos: float) -> float:
    if rendimentos <= 5000.0:
        redutor = min(irrf_sem_redutor, 312.89)
        return round(irrf_sem_redutor - redutor, 2)
    elif rendimentos <= 7350.0:
        redutor = 978.61 - (0.133145 * rendimentos)
        redutor = max(redutor, 0)
        return round(max(irrf_sem_redutor - redutor, 0), 2)
    else:
        return irrf_sem_redutor

def fmt(valor):
    """Formata valor para padrão brasileiro: 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular(
    base_irrf,
    base_pensao,
    dependentes,
    percentual,
    prev_privada=0.0,
    considerar_inss=True,
    considerar_irrf=True,
):
    inss = calcular_inss(base_irrf) if considerar_inss else 0.0
    valor_pensao = 0.0
    irrf = 0.0

    for _ in range(50):
        base_calc = base_irrf - inss - (dependentes * 189.59) - prev_privada - valor_pensao
        base_calc = max(base_calc, 0)

        irrf_novo = 0.0
        if considerar_irrf:
            irrf_novo = calcular_irrf_puro(base_calc)
            irrf_novo = aplicar_redutor(irrf_novo, base_irrf)

        base_liquida = base_pensao - inss - irrf_novo
        novo_pensao = round(base_liquida * (percentual / 100), 2)

        if abs(novo_pensao - valor_pensao) < 0.01 and abs(irrf_novo - irrf) < 0.01:
            valor_pensao = novo_pensao
            irrf = irrf_novo
            break

        valor_pensao = novo_pensao
        irrf = irrf_novo

    base_irrf_final = base_irrf - inss - (dependentes * 189.59) - prev_privada - valor_pensao
    base_irrf_final = max(base_irrf_final, 0)

    return {
        "base_irrf": round(base_irrf, 2),
        "base_pensao": round(base_pensao, 2),
        "inss": inss,
        "dependentes": dependentes,
        "deducao_dep": round(dependentes * 189.59, 2),
        "prev_privada": round(prev_privada, 2),
        "base_irrf_calc": round(base_irrf_final, 2),
        "irrf": irrf,
        "base_liquida": round(base_pensao - inss - irrf, 2),
        "percentual": percentual,
        "pensao": valor_pensao,
    }

# --- INTERFACE ---

st.subheader("Bases de calculo")

c1, c2 = st.columns(2)
with c1:
    b_irrf = st.number_input("Base INSS e IRRF (R$)", min_value=0.0, step=100.0, format="%.2f",
                             help="Salario + medias + 1/3 ferias + HE + demais verbas")
with c2:
    b_pensao = st.number_input("Base da Pensao (R$)", min_value=0.0, step=100.0, format="%.2f",
                               help="Apenas as verbas que incidem pensao")

st.divider()
st.subheader("Deducoes do IRRF")

c3, c4 = st.columns(2)
with c3:
    dep = st.number_input("Numero de dependentes", min_value=0, step=1)
    com_inss = st.checkbox("Considerar INSS", value=True)
with c4:
    prev = st.number_input("Previdencia Privada (PGBL) R$", min_value=0.0, step=50.0, format="%.2f",
                           help="Valor pago de previdencia privada no mes")
    com_irrf = st.checkbox("Considerar IRRF", value=True)

perc = st.number_input("Percentual da pensao (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f")

calcular_btn = st.button("Calcular pensao", type="primary", use_container_width=True)

# --- RESULTADO ---

if calcular_btn and b_irrf > 0 and b_pensao > 0:
    r = calcular(b_irrf, b_pensao, dep, perc, prev, com_inss, com_irrf)

    st.divider()
    st.subheader("Resultado")

    cr1, cr2, cr3 = st.columns(3)
    cr1.metric("Base IRRF", fmt(r["base_irrf"]))
    cr2.metric("Base Pensao", fmt(r["base_pensao"]))
    cr3.metric("Percentual", f'{r["percentual"]:.1f}%')

    st.divider()

    cd1, cd2, cd3 = st.columns(3)
    cd1.metric("INSS", fmt(r["inss"]), delta="Desconsiderado" if not com_inss else "", delta_color="off")
    cd2.metric("IRRF", fmt(r["irrf"]), delta="Desconsiderado" if not com_irrf else "", delta_color="off")
    cd3.metric("Prev. Privada", fmt(r["prev_privada"]))

    st.divider()

    st.success(f'Valor da pensao a descontar: {fmt(r["pensao"])}')

    with st.expander("Ver demonstrativo completo"):
        txt = f"""
**1. Bases informadas**
| Item | Valor |
|---|---:|
| Base INSS e IRRF | {fmt(r["base_irrf"])} |
| Base Pensao | {fmt(r["base_pensao"])} |

**2. Calculo do IRRF** (iterativo com pensao)
| Item | Valor |
|---|---:|
| Base IRRF total | {fmt(r["base_irrf"])} |
| (-) INSS | {fmt(r["inss"])} |
| (-) Dependentes ({r["dependentes"]} x 189,59) | {fmt(r["deducao_dep"])} |
| (-) Previdencia Privada | {fmt(r["prev_privada"])} |
| (-) Pensao | {fmt(r["pensao"])} |
| **= Base de calculo IRRF** | **{fmt(r["base_irrf_calc"])}** |
| IRRF (com redutor 2026) | {fmt(r["irrf"])} |

**3. Calculo da Pensao**
| Item | Valor |
|---|---:|
| Base pensao | {fmt(r["base_pensao"])} |
| (-) INSS | {fmt(r["inss"])} |
| (-) IRRF | {fmt(r["irrf"])} |
| **= Base liquida** | **{fmt(r["base_liquida"])}** |
| x Percentual | {r["percentual"]:.1f}% |
| **= Pensao** | **{fmt(r["pensao"])}** |
"""
        st.markdown(txt)

elif calcular_btn:
    st.warning("Preencha a base IRRF e a base Pensao com valores maiores que zero.")
