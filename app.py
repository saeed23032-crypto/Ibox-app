import datetime as dt
import hmac
import re

import pandas as pd
import stripe
import streamlit as st
from supabase import create_client

# ============================================================
# الإعدادات العامة
# ============================================================
st.set_page_config(page_title="E Mercato", page_icon="🛒", layout="wide")

st.markdown(
    """
    <style>
    .stApp { direction: rtl; text-align: right; }
    .stMarkdown, .stTextInput label, .stTextArea label,
    .stSelectbox label, .stNumberInput label { text-align: right; }
    </style>
    """,
    unsafe_allow_html=True,
)

CURRENCY = str(st.secrets.get("currency", "USD")).upper()
APP_URL = str(st.secrets.get("app_url", "")).rstrip("/")
STRIPE_FEE_PCT = 0.03  # تقدير تقريبي لرسوم Stripe (عدّله حسب بلدك)

STATUS_LABELS = {
    "pending_payment": "بانتظار الدفع",
    "paid": "مدفوع - جاهز للطلب من المورد",
    "ordered_from_supplier": "تم الطلب من المورد",
    "shipped": "تم الشحن",
    "delivered": "تم التسليم",
    "cancelled": "ملغي",
}
COUNTED_STATUSES = ["paid", "ordered_from_supplier", "shipped", "delivered"]

# ============================================================
# الاتصال بـ Supabase و Stripe
# ============================================================


@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
    )


try:
    supabase = get_supabase()
    stripe.api_key = st.secrets["stripe_secret_key"]
except Exception as e:
    st.error(f"⚠️ خطأ في الإعدادات (Secrets): {e}")
    st.stop()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def money(x) -> str:
    return f"{float(x):,.2f} {CURRENCY}"


# ============================================================
# التحقق من الدفع عند عودة العميل من Stripe
# ============================================================


def confirm_payment(session_id: str) -> bool:
    """يتحقق من Stripe مباشرة، ثم يحدّث الطلب إلى مدفوع."""
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        supabase.table("orders").update({"status": "paid"}).eq(
            "stripe_session_id", session_id
        ).eq("status", "pending_payment").execute()
        return True
    return False


def handle_return_from_stripe():
    params = st.query_params
    if params.get("status") == "success" and params.get("session_id"):
        try:
            if confirm_payment(params["session_id"]):
                st.success("✅ تم الدفع بنجاح! سنتواصل معك قريباً لتأكيد الشحن.")
                st.balloons()
            else:
                st.warning("لم يتم تأكيد الدفع بعد. إذا خُصم المبلغ تواصل معنا.")
        except Exception as e:
            st.error(f"تعذّر التحقق من الدفع: {e}")
    elif params.get("status") == "canceled":
        st.info("تم إلغاء عملية الدفع. يمكنك المحاولة مرة أخرى.")


# ============================================================
# واجهة العميل (المتجر)
# ============================================================
PHONE_RE = re.compile(r"^\+?[0-9\s\-]{7,15}$")


def storefront():
    st.title("🛒 E Mercato المتجر الإلكتروني")
    handle_return_from_stripe()

    try:
        products = (
            supabase.table("products")
            .select("*")
            .eq("active", True)
            .execute()
            .data
        )
    except Exception as e:
        st.error(f"خطأ في تحميل المنتجات: {e}")
        return

    if not products:
        st.info("لا توجد منتجات متاحة حالياً.")
        return

    options = {p["name"]: p for p in products}
    name = st.selectbox("اختر المنتج:", list(options.keys()))
    product = options[name]

    col_img, col_info = st.columns([1, 2])
    with col_img:
        if product.get("image_url"):
            st.image(product["image_url"], use_container_width=True)
    with col_info:
        st.subheader(product["name"])
        if product.get("description"):
            st.write(product["description"])
        st.markdown(f"### السعر: {money(product['price'])}")

    with st.form("checkout_form"):
        st.subheader("بيانات الشحن")
        cust_name = st.text_input("الاسم الكامل *")
        cust_phone = st.text_input("رقم الهاتف * (مثال: +971501234567)")
        cust_address = st.text_area("عنوان الشحن بالتفصيل *")
        qty = st.number_input("الكمية", min_value=1, max_value=10, value=1)
        submitted = st.form_submit_button("إتمام الدفع الآمن عبر Stripe 💳")

    if not submitted:
        return

    # ---- التحقق من المدخلات ----
    if len(cust_name.strip()) < 3 or len(cust_address.strip()) < 10:
        st.warning("يرجى كتابة الاسم الكامل وعنوان شحن مفصّل.")
        return
    if not PHONE_RE.match(cust_phone.strip()):
        st.warning("رقم الهاتف غير صالح.")
        return
    if not APP_URL:
        st.error("لم يتم ضبط app_url في Secrets.")
        return

    qty = int(qty)
    unit_price = float(product["price"])
    cost_price = float(product.get("cost_price") or 0)
    total = round(unit_price * qty, 2)

    order_id = None
    try:
        # 1) سجّل الطلب كـ "بانتظار الدفع" (وليس مدفوعاً)
        order = (
            supabase.table("orders")
            .insert(
                {
                    "customer_name": cust_name.strip(),
                    "customer_phone": cust_phone.strip(),
                    "customer_address": cust_address.strip(),
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "cost_price": cost_price,
                    "total_price": total,
                    "currency": CURRENCY,
                    "status": "pending_payment",
                    "created_at": now_iso(),
                }
            )
            .execute()
            .data[0]
        )
        order_id = order["id"]

        # 2) أنشئ جلسة الدفع (السعر يأتي من قاعدة البيانات وليس من العميل)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": CURRENCY.lower(),
                        "product_data": {"name": product["name"]},
                        "unit_amount": int(round(unit_price * 100)),
                    },
                    "quantity": qty,
                }
            ],
            mode="payment",
            metadata={"order_id": str(order_id)},
            success_url=(
                f"{APP_URL}/?status=success&session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{APP_URL}/?status=canceled",
        )

        # 3) اربط الجلسة بالطلب
        supabase.table("orders").update({"stripe_session_id": session.id}).eq(
            "id", order_id
        ).execute()

        st.success("تم تجهيز الطلب! أكمل الدفع من الرابط التالي:")
        st.markdown(f"### [👉 اضغط هنا للدفع بأمان عبر Stripe]({session.url})")

    except Exception as e:
        if order_id:
            supabase.table("orders").update({"status": "cancelled"}).eq(
                "id", order_id
            ).execute()
        st.error(f"حدث خطأ أثناء معالجة الطلب: {e}")


# ============================================================
# لوحة الإدارة (محمية بكلمة مرور)
# ============================================================


def admin_login() -> bool:
    if st.session_state.get("is_admin"):
        return True
    st.header("🔐 دخول الإدارة")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        real = str(st.secrets.get("admin_password", ""))
        if real and hmac.compare_digest(pwd.encode(), real.encode()):
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("كلمة المرور غير صحيحة.")
    return False


def sync_pending_orders():
    """يراجع Stripe لكل الطلبات المعلقة ويحدّث ما تم دفعه."""
    pending = (
        supabase.table("orders")
        .select("stripe_session_id")
        .eq("status", "pending_payment")
        .not_.is_("stripe_session_id", "null")
        .execute()
        .data
    )
    updated = 0
    for row in pending:
        try:
            if confirm_payment(row["stripe_session_id"]):
                updated += 1
        except Exception:
            pass
    return updated


def dashboard_tab(orders):
    paid = [o for o in orders if o["status"] in COUNTED_STATUSES]
    revenue = sum(float(o["total_price"]) for o in paid)
    cost = sum(float(o.get("cost_price") or 0) * o["quantity"] for o in paid)
    fees = revenue * STRIPE_FEE_PCT
    profit = revenue - cost - fees

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("عدد الطلبات المدفوعة", len(paid))
    c2.metric("الإيرادات", money(revenue))
    c3.metric("تكلفة المورد + الرسوم", money(cost + fees))
    c4.metric("صافي الربح التقريبي", money(profit))
    st.caption(
        f"الرسوم محسوبة بنسبة {STRIPE_FEE_PCT:.0%} تقريباً. "
        "لا تنسَ احتساب الإعلانات والمرتجعات."
    )

    to_order = [o for o in orders if o["status"] == "paid"]
    if to_order:
        st.warning(f"📦 لديك {len(to_order)} طلب مدفوع يجب طلبه من المورد.")


def orders_tab(orders):
    if st.button("🔄 تحديث حالة الدفع من Stripe"):
        n = sync_pending_orders()
        st.success(f"تم تحديث {n} طلب.")
        st.rerun()

    if not orders:
        st.info("لا توجد طلبات.")
        return

    df = pd.DataFrame(orders)
    df["status_ar"] = df["status"].map(STATUS_LABELS)
    df["profit"] = (df["unit_price"] - df["cost_price"].fillna(0)) * df["quantity"]
    view = df[
        [
            "id", "created_at", "customer_name", "customer_phone",
            "customer_address", "product_name", "quantity",
            "total_price", "profit", "status_ar",
        ]
    ].rename(
        columns={
            "id": "رقم", "created_at": "التاريخ", "customer_name": "العميل",
            "customer_phone": "الهاتف", "customer_address": "العنوان",
            "product_name": "المنتج", "quantity": "الكمية",
            "total_price": "الإجمالي", "profit": "الربح قبل الرسوم",
            "status_ar": "الحالة",
        }
    )
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.subheader("تغيير حالة طلب")
    ids = [o["id"] for o in orders]
    oid = st.selectbox("رقم الطلب", ids)
    new_status = st.selectbox(
        "الحالة الجديدة",
        list(STATUS_LABELS.keys()),
        format_func=lambda k: STATUS_LABELS[k],
    )
    if st.button("حفظ الحالة"):
        supabase.table("orders").update({"status": new_status}).eq(
            "id", oid
        ).execute()
        st.success("تم التحديث.")
        st.rerun()


def products_tab():
    products = supabase.table("products").select("*").order("id").execute().data
    if products:
        rows = []
        for p in products:
            price = float(p["price"])
            cost = float(p.get("cost_price") or 0)
            margin = (price - cost) / price * 100 if price else 0
            rows.append(
                {
                    "رقم": p["id"], "المنتج": p["name"],
                    "التكلفة": cost, "سعر البيع": price,
                    "الربح للقطعة": round(price - cost, 2),
                    "الهامش %": round(margin, 1),
                    "فعّال": p["active"],
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.subheader("تفعيل / إيقاف منتج")
        pid = st.selectbox(
            "المنتج", [p["id"] for p in products],
            format_func=lambda i: next(p["name"] for p in products if p["id"] == i),
        )
        cur = next(p for p in products if p["id"] == pid)
        if st.button("إيقاف" if cur["active"] else "تفعيل"):
            supabase.table("products").update({"active": not cur["active"]}).eq(
                "id", pid
            ).execute()
            st.rerun()

    st.subheader("➕ إضافة منتج جديد")
    with st.form("add_product"):
        name = st.text_input("اسم المنتج")
        desc = st.text_area("الوصف")
        img = st.text_input("رابط الصورة")
        supplier = st.text_input("رابط المورد (للاستخدام الداخلي)")
        cost = st.number_input("سعر التكلفة (من المورد + الشحن)", min_value=0.0, step=0.5)
        price = st.number_input("سعر البيع", min_value=0.0, step=0.5)
        ok = st.form_submit_button("إضافة")
    if ok:
        if not name.strip() or price <= 0:
            st.warning("أدخل الاسم وسعر بيع صحيح.")
        elif price <= cost * (1 + STRIPE_FEE_PCT):
            st.warning("سعر البيع لا يغطي التكلفة + رسوم الدفع. ارفع السعر.")
        else:
            supabase.table("products").insert(
                {
                    "name": name.strip(), "description": desc.strip(),
                    "image_url": img.strip(), "supplier_url": supplier.strip(),
                    "cost_price": cost, "price": price, "active": True,
                }
            ).execute()
            st.success("تمت الإضافة.")
            st.rerun()


def admin_page():
    if not admin_login():
        return
    st.header("📊 لوحة الإدارة")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.is_admin = False
        st.rerun()

    try:
        orders = (
            supabase.table("orders")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        )
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات: {e}")
        return

    t1, t2, t3 = st.tabs(["الأرباح", "الطلبات", "المنتجات"])
    with t1:
        dashboard_tab(orders)
    with t2:
        orders_tab(orders)
    with t3:
        products_tab()


# ============================================================
# التنقل
# ============================================================
page = st.sidebar.radio("القائمة", ["🛍️ المتجر", "🔐 الإدارة"])
if page == "🛍️ المتجر":
    storefront()
else:
    admin_page()
