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
            background-color: color-mix(in srgb, {theme["addr_bg"]} 28%, var(--surface)) !important;
            border: 1px solid color-mix(in srgb, {theme["addr_border"]} 72%, var(--line)) !important;
            border-left: 4px solid {theme["addr_accent"]} !important;
            color: var(--ink) !important;
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

        .stApp {
            --ink: #17212f;
            --ink: light-dark(#17212f, #e7ebf1);
            --muted: #687386;
            --muted: color-mix(in srgb, var(--ink) 64%, transparent);
            --line: #e5e9f0;
            --line: light-dark(rgba(23, 33, 47, 0.14), rgba(231, 235, 241, 0.16));
            --canvas: #f4f6fa;
            --canvas: light-dark(#f4f6fa, #101722);
            --surface: #ffffff;
            --surface: light-dark(#ffffff, #171f2b);
            --surface-alt: #f0f2f6;
            --surface-alt: light-dark(#f0f2f6, #202a38);
            --accent: #a52b36;
            --accent: light-dark(#a52b36, #f28691);
            --accent-deep: #7f1d2b;
            --accent-soft: #fbf0f0;
            --accent-soft: color-mix(in srgb, var(--accent) 9%, var(--surface));
            --positive-text: #087443;
            --positive-text: light-dark(#087443, #6bd3a0);
            --danger-text: #b42318;
            --danger-text: light-dark(#b42318, #ff8a80);
            --accent-deep: color-mix(in srgb, var(--accent) 78%, #111827);
            --shadow-card: 0 14px 36px rgba(22, 34, 51, 0.07);
        }

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 10% 0%, color-mix(in srgb, var(--ink) 4%, transparent), transparent 34rem),
                var(--canvas);
            color: var(--ink);
        }

        header[data-testid="stHeader"] {
            background: color-mix(in srgb, var(--canvas) 88%, transparent);
        }

        [data-testid="stMainBlockContainer"],
        .main .block-container {
            max-width: 1480px;
            padding: 2rem clamp(1rem, 3vw, 2.5rem) 4rem;
        }

        h1, h2, h3, h4 {
            color: var(--ink);
            letter-spacing: -0.035em;
        }

        h1 { font-weight: 800; }
        h2, h3 { font-weight: 750; }
        [data-testid="stCaptionContainer"], .stMarkdown small { color: var(--muted); }
        hr { border-color: var(--line); margin: 1.5rem 0; }

        .login-header {
            isolation: isolate;
            position: relative;
            overflow: hidden;
            margin: 0 0 2rem;
            padding: clamp(2rem, 5vw, 3.5rem) 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 28px;
            background:
                radial-gradient(circle at 82% 18%, rgba(255, 255, 255, 0.15), transparent 15rem),
                linear-gradient(128deg, #202a39 0%, #111927 58%, #6f202b 100%);
            color: #fff;
            text-align: center;
            box-shadow: 0 24px 54px rgba(31, 40, 55, 0.2);
        }
        .login-header::before,
        .login-header::after {
            position: absolute;
            z-index: -1;
            content: "";
            border: 1px solid rgba(255, 255, 255, 0.11);
            border-radius: 50%;
            pointer-events: none;
        }
        .login-header::before {
            width: 310px;
            height: 310px;
            top: -190px;
            right: -70px;
        }
        .login-header::after {
            width: 230px;
            height: 230px;
            bottom: -180px;
            left: -40px;
        }
        .login-header > div:first-child {
            display: grid;
            width: 62px;
            height: 62px;
            place-items: center;
            margin: 0 auto 1rem !important;
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.12);
            box-shadow: inset 0 1px rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(8px);
        }
        .login-kicker {
            display: block;
            margin-bottom: 0.65rem;
            color: #f6c7c9;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.19em;
        }
        .login-header h1 {
            margin: 0;
            color: #fff;
            font-size: clamp(1.45rem, 3vw, 2.15rem);
            font-weight: 800;
            letter-spacing: -0.045em;
        }
        .login-header p {
            max-width: 38rem;
            margin: 0.7rem auto 0;
            color: #d7dce5;
            font-size: 0.95rem;
            font-weight: 500;
            line-height: 1.65;
        }

        .ui-card {
            margin-bottom: 1rem;
            padding: 1.4rem;
            border: 1px solid var(--line);
            border-radius: 20px;
            background: var(--surface);
            box-shadow: var(--shadow-card);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line) !important;
            border-radius: 20px !important;
            background: var(--surface);
            box-shadow: 0 10px 28px rgba(22, 34, 51, 0.045);
        }
        [data-testid="stForm"] {
            padding: clamp(1rem, 2.5vw, 1.6rem);
            border: 1px solid var(--line);
            border-radius: 20px;
            background: var(--surface);
            box-shadow: 0 12px 32px rgba(22, 34, 51, 0.06);
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTimeInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div {
            border-color: var(--line) !important;
            border-radius: 12px !important;
            background-color: var(--canvas) !important;
            color: var(--ink) !important;
            transition: border-color 160ms ease, box-shadow 160ms ease;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus,
        .stTextArea textarea:focus,
        [data-baseweb="select"]:focus-within > div {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(165, 43, 54, 0.11) !important;
        }
        label, [data-testid="stWidgetLabel"] p {
            color: var(--ink) !important;
            font-weight: 650 !important;
        }

        div.stButton > button,
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="stDownloadButton"] > button {
            min-height: 2.7rem;
            border-radius: 12px !important;
            font-weight: 700 !important;
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease !important;
        }
        div.stButton > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="stDownloadButton"] > button {
            border: 1px solid transparent !important;
            background: linear-gradient(135deg, #ad3540 0%, #83222e 100%) !important;
            color: #fff !important;
            box-shadow: 0 8px 18px rgba(146, 36, 48, 0.2) !important;
        }
        div.stButton > button[kind="primary"]:hover,
        [data-testid="stFormSubmitButton"] > button:hover,
        [data-testid="stDownloadButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 22px rgba(146, 36, 48, 0.26) !important;
        }
        div.stButton > button[kind="secondary"] {
            border: 1px solid var(--line) !important;
            background: var(--surface) !important;
            color: var(--ink) !important;
            box-shadow: 0 2px 6px rgba(22, 34, 51, 0.035);
        }
        div.stButton > button[kind="secondary"]:hover {
            border-color: color-mix(in srgb, var(--ink) 28%, transparent) !important;
            background: var(--surface-alt) !important;
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--line);
        }
        [data-testid="stTabs"] button[role="tab"] {
            min-height: 2.8rem;
            border-radius: 11px 11px 0 0;
            color: var(--muted);
            font-weight: 700;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent) !important;
        }
        [data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--line);
            box-shadow: 0 6px 16px rgba(22, 34, 51, 0.035);
        }
        [data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--surface);
        }
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: var(--surface);
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed color-mix(in srgb, var(--ink) 25%, transparent);
            border-radius: 16px;
            background: var(--surface);
        }

        .user-banner {
            position: relative;
            overflow: hidden;
            margin-bottom: 1rem;
            padding: 1.2rem 1.35rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: 4px solid #b94a54;
            border-radius: 18px;
            background: linear-gradient(125deg, #1d2939 0%, #101827 100%);
            color: #f8fafc;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.16);
        }
        .user-banner-title {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.45rem;
            color: #fff;
            font-size: 1.08rem;
            font-weight: 750;
        }
        .badge-mode {
            padding: 0.25rem 0.65rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            color: #f2c6c8;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .user-banner-sub { color: #c6ced9; font-size: 0.84rem; }

        .dashboard-card {
            display: flex;
            min-height: 148px;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 0.75rem;
            padding: 1.2rem;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: linear-gradient(145deg, var(--surface) 0%, var(--surface-alt) 100%);
            box-shadow: 0 10px 24px rgba(22, 34, 51, 0.055);
            transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
        }
        .dashboard-card:hover {
            transform: translateY(-2px);
            border-color: color-mix(in srgb, var(--ink) 22%, transparent);
            box-shadow: 0 16px 30px rgba(22, 34, 51, 0.09);
        }
        .card-value, .card-value-green {
            color: var(--ink);
            font-size: clamp(1.45rem, 2.2vw, 1.9rem);
            font-weight: 800;
            letter-spacing: -0.045em;
            line-height: 1.15;
        }
        .card-value-green { color: var(--positive-text); }
        .card-subtext {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.79rem;
            line-height: 1.45;
        }
        .card-label {
            margin-top: 0.9rem;
            color: var(--muted);
            font-size: 0.79rem;
            font-weight: 700;
            letter-spacing: 0.015em;
        }
        .progress-bar-container {
            width: 100%;
            height: 8px;
            overflow: hidden;
            margin: 0.8rem 0 0.3rem;
            border-radius: 999px;
            background: var(--surface-alt);
        }
        .progress-bar-fill {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #16734d, #4baa78);
        }

        .address-box {
            margin: 0.6rem 0 1rem;
            padding: 0.9rem 1rem;
            border: 1px solid var(--line);
            border-left: 4px solid #547f91;
            border-radius: 14px;
            background: var(--surface);
            color: var(--ink);
            font-size: 0.86rem;
            line-height: 1.7;
        }
        .section-title {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin: 1.3rem 0 0.8rem;
            padding: 0.65rem 0.9rem;
            border: 1px solid var(--line);
            border-left: 3px solid var(--accent);
            border-radius: 0 12px 12px 0;
            background: var(--surface);
            color: var(--ink);
            font-size: 0.95rem;
            font-weight: 750;
        }
        .footer-note {
            margin-top: 2rem;
            padding: 1rem 0 0.5rem;
            border-top: 1px solid var(--line);
            color: var(--muted);
            font-size: 0.75rem;
            text-align: center;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            background: linear-gradient(180deg, #17212f 0%, #101722 100%);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        [data-testid="stSidebar"] label {
            color: #e7ebf1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #aab4c2 !important;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
            border-color: rgba(255, 255, 255, 0.12) !important;
            background: rgba(255, 255, 255, 0.055) !important;
            color: #e7ebf1 !important;
            box-shadow: none;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {
            border-color: rgba(255, 255, 255, 0.24) !important;
            background: rgba(255, 255, 255, 0.11) !important;
        }
        .card-person-name { color: var(--ink); }

        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"], .main .block-container {
                padding: 1rem 0.85rem 2.5rem;
            }
            .login-header {
                margin-bottom: 1.3rem;
                padding: 1.8rem 1rem;
                border-radius: 22px;
            }
            .login-header p { font-size: 0.86rem; }
            [data-testid="stForm"] { padding: 1rem; border-radius: 16px; }
            .dashboard-card { min-height: 128px; padding: 1rem; border-radius: 16px; }
            .section-title { font-size: 0.88rem; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                transition-duration: 0.01ms !important;
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
