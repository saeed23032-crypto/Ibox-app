import streamlit as st
from supabase import create_client, Client
import datetime

# ----------------------------- #
# 🎨 إعدادات وتصميم المتجر
# ----------------------------- #
st.set_page_config(page_title="Ibox Store", page_icon="🛍️", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# ----------------------------- #
# 🔗 إعداد قاعدة بيانات Supabase
# ----------------------------- #
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# إعداد الحالة الافتراضية لإعدادات المتجر
if "store_name" not in st.session_state:
    st.session_state.store_name = "Ibox Store"
if "currency" not in st.session_state:
    st.session_state.currency = "USD"

# ----------------------------- #
# 📂 القائمة الجانبية للتنقل
# ----------------------------- #
st.sidebar.title(f"🛍️ لوحة تحكم {st.session_state.store_name}")
page = st.sidebar.selectbox("اختر الصفحة", ["عرض المنتجات", "إضافة منتج تلقائي", "إدارة الطلبات", "محاكاة العميل (الشراء)", "الإعدادات"])

# ----------------------------- #
# 📦 صفحة عرض المنتجات المحفوظة
# ----------------------------- #
if page == "عرض المنتجات":
    st.header(f"📦 المنتجات المحفوظة في {st.session_state.store_name}")
    
    if st.button("🗑️ حذف جميع المنتجات المحفوظة", type="primary"):
        try:
            supabase.table("products").delete().neq("id", 0).execute()
            st.success("تم مسح جميع المنتجات من المتجر بنجاح!")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحذف: {e}")
            
    st.divider()
    
    try:
        response = supabase.table("products").select("*").execute()
        if response.data and len(response.data) > 0:
            st.success(f"لديك {len(response.data)} منتج جاهز ومعروض في متجرك:")
            for prod in response.data:
                col1, col2 = st.columns([1, 4])
                img_url = prod.get("image")
                curr = st.session_state.currency
                with col1:
                    if img_url:
                        st.image(str(img_url), width=110)
                    else:
                        st.write("📷 لا توجد صورة")
                with col2:
                    st.subheader(prod.get("name", "منتج بدون اسم"))
                    st.write(f"سعر المورد: **{prod.get('supplier_price', 0)} {curr}** | تكلفة الشحن: **{prod.get('shipping_cost', 0)} {curr}** | سعر البيع: **{prod.get('final_price', 0)} {curr}** | صافي الربح: **{prod.get('net_profit', 0)} {curr}**")
                st.divider()
        else:
            st.info("متجرك فارغ حالياً. اذهب إلى صفحة 'إضافة منتج تلقائي' لجلب أحدث المنتجات الرابحة.")
    except Exception as e:
        st.error(f"خطأ في جلب المنتجات: {e}")

# ----------------------------- #
# ⚡ صفحة سحب المنتجات التلقائية مع تعديل الأسعار
# ----------------------------- #
elif page == "إضافة منتج تلقائي":
    st.header("⚡ نظام السحب والتعديل التلقائي للمنتجات")
    st.caption("اختر المنتجات الرابحة، وقم بتخصيص سعر البيع قبل إضافتها للمتجر.")

    platform = st.selectbox("اختر المورد الأساسي:", ["AliExpress", "Temu", "Alibaba"])
    category = st.selectbox("اختر القسم المطلوب:", ["ملابس", "إلكترونيات", "أكسسوارات الهواتف", "منزل وديكور"])

    winning_products = {
        "ملابس": [
            {"name": "قميص رجالي قطني عصري Oversized", "supplier_price": 6.50, "shipping": 2.0, "orders": "18,400+ طلب", "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400"},
            {"name": "بنطال رياضي مريح Cargo Pants", "supplier_price": 9.20, "shipping": 3.0, "orders": "11,200+ طلب", "image": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400"}
        ],
        "إلكترونيات": [
            {"name": "ساعة ذكية متطورة Smart Watch Pro", "supplier_price": 12.00, "shipping": 2.5, "orders": "34,000+ طلب", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"},
            {"name": "سماعات بلوتوث لاسلكية عازلة للصوت TWS", "supplier_price": 5.80, "shipping": 1.5, "orders": "50,000+ طلب", "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"}
        ],
        "أكسسوارات الهواتف": [
            {"name": "غطاء حماية فاخر متوافق مع MagSafe", "supplier_price": 2.50, "shipping": 1.0, "orders": "42,100+ طلب", "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400"}
        ],
        "منزل وديكور": [
            {"name": "مصباح ليد ذكي بألوان متعددة RGB Ambient", "supplier_price": 7.00, "shipping": 2.5, "orders": "19,300+ طلب", "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400"}
        ]
    }

    items = winning_products.get(category, [])
    st.info(f"المنتجات المتاحة في قسم {category} (يمكنك تعديل سعر البيع لكل منتج قبل الحفظ):")

    for i, item in enumerate(items):
        col_img, col_info, col_edit, col_act = st.columns([1, 2, 2, 1])
        supp = item["supplier_price"]
        ship = item["shipping"]
        total_cost = supp + ship
        curr = st.session_state.currency

        with col_img:
            st.image(item["image"], width=90)
        with col_info:
            st.write(f"**{item['name']}**")
            st.caption(f"🔥 حجم الطلب: {item['orders']}")
            st.write(f"التكلفة الأساسية: **{total_cost} {curr}**")
        with col_edit:
            custom_final_price = st.number_input(
                "سعر البيع المقترح", 
                min_value=1.0, 
                value=round(total_cost * 2.2, 2), 
                step=0.5, 
                key=f"price_{i}"
            )
            custom_net_profit = round(custom_final_price - total_cost, 2)
            st.caption(f"الربح المتوقع: **{custom_net_profit} {curr}**")
        with col_act:
            st.write("")
            if st.button("📥 حفظ بالمتجر", key=f"add_{i}"):
                try:
                    supabase.table("products").insert({
                        "name": item["name"],
                        "supplier_price": supp,
                        "shipping_cost": ship,
                        "profit_margin": 120.0,
                        "final_price": custom_final_price,
                        "net_profit": custom_net_profit,
                        "image": item["image"],
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }).execute()
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ أثناء الحفظ: {e}")
        st.divider()

# ----------------------------- #
# 📋 صفحة إدارة الطلبات
# ----------------------------- #
elif page == "إدارة الطلبات":
    st.header("📋 سجل طلبات العملاء")
    try:
        response = supabase.table("orders").select("*").execute()
        if response.data and len(response.data) > 0:
            st.success(f"لديك {len(response.data)} طلب مسجل:")
            for order in response.data:
                curr = st.session_state.currency
                st.write(f"👤 **العميل:** {order.get('customer_name')} | 📦 **المنتج:** {order.get('product_name')} | 💰 **الإجمالي:** {order.get('total_price')} {curr} | 📌 **الحالة:** {order.get('status')}")
                st.divider()
        else:
            st.info("لا توجد طلبات جديدة مسجلة حتى الآن. يمكنك تجربة تقديم طلب من صفحة 'محاكاة العميل'.")
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات: {e}")

# ----------------------------- #
# 🛒 محاكاة واجهة العميل (إتمام الشراء Checkout)
# ----------------------------- #
elif page == "محاكاة العميل (الشراء)":
    st.header("🛒 تجربة واجهة متجرك (إتمام الشراء)")
    st.caption("هذه الصفحة تحاكي ما يراه العميل عند شراء منتج من متجرك لتسجيل طلب تجريبي.")

    try:
        response = supabase.table("products").select("*").execute()
        if response.data and len(response.data) > 0:
            product_options = {p["name"]: p for p in response.data}
            selected_prod_name = st.selectbox("اختر منتجاً لشرائه:", list(product_options.keys()))
            selected_prod = product_options[selected_prod_name]
            curr = st.session_state.currency

            st.write(f"السعر المطلوب: **{selected_prod.get('final_price')} {curr}**")

            with st.form("checkout_form"):
                st.subheader("بيانات الشحن الخاصة بالعميل")
                cust_name = st.text_input("الاسم الكامل:")
                cust_phone = st.text_input("رقم الهاتف:")
                cust_address = st.text_area("عنوان الشحن بالتفصيل:")
                
                submit_order = st.form_submit_button("تأكيد وإتمام الطلب 🚀")
                
                if submit_order:
                    if cust_name and cust_address:
                        try:
                            supabase.table("orders").insert({
                                "customer_name": cust_name,
                                "product_name": selected_prod_name,
                                "total_price": selected_prod.get('final_price'),
                                "status": "قيد المعالجة",
                                "created_at": datetime.datetime.utcnow().isoformat()
                            }).execute()
                            st.success("🎉 تم إتمام الطلب بنجاح! انتقل إلى صفحة 'إدارة الطلبات' لمشاهدته.")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء إرسال الطلب: {e}")
                    else:
                        st.warning("يرجى تعبئة الاسم وعنوان الشحن على الأقل.")
        else:
            st.info("لا توجد منتجات معروضة حالياً. أضف منتجات أولاً من صفحة 'إضافة منتج تلقائي'.")
    except Exception as e:
        st.error(f"خطأ في تحميل المنتجات: {e}")

# ----------------------------- #
# ⚙️ إعدادات المتجر المتقدمة
# ----------------------------- #
elif page == "الإعدادات":
    st.header(f"⚙️ إعدادات متجر {st.session_state.store_name}")
    
    with st.form("settings_form"):
        new_store_name = st.text_input("اسم المتجر:", value=st.session_state.store_name)
        new_currency = st.selectbox("العملة:", ["USD", "SAR", "EUR", "AED"], index=["USD", "SAR", "EUR", "AED"].index(st.session_state.currency))
        
        save_settings = st.form_submit_button("حفظ الإعدادات")
        
        if save_settings:
            st.session_state.store_name = new_store_name
            st.session_state.currency = new_currency
            st.success("تم تحديث إعدادات المتجر بنجاح!")
            st.rerun()
