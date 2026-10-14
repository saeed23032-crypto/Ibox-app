import datetime
import streamlit as st
import stripe
from supabase import create_client

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title="E Mercato المتجر الإلكتروني", page_icon="🛒", layout="wide"
)

# التهيئة الافتراضية للعملية
if "currency" not in st.session_state:
  st.session_state.currency = "USD"

# ربط Supabase و Stripe باستخدام إعدادات Streamlit Secrets الآمنة
try:
  SUPABASE_URL = st.secrets["supabase"]["url"]
  SUPABASE_KEY = st.secrets["supabase"]["key"]
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  st.error(
      f"⚠️ خطأ في الاتصال بقاعدة البيانات. تأكد من إعدادات Supabase Secrets: {e}"
  )
  st.stop()

# القائمة الجانبية للتنقل
st.sidebar.title("🛒 E Mercato لوحة تحكم")
page = st.sidebar.selectbox(
    "اختر الصفحة", ["محاكاة العميل (الشراء)", "إدارة الطلبات", "الإعدادات"]
)

# 1. صفحة محاكاة العميل (الشراء والدفع)
if page == "محاكاة العميل (الشراء)":
  st.title("🛒 تجربة واجهة متجر (إتمام الشراء والدفع الآمن)")
  st.write(
      "هذه الصفحة تحاکی ما يراه العميل عند شراء منتج وتسجيل طلب تجريبي مع الدفع"
      " الإلكتروني."
  )

  try:
    # جلب المنتجات من جدول products في Supabase
    response = supabase.table("products").select("*").execute()

    if response.data and len(response.data) > 0:
      product_options = {p["name"]: p for p in response.data}
      selected_prod_name = st.selectbox(
          "اختر منتجاً لشراوئه:", list(product_options.keys())
      )
      selected_prod = product_options[selected_prod_name]

      curr = st.session_state.currency
      # التأكد من وجود الحقل الخاص بالسعر
      price_amount = float(
          selected_prod.get("final_price", selected_prod.get("price", 10.0))
      )
      st.write(f"السعر المطلوب: **{price_amount} {curr}**")

      with st.form("checkout_form"):
        st.subheader("بيانات الشحن الخاصة بالعميل")
        cust_name = st.text_input("الاسم الكامل:")
        cust_phone = st.text_input("رقم الهاتف:")
        cust_address = st.text_area("عنوان الشحن بالتفصيل:")

        pay_button = st.form_submit_button("إتمام الدفع الإلكتروني عبر Stripe 💳")

      if pay_button:
        if cust_name and cust_address:
          try:
            # تفعيل مفتاح Stripe السري
            stripe.api_key = st.secrets["stripe_secret_key"]

            # إنشاء جلسة دفع عبر Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": curr.lower(),
                            "product_data": {
                                "name": selected_prod_name,
                            },
                            "unit_amount": int(price_amount * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url="https://streamlit.io?success=true",
                cancel_url="https://streamlit.io?canceled=true",
            )

            # تسجيل الطلب في قاعدة البيانات Supabase
            supabase.table("orders").insert({
                "customer_name": cust_name,
                "customer_phone": cust_phone,
                "customer_address": cust_address,
                "product_name": selected_prod_name,
                "total_price": price_amount,
                "status": "مدفوع (قيد التجهيز)",
                "created_at": datetime.datetime.utcnow().isoformat(),
            }).execute()

            st.success("🎉 تم إنشاء رابط الدفع بنجاح!")
            st.markdown(
                f"### [اضغط هنا للدفع بأمان عبر"
                f" Stripe]({checkout_session.url})"
            )

          except Exception as e:
            st.error(
                f"حدث خطأ أثناء معالجة الدفع (تأكد من إعدادات Stripe Secrets):"
                f" {e}"
            )
        else:
          st.warning("يرجى تعبئة الاسم وعنوان الشحن.")
    else:
      st.info("لا توجد منتجات متاحة للشراء حالياً في قاعدة البيانات.")

  except Exception as e:
    st.error(f"خطأ في التحميل: {e}")

# 2. صفحة إدارة الطلبات
elif page == "إدارة الطلبات":
  st.header("📋 سجل طلبات العملاء")
  try:
    orders_response = supabase.table("orders").select("*").execute()
    if orders_response.data and len(orders_response.data) > 0:
      st.success(f"لديك {len(orders_response.data)} طلب مسجل.")
      for ord_item in orders_response.data:
        st.write(
            f"العميل: **{ord_item.get('customer_name')}** | الهاتف:"
            f" **{ord_item.get('customer_phone', 'غير متوفر')}** 📦 المنتج:"
            f" **{ord_item.get('product_name')}** 💰 الإجمالي:"
            f" **{ord_item.get('total_price')}** | الحالة: 📌"
            f" {ord_item.get('status')}"
        )
        st.divider()
    else:
      st.info("لا توجد طلبات حتى الآن.")
  except Exception as e:
    st.error(f"خطأ في جلب الطلبات: {e}")

# 3. صفحة الإعدادات
elif page == "الإعدادات":
  st.header("⚙ إعدادات المتجر")
  new_currency = st.selectbox(
      "اختر العملة الرئيسية:", ["USD", "AED", "SAR", "EUR"]
  )
  if new_currency != st.session_state.currency:
    st.session_state.currency = new_currency
    st.success(f"تم تحديث العملة إلى {new_currency}")
