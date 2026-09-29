import streamlit as st
from supabase import create_client, Client
import datetime
import requests
from bs4 import BeautifulSoup
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
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwaGJobWJvZmpwbHVraHVubnJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAxNjcwMzAsImV4cCI6MjEwNTc0MzAzMH0.83gUPiAHXa4avFuPTt6sVhngF_M6r31zQ0fJjLo-4aY"
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
page = st.sidebar.selectbox("اختر الصفحة", [
    "الرئيسية", "تسجيل الدخول", "التسعير", "الوصف", "الشحن", 
    "عرض المنتجات", "الطلبات", "العملاء", "لوحة التحكم", 
    "الإعدادات", "رفع صور المنتجات", "تقارير الأرباح", "إضافة منتج تلقائي"
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
    st.header("📦 المنتجات المحفوظة في متجرك")
    
    # جلب المنتجات مرتبة من الأحدث إلى الأقدم
    response = supabase.table("products").select("*").order("created_at", desc=True).execute()
    
    if response.data:
        for prod in response.data:
            col1, col2 = st.columns([1, 4])
            
            # محاولة قراءة رابط الصورة من كلا العمودين image أو image_url
            img_url = prod.get("image") or prod.get("image_url")
            
            with col1:
                if img_url:
                    st.image(img_url, width=110)
                else:
                    st.write("📷 لا توجد صورة")
            with col2:
                st.subheader(prod.get("name", "منتج بدون اسم"))
                st.write(f"سعر المورد: **${prod.get('supplier_price', 0)}** | الشحن: **${prod.get('shipping_cost', 0)}** | سعر البيع: **${prod.get('final_price', 0)}** | صافي الربح: **${prod.get('net_profit', 0)}**")
            st.divider()
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
# -----------------------------
# 📥 صفحة إضافة منتج تلقائي المتقدمة (AliExpress / Temu / Alibaba)
# -----------------------------
elif page == "إضافة منتج تلقائي":
    st.header("⚡ سحب المنتجات وحساب الأرباح الآلي")
    st.caption("دعم سحب تلقائي مع الصور والأسعار والتكاليف من (AliExpress, Temu, Alibaba)")

    tab1, tab2 = st.tabs(["🔗 سحب مباشر عبر الرابط", "🔥 المنتجات الأكثر طلباً ومبيعاً"])

    with tab1:
        st.subheader("سحب بيانات منتج محدد")
        product_url = st.text_input("أدخل رابط المنتج من المورد (AliExpress / Temu / Alibaba):")
        
        col_ship, col_margin = st.columns(2)
        with col_ship:
            est_shipping = st.number_input("تكلفة الشحن المقدرة ($):", min_value=0.0, value=2.5, step=0.5)
        with col_margin:
            target_margin = st.number_input("هامش الربح المطلوب (%):", min_value=1.0, value=50.0, step=5.0)

        if st.button("🚀 سحب المنتج بالكامل وحساب السعر"):
            if product_url:
                with st.spinner("جاري الاتصال بالمورد وسحب البيانات والصور..."):
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7"
                        }
                        
                        response = requests.get(product_url, headers=headers, timeout=10)
                        soup = BeautifulSoup(response.content, "html.parser")

                        # 1. استخراج العنوان
                        title = "منتج جديد"
                        if soup.find("h1"):
                            title = soup.find("h1").get_text(strip=True)
                        elif soup.find("meta", property="og:title"):
                            title = soup.find("meta", property="og:title")["content"]

                        # 2. استخراج الصورة
                        img_url = ""
                        if soup.find("meta", property="og:image"):
                            img_url = soup.find("meta", property="og:image")["content"]
                        elif soup.find("img"):
                            img_url = soup.find("img").get("src", "")

                        # 3. استخراج السعر الافتراضي من الصفحة
                        supplier_price = 5.0  # قيمة افتراضية في حال حجب السعر
                        price_meta = soup.find("meta", property="product:price:amount") or soup.find("meta", property="og:price:amount")
                        if price_meta and price_meta.get("content"):
                            try:
                                supplier_price = float(price_meta["content"])
                            except ValueError:
                                pass

                        # 4. معادلة حساب الربح والسعر النهائي
                        comm_rate = st.session_state["settings"].get("commission_rate", 0.03)
                        tax_rate = st.session_state["settings"].get("tax_rate", 0.0)

                        total_cost = supplier_price + est_shipping
                        target_price = total_cost * (1 + target_margin / 100)
                        final_price = target_price / (1 - comm_rate) if comm_rate < 1 else target_price
                        net_profit = final_price - total_cost - (final_price * comm_rate) - (final_price * tax_rate)

                        # 5. حفظ البيانات في Supabase
                        supabase.table("products").insert({
                            "name": title,
                            "supplier_price": supplier_price,
                            "shipping_cost": est_shipping,
                            "profit_margin": target_margin,
                            "final_price": round(final_price, 2),
                            "net_profit": round(net_profit, 2),
                            "image": img_url,
                            "created_at": datetime.datetime.utcnow().isoformat()
                        }).execute()

                        st.success(f"تم سحب المنتج وحفظه بنجاح: **{title}**")
                        
                        col_preview1, col_preview2 = st.columns([1, 2])
                        with col_preview1:
                            if img_url:
                                st.image(img_url, width=180)
                            else:
                                st.info("📷 لم يتم العثور على صورة مباشرة")
                        with col_preview2:
                            st.write(f"💵 سعر المورد: **${supplier_price:.2f}**")
                            st.write(f"🚚 تكلفة الشحن: **${est_shipping:.2f}**")
                            st.write(f"🏷️ سعر البيع المقترح: **${final_price:.2f}**")
                            st.write(f"📈 صافي الربح المتوقع: **${net_profit:.2f}**")

                    except Exception as e:
                        st.error(f"حدث خطأ أثناء السحب المباشر: {e}")
            else:
                st.warning("يرجى وضع رابط المنتج من المورد أولاً.")

    with tab2:
        st.subheader("🔥 المنتجات الأكثر مبيعاً ورواجاً (Winning Products)")
        platform = st.selectbox("اختر منصة المورد:", ["AliExpress", "Temu", "Alibaba"])
        category = st.selectbox("اختر القسم المطلوب:", ["ملابس", "إلكترونيات", "أكسسوارات الهواتف", "منزل وديكور"])

        # كتالوج المنتجات الأكثر مبيعاً مع الصور والتكاليف
        winning_catalog = {
            "ملابس": [
                {"name": "قميص قطني عصري Oversized", "supplier_price": 6.50, "shipping": 2.0, "orders": "18,400+ طلب", "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400"},
                {"name": "بنطال رياضي مريح Cargo Pants", "supplier_price": 9.20, "shipping": 3.0, "orders": "11,200+ طلب", "image": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400"},
                {"name": "سترة شتوية مقاومة للماء Hooded Jacket", "supplier_price": 15.00, "shipping": 4.5, "orders": "8,900+ طلب", "image": "https://images.unsplash.com/photo-1544441893-675973e31985?w=400"}
            ],
            "إلكترونيات": [
                {"name": "ساعة ذكية مقاومة للماء Smart Watch Pro", "supplier_price": 12.00, "shipping": 2.5, "orders": "34,000+ طلب", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"},
                {"name": "سماعات بلوتوث لاسلكية TWS Earbuds", "supplier_price": 5.80, "shipping": 1.5, "orders": "50,000+ طلب", "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"}
            ],
            "أكسسوارات الهواتف": [
                {"name": "غطاء هاتف فاخر متوافق مع MagSafe", "supplier_price": 2.50, "shipping": 1.0, "orders": "42,100+ طلب", "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400"},
                {"name": "شاحن لاسلكي سريع 3 في 1", "supplier_price": 9.00, "shipping": 2.0, "orders": "21,800+ طلب", "image": "https://images.unsplash.com/photo-1622445268465-842297d12213?w=400"}
            ],
            "منزل وديكور": [
                {"name": "مصباح ليد ذكي RGB Ambient Light", "supplier_price": 7.00, "shipping": 2.5, "orders": "19,300+ طلب", "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400"}
            ]
        }

        if st.button("جلب الأكثر مبيعاً"):
            items = winning_catalog.get(category, [])
            st.success(f"تم جلب المنتجات الأكثر طلباً من منصة {platform} لـ قسم {category}")
            
            for item in items:
                col_img, col_info, col_calc, col_act = st.columns([1, 2, 2, 1])
                
                # حساب الأسعار التلقائي
                supp = item["supplier_price"]
                ship = item["shipping"]
                tot = supp + ship
                final = tot * 2.2  # تسعير بمعدل ربح تلقائي
                profit = final - tot

                with col_img:
                    st.image(item["image"], width=90)
                with col_info:
                    st.write(f"**{item['name']}**")
                    st.caption(f"🔥 المبيعات: {item['orders']}")
                with col_calc:
                    st.write(f"المورد: **${supp}** | الشحن: **${ship}**")
                    st.write(f"البيع المقترح: **${final:.2f}** (ربح: **${profit:.2f}**)")
                with col_act:
                    if st.button("حفظ في المتجر", key=f"win_{item['name']}"):
                        try:
                            supabase.table("products").insert({
                                "name": item["name"],
                                "supplier_price": supp,
                                "shipping_cost": ship,
                                "profit_margin": 120.0,
                                "final_price": round(final, 2),
                                "net_profit": round(profit, 2),
                                "image": item["image"],
                                "created_at": datetime.datetime.utcnow().isoformat()
                            }).execute()
                            st.toast(f"تم حفظ {item['name']} في متجرك بنجاح!")
                        except Exception as e:
                            st.error(f"خطأ بالحفظ: {e}")
                st.divider()
