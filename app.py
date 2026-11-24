"""ONGI의 Streamlit 대시보드 화면입니다."""

from datetime import date
import html
import importlib

import altair as alt
import streamlit as st

import config
import services

# Streamlit 핫 리로드 시 이전 모듈 캐시로 인한 ImportError를 방지합니다.
importlib.reload(config)
importlib.reload(services)

from config import (
    APP_TITLE,
    CURRENT_STATUS_OPTIONS,
    FIELD_OPTIONS,
    FINANCE_DEFAULTS,
    GROWTH_ACTIONS,
    LIFE_CYCLE_OPTIONS,
    MICRO_KINDNESS_ACTIONS,
    OLLAMA_MODEL_NAME,
    PLAZA_POST_SPC_BONUS,
    PLAZA_REACTION_SPC_BONUS,
    PLAZA_REACTIONS,
    POSITIVE_ACTION_WEIGHTS,
    RECOMMENDED_ACTION_BONUS,
    THEME_COLORS,
    VOLUNTEER_TEMPLATE_ACTIONS,
)
from services import (
    add_plaza_post,
    analyze_happiness_compass,
    build_history_dataframe,
    calculate_community_thermometer,
    calculate_social_value_impact,
    calculate_spc_summary,
    clear_logs,
    evaluate_positive_badges,
    evaluate_proactive_agent_nudge,
    export_logs_to_csv,
    generate_deep_coaching_report,
    generate_partner_chat_reply,
    generate_sample_logs,
    generate_warm_feedback,
    get_field_special_action,
    get_recommended_actions,
    load_logs,
    load_plaza_state,
    react_to_plaza_post,
    save_daily_log,
    simulate_finance_and_spc_fusion,
    simulate_future_warmth,
)


def apply_light_glass_theme() -> None:
    """밝은 파스텔 그라데이션과 글래스모피즘 카드, 3탭 내비게이션, 고가독성 스타일을 적용합니다."""
    c = THEME_COLORS
    st.markdown(
        f"""
        <style>
        /* 전체 배경: 크림 화이트 ~ 연한 피치/민트 파스텔 그라데이션 */
        .stApp {{
            background: {c["bg_gradient"]};
            background-attachment: fixed;
            color: {c["text_body"]};
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.75rem;
            padding-bottom: 2.5rem;
        }}

        /* 사이드바: 반투명 유리 패널 */
        [data-testid="stSidebar"] {{
            background: {c["sidebar_bg"]};
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-right: 1px solid {c["glass_border"]};
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: transparent;
        }}

        /* 상단 3개 탭 바: 글래스모피즘 필 스타일 */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {c["glass_border"]};
            border-radius: 18px;
            padding: 0.35rem 0.45rem;
            gap: 0.4rem;
            box-shadow: 0 6px 20px rgba(30, 41, 59, 0.06);
            margin-bottom: 1.2rem;
        }}

        [data-testid="stTabs"] [data-baseweb="tab"] {{
            border-radius: 13px !important;
            padding: 0.58rem 1.05rem !important;
            font-weight: 700 !important;
            color: {c["text_body"]} !important;
            background: transparent !important;
        }}

        [data-testid="stTabs"] [data-baseweb="tab"] p {{
            color: {c["text_body"]} !important;
            font-weight: 700 !important;
            font-size: 0.96rem !important;
        }}

        [data-testid="stTabs"] [aria-selected="true"] {{
            background: rgba(255, 244, 236, 0.96) !important;
            border: 1px solid rgba(255, 122, 89, 0.38) !important;
            box-shadow: 0 4px 12px rgba(255, 122, 89, 0.14) !important;
        }}

        [data-testid="stTabs"] [aria-selected="true"] p {{
            color: #C2410C !important;
        }}

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
            background-color: {c["accent_coral"]} !important;
            height: 3px !important;
            border-radius: 999px !important;
        }}

        /* 글래스모피즘 카드 컨테이너 */
        [class*="st-key-glass_card_"] {{
            background: {c["glass_bg"]};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid {c["glass_border"]};
            border-radius: 20px;
            box-shadow: {c["glass_shadow"]};
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.15rem;
        }}

        [class*="st-key-glass_card_"] > [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
        }}

        /* 최우선 텍스트 가독성: 제목·본문·라벨·슬라이더·체크박스 진한 차콜/네이비 고정 */
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4 {{
            color: {c["text_heading"]} !important;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .stApp p,
        .stApp li,
        .stApp label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCheckbox"] label,
        [data-testid="stCheckbox"] span,
        [data-testid="stSlider"] label,
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"] {{
            color: {c["text_body"]} !important;
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: {c["text_muted"]} !important;
            font-weight: 500;
        }}

        /* 입력창 및 셀렉트박스 가독성 강화 */
        .stTextInput input,
        .stNumberInput input,
        [data-baseweb="select"] > div {{
            background-color: {c["input_bg"]} !important;
            color: {c["text_body"]} !important;
            border: 1px solid {c["input_border"]} !important;
            border-radius: 12px !important;
        }}

        .stTextInput input::placeholder {{
            color: #64748B !important;
            opacity: 1 !important;
        }}

        [data-baseweb="select"] span,
        [data-baseweb="select"] svg {{
            color: {c["text_body"]} !important;
            fill: {c["text_body"]} !important;
        }}

        /* 사이드바 메트릭 미니 글래스 카드 */
        [data-testid="stMetric"] {{
            background: {c["glass_bg"]};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {c["glass_border"]};
            box-shadow: 0 6px 18px rgba(30, 41, 59, 0.06);
            padding: 14px 16px;
            border-radius: 16px;
        }}

        [data-testid="stMetricLabel"] p {{
            color: {c["text_muted"]} !important;
            font-weight: 600;
        }}

        [data-testid="stMetricValue"] {{
            color: {c["text_heading"]} !important;
            font-weight: 800;
        }}

        /* 포인트 컬러 버튼: 산뜻한 코랄 오렌지 ~ 앰버 골드 그라데이션 */
        .stButton > button {{
            background: {c["accent_gradient"]} !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.65rem 1.2rem !important;
            font-weight: 700 !important;
            box-shadow: 0 8px 20px rgba(255, 122, 89, 0.28) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
        }}

        .stButton > button p,
        .stButton > button span {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}

        .stButton > button:hover {{
            background: {c["accent_gradient_hover"]} !important;
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(240, 100, 68, 0.34) !important;
        }}

        .stButton > button:active {{
            transform: translateY(0);
        }}

        /* 보조 버튼 (초기화 등): 깔끔한 반투명 화이트 아웃라인 */
        .st-key-btn_reset_logs button {{
            background: rgba(255, 255, 255, 0.85) !important;
            color: {c["text_body"]} !important;
            border: 1px solid rgba(148, 163, 184, 0.55) !important;
            box-shadow: 0 4px 12px rgba(30, 41, 59, 0.06) !important;
        }}

        .st-key-btn_reset_logs button p,
        .st-key-btn_reset_logs button span {{
            color: {c["text_body"]} !important;
        }}

        .st-key-btn_reset_logs button:hover {{
            background: rgba(254, 242, 242, 0.95) !important;
            border-color: rgba(239, 68, 68, 0.45) !important;
        }}

        /* CSV 다운로드 버튼 */
        .stDownloadButton > button {{
            background: rgba(255, 255, 255, 0.88) !important;
            color: {c["text_heading"]} !important;
            border: 1px solid rgba(255, 122, 89, 0.42) !important;
            border-radius: 14px !important;
            padding: 0.62rem 1.1rem !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(30, 41, 59, 0.06) !important;
            transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
        }}

        .stDownloadButton > button p,
        .stDownloadButton > button span {{
            color: {c["text_heading"]} !important;
            font-weight: 700 !important;
        }}

        .stDownloadButton > button:hover {{
            background: rgba(255, 247, 237, 0.98) !important;
            border-color: {c["accent_coral"]} !important;
            transform: translateY(-1px);
        }}

        /* SPC 게이지 바: 선명한 코랄 오렌지 ~ 앰버 골드 */
        [data-testid="stProgressBar"] > div {{
            background-color: {c["progress_track"]} !important;
            border-radius: 999px !important;
            height: 11px !important;
            overflow: hidden;
        }}

        [data-testid="stProgressBar"] > div > div {{
            background: {c["accent_gradient"]} !important;
            border-radius: 999px !important;
        }}

        /* 피드백·배너·리포트·시뮬레이터 카드 */
        .ongi-feedback-box {{
            background: {c["feedback_tint"]};
            border-left: 4px solid {c["accent_coral"]};
            border-radius: 14px;
            padding: 1rem 1.15rem;
            color: {c["text_body"]};
            line-height: 1.65;
            font-size: 0.96rem;
        }}

        .ongi-badge {{
            display: inline-block;
            background: rgba(255, 122, 89, 0.14);
            color: #C2410C;
            font-weight: 700;
            font-size: 0.82rem;
            padding: 0.22rem 0.65rem;
            border-radius: 999px;
            margin-bottom: 0.55rem;
            margin-right: 0.35rem;
        }}

        .ongi-rec-banner {{
            background: rgba(255, 247, 237, 0.88);
            border: 1px solid rgba(255, 122, 89, 0.28);
            border-radius: 12px;
            padding: 0.68rem 0.95rem;
            color: {c["text_body"]};
            font-size: 0.88rem;
            line-height: 1.5;
            margin-bottom: 0.75rem;
        }}

        .ongi-field-special-box {{
            background: linear-gradient(135deg, rgba(255, 247, 237, 0.95), rgba(236, 253, 245, 0.9));
            border: 1px solid rgba(245, 158, 11, 0.42);
            border-radius: 14px;
            padding: 0.75rem 0.95rem;
            margin-bottom: 0.8rem;
            color: {c["text_body"]};
            font-size: 0.86rem;
            line-height: 1.5;
        }}

        .ongi-compass-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.85rem;
            margin-bottom: 0.85rem;
        }}

        .ongi-compass-stat {{
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(255, 122, 89, 0.22);
            border-radius: 14px;
            padding: 0.7rem 0.85rem;
            text-align: center;
        }}

        .ongi-compass-stat-label {{
            font-size: 0.78rem;
            color: {c["text_muted"]};
            font-weight: 600;
            margin-bottom: 0.2rem;
        }}

        .ongi-compass-stat-value {{
            font-size: 1.18rem;
            color: {c["text_heading"]};
            font-weight: 800;
        }}

        .ongi-compass-rank-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.35rem;
        }}

        .ongi-compass-pill {{
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.32);
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 0.82rem;
            color: {c["text_body"]};
            font-weight: 600;
        }}

        .ongi-report-letter {{
            background: rgba(255, 252, 246, 0.94);
            border: 1px solid rgba(255, 122, 89, 0.28);
            border-left: 5px solid {c["accent_coral"]};
            border-radius: 16px;
            padding: 1.2rem 1.35rem;
            color: {c["text_body"]};
            line-height: 1.78;
            font-size: 0.95rem;
            margin-top: 0.75rem;
        }}

        /* 1개월~10년 미래 시뮬레이터 마일스톤 카드 */
        .ongi-future-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.9rem;
            margin-bottom: 1.1rem;
        }}

        .ongi-future-card {{
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(255, 122, 89, 0.26);
            border-radius: 18px;
            padding: 1rem 0.9rem;
            text-align: center;
            box-shadow: 0 6px 18px rgba(30, 41, 59, 0.06);
        }}

        .ongi-future-card.highlight {{
            background: linear-gradient(155deg, rgba(255, 248, 240, 0.98), rgba(255, 236, 224, 0.92));
            border: 1px solid rgba(255, 122, 89, 0.55);
            box-shadow: 0 8px 22px rgba(255, 122, 89, 0.16);
        }}

        .ongi-future-horizon {{
            font-size: 0.82rem;
            font-weight: 700;
            color: #C2410C;
            margin-bottom: 0.28rem;
        }}

        .ongi-future-spc {{
            font-size: 1.32rem;
            font-weight: 800;
            color: {c["text_heading"]};
            margin-bottom: 0.25rem;
        }}

        .ongi-future-title {{
            font-size: 0.86rem;
            font-weight: 700;
            color: {c["text_body"]};
            margin-bottom: 0.45rem;
        }}

        .ongi-future-meta {{
            font-size: 0.78rem;
            color: {c["text_muted"]};
            line-height: 1.45;
        }}

        /* SPC 사회적 가치 환산소 그리드 */
        .ongi-social-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.75rem;
            margin-bottom: 0.85rem;
        }}

        .ongi-social-card {{
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(255, 122, 89, 0.22);
            border-radius: 16px;
            padding: 1rem 0.9rem;
            text-align: center;
            box-shadow: 0 4px 14px rgba(30, 41, 59, 0.05);
        }}

        .ongi-social-icon {{
            font-size: 1.55rem;
            margin-bottom: 0.25rem;
        }}

        .ongi-social-value {{
            font-size: 1.28rem;
            font-weight: 800;
            color: {c["text_heading"]};
            margin-bottom: 0.2rem;
        }}

        .ongi-social-label {{
            font-size: 0.82rem;
            font-weight: 600;
            color: {c["text_muted"]};
        }}

        /* 비경쟁 포지티브 명예 배지 컬렉션 */
        .ongi-badge-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.75rem;
        }}

        .ongi-badge-card {{
            border-radius: 16px;
            padding: 0.85rem 0.75rem;
            text-align: center;
            border: 1px solid rgba(148, 163, 184, 0.28);
            background: rgba(255, 255, 255, 0.65);
        }}

        .ongi-badge-card.unlocked {{
            background: linear-gradient(145deg, rgba(255, 251, 245, 0.96), rgba(255, 239, 229, 0.88));
            border: 1px solid rgba(255, 122, 89, 0.42);
            box-shadow: 0 6px 16px rgba(255, 122, 89, 0.12);
        }}

        .ongi-badge-card.locked {{
            opacity: 0.78;
        }}

        .ongi-badge-icon {{
            font-size: 1.5rem;
            margin-bottom: 0.2rem;
        }}

        .ongi-badge-title {{
            font-size: 0.88rem;
            font-weight: 700;
            color: {c["text_heading"]};
            margin-bottom: 0.18rem;
        }}

        .ongi-badge-desc {{
            font-size: 0.75rem;
            color: {c["text_muted"]};
            line-height: 1.35;
            margin-bottom: 0.4rem;
        }}

        .ongi-badge-status {{
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.18);
            color: {c["text_body"]};
        }}

        .ongi-badge-card.unlocked .ongi-badge-status {{
            background: rgba(255, 122, 89, 0.18);
            color: #C2410C;
        }}

        [data-testid="stAlert"] {{
            border-radius: 14px;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }}

        /* AI 온기 대화방 채팅 버블 & 입력창 */
        [data-testid="stChatMessage"] {{
            background: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid {c["glass_border"]};
            border-radius: 18px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 4px 14px rgba(30, 41, 59, 0.05);
        }}

        [data-testid="stChatInput"] textarea {{
            background-color: {c["input_bg"]} !important;
            color: {c["text_body"]} !important;
        }}

        [data-testid="stChatInput"] textarea::placeholder {{
            color: #64748B !important;
        }}

        /* 온기 광장 온도계 & 소셜 피드 카드 */
        .ongi-thermo-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 0.65rem;
        }}

        .ongi-thermo-temp {{
            font-size: 2rem;
            font-weight: 800;
            color: #EA580C;
            line-height: 1.1;
        }}

        .ongi-thermo-sub {{
            font-size: 0.88rem;
            color: {c["text_muted"]};
            font-weight: 600;
        }}

        .ongi-plaza-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.5rem;
        }}

        .ongi-plaza-author {{
            font-size: 0.88rem;
            font-weight: 700;
            color: {c["text_heading"]};
        }}

        .ongi-plaza-time {{
            font-size: 0.8rem;
            color: {c["text_muted"]};
            font-weight: 600;
        }}

        .ongi-plaza-body {{
            background: rgba(255, 252, 246, 0.9);
            border: 1px solid rgba(255, 122, 89, 0.18);
            border-radius: 14px;
            padding: 0.9rem 1.05rem;
            color: {c["text_body"]};
            line-height: 1.65;
            font-size: 0.96rem;
            margin-bottom: 0.75rem;
        }}

        /* 광장 리액션 버튼: 부드러운 글래스 필 스타일 */
        [class*="st-key-btn_react_"] button {{
            background: rgba(255, 255, 255, 0.88) !important;
            color: {c["text_body"]} !important;
            border: 1px solid rgba(255, 122, 89, 0.34) !important;
            border-radius: 999px !important;
            padding: 0.45rem 0.85rem !important;
            box-shadow: 0 3px 10px rgba(30, 41, 59, 0.05) !important;
        }}

        [class*="st-key-btn_react_"] button p,
        [class*="st-key-btn_react_"] button span {{
            color: {c["text_body"]} !important;
            font-weight: 700 !important;
            font-size: 0.86rem !important;
        }}

        [class*="st-key-btn_react_"] button:hover {{
            background: rgba(255, 244, 236, 0.98) !important;
            border-color: {c["accent_coral"]} !important;
        }}

        /* 사이드바 컴팩트 티어 + 일일 레벨 + 연속 기록 글래스 카드 */
        .ongi-tier-card {{
            background: rgba(255, 255, 255, 0.84);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 122, 89, 0.34);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 6px 18px rgba(30, 41, 59, 0.06);
            margin-bottom: 0.6rem;
        }}

        .ongi-tier-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.4rem;
        }}

        .ongi-tier-title {{
            font-size: 0.92rem;
            font-weight: 800;
            color: {c["text_heading"]};
            line-height: 1.3;
        }}

        .ongi-level-pill {{
            display: inline-block;
            background: {c["accent_gradient"]};
            color: #FFFFFF;
            font-size: 0.76rem;
            font-weight: 800;
            padding: 0.16rem 0.55rem;
            border-radius: 999px;
            white-space: nowrap;
        }}

        .ongi-streak-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.55rem;
            gap: 0.35rem;
        }}

        .ongi-streak-tag {{
            display: inline-block;
            background: rgba(255, 122, 89, 0.13);
            color: #C2410C;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.14rem 0.52rem;
            border-radius: 999px;
        }}

        .ongi-spc-total {{
            font-size: 0.85rem;
            font-weight: 800;
            color: {c["text_heading"]};
        }}

        .ongi-mini-bar-wrap {{
            margin-top: 0.42rem;
        }}

        .ongi-mini-bar-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.73rem;
            font-weight: 600;
            color: {c["text_muted"]};
            margin-bottom: 0.2rem;
        }}

        .ongi-mini-bar-track {{
            width: 100%;
            height: 7px;
            background: rgba(255, 122, 89, 0.16);
            border-radius: 999px;
            overflow: hidden;
        }}

        .ongi-mini-bar-fill {{
            height: 100%;
            background: {c["accent_gradient"]};
            border-radius: 999px;
        }}

        .ongi-mini-bar-fill.exp {{
            background: linear-gradient(90deg, #F59E0B 0%, #10B981 100%);
        }}

        /* 온기 광장 이웃 프로필 옆 미니 티어 배지 */
        .ongi-tier-mini-tag {{
            display: inline-block;
            background: rgba(255, 244, 236, 0.96);
            border: 1px solid rgba(255, 122, 89, 0.36);
            color: #C2410C;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.12rem 0.52rem;
            border-radius: 999px;
            margin-left: 0.4rem;
            vertical-align: middle;
        }}

        /* 현실 자산 & SPC 융합 6개 시점 카드 */
        .ongi-finance-grid {{
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.6rem;
            margin-top: 0.8rem;
            margin-bottom: 1rem;
        }}

        .ongi-finance-card {{
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.3);
            border-radius: 14px;
            padding: 0.72rem 0.55rem;
            text-align: center;
        }}

        .ongi-finance-card.highlight {{
            background: linear-gradient(155deg, rgba(255, 248, 240, 0.98), rgba(236, 253, 245, 0.92));
            border: 1px solid rgba(255, 122, 89, 0.52);
            box-shadow: 0 6px 16px rgba(255, 122, 89, 0.14);
        }}

        .ongi-finance-period {{
            font-size: 0.76rem;
            font-weight: 700;
            color: #C2410C;
            margin-bottom: 0.2rem;
        }}

        .ongi-finance-total {{
            font-size: 0.98rem;
            font-weight: 800;
            color: {c["text_heading"]};
            margin-bottom: 0.16rem;
        }}

        .ongi-finance-sub {{
            font-size: 0.71rem;
            color: {c["text_muted"]};
            line-height: 1.35;
        }}

        hr {{
            border-color: rgba(148, 163, 184, 0.3) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(
    logs: list[dict],
    summary: dict,
    life_cycle: str,
    current_status: str,
    field: str,
) -> tuple[str, str, str]:
    """생애 주기·상태·소속 분야 프로필, SPC 레벨, 시뮬레이션 및 CSV 백업을 사이드바에 표시합니다."""
    with st.sidebar:
        st.markdown("## 나의 프로필")
        life_cycle_index = (
            LIFE_CYCLE_OPTIONS.index(life_cycle)
            if life_cycle in LIFE_CYCLE_OPTIONS
            else 2
        )
        status_index = (
            CURRENT_STATUS_OPTIONS.index(current_status)
            if current_status in CURRENT_STATUS_OPTIONS
            else 0
        )
        field_index = FIELD_OPTIONS.index(field) if field in FIELD_OPTIONS else 0

        selected_life_cycle = st.selectbox(
            "생애 주기",
            LIFE_CYCLE_OPTIONS,
            index=life_cycle_index,
            key="life_cycle",
        )
        selected_status = st.selectbox(
            "현재 상태",
            CURRENT_STATUS_OPTIONS,
            index=status_index,
            key="current_status",
        )
        selected_field = st.selectbox(
            "소속 분야 / 직종",
            FIELD_OPTIONS,
            index=field_index,
            key="field",
        )

        st.markdown("---")
        st.markdown("## 나의 SPC")
        streak_text = (
            f"🔥 {summary['current_streak']}일 연속 온기 중"
            if summary["current_streak"] > 0
            else "🌱 오늘 첫 온기 시작"
        )
        lp_pct = round(summary["progress"] * 100)
        exp_pct = round(summary["level_progress"] * 100)
        if summary["next_level"]:
            lp_right = f"승급까지 {summary['points_to_next']:,} SPC"
            lp_left = f"현재 단계 {summary['lp']} / 100 LP"
            next_caption = f"다음 승급: {summary['next_level']}"
        else:
            lp_right = "최고 티어 달성"
            lp_left = f"챌린저 {summary['lp']:,} LP"
            next_caption = "그랜드 온기 거장"

        st.markdown(
            f"""
            <div class="ongi-tier-card">
                <div class="ongi-tier-top">
                    <span class="ongi-tier-title">{html.escape(summary["tier_full"])}</span>
                    <span class="ongi-level-pill">Lv. {summary["daily_level"]}</span>
                </div>
                <div class="ongi-streak-row">
                    <span class="ongi-streak-tag">{html.escape(streak_text)}</span>
                    <span class="ongi-spc-total">{summary["total_points"]:,} SPC</span>
                </div>
                <div class="ongi-mini-bar-wrap">
                    <div class="ongi-mini-bar-label">
                        <span>{html.escape(lp_left)}</span>
                        <span>{html.escape(lp_right)}</span>
                    </div>
                    <div class="ongi-mini-bar-track">
                        <div class="ongi-mini-bar-fill" style="width: {lp_pct}%;"></div>
                    </div>
                </div>
                <div class="ongi-mini-bar-wrap">
                    <div class="ongi-mini-bar-label">
                        <span>일일 EXP {summary["level_exp_current"]} / {summary["level_exp_step"]}</span>
                        <span>Lv.{summary["daily_level"] + 1}까지 {summary["level_exp_to_next"]} SPC</span>
                    </div>
                    <div class="ongi-mini-bar-track">
                        <div class="ongi-mini-bar-fill exp" style="width: {exp_pct}%;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(next_caption)

        st.markdown("---")
        st.markdown("### 시뮬레이션 도구")
        st.caption("30일 흐름과 AI 행복 나침반, 10년 예측을 바로 체험해 보세요.")
        if st.button(
            "🧪 최근 30일 샘플 데이터 채우기",
            key="btn_fill_sample_logs",
            use_container_width=True,
        ):
            generated_logs = generate_sample_logs(
                days=30,
                life_cycle=selected_life_cycle,
                current_status=selected_status,
                field=selected_field,
            )
            st.session_state["ongi_logs"] = generated_logs
            st.session_state.pop("ongi_feedback", None)
            st.session_state.pop("ongi_saved_date", None)
            st.session_state.pop("ongi_deep_report", None)
            st.session_state.pop("ongi_deep_report_source", None)
            st.session_state["ongi_notice"] = (
                f"최근 30일 샘플 기록을 채웠어요 "
                f"({selected_life_cycle} · {selected_status} · {selected_field} 기준)."
            )
            st.rerun()

        if st.button(
            "🗑️ 기록 초기화",
            key="btn_reset_logs",
            use_container_width=True,
        ):
            st.session_state["ongi_logs"] = clear_logs()
            st.session_state["ongi_plaza"] = load_plaza_state()
            st.session_state.pop("ongi_feedback", None)
            st.session_state.pop("ongi_saved_date", None)
            st.session_state.pop("ongi_deep_report", None)
            st.session_state.pop("ongi_deep_report_source", None)
            st.session_state["ongi_notice"] = "모든 개인 기록을 깨끗하게 초기화했어요."
            st.rerun()

        st.markdown("---")
        st.markdown("### 백업 및 내보내기")
        csv_bytes = export_logs_to_csv(logs)
        st.download_button(
            "📥 내 기록 CSV 다운로드",
            data=csv_bytes,
            file_name=f"ongi_logs_{date.today().isoformat()}.csv",
            mime="text/csv",
            key="btn_download_csv",
            use_container_width=True,
            disabled=not logs,
        )
        if not logs:
            st.caption("기록이 1건 이상 쌓이면 CSV로 내려받을 수 있어요.")

        return selected_life_cycle, selected_status, selected_field


def render_daily_record_tab(
    life_cycle: str, current_status: str, field: str
) -> None:
    """탭 1: 오늘의 마음 슬라이더, 분야·생애 주기 맞춤 포지티브 행동, ONGI의 한마디를 표시합니다."""
    recommended_actions = get_recommended_actions(life_cycle, current_status, field)
    recommended_set = set(recommended_actions)
    field_special = get_field_special_action(field)

    left_col, right_col = st.columns([1, 1.15], gap="large")

    with left_col:
        # 1. 행복 점수 입력 글래스 카드
        with st.container(key="glass_card_mood"):
            st.subheader("오늘의 마음")
            st.caption(
                f"{date.today().strftime('%Y년 %m월 %d일')} · "
                f"{life_cycle} · {current_status} · {field}"
            )
            happiness = st.slider("오늘의 행복", min_value=1, max_value=10, value=6)
            energy = st.slider("오늘의 에너지", min_value=1, max_value=10, value=6)
            memo = st.text_input(
                "마음을 움직인 순간을 한 줄로 남겨보세요",
                placeholder="예: 보이지 않는 곳에서 묵묵히 할 일을 마친 스스로를 다독였어요.",
                max_chars=200,
            )

        # 2. ONGI의 한마디 (AI 피드백) 글래스 카드
        with st.container(key="glass_card_feedback"):
            st.subheader("ONGI의 한마디")
            if st.session_state.get("ongi_saved_date") == date.today().isoformat():
                feedback = st.session_state.get("ongi_feedback")
                if feedback:
                    st.markdown(
                        '<span class="ongi-badge">오늘 기록 저장 완료</span>',
                        unsafe_allow_html=True,
                    )
                    safe_feedback = html.escape(feedback).replace("\n", "<br>")
                    st.markdown(
                        f'<div class="ongi-feedback-box">{safe_feedback}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="ongi-feedback-box">'
                    "오늘의 마음과 포지티브 행동을 저장하면, "
                    "ONGI가 따뜻한 응원 메시지를 전해드려요."
                    "</div>",
                    unsafe_allow_html=True,
                )

    with right_col:
        # 3. 3가지 조화로운 카테고리(일상 온기 · 세부 봉사 템플릿 · 성장/직종 공헌) 글래스 카드
        with st.container(key="glass_card_actions"):
            st.subheader("오늘의 포지티브 행동")

            base_recommended = [
                a
                for a in recommended_actions
                if not field_special or a != field_special["action"]
            ]
            if base_recommended:
                st.markdown(
                    f'<div class="ongi-rec-banner">'
                    f"<strong>★ {html.escape(life_cycle)} · {html.escape(current_status)} 맞춤 추천:</strong> "
                    f"{html.escape(', '.join(base_recommended))} 선택 시 "
                    f"<strong>+{RECOMMENDED_ACTION_BONUS} SPC 보너스</strong>가 더해져요."
                    f"</div>",
                    unsafe_allow_html=True,
                )

            selected_actions: list[str] = []
            preview_action_spc = 0

            cat_micro, cat_volunteer, cat_growth = st.tabs(
                [
                    "☀️ 일상의 사소한 온기",
                    "🤝 세부 봉사 템플릿",
                    "📚 성장 & 직종 공헌",
                ]
            )

            with cat_micro:
                st.caption("매일 가볍게 실천할 수 있는 사소한 친절과 배려를 체크해 보세요.")
                for action, base_weight in MICRO_KINDNESS_ACTIONS.items():
                    is_rec = action in recommended_set
                    bonus = RECOMMENDED_ACTION_BONUS if is_rec else 0
                    label = (
                        f"★ {action} (+{base_weight} + {bonus} SPC)"
                        if is_rec
                        else f"{action} (+{base_weight} SPC)"
                    )
                    if st.checkbox(label, key=f"action_{action}"):
                        selected_actions.append(action)
                        preview_action_spc += base_weight + bonus

            with cat_volunteer:
                st.caption("연탄 나눔, 유기견 돌봄, 무료급식 등 구체적인 봉사 활동을 기록해 보세요.")
                for action, base_weight in VOLUNTEER_TEMPLATE_ACTIONS.items():
                    is_rec = action in recommended_set
                    bonus = RECOMMENDED_ACTION_BONUS if is_rec else 0
                    label = (
                        f"★ {action} (+{base_weight} + {bonus} SPC)"
                        if is_rec
                        else f"{action} (+{base_weight} SPC)"
                    )
                    if st.checkbox(label, key=f"action_{action}"):
                        selected_actions.append(action)
                        preview_action_spc += base_weight + bonus

            with cat_growth:
                if field_special:
                    st.markdown(
                        f'<div class="ongi-field-special-box">'
                        f'<strong>🏅 [{html.escape(field)}] 특별 맞춤 행동</strong><br>'
                        f'{html.escape(field_special["note"])}'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    special_name = field_special["action"]
                    special_label = (
                        f"★ [{field} 특화] {special_name} "
                        f"(+{field_special['weight']} + {field_special['bonus']} SPC)"
                    )
                    if st.checkbox(special_label, key=f"action_special_{field}"):
                        selected_actions.append(special_name)
                        preview_action_spc += (
                            int(field_special["weight"]) + int(field_special["bonus"])
                        )

                for action, base_weight in GROWTH_ACTIONS.items():
                    is_rec = action in recommended_set
                    bonus = RECOMMENDED_ACTION_BONUS if is_rec else 0
                    label = (
                        f"★ {action} (+{base_weight} + {bonus} SPC)"
                        if is_rec
                        else f"{action} (+{base_weight} SPC)"
                    )
                    if st.checkbox(label, key=f"action_{action}"):
                        selected_actions.append(action)
                        preview_action_spc += base_weight + bonus

            st.markdown(
                f'<div style="margin-top: 0.6rem; margin-bottom: 0.45rem;">'
                f'<span class="ongi-badge">선택한 행동 {len(selected_actions)}개 · '
                f"예상 행동 보너스 +{preview_action_spc:,} SPC</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if st.button("오늘 기록 저장하기", key="btn_save_daily", use_container_width=True):
                record = {
                    "date": date.today().isoformat(),
                    "life_cycle": life_cycle,
                    "current_status": current_status,
                    "field": field,
                    "happiness": happiness,
                    "energy": energy,
                    "memo": memo.strip(),
                    "positive_actions": selected_actions,
                }
                logs = save_daily_log(record)
                st.session_state["ongi_feedback"] = generate_warm_feedback(record)
                st.session_state["ongi_saved_date"] = record["date"]
                st.session_state["ongi_logs"] = logs
                st.rerun()


def render_happiness_compass(
    logs: list[dict], life_cycle: str, current_status: str, field: str
) -> None:
    """누적 데이터 기반 행복 상승 확률과 오늘의 추천 행동을 글래스 카드로 보여줍니다."""
    with st.container(key="glass_card_compass"):
        st.subheader("🧭 AI 행복 나침반")
        compass = analyze_happiness_compass(
            logs,
            life_cycle=life_cycle,
            current_status=current_status,
            field=field,
        )
        if not compass["has_enough_data"]:
            st.markdown(
                '<div class="ongi-feedback-box">'
                f"현재 <strong>{compass['total_days']}일</strong>의 기록이 모여 있어요. "
                "3일 이상 기록이 쌓이거나 사이드바의 <strong>🧪 최근 30일 샘플 데이터 채우기</strong>를 누르면, "
                "나의 행복도를 가장 크게 끌어올리는 포지티브 행동을 확률로 분석해 드려요."
                "</div>",
                unsafe_allow_html=True,
            )
            return

        best_action = html.escape(compass["best_action"])
        lift = compass["happiness_lift_pct"]
        if lift > 0:
            headline = (
                f"최근 <strong>{compass['total_days']}일</strong> 기록을 분석한 결과, "
                f"<strong>[{best_action}]</strong>을(를) 실천한 날 행복도가 평균 "
                f"<strong>{lift:.1f}%</strong> 높았어요! 오늘 가장 추천하는 포지티브 스텝입니다."
            )
            lift_display = f"+{lift:.1f}%"
        else:
            headline = (
                f"최근 <strong>{compass['total_days']}일</strong> 기록을 분석한 결과, "
                f"<strong>[{best_action}]</strong>을(를) 실천한 날 평균 행복도 "
                f"<strong>{compass['avg_happiness']:.1f}점</strong>으로 가장 안정적인 온기를 유지했어요! "
                "오늘 가장 추천하는 포지티브 스텝입니다."
            )
            lift_display = f"{lift:+.1f}%"

        st.markdown(
            f'<span class="ongi-badge">★ 오늘의 1순위 스텝 · {best_action}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="ongi-feedback-box">{headline}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="ongi-compass-grid">
                <div class="ongi-compass-stat">
                    <div class="ongi-compass-stat-label">행복도 상승률</div>
                    <div class="ongi-compass-stat-value">{lift_display}</div>
                </div>
                <div class="ongi-compass-stat">
                    <div class="ongi-compass-stat-label">고행복 달성 확률</div>
                    <div class="ongi-compass-stat-value">{compass["high_happiness_prob"]}%</div>
                </div>
                <div class="ongi-compass-stat">
                    <div class="ongi-compass-stat-label">기대 온기 지수</div>
                    <div class="ongi-compass-stat-value">{compass["expected_index"]:.1f}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pills_html = "".join(
            f'<span class="ongi-compass-pill">'
            f'{"★ " if item["is_recommended"] else ""}'
            f'{html.escape(item["action"])} · 기대지수 {item["expected_index"]:.1f} '
            f'({item["high_happiness_prob"]}%)</span>'
            for item in compass["top_actions"]
        )
        st.markdown(
            f'<div class="ongi-compass-rank-list">{pills_html}</div>',
            unsafe_allow_html=True,
        )


def render_history(logs: list[dict]) -> None:
    """날짜별 행복·에너지와 누적 SPC 추이를 글래스 카드 안의 차트로 보여줍니다."""
    with st.container(key="glass_card_charts"):
        st.subheader("나의 온기 흐름")
        history = build_history_dataframe(logs)
        if history.empty:
            st.caption("첫 기록을 남기면 날짜별 변화가 이곳에 쌓여요.")
            return

        st.caption(
            "행복과 에너지는 1~10점, SPC는 행동과 마음 점수를 합산한 누적 값입니다."
        )
        st.line_chart(
            history[["행복", "에너지"]],
            height=240,
            color=[THEME_COLORS["accent_coral"], THEME_COLORS["accent_amber"]],
        )
        st.area_chart(
            history[["누적 SPC"]],
            height=190,
            color=[THEME_COLORS["accent_coral"]],
        )


def render_deep_coaching_report(
    logs: list[dict], life_cycle: str, current_status: str, field: str
) -> None:
    """누적 데이터 기반 AI 월간 온기 심층 코칭 편지를 글래스 카드로 제공합니다."""
    with st.container(key="glass_card_deep_report"):
        st.subheader("✨ AI 월간 온기 리포트")
        st.caption(
            "누적된 행복·에너지 추세, 행복 확률 1위 행동, SPC 레벨을 종합해 맞춤 코칭 편지를 써드려요."
        )

        if st.button(
            "✨ 나의 온기 심층 리포트 받아보기",
            key="btn_generate_deep_report",
            use_container_width=True,
        ):
            with st.spinner("누적 온기 데이터를 바탕으로 맞춤 코칭 편지를 작성하고 있어요..."):
                report_text, report_source = generate_deep_coaching_report(
                    logs,
                    life_cycle=life_cycle,
                    current_status=current_status,
                    field=field,
                )
            st.session_state["ongi_deep_report"] = report_text
            st.session_state["ongi_deep_report_source"] = report_source

        report_text = st.session_state.get("ongi_deep_report")
        report_source = st.session_state.get("ongi_deep_report_source")
        if report_text:
            if report_source:
                st.markdown(
                    f'<span class="ongi-badge">{html.escape(report_source)}</span>',
                    unsafe_allow_html=True,
                )
            safe_report = html.escape(report_text).replace("\n", "<br>")
            st.markdown(
                f'<div class="ongi-report-letter">{safe_report}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ongi-feedback-box">'
                "버튼을 누르면 최근 기록의 흐름과 가장 효과적이었던 포지티브 행동을 분석해 "
                "나만을 위한 다정한 코칭 편지를 전해드려요."
                "</div>",
                unsafe_allow_html=True,
            )


def render_positive_badges(logs: list[dict]) -> None:
    """비경쟁 포지티브 명예 배지 컬렉션을 글래스 카드로 표시합니다."""
    with st.container(key="glass_card_badges"):
        badges = evaluate_positive_badges(logs)
        unlocked_count = sum(1 for item in badges if item["unlocked"])
        st.subheader("🏅 포지티브 명예 배지")
        st.caption(
            f"타인과의 랭킹 없이 나의 꾸준함을 기념해요 · 획득 배지 {unlocked_count} / {len(badges)}"
        )

        badge_cards_html = []
        for item in badges:
            state_class = "unlocked" if item["unlocked"] else "locked"
            status_text = (
                "획득 완료"
                if item["unlocked"]
                else f'{item["current"]} / {item["target"]}{item["unit"]}'
            )
            badge_cards_html.append(
                f'<div class="ongi-badge-card {state_class}">'
                f'<div class="ongi-badge-icon">{item["icon"]}</div>'
                f'<div class="ongi-badge-title">{html.escape(item["name"])}</div>'
                f'<div class="ongi-badge-desc">{html.escape(item["description"])}</div>'
                f'<span class="ongi-badge-status">{html.escape(status_text)}</span>'
                f"</div>"
            )
        st.markdown(
            f'<div class="ongi-badge-grid">{"".join(badge_cards_html)}</div>',
            unsafe_allow_html=True,
        )


def render_compass_and_future_tab(
    logs: list[dict],
    life_cycle: str,
    current_status: str,
    field: str,
    plaza_bonus_spc: int = 0,
) -> None:
    """탭 2: 행복 나침반, 30일 온기 흐름, 1개월~10년 시뮬레이터, SPC 사회적 가치 환산소, 배지를 표시합니다."""
    # 상단 2열: AI 행복 나침반 + 최근 30일 온기 흐름 차트
    top_left, top_right = st.columns([1, 1.15], gap="large")
    with top_left:
        render_happiness_compass(logs, life_cycle, current_status, field)
    with top_right:
        render_history(logs)

    # 중단 전체: 1개월·1년·5년·10년 장기 미래 시뮬레이터 (시간순 Altair 차트)
    with st.container(key="glass_card_future_sim"):
        st.subheader("🔭 1개월 · 1년 · 5년 · 10년 장기 온기 시뮬레이터")
        base_sim = simulate_future_warmth(logs)
        pace_note = (
            f"최근 {len(logs)}일 평균 속도(하루 {base_sim['observed_daily_spc']} SPC) 기준"
            if base_sim["has_observed_pace"]
            else "기록 시작 전 기본 목표 속도(하루 25 SPC) 기준"
        )
        st.caption(
            f"{pace_note} · 매일의 작은 실천이 해마다 습관 복리(연 {base_sim['annual_compound_rate_pct']}%)로 쌓이는 궤적입니다."
        )

        target_daily_spc = st.slider(
            "하루 목표 온기 속도 조절해보기 (SPC / 일)",
            min_value=10,
            max_value=80,
            value=min(80, max(10, base_sim["observed_daily_spc"])),
            step=5,
            key="future_daily_spc_slider",
        )
        sim = simulate_future_warmth(logs, custom_daily_spc=target_daily_spc)

        st.markdown(
            f'<div class="ongi-feedback-box">{html.escape(sim["headline"])}</div>',
            unsafe_allow_html=True,
        )

        milestone_cards = []
        for idx, item in enumerate(sim["milestones"]):
            highlight_class = " highlight" if idx == 3 else ""
            milestone_cards.append(
                f'<div class="ongi-future-card{highlight_class}">'
                f'<div class="ongi-future-horizon">{html.escape(item["label"])}</div>'
                f'<div class="ongi-future-spc">{item["projected_spc"]:,} SPC</div>'
                f'<div class="ongi-future-title">{html.escape(item["title"])}</div>'
                f'<div class="ongi-future-meta">'
                f'긍정 에너지 {item["positive_hours"]:,.1f}시간<br>'
                f'연탄 환산 {item["briquettes"]:,.1f}장'
                f"</div>"
                f"</div>"
            )
        st.markdown(
            f'<div class="ongi-future-grid">{"".join(milestone_cards)}</div>',
            unsafe_allow_html=True,
        )

        # 가로축을 '1개월 -> 1년 -> 2년 -> ... -> 10년' 시간 순서대로 엄격히 고정합니다.
        x_order = sim["ordered_labels"]
        axis_style = alt.Axis(
            labelColor=THEME_COLORS["text_body"],
            titleColor=THEME_COLORS["text_body"],
            labelAngle=0,
            gridColor="rgba(148, 163, 184, 0.2)",
        )

        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            st.caption("📈 10년 누적 SPC 복리 성장 궤적")
            spc_chart = (
                alt.Chart(sim["trajectory_df"])
                .mark_area(
                    line={"color": THEME_COLORS["accent_coral"], "strokeWidth": 3},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="rgba(255, 122, 89, 0.08)", offset=0),
                            alt.GradientStop(color="rgba(255, 122, 89, 0.45)", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    point={"color": THEME_COLORS["accent_coral"], "filled": True, "size": 55},
                )
                .encode(
                    x=alt.X("시점:N", sort=x_order, title=None, axis=axis_style),
                    y=alt.Y("예측 누적 SPC:Q", title="예측 누적 SPC", axis=axis_style),
                    tooltip=[
                        alt.Tooltip("시점:N", title="시점"),
                        alt.Tooltip("예측 누적 SPC:Q", title="예측 누적 SPC", format=","),
                    ],
                )
                .properties(height=245)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(spc_chart, use_container_width=True)

        with chart_right:
            st.caption("⏳ 지역사회·나를 살리는 긍정 에너지 누적(시간)")
            hours_chart = (
                alt.Chart(sim["trajectory_df"])
                .mark_bar(
                    color=THEME_COLORS["accent_amber"],
                    cornerRadiusTopLeft=7,
                    cornerRadiusTopRight=7,
                )
                .encode(
                    x=alt.X("시점:N", sort=x_order, title=None, axis=axis_style),
                    y=alt.Y("긍정 에너지(시간):Q", title="긍정 에너지(시간)", axis=axis_style),
                    tooltip=[
                        alt.Tooltip("시점:N", title="시점"),
                        alt.Tooltip("긍정 에너지(시간):Q", title="긍정 에너지(시간)", format=",.1f"),
                    ],
                )
                .properties(height=245)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(hours_chart, use_container_width=True)

    # 하단 2열: SPC 사회적 가치 환산소 + 포지티브 명예 배지
    bottom_left, bottom_right = st.columns([1, 1.1], gap="large")
    with bottom_left:
        with st.container(key="glass_card_social_value"):
            st.subheader("🌍 SPC 사회적 가치 환산소")
            st.caption(
                "과시나 타인과의 비교 대신, 지금까지 내가 쌓은 긍정 에너지가 세상에 전하는 따뜻한 온기 가치입니다."
            )
            impact = calculate_social_value_impact(logs, plaza_bonus_spc=plaza_bonus_spc)
            st.markdown(
                f"""
                <div class="ongi-social-grid">
                    <div class="ongi-social-card">
                        <div class="ongi-social-icon">🔥</div>
                        <div class="ongi-social-value">{impact["briquettes"]:,.1f}장</div>
                        <div class="ongi-social-label">전달된 따뜻한 연탄</div>
                    </div>
                    <div class="ongi-social-card">
                        <div class="ongi-social-icon">🐶</div>
                        <div class="ongi-social-value">{impact["positive_hours"]:,.1f}시간</div>
                        <div class="ongi-social-label">유기동물·이웃 돌봄 온기</div>
                    </div>
                    <div class="ongi-social-card">
                        <div class="ongi-social-icon">👋</div>
                        <div class="ongi-social-value">{impact["micro_smiles"]:,}회</div>
                        <div class="ongi-social-label">세상을 밝힌 사소한 인사와 미소</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="ongi-feedback-box">{html.escape(impact["narrative"])}</div>',
                unsafe_allow_html=True,
            )
    with bottom_right:
        render_positive_badges(logs)

    # 최하단: 💰 현실 자산 & SPC 융합 시뮬레이터 (주거비·소비 패턴 + 사회적 신뢰 자본)
    with st.container(key="glass_card_finance_fusion"):
        st.subheader("💰 현실 자산 & SPC 융합 시뮬레이터")
        st.caption(
            "월 수입과 주거비·생활비·변수 비용을 바탕으로 1개월~10년 자산 흐름과 "
            "나의 SPC 사회적 신뢰 자본(우대 금리 + 사회성과 인센티브 환산)을 함께 예측해 보세요."
        )

        f_col1, f_col2, f_col3, f_col4 = st.columns(4, gap="medium")
        with f_col1:
            monthly_income = st.number_input(
                "월 평균 수입 (만원)",
                min_value=0,
                max_value=5000,
                value=int(
                    st.session_state.get(
                        "fin_monthly_income", FINANCE_DEFAULTS["monthly_income"]
                    )
                ),
                step=10,
                key="fin_monthly_income",
            )
        with f_col2:
            housing_cost = st.number_input(
                "월 주거비용 (만원)",
                min_value=0,
                max_value=2000,
                value=int(
                    st.session_state.get(
                        "fin_housing_cost", FINANCE_DEFAULTS["housing_cost"]
                    )
                ),
                step=5,
                help="월세, 관리비, 주택 대출이자 포함",
                key="fin_housing_cost",
            )
        with f_col3:
            living_cost = st.number_input(
                "기본 생활비 (만원)",
                min_value=0,
                max_value=2000,
                value=int(
                    st.session_state.get(
                        "fin_living_cost", FINANCE_DEFAULTS["living_cost"]
                    )
                ),
                step=5,
                help="식비, 배달, 카페, 구독료, 교통비 포함",
                key="fin_living_cost",
            )
        with f_col4:
            variable_cost = st.number_input(
                "월평균 변수 비용 (만원)",
                min_value=0,
                max_value=1000,
                value=int(
                    st.session_state.get(
                        "fin_variable_cost", FINANCE_DEFAULTS["variable_cost"]
                    )
                ),
                step=5,
                help="경조사, 병원비, 비상금 적립",
                key="fin_variable_cost",
            )

        fin = simulate_finance_and_spc_fusion(
            logs=logs,
            monthly_income=monthly_income,
            housing_cost=housing_cost,
            living_cost=living_cost,
            variable_cost=variable_cost,
            plaza_bonus_spc=plaza_bonus_spc,
        )

        st.markdown(
            f'<div style="margin-top: 0.35rem; margin-bottom: 0.45rem;">'
            f'<span class="ongi-badge">융합 성장 레벨 · {html.escape(fin["fusion_level"])}</span>'
            f'<span class="ongi-badge">월 저축 여력 {fin["monthly_savings"]:+,}만원 ({fin["savings_ratio"]:.0f}%)</span>'
            f'<span class="ongi-badge">SPC 신뢰 우대 +{fin["spc_bonus_rate_pct"]:.2f}%p</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="ongi-feedback-box">💌 <strong>다정한 AI 소비 코칭:</strong> '
            f'{html.escape(fin["gentle_feedback"])}</div>',
            unsafe_allow_html=True,
        )

        fin_cards = []
        for idx, item in enumerate(fin["milestones"]):
            hl = " highlight" if idx == len(fin["milestones"]) - 1 else ""
            fin_cards.append(
                f'<div class="ongi-finance-card{hl}">'
                f'<div class="ongi-finance-period">{html.escape(item["label"])} 뒤</div>'
                f'<div class="ongi-finance-total">{item["total_fusion_value"]:,.0f}만원</div>'
                f'<div class="ongi-finance-sub">'
                f'현실 {item["real_assets"]:,.0f}만<br>'
                f'+SPC {item["spc_capital_value"]:,.0f}만'
                f"</div>"
                f"</div>"
            )
        st.markdown(
            f'<div class="ongi-finance-grid">{"".join(fin_cards)}</div>',
            unsafe_allow_html=True,
        )

        fin_chart = (
            alt.Chart(fin["trajectory_df"])
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X(
                    "시점:N",
                    sort=fin["ordered_labels"],
                    title=None,
                    axis=axis_style,
                ),
                xOffset="구분:N",
                y=alt.Y("금액(만원):Q", title="누적 가치 (만원)", axis=axis_style),
                color=alt.Color(
                    "구분:N",
                    scale=alt.Scale(
                        domain=["현실 누적 자산(만원)", "자본+SPC 융합 총가치(만원)"],
                        range=["#94A3B8", THEME_COLORS["accent_coral"]],
                    ),
                    legend=alt.Legend(
                        orient="top",
                        title=None,
                        labelColor=THEME_COLORS["text_body"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("시점:N", title="시점"),
                    alt.Tooltip("구분:N", title="구분"),
                    alt.Tooltip("금액(만원):Q", title="금액(만원)", format=",.1f"),
                ],
            )
            .properties(height=250)
            .configure_view(strokeWidth=0)
            .configure(background="transparent")
        )
        st.altair_chart(fin_chart, use_container_width=True)


def render_partner_chat_tab(
    logs: list[dict],
    summary: dict,
    life_cycle: str,
    current_status: str,
    field: str,
    finance_context: dict | None = None,
) -> None:
    """탭 3: 누적 데이터를 기억하는 AI 온기 파트너 채팅방과 원클릭 월간 심층 리포트를 표시합니다."""
    compass = analyze_happiness_compass(
        logs, life_cycle=life_cycle, current_status=current_status, field=field
    )
    nudge = evaluate_proactive_agent_nudge(
        logs, life_cycle=life_cycle, current_status=current_status, field=field
    )

    chat_col, report_col = st.columns([1.3, 1.0], gap="large")

    with chat_col:
        with st.container(key="glass_card_chat_header"):
            header_left, header_right = st.columns([3.4, 1])
            with header_left:
                st.subheader("💬 AI 온기 파트너 대화방")
                context_summary = (
                    f"**{life_cycle} · {current_status} · {field}** · "
                    f"**{summary['short_tag']}** ({summary['total_points']:,} SPC)"
                )
                if compass.get("has_enough_data"):
                    context_summary += (
                        f" · 행복 1위 **{compass['best_action']}** "
                        f"({compass['happiness_lift_pct']:+.1f}%)"
                    )
                if finance_context:
                    context_summary += (
                        f" · 월 저축 여력 **{finance_context['monthly_savings']:+,}만원**"
                    )
                st.caption(context_summary)
            with header_right:
                if st.button("🔄 초기화", key="btn_reset_chat", use_container_width=True):
                    st.session_state["ongi_chat_messages"] = []
                    st.rerun()

            if nudge.get("should_nudge"):
                st.markdown(
                    f'<div class="ongi-field-special-box">'
                    f"<strong>🤖 ONGI 선제적 안부 제안</strong><br>{nudge['message']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            quick_cols = st.columns(3)
            quick_prompts = (
                "오늘 하루가 조금 지치고 힘들어요",
                "이번 달 내 소비·주거비 밸런스 어때?",
                "내 기록 기준 추천 행복 습관은?",
            )
            selected_quick_prompt = None
            for idx, text in enumerate(quick_prompts):
                with quick_cols[idx]:
                    if st.button(text, key=f"btn_quick_chat_{idx}", use_container_width=True):
                        selected_quick_prompt = text

        if "ongi_chat_messages" not in st.session_state:
            st.session_state["ongi_chat_messages"] = []

        messages: list[dict[str, str]] = st.session_state["ongi_chat_messages"]

        if not messages:
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(
                    f"안녕하세요! **{life_cycle} · {current_status} · {field}**의 페이스메이커 **ONGI**예요. "
                    f"지금까지 쌓아오신 **{summary['total_points']:,} SPC ({summary['tier_full']})**의 여정을 기억하고 있어요.\n\n"
                    "오늘 마음속 고민이나 기분, 앞으로의 작은 계획을 편하게 들려주세요."
                )

        for item in messages:
            avatar = "🌿" if item["role"] == "assistant" else "🙂"
            with st.chat_message(item["role"], avatar=avatar):
                st.markdown(item["content"])
                if item.get("source"):
                    st.caption(f"응답 출처: {item['source']}")

        typed_prompt = st.chat_input(
            "오늘의 기분이나 고민을 ONGI에게 편하게 들려주세요...",
            key="ongi_chat_input",
        )
        active_prompt = selected_quick_prompt or typed_prompt

        if active_prompt:
            messages.append({"role": "user", "content": active_prompt})
            with st.spinner("ONGI가 나의 기록을 떠올리며 답장을 적고 있어요..."):
                reply_text, reply_source = generate_partner_chat_reply(
                    user_message=active_prompt,
                    chat_history=messages[:-1],
                    logs=logs,
                    life_cycle=life_cycle,
                    current_status=current_status,
                    field=field,
                    finance_context=finance_context,
                )
            messages.append(
                {"role": "assistant", "content": reply_text, "source": reply_source}
            )
            st.session_state["ongi_chat_messages"] = messages
            st.rerun()

    with report_col:
        render_deep_coaching_report(logs, life_cycle, current_status, field)


def render_plaza_tab(
    logs: list[dict],
    plaza_state: dict,
    summary: dict,
    life_cycle: str,
    current_status: str,
    field: str,
) -> None:
    """탭 5: 비교와 과시 없이 선한 실천을 나누는 온기 광장(포지티브 소셜 피드)을 표시합니다."""
    thermo = calculate_community_thermometer(logs, plaza_state)

    # 1. 우리 사회 온기 온도계 글래스 카드
    with st.container(key="glass_card_thermometer"):
        st.subheader("🌡️ 우리 사회 온기 온도계")
        st.markdown(
            f"""
            <div class="ongi-thermo-header">
                <div>
                    <div class="ongi-thermo-temp">{thermo["temperature"]:.1f}°C</div>
                    <div class="ongi-thermo-sub">
                        대한민국 공동체 누적 <strong>{thermo["total_community_spc"]:,} SPC</strong>
                        / 목표 {thermo["goal_spc"]:,} SPC
                    </div>
                </div>
                <div class="ongi-thermo-sub">
                    내가 광장에서 나눈 응원·공유 보너스: <strong>+{thermo["user_bonus_spc"]:,} SPC</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(thermo["progress"])
        st.caption(
            "과시나 랭킹 없이 이웃의 작은 선행에 리액션을 누를 때마다 "
            f"나의 누적 SPC(+{PLAZA_REACTION_SPC_BONUS} SPC)와 우리 사회 온기 온도계가 함께 올라가요."
        )

    # 2. 나의 포지티브 한 줄 공유 카드
    with st.container(key="glass_card_plaza_composer"):
        st.subheader("✍️ 오늘의 포지티브 한 줄 나누기")
        special = get_field_special_action(field)
        action_options = (
            list(MICRO_KINDNESS_ACTIONS.keys())
            + list(VOLUNTEER_TEMPLATE_ACTIONS.keys())
            + list(GROWTH_ACTIONS.keys())
        )
        if special and special["action"] not in action_options:
            action_options.insert(0, special["action"])

        comp_left, comp_right = st.columns([1.2, 2.3], gap="medium")
        with comp_left:
            selected_tag = st.selectbox(
                "실천 카테고리",
                action_options,
                key="plaza_action_tag",
            )
        with comp_right:
            post_text = st.text_input(
                "오늘 실천한 작은 선행이나 배움을 이웃과 나눠보세요",
                placeholder="예: 바쁜 동료의 자료 정리를 조용히 도왔더니 마음이 따뜻해졌어요.",
                max_chars=240,
                key="plaza_post_input",
            )

        if st.button(
            f"🌿 온기 광장에 공유하기 (+{PLAZA_POST_SPC_BONUS} SPC)",
            key="btn_publish_plaza_post",
            use_container_width=True,
        ):
            if not post_text.strip():
                st.warning("공유할 포지티브 한 줄을 먼저 입력해 주세요.")
            else:
                updated_state = add_plaza_post(
                    life_cycle=life_cycle,
                    current_status=current_status,
                    field=field,
                    action_tag=selected_tag,
                    content=post_text,
                    tier_tag=summary["short_tag"],
                )
                st.session_state["ongi_plaza"] = updated_state
                st.session_state["ongi_notice"] = (
                    f"온기 광장에 따뜻한 이야기를 나눴어요! (+{PLAZA_POST_SPC_BONUS} SPC 적립)"
                )
                st.rerun()

    # 3. 이웃들의 포지티브 타임라인
    st.markdown("### 🌿 이웃들의 오늘 온기 타임라인")
    for post in plaza_state.get("posts", []):
        post_id = post["id"]
        reactions = post.get("reactions", {})
        tier_tag = post.get("tier_tag", "🌱 브론즈 IV · Lv.1")
        with st.container(key=f"glass_card_plaza_post_{post_id}"):
            st.markdown(
                f"""
                <div class="ongi-plaza-meta">
                    <span class="ongi-plaza-author">
                        {html.escape(post["author_badge"])}
                        <span class="ongi-tier-mini-tag">[{html.escape(tier_tag)}]</span>
                    </span>
                    <span class="ongi-plaza-time">
                        {html.escape(post.get("created_at", ""))} · 🔥 +{int(post.get("warmth_spc", 0)):,} SPC
                    </span>
                </div>
                <span class="ongi-badge">{html.escape(post.get("action_tag", "포지티브 실천"))}</span>
                <div class="ongi-plaza-body">{html.escape(post.get("content", ""))}</div>
                """,
                unsafe_allow_html=True,
            )

            react_cols = st.columns(3, gap="small")
            for idx, (r_key, r_label) in enumerate(PLAZA_REACTIONS):
                count = int(reactions.get(r_key, 0))
                with react_cols[idx]:
                    if st.button(
                        f"{r_label} ({count})",
                        key=f"btn_react_{post_id}_{r_key}",
                        use_container_width=True,
                    ):
                        updated_state = react_to_plaza_post(post_id, r_key)
                        st.session_state["ongi_plaza"] = updated_state
                        st.session_state["ongi_notice"] = (
                            f"'{r_label}' 응원을 전했어요! "
                            f"나의 누적 SPC(+{PLAZA_REACTION_SPC_BONUS} SPC)와 공동체 온기 온도계가 올랐어요."
                        )
                        st.rerun()


def main() -> None:
    """설정, 사이드바, 상단 5개 탭 대시보드를 조합해 메인 화면을 그립니다."""
    st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")
    apply_light_glass_theme()

    # 손상된 JSON이나 저장 오류는 숨기지 않고 화면에서 확인할 수 있게 합니다.
    try:
        logs = st.session_state.get("ongi_logs")
        if logs is None:
            logs = load_logs()
            st.session_state["ongi_logs"] = logs
    except (OSError, ValueError) as error:
        st.error(f"기록 파일을 불러오지 못했습니다: {error}")
        st.stop()

    plaza_state = st.session_state.get("ongi_plaza")
    if plaza_state is None:
        plaza_state = load_plaza_state()
        st.session_state["ongi_plaza"] = plaza_state

    plaza_bonus_spc = int(plaza_state.get("user_bonus_spc", 0))
    summary = calculate_spc_summary(logs, plaza_bonus_spc=plaza_bonus_spc)
    st.title("🌿 ONGI")
    st.caption("오늘의 작은 행복과 선한 실천을 차곡차곡 쌓아가는 나만의 공간")

    notice = st.session_state.pop("ongi_notice", None)
    if notice:
        st.success(notice)

    life_cycle, current_status, field = render_sidebar(
        logs,
        summary,
        st.session_state.get("life_cycle", LIFE_CYCLE_OPTIONS[2]),
        st.session_state.get("current_status", CURRENT_STATUS_OPTIONS[0]),
        st.session_state.get("field", FIELD_OPTIONS[0]),
    )

    finance_snapshot = simulate_finance_and_spc_fusion(
        logs=logs,
        monthly_income=int(
            st.session_state.get("fin_monthly_income", FINANCE_DEFAULTS["monthly_income"])
        ),
        housing_cost=int(
            st.session_state.get("fin_housing_cost", FINANCE_DEFAULTS["housing_cost"])
        ),
        living_cost=int(
            st.session_state.get("fin_living_cost", FINANCE_DEFAULTS["living_cost"])
        ),
        variable_cost=int(
            st.session_state.get("fin_variable_cost", FINANCE_DEFAULTS["variable_cost"])
        ),
        plaza_bonus_spc=plaza_bonus_spc,
    )

    tab_record, tab_compass, tab_partner, tab_plaza = st.tabs(
        [
            "🌱 오늘의 온기 기록",
            "🧭 행복 나침반 & 10년 시뮬레이터",
            "💬 AI 온기 파트너 (코칭 & 채팅)",
            "🌐 온기 광장 (포지티브 SNS)",
        ]
    )

    with tab_record:
        render_daily_record_tab(life_cycle, current_status, field)
    with tab_compass:
        render_compass_and_future_tab(
            logs, life_cycle, current_status, field, plaza_bonus_spc=plaza_bonus_spc
        )
    with tab_partner:
        render_partner_chat_tab(
            logs,
            summary,
            life_cycle,
            current_status,
            field,
            finance_context=finance_snapshot,
        )
    with tab_plaza:
        render_plaza_tab(logs, plaza_state, summary, life_cycle, current_status, field)

    st.caption(
        f"로컬 AI 모델: {OLLAMA_MODEL_NAME} · Ollama가 꺼져 있어도 누적 통계 기반 맞춤 코칭과 대화를 제공합니다."
    )


if __name__ == "__main__":
    main()
