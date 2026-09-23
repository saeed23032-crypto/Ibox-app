import streamlit as st

st.set_page_config(page_title="DropPilot AI", page_icon="🚀", layout="centered")

st.title("🚀 DropPilot AI")
st.caption("مساعد الذكاء الاصطناعي للتجارة الإلكترونية والدروب شيبينغ")

st.divider()

st.subheader("📝 إدخال بيانات المنتج والمورد")
col1, col2 = st.columns(2)

with col1:
    product_name = st.text_input("اسم المنتج", value="حامل هاتف ذكي للسيارة")
    cost_price = st.number_input("سعر المنتج من المورد ($)", value=4.50, step=0.5)

with col2:
    shipping_cost = st.number_input("تكلفة الشحن ($)", value=2.00, step=0.5)
    profit_margin = st.slider("نسبة الربح المطلوبة (%)", min_value=10, max_value=200, value=50)

# معادلات الحساب
total_cost = cost_price + shipping_cost
target_price = total_cost * (1 + (profit_margin / 100))
final_price = target_price / (1 - 0.03)
net_profit = final_price - total_cost - (final_price * 0.03)

st.divider()

st.subheader("📊 نتائج التسعير الآلي")
m1, m2, m3 = st.columns(3)
m1.metric("التكلفة الإجمالية", f"${total_cost:.2f}")
m2.metric("السعر النهائي للعميل", f"${final_price:.2f}")
m3.metric("صافي أرباحك", f"${net_profit:.2f}")

st.divider()

# ميزة توليد الوصف التسويقي
st.subheader("✨ توليد وصف تسويقي احترافي")
if st.button("توليد وصف للمنتج بالذكاء الاصطناعي 🪄"):
    st.info(f"جاري توليد الوصف لـ: **{product_name}**...")
    
    sample_description = f"""
    ### 🌟 {product_name} - الحل المثالي لاحتياجاتك اليومية!
    
    هل تبحث عن الأداء العالي والجودة الفائقة؟ يقدم لك **{product_name}** تجربة فريدة تجمع بين التصميم العصري والاعتمادية العالية.
    
    #### 🔹 المميزات الرئيسية:
    - **جودة تصنيع عالية:** مصمم ليدوم طويلاً مع استخدام أحدث التقنيات.
    - **سهولة الاستخدام:** تصميم مريح يناسب جميع الاستخدامات.
    - **شحن سريع وتغليف آمن:** يصلك المنتج حتى باب منزلك بأعلى معايير الأمان.
    
    🔥 **اطلبه الآن واحصل على خصم لفترة محدودة!**
    """
    st.markdown(sample_description)

st.divider()

st.subheader("📦 ملاحظة الشحن المباشر (Blind Dropshipping)")
st.info("We are dropshipping. Do not include any invoices, promo materials, or brand logos in the package.")

import streamlit as st
from supabase import create_client, Client

from supabase import create_client, Client

url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_key"]

supabase: Client = create_client(url, key)

st.header("🔌 اختبار الاتصال مع Supabase")

def test_connection():
    try:
        response = supabase.table("products").select("*").limit(1).execute()
        return True, response
    except Exception as e:
        return False, str(e)

success, result = test_connection()

if success:
    st.success("✔ الاتصال مع Supabase يعمل بنجاح!")
    st.write(result)
else:
    st.error("❌ فشل الاتصال مع Supabase")
    st.write(result)
