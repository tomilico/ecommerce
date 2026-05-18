"""
E-commerce Analytics Dashboard
Streamlit + Supabase (PostgreSQL)
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Config geral
# ─────────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Paleta de cores consistente
# ─────────────────────────────────────────────
COLOR_PRIMARY   = "#6C63FF"
COLOR_SUCCESS   = "#22C55E"
COLOR_WARNING   = "#F59E0B"
COLOR_DANGER    = "#EF4444"
COLOR_NEUTRAL   = "#94A3B8"

SEGMENT_COLORS = {
    "VIP":       "#6C63FF",
    "TOP_TIER":  "#F59E0B",
    "REGULAR":   "#94A3B8",
}

PRICE_COLORS = {
    "MAIS_CARO_QUE_TODOS":   "#EF4444",
    "ACIMA_DA_MEDIA":        "#F97316",
    "NA_MEDIA":              "#94A3B8",
    "ABAIXO_DA_MEDIA":       "#34D399",
    "MAIS_BARATO_QUE_TODOS": "#22C55E",
}

TEMPLATE = "plotly_dark"

# ─────────────────────────────────────────────
# CSS customizado
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Fundo geral */
    [data-testid="stAppViewContainer"] {
        background: #0F1117;
    }
    [data-testid="stSidebar"] {
        background: #1A1D27;
        border-right: 1px solid #2D3148;
    }

    /* Métrica cards */
    [data-testid="metric-container"] {
        background: #1A1D27;
        border: 1px solid #2D3148;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="metric-container"] label {
        color: #94A3B8 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #F1F5F9 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* Título sidebar */
    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #6C63FF;
        margin-bottom: 0.25rem;
    }
    .sidebar-sub {
        font-size: 0.75rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }

    /* Alert box */
    .alert-box {
        background: #2D1B1B;
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 12px 16px;
        color: #FCA5A5;
        font-size: 0.85rem;
    }

    /* Section header */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #CBD5E1;
        border-left: 3px solid #6C63FF;
        padding-left: 10px;
        margin: 1.5rem 0 0.75rem 0;
    }

    /* Esconde botão "Made with Streamlit" */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers de formatação
# ─────────────────────────────────────────────
def fmt_brl(value: float) -> str:
    """Formata número como moeda brasileira: R$ 1.234,56"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(value) -> str:
    """Formata inteiro com separador de milhar."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "0"
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float) -> str:
    """Formata percentual com sinal: +1.5% ou -2.3%"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "0,0%"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%".replace(".", ",")


# ─────────────────────────────────────────────
# Conexão com o banco
# ─────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=int(os.getenv("SUPABASE_PORT", 5432)),
        dbname=os.getenv("SUPABASE_DB", "postgres"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD"),
        connect_timeout=10,
    )


def run_query(sql: str) -> pd.DataFrame:
    """Executa SQL e retorna DataFrame. Sem cache para refletir dbt run."""
    try:
        conn = get_connection()
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ **Erro de conexão com o banco:** {e}")
        st.stop()


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📊 E-commerce Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Gold Layer · Supabase PostgreSQL</div>', unsafe_allow_html=True)

    pagina = st.radio(
        "Navegação",
        options=["📈 Vendas", "👥 Clientes", "💰 Pricing"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown('<div style="font-size:0.7rem;color:#475569;">Dados via dbt Gold Layer<br>Atualizado a cada dbt run</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# PÁGINA 1 — VENDAS
# ═══════════════════════════════════════════════
if pagina == "📈 Vendas":
    st.markdown("## 📈 Vendas — Visão Comercial")

    # Carrega dados
    df = run_query("SELECT * FROM public_gold_sales.vendas_temporais ORDER BY data_venda, hora_venda")

    # Filtro de mês
    meses_disponiveis = sorted(df["mes_venda"].unique())
    meses_label = {m: f"Mês {int(m):02d}" for m in meses_disponiveis}
    col_f, _ = st.columns([2, 8])
    with col_f:
        mes_sel = st.selectbox(
            "Filtrar por mês",
            options=["Todos"] + [meses_label[m] for m in meses_disponiveis],
        )

    if mes_sel != "Todos":
        mes_num = int(mes_sel.split(" ")[1])
        df = df[df["mes_venda"] == mes_num]

    # ── KPIs ──────────────────────────────────
    receita_total  = df["receita_total"].sum()
    total_vendas   = df["total_vendas"].sum()
    ticket_medio   = receita_total / total_vendas if total_vendas > 0 else 0
    clientes_unicos = df.groupby("data_venda")["total_clientes_unicos"].max().sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💵 Receita Total",    fmt_brl(receita_total))
    k2.metric("🛒 Total de Vendas",  fmt_int(total_vendas))
    k3.metric("🎯 Ticket Médio",     fmt_brl(ticket_medio))
    k4.metric("👤 Clientes Únicos",  fmt_int(clientes_unicos))

    st.markdown("---")

    # ── Gráfico 1: Receita Diária ─────────────
    st.markdown('<div class="section-header">Receita Diária</div>', unsafe_allow_html=True)
    df_dia = df.groupby("data_venda", as_index=False)["receita_total"].sum()
    fig1 = px.line(
        df_dia,
        x="data_venda",
        y="receita_total",
        title="",
        labels={"data_venda": "Data", "receita_total": "Receita (R$)"},
        template=TEMPLATE,
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig1.update_traces(line_width=2.5, fill="tozeroy", fillcolor="rgba(108,99,255,0.12)")
    fig1.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#1E2235"),
        margin=dict(t=10, b=20),
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ── Gráficos 2 & 3 lado a lado ───────────
    col_g2, col_g3 = st.columns(2)

    with col_g2:
        st.markdown('<div class="section-header">Receita por Dia da Semana</div>', unsafe_allow_html=True)
        ordem_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        df_sem = df.groupby("dia_semana_nome", as_index=False)["receita_total"].sum()
        df_sem["dia_semana_nome"] = pd.Categorical(df_sem["dia_semana_nome"], categories=ordem_dias, ordered=True)
        df_sem = df_sem.sort_values("dia_semana_nome")
        fig2 = px.bar(
            df_sem,
            x="dia_semana_nome",
            y="receita_total",
            labels={"dia_semana_nome": "Dia", "receita_total": "Receita (R$)"},
            template=TEMPLATE,
            color_discrete_sequence=[COLOR_PRIMARY],
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#1E2235"),
            margin=dict(t=10, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_g3:
        st.markdown('<div class="section-header">Volume de Vendas por Hora</div>', unsafe_allow_html=True)
        df_hora = df.groupby("hora_venda", as_index=False)["total_vendas"].sum()
        fig3 = px.bar(
            df_hora,
            x="hora_venda",
            y="total_vendas",
            labels={"hora_venda": "Hora", "total_vendas": "Vendas"},
            template=TEMPLATE,
            color_discrete_sequence=[COLOR_WARNING],
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#1E2235"),
            xaxis=dict(tickmode="linear", dtick=1),
            margin=dict(t=10, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════
# PÁGINA 2 — CLIENTES
# ═══════════════════════════════════════════════
elif pagina == "👥 Clientes":
    st.markdown("## 👥 Clientes — Customer Success")

    df = run_query("SELECT * FROM public_gold_cs.clientes_segmentacao ORDER BY ranking_receita")

    # ── KPIs ──────────────────────────────────
    total_clientes  = len(df)
    df_vip          = df[df["segmento_cliente"] == "VIP"]
    clientes_vip    = len(df_vip)
    receita_vip     = df_vip["receita_total"].sum()
    ticket_medio    = df["ticket_medio"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Total de Clientes",  fmt_int(total_clientes))
    k2.metric("⭐ Clientes VIP",       fmt_int(clientes_vip))
    k3.metric("💎 Receita VIP",        fmt_brl(receita_vip))
    k4.metric("🎯 Ticket Médio Geral", fmt_brl(ticket_medio))

    st.markdown("---")

    # ── Gráficos 1 & 2 lado a lado ───────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown('<div class="section-header">Distribuição por Segmento</div>', unsafe_allow_html=True)
        df_seg = df.groupby("segmento_cliente", as_index=False).size().rename(columns={"size": "total"})
        fig1 = px.pie(
            df_seg,
            names="segmento_cliente",
            values="total",
            hole=0.5,
            color="segmento_cliente",
            color_discrete_map=SEGMENT_COLORS,
            template=TEMPLATE,
        )
        fig1.update_traces(textposition="outside", textinfo="percent+label")
        fig1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        st.markdown('<div class="section-header">Receita por Segmento</div>', unsafe_allow_html=True)
        df_rec_seg = df.groupby("segmento_cliente", as_index=False)["receita_total"].sum()
        ordem_seg = ["VIP", "TOP_TIER", "REGULAR"]
        df_rec_seg["segmento_cliente"] = pd.Categorical(df_rec_seg["segmento_cliente"], categories=ordem_seg, ordered=True)
        df_rec_seg = df_rec_seg.sort_values("segmento_cliente")
        fig2 = px.bar(
            df_rec_seg,
            x="segmento_cliente",
            y="receita_total",
            color="segmento_cliente",
            color_discrete_map=SEGMENT_COLORS,
            template=TEMPLATE,
            labels={"segmento_cliente": "Segmento", "receita_total": "Receita (R$)"},
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#1E2235"),
            showlegend=False,
            margin=dict(t=10, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Gráfico 3: Top 10 Clientes ────────────
    st.markdown('<div class="section-header">Top 10 Clientes por Receita</div>', unsafe_allow_html=True)
    df_top10 = df[df["ranking_receita"] <= 10].sort_values("receita_total")
    fig3 = px.bar(
        df_top10,
        x="receita_total",
        y="nome_cliente",
        orientation="h",
        color="segmento_cliente",
        color_discrete_map=SEGMENT_COLORS,
        template=TEMPLATE,
        labels={"receita_total": "Receita (R$)", "nome_cliente": ""},
        text="receita_total",
    )
    fig3.update_traces(texttemplate="R$ %{x:,.0f}", textposition="outside")
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#1E2235"),
        margin=dict(t=10, b=20, l=10),
        height=380,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Gráfico 4: Clientes por Estado ────────
    st.markdown('<div class="section-header">Clientes por Estado</div>', unsafe_allow_html=True)
    df_estado = df.groupby("estado", as_index=False).size().rename(columns={"size": "total"}).sort_values("total", ascending=False)
    fig4 = px.bar(
        df_estado,
        x="estado",
        y="total",
        template=TEMPLATE,
        color_discrete_sequence=[COLOR_PRIMARY],
        labels={"estado": "Estado (UF)", "total": "Clientes"},
    )
    fig4.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#1E2235"),
        margin=dict(t=10, b=20),
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ── Tabela detalhada ──────────────────────
    st.markdown('<div class="section-header">Tabela de Clientes</div>', unsafe_allow_html=True)
    col_filt, _ = st.columns([2, 8])
    with col_filt:
        seg_filter = st.selectbox("Filtrar por segmento", ["Todos", "VIP", "TOP_TIER", "REGULAR"])

    df_tabela = df if seg_filter == "Todos" else df[df["segmento_cliente"] == seg_filter]
    st.dataframe(
        df_tabela[[
            "ranking_receita", "nome_cliente", "estado", "segmento_cliente",
            "receita_total", "total_compras", "ticket_medio",
            "primeira_compra", "ultima_compra",
        ]].rename(columns={
            "ranking_receita": "Rank",
            "nome_cliente": "Nome",
            "estado": "UF",
            "segmento_cliente": "Segmento",
            "receita_total": "Receita (R$)",
            "total_compras": "Compras",
            "ticket_medio": "Ticket Médio",
            "primeira_compra": "1ª Compra",
            "ultima_compra": "Última Compra",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ═══════════════════════════════════════════════
# PÁGINA 3 — PRICING
# ═══════════════════════════════════════════════
elif pagina == "💰 Pricing":
    st.markdown("## 💰 Pricing — Inteligência Competitiva")

    df = run_query("SELECT * FROM public_gold_pricing.precos_competitividade")

    # ── Filtro por categoria ──────────────────
    categorias = sorted(df["categoria"].unique())
    cats_sel = st.multiselect(
        "Filtrar por categoria",
        options=categorias,
        default=categorias,
        placeholder="Selecione categorias...",
    )
    if cats_sel:
        df = df[df["categoria"].isin(cats_sel)]

    # ── KPIs ──────────────────────────────────
    total_produtos   = len(df)
    mais_caros       = len(df[df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"])
    mais_baratos     = len(df[df["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS"])
    dif_media        = df["diferenca_percentual_vs_media"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📦 Produtos Monitorados",   fmt_int(total_produtos))
    k2.metric("🔴 Mais Caros que Todos",   fmt_int(mais_caros))
    k3.metric("🟢 Mais Baratos que Todos", fmt_int(mais_baratos))
    k4.metric("📊 Diferença Média vs Mercado", fmt_pct(dif_media))

    st.markdown("---")

    # ── Gráficos 1 & 2 lado a lado ───────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown('<div class="section-header">Posicionamento vs Concorrência</div>', unsafe_allow_html=True)
        df_class = df.groupby("classificacao_preco", as_index=False).size().rename(columns={"size": "total"})
        fig1 = px.pie(
            df_class,
            names="classificacao_preco",
            values="total",
            hole=0.45,
            color="classificacao_preco",
            color_discrete_map=PRICE_COLORS,
            template=TEMPLATE,
        )
        fig1.update_traces(textposition="outside", textinfo="percent+label")
        fig1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        st.markdown('<div class="section-header">Competitividade por Categoria</div>', unsafe_allow_html=True)
        df_cat = df.groupby("categoria", as_index=False)["diferenca_percentual_vs_media"].mean().sort_values("diferenca_percentual_vs_media")
        df_cat["cor"] = df_cat["diferenca_percentual_vs_media"].apply(
            lambda x: COLOR_SUCCESS if x < 0 else COLOR_DANGER
        )
        fig2 = px.bar(
            df_cat,
            x="categoria",
            y="diferenca_percentual_vs_media",
            color="diferenca_percentual_vs_media",
            color_continuous_scale=[[0, COLOR_SUCCESS], [0.5, COLOR_NEUTRAL], [1, COLOR_DANGER]],
            template=TEMPLATE,
            labels={"categoria": "Categoria", "diferenca_percentual_vs_media": "Dif. % vs Média"},
            text="diferenca_percentual_vs_media",
        )
        fig2.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#1E2235", zeroline=True, zerolinecolor="#475569"),
            coloraxis_showscale=False,
            margin=dict(t=10, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Gráfico 3: Scatter ────────────────────
    st.markdown('<div class="section-header">Competitividade × Volume de Vendas</div>', unsafe_allow_html=True)
    df_scatter = df[df["quantidade_total"] > 0].copy()
    fig3 = px.scatter(
        df_scatter,
        x="diferenca_percentual_vs_media",
        y="quantidade_total",
        color="classificacao_preco",
        size="receita_total",
        size_max=40,
        hover_data=["nome_produto", "categoria", "nosso_preco", "preco_medio_concorrentes"],
        color_discrete_map=PRICE_COLORS,
        template=TEMPLATE,
        labels={
            "diferenca_percentual_vs_media": "Diferença % vs Média Concorrentes",
            "quantidade_total": "Quantidade Total Vendida",
        },
    )
    fig3.add_vline(x=0, line_dash="dash", line_color="#475569", annotation_text="Média do mercado")
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#1E2235", zeroline=False),
        yaxis=dict(gridcolor="#1E2235"),
        margin=dict(t=10, b=20),
        height=420,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Tabela de Alertas ────────────────────
    st.markdown('<div class="section-header">🚨 Produtos em Alerta — Mais Caros que Todos os Concorrentes</div>', unsafe_allow_html=True)
    df_alerta = df[df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"][[
        "produto_id", "nome_produto", "categoria", "marca",
        "nosso_preco", "preco_maximo_concorrentes", "diferenca_percentual_vs_media",
    ]].sort_values("diferenca_percentual_vs_media", ascending=False)

    if df_alerta.empty:
        st.success("✅ Nenhum produto mais caro que todos os concorrentes no filtro atual.")
    else:
        st.markdown(
            f'<div class="alert-box">⚠️ <strong>{len(df_alerta)} produto(s)</strong> com preço acima de todos os concorrentes monitorados.</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            df_alerta.rename(columns={
                "produto_id": "ID",
                "nome_produto": "Produto",
                "categoria": "Categoria",
                "marca": "Marca",
                "nosso_preco": "Nosso Preço (R$)",
                "preco_maximo_concorrentes": "Máx. Concorrente (R$)",
                "diferenca_percentual_vs_media": "Dif. % vs Média",
            }),
            use_container_width=True,
            hide_index=True,
        )
