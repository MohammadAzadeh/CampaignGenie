from __future__ import annotations

import json
from typing import Sequence

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from pages.models import CampaignRequest, IRAN_PROVINCES, Landing, Business


def inject_global_css() -> None:
    """Add RTL direction, Persian font, and fix number inputs inside this page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');

        html, body, * {
            font-family: 'Vazirmatn', sans-serif !important;
            direction: rtl;
            text-align: right;
        }
        /* Data-grid RTL */
        .stDataFrame div[data-testid="data-grid"],
        .stDataFrame div[data-testid="data-grid"] div {
            direction: rtl !important;
            text-align: right !important;
        }
        /* Keep numbers LTR */
        input[type="number"] {
            direction: ltr !important;
            text-align: right !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _display_rows(rows: Sequence[dict]) -> None:
    """Render rows in a Streamlit dataframe with RTL column order."""
    if not rows:
        st.info("درخواستی وجود ندارد.")
        return

    df = pd.DataFrame(rows)
    df = df[df.columns[::-1]]  # reverse order for RTL look

    st.dataframe(
        df.style.format(
            subset=["بودجه روزانه (تومان)"],
            formatter=lambda x: f"{x:,.0f}",
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_campaigns_table() -> None:
    processed: list[dict] = []
    for row in fetch_campaign_requests():
        processed.append(
            {
                "شناسه": row["id"],
                "نوع کسب‌وکار": row["business_type"],
                "نام کسب‌وکار": row["business_name"],
                "نوع مخاطب": row["target_audience"],
                "لوکیشن‌ها": ", ".join(json.loads(row["locations"])),
                "بودجه روزانه (تومان)": row["daily_budget"],
                "بودجه کل (تومان)": row["total_budget"],
                "نوع لندینگ": row["landing_type"],
                "آدرس لندینگ": row["landing_address"],
                "وضعیت": row["status"],
                "تاریخ ایجاد": row["created_at"].split("T")[0],
            }
        )
    _display_rows(processed)


def render_create_form() -> None:
    """Form for inserting a new campaign request."""
    with st.expander("ایجاد درخواست جدید", expanded=False):
        with st.form(
            "create_campaign_form", clear_on_submit=True, enter_to_submit=False
        ):
            col1, col2 = st.columns(2)
            with col1:
                business_type = st.text_input("نوع کسب‌وکار")
                target_audience = st.text_input("نوع مخاطبین هدف")
                daily_budget = st.number_input(
                    "بودجه روزانه کمپین (تومان)",
                    min_value=0,
                    step=50_000,
                    format="%d",
                )
                landing_type = st.selectbox(
                    "نوع لندینگ", ["سایت", "شماره تماس", "اکانت بیزنسی", "اپلیکیشن"]
                )
                goal = st.selectbox(
                    "هدف تبلیغاتی",
                    [
                        "انتخاب توسط کمپین جن",
                        "افزایش فروش",
                        "جمع آوری لید",
                        "افزایش ترافیک",
                    ],
                )

            with col2:
                business_name = st.text_input("نام کسب‌و‌کار")
                locations = st.multiselect(
                    "استان‌های ارائه‌دهنده سرویس",
                    options=IRAN_PROVINCES,
                    placeholder="انتخاب استان‌ها",
                )
                total_budget = st.number_input(
                    "بودجه کل کمپین (تومان)",
                    min_value=0,
                    step=50_000,
                    format="%d",
                )
                landing_address = st.text_input("آدرس لندینگ")
            submitted = st.form_submit_button("ثبت درخواست", use_container_width=True)
            if submitted:
                try:
                    campaign = CampaignRequest(
                        advertiser_id=1,
                        goal=goal,
                        business=Business(name=business_name, type=business_type),
                        target_audience=target_audience,
                        locations=locations,
                        daily_budget=daily_budget,
                        total_budget=total_budget,
                        landing=Landing(address=landing_address, type=landing_type),
                    )
                    insert_campaign_request(campaign)
                    st.toast("درخواست با موفقیت ثبت شد!", icon="✅")
                    st.rerun()
                except ValidationError as exc:
                    st.error("خطا در اعتبارسنجی داده‌ها:")
                    st.json(exc.errors())


def main() -> None:
    st.set_page_config(
        page_title="کمپین‌ساز یکتانت – مدیریت درخواست‌ها",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_css()

    st.header("📄 مدیریت درخواست‌های کمپین")
    render_campaigns_table()
    st.divider()
    render_create_form()


if __name__ == "__main__":
    main()
