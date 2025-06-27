from __future__ import annotations

import sys
from pathlib import Path

# ------------------------------------------------------------------------- #
#                     Ensure project root is on sys.path                    #
# ------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent  # one level above /pages
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# ------------------------------------------------------------------------- #
#                          Third‑party imports                              #
# ------------------------------------------------------------------------- #

import json
from typing import Sequence

import pandas as pd
import streamlit as st
from pydantic import ValidationError

# ------------------------------------------------------------------------- #
#                         Internal / project imports                        #
# ------------------------------------------------------------------------- #

from db import init_db
from models import CampaignRequest, IRAN_PROVINCES
from campaign_request_crud import insert_campaign_request, fetch_campaign_requests


# ------------------------------------------------------------------------- #
#                               Styling                                     #
# ------------------------------------------------------------------------- #


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


# ------------------------------------------------------------------------- #
#                         Helper & render functions                          #
# ------------------------------------------------------------------------- #


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
                "نوع مخاطب": row["target_audience"],
                "لوکیشن‌ها": ", ".join(json.loads(row["locations"])),
                "بودجه روزانه (تومان)": row["daily_budget"],
                "نوع لندینگ": row["landing_type"],
                "وضعیت": row["status"],
                "تاریخ ایجاد": row["created_at"].split("T")[0],
            }
        )
    _display_rows(processed)


def render_create_form() -> None:
    """Form for inserting a new campaign request."""
    with st.expander("ایجاد درخواست جدید", expanded=False):
        with st.form("create_campaign_form", clear_on_submit=True):
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
            with col2:
                locations = st.multiselect(
                    "استان‌های ارائه‌دهنده سرویس",
                    options=IRAN_PROVINCES,
                    placeholder="انتخاب استان‌ها",
                )
                landing_type = st.selectbox("نوع لندینگ", ["پیج", "شماره تماس", "لینک دیگر"])

            submitted = st.form_submit_button("ثبت درخواست", use_container_width=True)
            if submitted:
                try:
                    campaign = CampaignRequest(
                        business_type=business_type,
                        target_audience=target_audience,
                        locations=locations,
                        daily_budget=daily_budget,
                        landing_type=landing_type,
                    )
                    insert_campaign_request(campaign)
                    st.toast("درخواست با موفقیت ثبت شد!", icon="✅")
                    st.rerun()
                except ValidationError as exc:
                    st.error("خطا در اعتبارسنجی داده‌ها:")
                    st.json(exc.errors())


# ------------------------------------------------------------------------- #
#                                   Main                                    #
# ------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(
        page_title="کمپین‌ساز یکتانت – مدیریت درخواست‌ها",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_css()
    init_db()

    st.header("📄 مدیریت درخواست‌های کمپین")
    render_campaigns_table()
    st.divider()
    render_create_form()


if __name__ == "__main__":
    main()
