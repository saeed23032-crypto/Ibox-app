import streamlit as st
from supabase import create_client
import stripe
import datetime

# إعداد الاتصال بقاعدة بيانات Supabase من الأسرار
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعداد العملة الافتراضية
if 'currency' not in st.session_state:
    st.session_state.currency = "USD"

st.sidebar.title("🛍️ لوحة تحكم E Mercato")
page = st.sidebar.selectbox("اختر الصفحة", ["عرض المنتجات", "محاكاة العميل (الشراء)", "إدارة الطلبات", "الإعدادات"])

# 1. صفحة عرض المنتجات المحفوظة
if page == "عرض المنتجات":
    st.header("📦 المنتجات المحفوظة في E Mercato")
    try:
        response = supabase.table("products").select("*").execute()
        if response.data and len(response.data) > 0:
            st.success(f"لديك {len(response.data)} منتج جاهز ومعروض في متجرك.")
            for prod in response.data:
                col1, col2 = st.columns([1, 4])
                img_url = prod.get("image_url")
                curr = st.session_state.currency
                with col1:
                    if img_url:
                        st.image(img_url, width=110)
                    else:
                        st.write("لا توجد صورة")
                with col2:
                    st.subheader(prod.get("name"))
                    st.write(f"صافي الربح: **{prod.get('net_profit', 0)} {curr}** | سعر البيع: **{prod.get('final_price', 0)} {curr}** | تكلفة الشحن: **{prod.get('shipping_cost', 0)} {curr}** | سعر المورد: **{prod.get('supplier_price', 0)} {curr}**")
                st.divider()
        else:
            st.info("لا توجد منتجات محفوظة حالياً.")
    except Exception as e:
        st.error(f"خطأ في جلب المنتجات: {e}")

# 2. صفحة محاكاة العميل وإتمام الدفع الحقيقي عبر Stripe
elif page == "محاكاة العميل (الشراء)":
    st.header("🛒 تجربة واجهة متجرك (إتمام الشراء والدفع الآمن)")
    st.caption("هذه الصفحة تحاكي ما يراه العميل عند شراء منتج وتسجيل طلب تجريبي مع الدفع الإلكتروني.")

    try:
        response = supabase.table("products").select("*").execute()
        if response.data and len(response.data) > 0:
            product_options = {p["name"]: p for p in response.data}
            selected_prod_name = st.selectbox("اختر منتجاً لشراوئه:", list(product_options.keys()))
            selected_prod = product_options[selected_prod_name]
            curr = st.session_state.currency
            price_amount = float(selected_prod.get('final_price'))

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
                            # تفعيل مفتاح Stripe السري من إعدادات Streamlit Secrets
                            stripe.api_key = st.secrets["stripe_secret_key"]
                            
                            # إنشاء جلسة دفع عبر Stripe
                            checkout_session = stripe.checkout.Session.create(
                                payment_method_types=['card'],
                                line_items=[{
                                    'price_data': {
                                        'currency': curr.lower(),
                                        'product_data': {
                                            'name': selected_prod_name,
                                        },
                                        'unit_amount': int(price_amount * 100),
                                    },
                                    'quantity': 1,
                                }],
                                mode='payment',
                                success_url='https://streamlit.io?success=true',
                                cancel_url='https://streamlit.io?canceled=true',
                            )

                            # تسجيل الطلب في قاعدة البيانات
                            supabase.table("orders").insert({
                                "customer_name": cust_name,
                                "product_name": selected_prod_name,
                                "total_price": price_amount,
                                "status": "مدفوع (قيد التجهيز)",
                                "created_at": datetime.datetime.utcnow().isoformat()
                            }).execute()

                            st.success("🎉 تم إنشاء رابط الدفع بنجاح!")
                            st.markdown(f"### [اضغط هنا للدفع بأمان عبر Stripe]({checkout_session.url})", unsafe_allow_html=True)

                        except Exception as e:
                            st.error(f"حدث خطأ أثناء معالجة الدفع: {e}")
                    else:
                        st.warning("يرجى تعبئة الاسم وعنوان الشحن.")
        else:
            st.info("لا توجد منتجات متاحة للشراء حالياً.")
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")

# 3. صفحة إدارة الطلبات
elif page == "إدارة الطلبات":
    st.header("📋 سجل طلبات العملاء")
    try:
        orders_response = supabase.table("orders").select("*").execute()
        if orders_response.data and len(orders_response.data) > 0:
            st.success(f"لديك {len(orders_response.data)} طلب مسجل.")
            for ord_item in orders_response.data:
                st.write(f"العميل: **{ord_item.get('customer_name')}** 📦 المنتج: **{ord_item.get('product_name')}** 💰 الإجمالي: **{ord_item.get('total_price')}** | الحالة: 📌 {ord_item.get('status')}")
                st.divider()
        else:
            st.info("لا توجد طلبات حتى الآن.")
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات: {e}")

# 4. صفحة الإعدادات
elif page == "الإعدادات":
    st.header("⚙ إعدادات المتجر")
    new_currency = st.selectbox("اختر العملة الرئيسية:", ["USD", "AED", "SAR", "EUR"])
    if new_currency != st.session_state.currency:
        st.session_state.currency = new_currency
        st.success(f"تم تحديث العملة إلى {new_currency}")
