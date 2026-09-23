import streamlit as st
from supabase import create_client, Client

# -----------------------------
# 🎨 تحسين شكل التطبيق (CSS)
# -----------------------------
st.markdown("""
<style>
    .main {
        background-color: #f7f9fc;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 📂 Sidebar للتنقل بين الصفحات
# -----------------------------
st.sidebar.title("📂 قائمة التنقل")
page = st.sidebar.selectbox(
    "اختر الصفحة",
    ["الرئيسية", "التسعير", "الوصف", "الشحن", "اختبار الاتصال"]
)

# -----------------------------
# 🔗 إعداد Supabase
# -----------------------------
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# -----------------------------
# 🏠 الصفحة الرئيسية
# -----------------------------
if page == "الرئيسية":
    st.header("🚀 DropPilot AI — منصة التسعير الذكية")
    st.write("مساعد الذكاء الاصطناعي للتجارة الإلكترونية ودروبشيبينغ")

# -----------------------------
# 💰 صفحة التسعير
# -----------------------------
elif page == "التسعير":
    st.header("💰 نظام التسعير الآلي")

    product_name = st.text_input("اسم المنتج")
    shipping_cost = st.number_input("تكلفة الشحن ($)", min_value=0.0, value=2.0)
    supplier_price = st.number_input("سعر المنتج من المورد ($)", min_value=0.0, value=4.5)
    profit_margin = st.number_input("نسبة الربح المطلوبة (%)", min_value=0, value=50)

    if st.button("احسب السعر النهائي"):
        total_cost = shipping_cost + supplier_price
        final_price = total_cost * (1 + profit_margin / 100)
        net_profit = final_price - total_cost

        st.metric("إجمالي التكلفة", f"${total_cost:.2f}")
        st.metric("السعر النهائي", f"${final_price:.2f}")
        st.metric("صافي الربح", f"${net_profit:.2f}")

# -----------------------------
# 📝 صفحة الوصف التسويقي
# -----------------------------
elif page == "الوصف":
    st.header("📝 توليد وصف المنتج")

    product_name = st.text_input("اسم المنتج")

    if st.button("أريد رؤية وصف المنتج الخاص بي"):
        sample_description = f"""
        ### 🌟 {product_name} - الحل المثالي لاحتياجاتك اليومية

        تجربة فريدة تجمع بين التصميم العصري والأداء المتميز لـ **{product_name}**.
        - جودة عالية تضمن لك أداءً رائعًا يدوم طويلًا.
        - تصميم أنيق يناسب جميع الأذواق والمناسبات.
        - سهل الاستخدام والتنظيف، مما يجعله خيارًا مثاليًا للجميع.
        - متوفر بسعر رائع يناسب ميزانيتك.

        🔥 احصل عليه الآن واستمتع بأفضل تجربة ممكنة! 🔥
        """
        st.markdown(sample_description)

# -----------------------------
# 🚚 صفحة الشحن المباشر
# -----------------------------
elif page == "الشحن":
    st.header("🚚 ملاحظة الشحن المباشر (Blind Dropshipping)")
    st.info("We are dropshipping. Do not include any invoices, promo materials, or brand logos in the package.")

# -----------------------------
# 🧾 صفحة اختبار الاتصال مع Supabase
# -----------------------------
elif page == "اختبار الاتصال":
    st.header("🧾 اختبار الاتصال مع Supabase")

    def test_connection():
        try:
            response = supabase.table("products").select("*").limit(1).execute()
            return True, response
        except Exception as e:
            return False, str(e)

    if st.button("اختبار الاتصال"):
        ok, result = test_connection()
        if ok:
            st.success("تم الاتصال بنجاح!")
            st.json(result)
        else:
            st.error("فشل الاتصال")
            st.write(result)
