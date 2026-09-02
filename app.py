import libsql_client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. الاتصال بقاعدة البيانات
@st.cache_resource
def get_db_client():
    return libsql_client.create_client_sync(
        url=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"],
    )

client = get_db_client()

st.title("📊 لوحة التحليلات والرسوم البيانية (Dashboard)")

# 2. جلب البيانات وتجهيزها
@st.cache_data(ttl=60)
def load_dashboard_data():
    res = client.execute("SELECT id, name, price, stock FROM products")
    if res.rows:
        df = pd.DataFrame(res.rows, columns=res.columns)
        # حساب القيمة الافتراضية المباشرة (إجمالي قيمة المخزون)
        df["total_value"] = df["price"] * df["stock"]
        return df
    return pd.DataFrame()

df = load_dashboard_data()

if not df.empty:
    # ---------------------------------------------------------
    # 1. بطاقات المؤشرات الرئيسية (KPIs / Metrics)
    # ---------------------------------------------------------
    total_products = len(df)
    total_stock = int(df["stock"].sum())
    total_inventory_value = float(df["total_value"].sum())
    avg_price = float(df["price"].mean())

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="إجمالي المنتجات", value=f"{total_products}")
    kpi2.metric(label="إجمالي القطع بالمخزن", value=f"{total_stock}")
    kpi3.metric(label="قيمة المخزون الكلية", value=f"{total_inventory_value:,.2f} $")
    kpi4.metric(label="متوسط سعر المنتج", value=f"{avg_price:,.2f} $")

    st.divider()

    # ---------------------------------------------------------
    # 2. الرسوم البيانية التفاعلية (Plotly Charts)
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns(2)

    # --- الرسم الأول: أعلى 10 منتجات من حيث الكمية المتاحة ---
    with col_chart1:
        st.subheader("📦 الكميات المتاحة حسب المنتج")
        top_stock_df = df.sort_values(by="stock", ascending=False).head(10)
        
        fig_stock = px.bar(
            top_stock_df,
            x="name",
            y="stock",
            labels={"name": "المنتج", "stock": "الكمية"},
            color="stock",
            color_continuous_scale="Blues",
            text_auto=True
        )
        fig_stock.update_layout(xaxis_title="", yaxis_title="العدد")
        st.plotly_chart(fig_stock, use_container_width=True)

    # --- الرسم الثاني: توزيع قيمة المخزون (Pie Chart) ---
    with col_chart2:
        st.subheader("💰 توزيع قيمة المخزون الكلية")
        fig_pie = px.pie(
            df,
            names="name",
            values="total_value",
            hole=0.4, # Donut Chart
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------------------------------------------------
    # 3. تحليل إضافي: مقارنة الأسعار مع المخطط المبعثر (Scatter Plot)
    # ---------------------------------------------------------
    st.divider()
    st.subheader("📈 العلاقة بين السعر والكمية المتاحة")
    
    fig_scatter = px.scatter(
        df,
        x="price",
        y="stock",
        size="total_value",
        color="name",
        hover_name="name",
        labels={"price": "السعر ($)", "stock": "الكمية بالمخزن"},
        size_max=40
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.info("لا توجد بيانات متاحة لعرض التحليلات. قم بتبويب الإضافة لإدخال بيانات جديدة.")