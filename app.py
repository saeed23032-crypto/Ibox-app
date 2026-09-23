import streamlit as st
from supabase import create_client, Client
import datetime

# -----------------------------
# 🎨 تحسين شكل التطبيق (CSS)
# -----------------------------
st.set_page_config(page_title="DropPilot AI", page_icon="💧", layout="wide")

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
# 🧩 إعداد الجلسات الافتراضية
# -----------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if "role" not in st.session_state:
    st.session_state["role"] = "guest"  # guest, user, staff, admin

if "settings" not in st.session_state:
    st.session_state["settings"] = {
        "store_name": "متجر DropPilot",
        "currency": "USD",
        "tax_rate": 0.0,
        "commission_rate": 0.03
    }

# -----------------------------
# 🔐 الصفحات المحمية
# -----------------------------
protected_pages = [
    "التسعير",
    "الوصف",
    "الشحن",
    "عرض المنتجات",
    "الطلبات",
    "العملاء",
    "لوحة التحكم",
    "الإعدادات",
    "رفع صور المنتجات",
    "تقارير الأرباح"
]

# -----------------------------
# 📂 Sidebar للتنقل بين الصفحات
# -----------------------------
st.sidebar.title("📂 قائمة التنقل")
page = st.sidebar.selectbox(
    "اختر الصفحة",
    [
        "الرئيسية",
        "تسجيل الدخول",
        "التسعير",
        "الوصف",
        "الشحن",
        "عرض المنتجات",
        "الطلبات",
        "العملاء",
        "لوحة التحكم",
        "الإعدادات",
        "رفع صور المنتجات",
        "تقارير الأرباح"
    ]
)

# زر تسجيل الخروج
if st.session_state["user"]:
    if st.sidebar.button("🔓 تسجيل الخروج"):
        st.session_state["user"] = None
        st.session_state["role"] = "guest"
        st.success("تم تسجيل الخروج بنجاح!")

# منع الوصول للصفحات المحمية
if not st.session_state["user"] and page in protected_pages:
    st.warning("يجب تسجيل الدخول للوصول إلى هذه الصفحة.")
    st.stop()

# -----------------------------
# 🏠 الصفحة الرئيسية
# -----------------------------
if page == "الرئيسية":
    st.header("🚀 DropPilot AI — منصة التسعير وإدارة الدروبشيبينغ")
    st.write("منصة SaaS مبنية على Streamlit + Supabase لإدارة المنتجات، الطلبات، العملاء، والتسعير.")

    if st.session_state["user"]:
        st.info(f"مرحباً، {st.session_state['user'].user.email} — الدور: {st.session_state['role']}")
    else:
        st.info("أنت حالياً غير مسجل دخول (Guest).")

# -----------------------------
# 🔐 صفحة تسجيل الدخول + الصلاحيات
# -----------------------------
elif page == "تسجيل الدخول":
    st.header("🔐 تسجيل الدخول")

    email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة المرور", type="password")
    role = st.selectbox("اختر الدور (للتجربة)", ["user", "staff", "admin"])

    if st.button("تسجيل الدخول"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = user
            st.session_state["role"] = role
            st.success("تم تسجيل الدخول بنجاح!")
        except Exception as e:
            st.error("فشل تسجيل الدخول")
            st.write(e)

# -----------------------------
# 💰 صفحة التسعير
# -----------------------------
elif page == "التسعير":
    st.header("💰 نظام التسعير الآلي")

    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input("اسم المنتج")
        supplier_price = st.number_input("سعر المنتج من المورد ($)", min_value=0.0, value=4.5)
        shipping_cost = st.number_input("تكلفة الشحن ($)", min_value=0.0, value=2.0)

    with col2:
        profit_margin = st.number_input("نسبة الربح المطلوبة (%)", min_value=0, value=50)
        tax_rate = st.session_state["settings"]["tax_rate"]
        commission_rate = st.session_state["settings"]["commission_rate"]

    if st.button("احسب السعر النهائي"):
        total_cost = supplier_price + shipping_cost
        target_price = total_cost * (1 + profit_margin / 100)
        final_price = target_price / (1 - commission_rate)
        net_profit = final_price - total_cost - (final_price * commission_rate) - (final_price * tax_rate)

        m1, m2, m3 = st.columns(3)
        m1.metric("إجمالي التكلفة", f"${total_cost:.2f}")
        m2.metric("السعر النهائي", f"${final_price:.2f}")
        m3.metric("صافي الربح", f"${net_profit:.2f}")

        st.session_state["last_pricing"] = {
            "name": product_name,
            "supplier_price": supplier_price,
            "shipping_cost": shipping_cost,
            "profit_margin": profit_margin,
            "final_price": final_price,
            "net_profit": net_profit
        }

    if st.button("💾 حفظ المنتج في قاعدة البيانات"):
        if "last_pricing" in st.session_state:
            lp = st.session_state["last_pricing"]
            supabase.table("products").insert({
                "name": lp["name"],
                "supplier_price": lp["supplier_price"],
                "shipping_cost": lp["shipping_cost"],
                "profit_margin": lp["profit_margin"],
                "final_price": lp["final_price"],
                "net_profit": lp["net_profit"],
                "created_at": datetime.datetime.utcnow().isoformat()
            }).execute()
            st.success("تم حفظ المنتج بنجاح!")
        else:
            st.warning("احسب السعر أولاً قبل الحفظ.")

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
            "status": status,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
        st.success("تم حفظ الطلب بنجاح!")

    st.divider()
    st.subheader("📄 جميع الطلبات")

    orders = supabase.table("orders").select("*").execute()
    st.table(orders.data)

# -----------------------------
# 👥 صفحة العملاء
# -----------------------------
elif page == "العملاء":
    st.header("👥 إدارة العملاء")

    name = st.text_input("اسم العميل")
    email = st.text_input("البريد الإلكتروني")
    phone = st.text_input("رقم الهاتف")
    address = st.text_area("العنوان")

    if st.button("💾 حفظ العميل"):
        supabase.table("customers").insert({
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
        st.success("تم حفظ العميل بنجاح!")

    st.divider()
    st.subheader("📄 جميع العملاء")

    customers = supabase.table("customers").select("*").execute()
    st.table(customers.data)

# -----------------------------
# ⚙️ صفحة الإعدادات
# -----------------------------
elif page == "الإعدادات":
    st.header("⚙️ إعدادات المنصة")

    if st.session_state["role"] != "admin":
        st.warning("هذه الصفحة متاحة للمدير فقط.")
        st.stop()

    store_name = st.text_input("اسم المتجر", value=st.session_state["settings"]["store_name"])
    currency = st.selectbox("العملة", ["USD", "EUR", "SAR", "AED"], index=0)
    tax_rate = st.number_input("نسبة الضريبة (%)", min_value=0.0, max_value=50.0, value=st.session_state["settings"]["tax_rate"] * 100) / 100
    commission_rate = st.number_input("نسبة العمولة (Stripe/بوابة دفع) (%)", min_value=0.0, max_value=20.0, value=st.session_state["settings"]["commission_rate"] * 100) / 100

    if st.button("💾 حفظ الإعدادات"):
        st.session_state["settings"] = {
            "store_name": store_name,
            "currency": currency,
            "tax_rate": tax_rate,
            "commission_rate": commission_rate
        }
        st.success("تم حفظ الإعدادات بنجاح!")

# -----------------------------
# 🖼️ صفحة رفع صور المنتجات (Supabase Storage)
# -----------------------------
elif page == "رفع صور المنتجات":
    st.header("🖼️ رفع صور المنتجات")

    uploaded_file = st.file_uploader("اختر صورة المنتج", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = f"products/{uploaded_file.name}"

        try:
            supabase.storage.from_("product-images").upload(file_name, file_bytes)
            st.success("تم رفع الصورة بنجاح!")
            st.info(f"تم حفظ الصورة في المسار: {file_name}")
        except Exception as e:
            st.error("فشل رفع الصورة")
            st.write(e)

# -----------------------------
# 📊 صفحة تقارير الأرباح
# -----------------------------
elif page == "تقارير الأرباح":
    st.header("📊 تقارير الأرباح")

    products = supabase.table("products").select("*").execute()

    if products.data:
        total_profit = sum([p.get("net_profit", 0) for p in products.data])
        total_final_price = sum([p.get("final_price", 0) for p in products.data])
        total_count = len(products.data)

        c1, c2, c3 = st.columns(3)
        c1.metric("عدد المنتجات", total_count)
        c2.metric("إجمالي السعر النهائي", f"${total_final_price:.2f}")
        c3.metric("إجمالي صافي الربح", f"${total_profit:.2f}")

        st.subheader("📄 تفاصيل المنتجات")
        st.table(products.data)
    else:
        st.info("لا توجد بيانات منتجات كافية لعرض التقارير حالياً.")
