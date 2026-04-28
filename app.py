import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Olist Business Intelligence", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_all_data():
    try:
        orders = pd.read_csv('data/olist_orders_dataset.csv')
        items = pd.read_csv('data/olist_order_items_dataset.csv')
        products = pd.read_csv('data/olist_products_dataset.csv')
        customers = pd.read_csv('data/olist_customers_dataset.csv')
        payments = pd.read_csv('data/olist_order_payments_dataset.csv')
        
        orders['order_approved_at'] = pd.to_datetime(orders['order_approved_at'])
        orders = orders.dropna(subset=['order_approved_at'])
        
        df = pd.merge(orders, items, on='order_id', how='inner')
        df = pd.merge(df, products, on='product_id', how='inner')
        df = pd.merge(df, customers, on='customer_id', how='inner')
        
        return df, payments
    except Exception as e:
        st.error(f"Dosyalar yüklenirken hata oluştu: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_final, df_payments = load_all_data()

if not df_final.empty:
    st.title("🛍️ Olist E-Ticaret Yönetim Paneli")
    st.divider()

    st.sidebar.header("📊 Analiz Filtreleri")
    top_5_cat = df_final['product_category_name'].value_counts().head(5).index.tolist()
    category_filter = st.sidebar.multiselect(
        "Kategori Seçin:", 
        options=sorted(df_final['product_category_name'].dropna().unique()),
        default=top_5_cat
    )

    filtered_df = df_final[df_final['product_category_name'].isin(category_filter)]

    if not filtered_df.empty:

        total_revenue = filtered_df['price'].sum()
        total_orders = filtered_df['order_id'].nunique()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        total_customers = filtered_df['customer_unique_id'].nunique()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Toplam Ciro", f"R$ {total_revenue:,.0f}")
        col2.metric("📦 Toplam Sipariş", f"{total_orders:,}")
        col3.metric("🛒 Ortalama Sepet", f"R$ {avg_order_value:.2f}")
        col4.metric("👥 Eşsiz Müşteri", f"{total_customers:,}")

        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("📈 Aylık Satış Trendi")
            chart_df = filtered_df.copy()
            chart_df['month_year'] = chart_df['order_approved_at'].dt.to_period('M').astype(str)
            monthly_rev = chart_df.groupby('month_year')['price'].sum().reset_index()
            
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=monthly_rev, x='month_year', y='price', marker='o', color='#1f77b4', ax=ax1)
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig1)

            st.subheader("💳 Ödeme Yöntemleri Dağılımı")
            filtered_order_ids = filtered_df['order_id'].unique()
            filtered_payments = df_payments[df_payments['order_id'].isin(filtered_order_ids)]
            pay_counts = filtered_payments['payment_type'].value_counts()
            
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            ax2.pie(pay_counts, labels=pay_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
            st.pyplot(fig2)

        with right_col:
            st.subheader("🏆 Seçili Kategorilerde Ciro")
            cat_rev = filtered_df.groupby('product_category_name')['price'].sum().sort_values(ascending=False)
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=cat_rev.values, y=cat_rev.index, palette='viridis', ax=ax3)
            st.pyplot(fig3)

            st.subheader("📍 Eyalet Bazlı Satış Hacmi")
            state_dist = filtered_df['customer_state'].value_counts().head(10)
            fig4, ax4 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=state_dist.values, y=state_dist.index, palette='coolwarm', ax=ax4)
            st.pyplot(fig4)
    else:
        st.warning("Lütfen sol menüden en az bir kategori seçin.")

else:
    st.error("Veri çerçevesi boş. Lütfen CSV dosyalarınızın 'archive-2' klasöründe olduğunu kontrol edin.")