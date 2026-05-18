# 📊 E-commerce Analytics Project

> A complete data pipeline for a Brazilian e-commerce company — from raw sales data to an interactive analytics dashboard, built with **Supabase**, **dbt**, and **Streamlit**.

---

## 🗺️ Table of Contents

1. [What This Project Does](#-what-this-project-does)
2. [The Big Picture — Architecture](#-the-big-picture--architecture)
3. [Tech Stack](#-tech-stack)
4. [The Database — Supabase](#-the-database--supabase)
5. [Data Transformation — dbt & the Medallion Architecture](#-data-transformation--dbt--the-medallion-architecture)
   - [Bronze Layer — Raw Copy](#bronze-layer--raw-copy)
   - [Silver Layer — Cleaned & Enriched](#silver-layer--cleaned--enriched)
   - [Gold Layer — Business KPIs](#gold-layer--business-kpis)
6. [The Dashboard — Streamlit](#-the-dashboard--streamlit)
   - [Page 1: Vendas (Sales)](#page-1-vendas-sales)
   - [Page 2: Clientes (Customer Success)](#page-2-clientes-customer-success)
   - [Page 3: Pricing (Competitive Intelligence)](#page-3-pricing-competitive-intelligence)
7. [Project Structure](#-project-structure)
8. [How to Run Everything](#-how-to-run-everything)
9. [Environment Variables](#-environment-variables)

---

## 🎯 What This Project Does

Imagine you're a data engineer at a Brazilian e-commerce company. Three directors need answers from data:

- 📈 **Commercial Director** — "How are our sales trending? What's our best hour to sell?"
- 👥 **Customer Success Director** — "Who are our VIP customers? Which states have the most buyers?"
- 💰 **Pricing Director** — "Are we more expensive than Amazon and Mercado Livre?"

This project automates the entire journey: it takes raw database records, cleans and structures them through a multi-layer pipeline, and delivers the answers directly to a beautiful self-service dashboard. No SQL knowledge required for the end user.

---

## 🏗️ The Big Picture — Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  SUPABASE (PostgreSQL)                   │
│                                                          │
│  Raw Tables (schema: public)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ vendas   │ │ clientes │ │ produtos │ │preco_comp..│  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │
                    dbt runs here
                         │
          ┌──────────────▼──────────────┐
          │     BRONZE LAYER (views)    │  ← exact copy of raw data
          │  bronze_vendas, bronze_*    │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │     SILVER LAYER (tables)   │  ← cleaned, typed, enriched
          │  silver_vendas, silver_*    │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │      GOLD LAYER (tables)    │  ← ready-to-use KPIs
          │  vendas_temporais           │
          │  clientes_segmentacao       │
          │  precos_competitividade     │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    STREAMLIT DASHBOARD      │  ← 3-page analytics app
          │    case-01-dashboard/app.py │
          └─────────────────────────────┘
```

The flow is always **one-way**: raw data → bronze → silver → gold → dashboard. This is called the **Medallion Architecture** (🥉 → 🥈 → 🥇).

---

## 🛠️ Tech Stack

| Tool | Role | Why |
|---|---|---|
| **Supabase** | Cloud PostgreSQL database | Hosts all raw and transformed data |
| **dbt** | Data transformation framework | Turns SQL into a clean, tested pipeline |
| **Streamlit** | Python web framework for dashboards | Fast, interactive, Python-native |
| **Plotly** | Interactive charts library | Rich visuals — scatter, bar, pie, line |
| **psycopg2** | PostgreSQL driver for Python | Connects the dashboard to Supabase |
| **python-dotenv** | Env variable loader | Keeps credentials out of code |
| **uv** | Python package manager | Fast dependency management |

---

## 🗄️ The Database — Supabase

**Supabase** is an open-source Firebase alternative built on top of PostgreSQL. We use it as our cloud database — it manages hosting, authentication, and gives us a direct PostgreSQL connection.

Our raw data lives in 4 tables in the `public` schema:

### Raw Tables

| Table | Records | Description |
|---|---|---|
| `vendas` | ~3,020 | Every individual sale transaction |
| `clientes` | 50 | Customer registry |
| `produtos` | 215 | Product catalog |
| `preco_competidores` | ~728 | Competitor prices (Mercado Livre, Amazon, Shopee, Magalu) |

### Connecting to Supabase

The project connects via a standard PostgreSQL connection string. dbt uses `~/.dbt/profiles.yml` for its queries; the Streamlit dashboard reads credentials from a `.env` file.

```
Host:     aws-1-us-east-2.pooler.supabase.com
Port:     5432
Database: postgres
```

Both tools talk to the exact same database — dbt writes the transformed tables, and the dashboard reads them.

---

## 🔄 Data Transformation — dbt & the Medallion Architecture

**dbt** (data build tool) is the engine that transforms data. You write SQL `SELECT` statements, and dbt handles the rest: creating views/tables, tracking dependencies, running tests, and documenting everything.

The project uses the **Medallion Architecture**, a well-known pattern in data engineering that processes data through 3 quality layers:

---

### 🥉 Bronze Layer — Raw Copy

**Location:** `ecommerce/models/bronze/`

**What it does:** Takes data exactly as it comes from the source — no changes, no filters. Think of it as a safe snapshot.

**Why it matters:** If something goes wrong downstream, you can always replay from bronze without hitting the original source again.

**Models:**
- `bronze_vendas.sql` — raw sales
- `bronze_clientes.sql` — raw customers
- `bronze_produtos.sql` — raw products
- `bronze_preco_competidores.sql` — raw competitor prices

**Materialized as:** `view` (no storage cost — just a window to the source)

```sql
-- Example: bronze_vendas.sql
SELECT
    id_venda,
    data_venda,
    id_cliente,
    id_produto,
    canal_venda,
    quantidade,
    preco_unitario
FROM {{ source('raw', 'vendas') }}
```

---

### 🥈 Silver Layer — Cleaned & Enriched

**Location:** `ecommerce/models/silver/`

**What it does:** Cleans the data, fixes types, adds calculated columns. This is where raw timestamps become date/hour fields, and where we compute things like `receita_total = quantidade × preco_unitario`.

**Why it matters:** Downstream models don't need to worry about data quality — they can trust silver.

**Key transformations:**

| Model | Key Additions |
|---|---|
| `silver_vendas` | `receita_total`, `data_venda_date`, `ano_venda`, `mes_venda`, `dia_semana`, `hora_venda` |
| `silver_produtos` | `faixa_preco` (PREMIUM / MEDIO / BASICO based on price) |
| `silver_clientes` | Clean column types |
| `silver_preco_competidores` | Clean column types |

**Materialized as:** `view`

---

### 🥇 Gold Layer — Business KPIs

**Location:** `ecommerce/models/gold/`

**What it does:** Aggregates silver data into ready-to-consume business metrics. These are the tables the dashboard reads directly. No further transformation needed.

**Materialized as:** `table` (pre-computed for fast dashboard queries)

#### 📊 `vendas_temporais` (schema: `public_gold_sales`)

Aggregated sales metrics broken down by date + hour. One row per `(date, hour)` combination.

| Column | Description |
|---|---|
| `data_venda` | Date of the sales |
| `dia_semana_nome` | Day name in Portuguese (Segunda, Terça...) |
| `hora_venda` | Hour of the day (0–23) |
| `receita_total` | Total revenue in that period |
| `total_vendas` | Number of distinct transactions |
| `total_clientes_unicos` | Number of distinct customers |
| `ticket_medio` | Average revenue per transaction |

#### 👥 `clientes_segmentacao` (schema: `public_gold_cs`)

One row per customer with their segment classification.

| Segment | Rule |
|---|---|
| 🟣 **VIP** | `receita_total >= R$ 10,000` |
| 🟡 **TOP_TIER** | `receita_total >= R$ 5,000 and < R$ 10,000` |
| ⚪ **REGULAR** | `receita_total < R$ 5,000` |

#### 💰 `precos_competitividade` (schema: `public_gold_pricing`)

One row per product, comparing our price against competitors.

| Classification | Meaning |
|---|---|
| 🔴 `MAIS_CARO_QUE_TODOS` | Our price is above every competitor |
| 🟠 `ACIMA_DA_MEDIA` | Our price is above the average |
| ⚪ `NA_MEDIA` | Our price matches the average |
| 🟢 `ABAIXO_DA_MEDIA` | Our price is below the average |
| 💚 `MAIS_BARATO_QUE_TODOS` | Our price is below every competitor |

---

## 📱 The Dashboard — Streamlit

**Location:** `case-01-dashboard/app.py`

The dashboard is a **self-service analytics app** — directors open it, select filters, and see the numbers. No SQL. No spreadsheets.

It connects directly to the Gold Layer tables in Supabase and refreshes data after every `dbt run`.

**Design choices:**
- Dark theme for readability in presentations
- Consistent color palette across all 3 pages
- All numbers formatted in Brazilian style (R$ 1.234,56)
- No aggressive caching — always shows latest data

---

### Page 1: Vendas (Sales)

> For the **Commercial Director**

**Source table:** `public_gold_sales.vendas_temporais`

**KPIs at a glance:**

| Metric | How it's calculated |
|---|---|
| Receita Total | `SUM(receita_total)` |
| Total de Vendas | `SUM(total_vendas)` |
| Ticket Médio | Receita Total / Total de Vendas |
| Clientes Únicos | Max unique customers per day, summed |

**Charts:**
- 📈 **Receita Diária** — Line chart showing revenue over time, with a filled area under the curve
- 📅 **Receita por Dia da Semana** — Which day of the week sells the most
- ⏰ **Volume de Vendas por Hora** — Peak hours across the day (0–23)

**Filter:** Month selector at the top of the page

---

> 📸 **Screenshot placeholder — Vendas page**
>
> ![Dashboard - Página Vendas](./docs/screenshots/dashboard_vendas.png)

---

### Page 2: Clientes (Customer Success)

> For the **Customer Success Director**

**Source table:** `public_gold_cs.clientes_segmentacao`

**KPIs at a glance:**

| Metric | How it's calculated |
|---|---|
| Total Clientes | `COUNT(*)` |
| Clientes VIP | `COUNT(*) WHERE segmento = 'VIP'` |
| Receita VIP | `SUM(receita_total) WHERE segmento = 'VIP'` |
| Ticket Médio Geral | `AVG(ticket_medio)` |

**Charts:**
- 🍩 **Distribuição por Segmento** — Donut chart (VIP / TOP_TIER / REGULAR)
- 📊 **Receita por Segmento** — Revenue contribution of each tier
- 🏆 **Top 10 Clientes** — Horizontal bar chart of highest-revenue customers
- 🗺️ **Clientes por Estado** — Which Brazilian states have the most buyers

**Table:** Filterable by segment, showing all customer details

---

> 📸 **Screenshot placeholder — Clientes page**
>
> ![Dashboard - Página Clientes](./docs/screenshots/dashboard_clientes.png)

---

### Page 3: Pricing (Competitive Intelligence)

> For the **Pricing Director**

**Source table:** `public_gold_pricing.precos_competitividade`

**KPIs at a glance:**

| Metric | How it's calculated |
|---|---|
| Produtos Monitorados | `COUNT(*)` |
| Mais Caros que Todos | `COUNT(*) WHERE classificacao = 'MAIS_CARO_QUE_TODOS'` |
| Mais Baratos que Todos | `COUNT(*) WHERE classificacao = 'MAIS_BARATO_QUE_TODOS'` |
| Diferença Média vs Mercado | `AVG(diferenca_percentual_vs_media)` |

**Charts:**
- 🍩 **Posicionamento vs Concorrência** — Distribution of price classifications
- 📊 **Competitividade por Categoria** — Average price gap per product category (green = cheaper, red = more expensive)
- 🔵 **Scatter: Preço vs Volume** — Are cheaper products actually selling more?

**Alert table:** Products flagged as more expensive than ALL competitors — actionable pricing opportunities

**Filter:** Multi-select by product category

---

> 📸 **Screenshot placeholder — Pricing page**
>
> ![Dashboard - Página Pricing](./docs/screenshots/dashboard_pricing.png)

---

## 📁 Project Structure

```
ecommerce-project/
│
├── 📂 ecommerce/                    # dbt project root
│   ├── dbt_project.yml              # Project config (layers, schemas, tags)
│   ├── 📂 models/
│   │   ├── _sources.yml             # Declares the raw Supabase tables
│   │   ├── 📂 bronze/               # 🥉 Raw copies (views)
│   │   │   ├── bronze_vendas.sql
│   │   │   ├── bronze_clientes.sql
│   │   │   ├── bronze_produtos.sql
│   │   │   └── bronze_preco_competidores.sql
│   │   ├── 📂 silver/               # 🥈 Cleaned & enriched (views)
│   │   │   ├── silver_vendas.sql
│   │   │   ├── silver_clientes.sql
│   │   │   ├── silver_produtos.sql
│   │   │   └── silver_preco_competidores.sql
│   │   └── 📂 gold/                 # 🥇 Business KPIs (tables)
│   │       ├── 📂 sales/
│   │       │   └── vendas_temporais.sql
│   │       ├── 📂 customer_success/
│   │       │   └── clientes_segmentacao.sql
│   │       └── 📂 pricing/
│   │           └── precos_competitividade.sql
│   └── 📂 .llm/                     # AI context files (PRD, database docs)
│       ├── prd-dashboard.md
│       └── database.md
│
├── 📂 case-01-dashboard/            # Streamlit dashboard
│   ├── app.py                       # Main app — 3 pages, all charts
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Credentials (not committed to git)
│   └── .env.example                 # Template for new environments
│
├── 📂 .agents/                      # AI agent skills
│   └── 📂 skills/
│       ├── supabase/                # Supabase best practices for AI
│       └── supabase-postgres-best-practices/
│
├── .mcp.json                        # MCP server config (Supabase AI integration)
├── pyproject.toml                   # Python project metadata
├── uv.lock                          # Dependency lock file
└── README.md                        # This file
```

---

## 🚀 How to Run Everything

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager) or standard pip
- Access to a Supabase project with the raw tables populated

---

### Step 1 — Run the dbt pipeline

This transforms the raw data through Bronze → Silver → Gold.

```bash
# Navigate to the dbt project
cd ecommerce/

# Check connection to Supabase
dbt debug

# Run all models (creates/refreshes bronze, silver, and gold)
dbt run

# (Optional) Run data quality tests
dbt test
```

After `dbt run`, the three Gold tables will exist in Supabase:
- `public_gold_sales.vendas_temporais`
- `public_gold_cs.clientes_segmentacao`
- `public_gold_pricing.precos_competitividade`

---

### Step 2 — Run the Dashboard

```bash
# Navigate to the dashboard folder
cd case-01-dashboard/

# Copy and fill in environment variables (first time only)
cp .env.example .env
# Edit .env with your Supabase credentials

# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run app.py
```

Open your browser at **http://localhost:8501** 🎉

> **Tip:** Run `dbt run` whenever your source data changes, then refresh the dashboard to see updated numbers.

---

## 🔐 Environment Variables

The dashboard reads credentials from a `.env` file in `case-01-dashboard/`:

```env
SUPABASE_HOST=aws-1-us-east-2.pooler.supabase.com
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=postgres.YOUR_PROJECT_REF
SUPABASE_PASSWORD=YOUR_DATABASE_PASSWORD
```

> ⚠️ Never commit the `.env` file to version control. It's already listed in `.gitignore`.

The dbt connection is configured separately in `~/.dbt/profiles.yml` on your local machine:

```yaml
ecommerce_project:
  target: dev
  outputs:
    dev:
      type: postgres
      host: aws-1-us-east-2.pooler.supabase.com
      port: 5432
      dbname: postgres
      user: postgres.YOUR_PROJECT_REF
      password: YOUR_DATABASE_PASSWORD
      schema: public
      threads: 4
```

---

## 📌 Key Design Decisions

**Why Medallion Architecture?**
It separates concerns cleanly. If the business logic for "VIP customer" changes (say, the threshold moves from R$ 10,000 to R$ 15,000), you only touch the Gold model — Bronze and Silver stay untouched.

**Why dbt?**
dbt turns SQL into software: version control, tests, documentation, and dependency tracking come for free. Running `dbt run` is all it takes to rebuild the entire pipeline.

**Why Supabase?**
It gives us a production-grade PostgreSQL database with zero infrastructure management, plus a clean connection pooler that works well with both dbt and psycopg2.

**Why Streamlit?**
For internal analytics dashboards, Streamlit is unbeatable for speed of development. The entire 3-page dashboard was built in a single `app.py` file.

---

*Built with 🤖 Antigravity + dbt + Supabase + Streamlit*
