import streamlit as st


def get_team_theme(team_name: str) -> dict:
    """Return a dynamic color palette based on the team name."""
    name = str(team_name or "").casefold()
    if "matcha" in name:
        return {
            "banner_bg": "linear-gradient(135deg, #090D0B 0%, #132A1E 100%)",
            "banner_border": "#22C55E",
            "badge_bg": "rgba(34, 197, 94, 0.18)",
            "badge_color": "#4ADE80",
            "btn_bg": "linear-gradient(135deg, #16A34A 0%, #052E16 100%)",
            "btn_shadow": "0 4px 12px rgba(22, 163, 74, 0.30)",
            "addr_bg": "#ECFDF5",
            "addr_border": "#86EFAC",
            "addr_accent": "#16A34A",
            "addr_text": "#064E3B",
            "accent_hex": "#22C55E",
        }
    if "super" in name:
        return {
            "banner_bg": "linear-gradient(135deg, #7F1D1D 0%, #450A0A 100%)",
            "banner_border": "#F59E0B",
            "badge_bg": "rgba(245, 158, 11, 0.20)",
            "badge_color": "#FCD34D",
            "btn_bg": "linear-gradient(135deg, #DC2626 0%, #B45309 100%)",
            "btn_shadow": "0 4px 12px rgba(220, 38, 38, 0.30)",
            "addr_bg": "#FFFBEB",
            "addr_border": "#FDE68A",
            "addr_accent": "#D97706",
            "addr_text": "#78350F",
            "accent_hex": "#F59E0B",
        }
    if "aksara" in name or "akasar" in name:
        return {
            "banner_bg": "linear-gradient(135deg, #0F1115 0%, #27200E 100%)",
            "banner_border": "#EAB308",
            "badge_bg": "rgba(234, 179, 8, 0.20)",
            "badge_color": "#FACC15",
            "btn_bg": "linear-gradient(135deg, #18181B 0%, #CA8A04 100%)",
            "btn_shadow": "0 4px 12px rgba(202, 138, 4, 0.28)",
            "addr_bg": "#FEFCE8",
            "addr_border": "#FEF08A",
            "addr_accent": "#CA8A04",
            "addr_text": "#713F3F",
            "accent_hex": "#EAB308",
        }
    if "apel" in name:
        return {
            "banner_bg": "linear-gradient(135deg, #9A3412 0%, #7F1D1D 100%)",
            "banner_border": "#EF4444",
            "badge_bg": "rgba(239, 68, 68, 0.20)",
            "badge_color": "#FCA5A5",
            "btn_bg": "linear-gradient(135deg, #EA580C 0%, #DC2626 100%)",
            "btn_shadow": "0 4px 12px rgba(234, 88, 12, 0.30)",
            "addr_bg": "#FFF7ED",
            "addr_border": "#FDBA74",
            "addr_accent": "#EA580C",
            "addr_text": "#7C2D12",
            "accent_hex": "#EF4444",
        }
    return {
        "banner_bg": "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
        "banner_border": "#DC2626",
        "badge_bg": "rgba(56, 189, 248, 0.15)",
        "badge_color": "#38BDF8",
        "btn_bg": "linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)",
        "btn_shadow": "0 4px 12px rgba(220, 38, 38, 0.25)",
        "addr_bg": "#EFF6FF",
        "addr_border": "#BFDBFE",
        "addr_accent": "#2563EB",
        "addr_text": "#1E3A8A",
        "accent_hex": "#DC2626",
    }


def apply_team_theme_css(team_name: str):
    """Apply the team color theme to SPG and supervisor pages."""
    theme = get_team_theme(team_name)
    st.markdown(
        f"""
        <style>
        .user-banner {{
            background: {theme["banner_bg"]} !important;
            border-left: 5px solid {theme["banner_border"]} !important;
        }}
        .badge-mode {{
            background-color: {theme["badge_bg"]} !important;
            color: {theme["badge_color"]} !important;
        }}
        [data-testid="stFormSubmitButton"] > button,
        div.stButton > button[kind="primary"] {{
            background: {theme["btn_bg"]} !important;
            box-shadow: {theme["btn_shadow"]} !important;
        }}
        .address-box {{
            background-color: {theme["addr_bg"]} !important;
            border: 1px solid {theme["addr_border"]} !important;
            border-left: 4px solid {theme["addr_accent"]} !important;
            color: {theme["addr_text"]} !important;
        }}
        .section-title {{
            border-left: 4px solid {theme["accent_hex"]};
            padding-left: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_global_styles():
    if str(st.query_params.get("page", "")).strip().lower() != "admin":
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"],
            [data-testid="stSidebarNav"],
            [data-testid="collapsedControl"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Background Utama */
        .stApp {
            background-color: #F8FAFC;
            color: #1E293B;
        }

        /* Header Login */
        .login-header {
            background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
            padding: 32px 24px;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 12px 28px -6px rgba(220, 38, 38, 0.35);
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }
        .login-header h1 {
            margin: 0;
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .login-header p {
            margin: 6px 0 0 0;
            font-size: 0.9rem;
            color: #FEE2E2;
            font-weight: 500;
        }

        /* Styling Container / Card */
        .ui-card {
            background-color: #FFFFFF;
            padding: 22px;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.04);
            margin-bottom: 16px;
        }

        /* Form Styling */
        [data-testid="stForm"] {
            background-color: #FFFFFF;
            padding: 24px 20px;
            border-radius: 18px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.05);
        }

        /* Tombol Utama & Submit */
        [data-testid="stFormSubmitButton"] > button,
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 1.2rem !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25) !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stFormSubmitButton"] > button:hover,
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(220, 38, 38, 0.35) !important;
        }

        /* Tombol Sekunder */
        div.stButton > button[kind="secondary"] {
            background-color: #FFFFFF !important;
            color: #334155 !important;
            font-weight: 600 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 12px !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            border-color: #94A3B8 !important;
            background-color: #F1F5F9 !important;
        }

        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            border-color: #CBD5E1 !important;
        }

        /* User Banner setelah Login */
        .user-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #F8FAFC;
            padding: 18px 20px;
            border-radius: 16px;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.2);
            border-left: 5px solid #DC2626;
        }
        .user-banner-title {
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .badge-mode {
            background-color: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .user-banner-sub {
            font-size: 0.85rem;
            color: #CBD5E1;
        }

        /* KPI Dashboard Card */
        .dashboard-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 18px;
            border-radius: 16px;
            box-shadow: 0 4px 10px -2px rgba(15, 23, 42, 0.04);
            margin-bottom: 12px;
            min-height: 138px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease;
        }
        .dashboard-card:hover {
            transform: translateY(-2px);
            border-color: #CBD5E1;
        }
        .card-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.15;
        }
        .card-value-green {
            font-size: 1.75rem;
            font-weight: 800;
            color: #16A34A;
            line-height: 1.15;
        }
        .card-subtext {
            font-size: 0.8rem;
            color: #64748B;
            margin-top: 4px;
        }
        .card-label {
            font-size: 0.88rem;
            color: #475569;
            font-weight: 600;
            margin-top: 8px;
        }

        /* Progress Bar */
        .progress-bar-container {
            width: 100%;
            background-color: #E2E8F0;
            border-radius: 999px;
            height: 8px;
            margin: 10px 0 4px 0;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #16A34A 0%, #22C55E 100%);
            border-radius: 999px;
        }

        /* Box Alamat Warkop */
        .address-box {
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-left: 4px solid #2563EB;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.88rem;
            color: #1E3A8A;
            margin-top: 8px;
            margin-bottom: 16px;
        }

        /* Section Title Pill */
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0F172A;
            margin: 18px 0 10px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .footer-note {
            text-align: center;
            font-size: 0.78rem;
            color: #94A3B8;
            margin-top: 24px;
            padding-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
