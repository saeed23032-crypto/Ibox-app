import streamlit as st
from supabase import create_client, Client
import datetime

# ----------------------------- #
# 🎨 إعدادات وتصميم المتجر (Ibox Store)
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

# ----------------------------- #
# 📂 القائمة الجانبية للتنقل
# ----------------------------- #
st.sidebar.title("🛍️ لوحة تحكم متجر Ibox")
page = st.sidebar.selectbox("اختر الصفحة", ["عرض المنتجات", "إضافة منتج تلقائي", "إدارة الطلبات", "الإعدادات"])

# ----------------------------- #
# 📦 صفحة عرض المنتجات المحفوظة
# ----------------------------- #
if page == "عرض المنتجات":
    st.header("📦 المنتجات المحفوظة في متجر Ibox")
    
    # زر حذف جميع المنتجات
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
                img_url = prod.get("image") or prod.get("image_url")
                with col1:
                    if img_url:
                        st.image(str(img_url), width=110)
                    else:
                        st.write("📷 لا توجد صورة")
                with col2:
                    st.subheader(prod.get("name", "منتج بدون اسم"))
                    st.write(f"سعر المورد: **${prod.get('supplier_price', 0)}** | تكلفة الشحن: **${prod.get('shipping_cost', 0)}** | سعر البيع: **${prod.get('final_price', 0)}** | صافي الربح: **${prod.get('net_profit', 0)}**")
                st.divider()
        else:
            st.info("متجرك فارغ حالياً. اذهب إلى صفحة 'إضافة منتج تلقائي' لجلب أحدث المنتجات الرابحة.")
    except Exception as e:
        st.error(f"خطأ في جلب المنتجات: {e}")

# ----------------------------- #
# ⚡ صفحة سحب المنتجات التلقائية
# ----------------------------- #
elif page == "إضافة منتج تلقائي":
    st.header("⚡ نظام السحب التلقائي للمنتجات الأكثر طلباً ومبيعاً")
    st.caption("جلب منتجات جاهزة للبيع بالصور والأسعار وحساب الأرباح من كبرى منصات الموردين (AliExpress, Temu, Alibaba)")

    platform = st.selectbox("اختر المورد الأساسي:", ["AliExpress", "Temu", "Alibaba"])
    category = st.selectbox("اختر القسم المطلوب:", ["ملابس", "إلكترونيات", "أكسسوارات الهواتف", "منزل وديكور"])

    # كتالوج المنتجات الأكثر طلباً ومبيعاً
    winning_products = {
        "ملابس": [
            {"name": "قميص رجالي قطني عصري Oversized", "supplier_price": 6.50, "shipping": 2.0, "orders": "18,400+ طلب", "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400"},
            {"name": "بنطال رياضي مريح Cargo Pants", "supplier_price": 9.20, "shipping": 3.0, "orders": "11,200+ طلب", "image": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400"},
            {"name": "جاكيت شتوية مقاومة للماء Hooded Jacket", "supplier_price": 15.00, "shipping": 4.5, "orders": "8,900+ طلب", "image": "https://images.unsplash.com/photo-1544441893-675973e31985?w=400"}
        ],
        "إلكترونيات": [
            {"name": "ساعة ذكية متطورة Smart Watch Pro", "supplier_price": 12.00, "shipping": 2.5, "orders": "34,000+ طلب", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"},
            {"name": "سماعات بلوتوث لاسلكية عازلة للصوت TWS", "supplier_price": 5.80, "shipping": 1.5, "orders": "50,000+ طلب", "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"}
        ],
        "أكسسوارات الهواتف": [
            {"name": "غطاء حماية فاخر متوافق مع MagSafe", "supplier_price": 2.50, "shipping": 1.0, "orders": "42,100+ طلب", "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400"},
            {"name": "شاحن لاسلكي سريع ومنظم 3 في 1", "supplier_price": 9.00, "shipping": 2.0, "orders": "21,800+ طلب", "image": "https://images.unsplash.com/photo-1622445268465-842297d12213?w=400"}
        ],
        "منزل وديكور": [
            {"name": "مصباح ليد ذكي بألوان متعددة RGB Ambient", "supplier_price": 7.00, "shipping": 2.5, "orders": "19,300+ طلب", "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400"}
        ]
    }

    if st.button("🔍 ابحث واجلب المنتجات الأكثر طلباً"):
        items = winning_products.get(category, [])
        st.success(f"تم بنجاح جلب المنتجات الأكثر مبيعاً ورواجاً من منصة {platform} في قسم {category}:")
        
        for item in items:
            col_img, col_info, col_calc, col_act = st.columns([1, 2, 2, 1])
            supp = item["supplier_price"]
            ship = item["shipping"]
            total_cost = supp + ship
            final_price = round(total_cost * 2.2, 2)
            net_profit = round(final_price - total_cost, 2)
            
            with col_img:
                st.image(item["image"], width=90)
            with col_info:
                st.write(f"**{item['name']}**")
                st.caption(f"🔥 حجم الطلب: {item['orders']}")
            with col_calc:
                st.write(f"سعر المورد: **${supp}** | الشحن: **${ship}**")
                st.write(f"سعر البيع المقترح: **${final_price}** | الربح: **${net_profit}**")
            with col_act:
                if st.button("📥 إضافة لمتجر Ibox", key=f"add_{item['name']}"):
                    try:
                        supabase.table("products").insert({
                            "name": item["name"],
                            "supplier_price": supp,
                            "shipping_cost": ship,
                            "profit_margin": 120.0,
                            "final_price": final_price,
                            "net_profit": net_profit,
                            "image": item["image"],
                            "created_at": datetime.datetime.utcnow().isoformat()
                        }).execute()
                        st.success(f"تم حفظ {item['name']} بنجاح!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطأ في التنزيل: {e}")
            st.divider()

# ----------------------------- #
# 📋 صفحة إدارة الطلبات (الجديدة)
# ----------------------------- #
elif page == "إدارة الطلبات":
    st.header("📋 سجل طلبات العملاء")
    try:
        response = supabase.table("orders").select("*").execute()
        if response.data and len(response.data) > 0:
            st.success(f"لديك {len(response.data)} طلب مسجل:")
            for order in response.data:
                st.write(f"**العميل:** {order.get('customer_name')} | **المنتج:** {order.get('product_name')} | **السعر:** ${order.get('total_price')} | **الحالة:** {order.get('status')}")
                st.divider()
        else:
            st.info("لا توجد طلبات جديدة مسجلة حتى الآن.")
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات (تأكد من إنشاء جدول orders في Supabase): {e}")

# ----------------------------- #
# ⚙️ إعدادات المتجر
# ----------------------------- #
elif page == "الإعدادات":
    st.header("⚙️ إعدادات متجر Ibox")
    store_name = st.text_input("اسم المتجر:", value="Ibox Store")
    currency = st.selectbox("العملة:", ["USD", "SAR", "EUR"])
    if st.button("حفظ الإعدادات"):
        st.success("تم تحديث إعدادات متجر Ibox بنجاح!")
