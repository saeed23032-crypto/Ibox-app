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
# 🔗 إعداد Supabase
# -----------------------------
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# -----------------------------
# 📂 Sidebar للتنقل بين الصفحات
# -----------------------------
st.sidebar.title("📂 قائمة التنقل")
page = st.sidebar.selectbox(
    "اختر الصفحة",
    [
        "الرئيسية",
        "التسعير",
        "الوصف",
        "الشحن",
        "اختبار الاتصال",
        "عرض المنتجات",
        "تسجيل الدخول",
        "الطلبات",
        "لوحة التحكم"
    ]
)

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

    # زر حفظ المنتج في Supabase
    if st.button("💾 حفظ المنتج في قاعدة البيانات"):
        supabase.table("products").insert({
            "name": product_name,
            "supplier_price": supplier_price,
            "shipping_cost": shipping_cost,
            "profit_margin": profit_margin,
            "final_price": final_price
        }).execute()
        st.success("تم حفظ المنتج بنجاح!")

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

# -----------------------------
# 📦 صفحة عرض المنتجات
# -----------------------------
elif page == "عرض المنتجات":
    st.header("📦 المنتجات المحفوظة")

    data = supabase.table("products").select("*").execute()

    if data.data:
        st.table(data.data)
    else:
        st.info("لا توجد منتجات محفوظة بعد.")

# -----------------------------
# 🔐 صفحة تسجيل الدخول
# -----------------------------
elif page == "تسجيل الدخول":
    st.header("🔐 تسجيل الدخول")

    email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("تسجيل الدخول"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.success("تم تسجيل الدخول بنجاح!")
            st.json(user)
        except Exception as e:
            st.error("فشل تسجيل الدخول")
            st.write(e)

# -----------------------------
# 📬 صفحة الطلبات
# -----------------------------
elif page == "الطلبات":
    st.header("📬 إدارة الطلبات")

    customer_name = st.text_input("اسم العميل")
    product_name = st.text_input("اسم المنتج")
    status = st.selectbox("حالة الطلب", ["جديد", "قيد التجهيز", "مكتمل"])

    if st.button("حفظ الطلب"):
        supabase.table("orders").insert({
            "customer_name": customer_name,
            "product_name": product_name,
            "status": status
        }).execute()
        st.success("تم حفظ الطلب بنجاح!")

    st.divider()
    st.subheader("📄 جميع الطلبات")

    orders = supabase.table("orders").select("*").execute()
    st.table(orders.data)

# -----------------------------
# 📊 لوحة التحكم
# -----------------------------
elif page == "لوحة التحكم":
    st.header("📊 لوحة التحكم")

    products = supabase.table("products").select("*").execute()
    orders = supabase.table("orders").select("*").execute()

    st.metric("عدد المنتجات", len(products.data))
    st.metric("عدد الطلبات", len(orders.data))
