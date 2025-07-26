from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    """Inject RTL + Persian font and fix number‑field direction."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');

        html, body, * {
            font-family: 'Vazirmatn', sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Hero section with app title and subtitle."""
    st.markdown(
        """
        <div style="text-align:center; margin-top:4rem;">
            <h1 style="margin-bottom:0;">🤖 کمپین‌ساز هوشمند یکتانت</h1>
            <h4 style="color:#666; margin-top:0.25rem;">تبلیغات مؤثر، فقط با چند کلیک</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_about_agent() -> None:
    """Explain what the agent does and its main benefits."""
    st.markdown(
        """
        ### Agent ما چه‌کاری انجام می‌دهد؟
        **کمپین‌ساز هوشمند** یک عامل نرم‌افزاری (AI Agent) است که با دریافت چند دادهٔ ساده:
        * مناسب‌ترین مخاطبان را می‌یابد؛
        * بودجه و زمان‌بندی بهینه را پیشنهاد می‌دهد؛
        * لندینگ و پیام تبلیغاتی شما را تنظیم می‌کند.

        نتیجه؟  
        کاهش هزینهٔ آزمایش (A/B) و افزایش نرخ تبدیل در کوتاه‌ترین زمان ممکن.
        """,
        unsafe_allow_html=False,
    )


def render_get_started_button() -> None:
    """Primary CTA that routes user to the campaigns page."""
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 شروع ساخت کمپین (فرم)", type="primary", use_container_width=True):
            st.switch_page("pages/campaign_requests.py")
        if st.button("🚀 شروع ساخت کمپین (چت)", type="primary", use_container_width=True):
            st.switch_page("pages/chat.py")
        if st.button("📊 مشاهده تاریخچه عامل‌ها", type="secondary", use_container_width=True):
            st.switch_page("pages/agent_history.py")


def main() -> None:
    st.set_page_config(
        page_title="کمپین‌ساز یکتانت – خانه",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_css()

    render_hero()
    render_about_agent()
    render_get_started_button()


if __name__ == "__main__":
    main()
