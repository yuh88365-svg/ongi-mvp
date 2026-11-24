"""ONGI 앱에서 공통으로 사용하는 설정을 관리합니다."""

# 앱의 기본 제목과 로컬 저장 파일 이름입니다.
APP_TITLE = "ONGI | 오늘의 온기"
LOG_FILE_NAME = "ongi_logs.json"
PLAZA_FILE_NAME = "ongi_plaza.json"

# 유아기부터 노년기까지 전 생애 주기를 포괄하는 선택지입니다.
LIFE_CYCLE_OPTIONS = (
    "어린이/유치원",
    "초/중/고등학생",
    "20대",
    "30대",
    "40대",
    "50대",
    "60대",
    "70대",
    "80대",
    "90대",
)

CURRENT_STATUS_OPTIONS = (
    "학생",
    "취준·학습자",
    "직장인",
    "자영업자",
    "돌봄·가사 중",
    "은퇴 후",
    "기타",
)

# 전공·산업·직종(공직 포함) 세부 프로필 선택지입니다.
FIELD_OPTIONS = (
    "IT/AI·개발",
    "공직/공공기관",
    "교육/연구",
    "예술/창작",
    "서비스/자영업",
    "보건/돌봄·복지",
    "학생/전공 탐색 중",
    "기타·자유 탐색",
)

# [카테고리 A] ☀️ 일상의 사소한 온기 (Micro-Kindness)
MICRO_KINDNESS_ACTIONS = {
    "👋 먼저 건네는 밝은 인사·미소": 8,
    "🚪 작은 배려와 양보": 8,
    "💬 따뜻한 안부·감사·칭찬 한마디": 10,
    "📱 포지티브 디지털 온기": 10,
    "🌱 일상 속 작은 지구 아끼기": 8,
}

# [카테고리 B] 🤝 본격 봉사 & 사회적 나눔 템플릿
VOLUNTEER_TEMPLATE_ACTIONS = {
    "🔥 연탄 나눔·난방 배달 봉사": 35,
    "🐶 유기견·유기동물 보호소 돌봄 및 산책 봉사": 35,
    "🍚 무료급식·배식 및 도시락 나눔 봉사": 35,
    "🧒 아동·청소년 문화/학습 멘토링 봉사": 30,
    "💻 어르신·취약계층 디지털/IT·민원 서류 길잡이": 30,
    "🌿 플로깅(쓰레기 줍기)·동네 환경 정화 활동": 25,
    "🩸 헌혈·생명 나눔 및 소액 정기 기부": 30,
}

# [카테고리 C] 📚 나를 키우는 성장 (직종별 특별 행동은 FIELD_SPECIAL_ACTIONS에서 동적 결합)
GROWTH_ACTIONS = {
    "새로운 지식 학습": 15,
    "규칙적인 운동·산책": 10,
}

# 기존 저장 기록(v1.0~v1.1)과의 하위 호환을 위한 레거시 행동 가중치입니다.
LEGACY_ACTION_WEIGHTS = {
    "작은 선행": 10,
    "봉사·나눔": 25,
    "감사 표현": 10,
}

# 전체 포지티브 행동 가중치 통합 사전입니다.
POSITIVE_ACTION_WEIGHTS = {
    **MICRO_KINDNESS_ACTIONS,
    **VOLUNTEER_TEMPLATE_ACTIONS,
    **GROWTH_ACTIONS,
}

# 생애 주기 및 현재 상태에 맞춘 추천 행동과 추가 보너스 가중치(+5 SPC)입니다.
RECOMMENDED_ACTION_BONUS = 5

LIFE_CYCLE_RECOMMENDED_ACTIONS = {
    "어린이/유치원": ("👋 먼저 건네는 밝은 인사·미소", "💬 따뜻한 안부·감사·칭찬 한마디"),
    "초/중/고등학생": ("새로운 지식 학습", "👋 먼저 건네는 밝은 인사·미소"),
    "20대": ("새로운 지식 학습", "📱 포지티브 디지털 온기"),
    "30대": ("규칙적인 운동·산책", "💬 따뜻한 안부·감사·칭찬 한마디"),
    "40대": ("🌿 플로깅(쓰레기 줍기)·동네 환경 정화 활동", "🚪 작은 배려와 양보"),
    "50대": ("🔥 연탄 나눔·난방 배달 봉사", "규칙적인 운동·산책"),
    "60대": ("규칙적인 운동·산책", "🍚 무료급식·배식 및 도시락 나눔 봉사"),
    "70대": ("💬 따뜻한 안부·감사·칭찬 한마디", "👋 먼저 건네는 밝은 인사·미소"),
    "80대": ("💬 따뜻한 안부·감사·칭찬 한마디", "👋 먼저 건네는 밝은 인사·미소"),
    "90대": ("💬 따뜻한 안부·감사·칭찬 한마디", "👋 먼저 건네는 밝은 인사·미소"),
}

STATUS_RECOMMENDED_ACTIONS = {
    "학생": ("👋 먼저 건네는 밝은 인사·미소",),
    "취준·학습자": ("새로운 지식 학습",),
    "직장인": ("규칙적인 운동·산책",),
    "자영업자": ("👋 먼저 건네는 밝은 인사·미소",),
    "돌봄·가사 중": ("💬 따뜻한 안부·감사·칭찬 한마디",),
    "은퇴 후": ("🌿 플로깅(쓰레기 줍기)·동네 환경 정화 활동",),
    "기타": ("🌱 일상 속 작은 지구 아끼기",),
}

# 소속 분야·직종별 맞춤 포지티브 행동과 특별 가중치입니다.
# 특히 공직/공공기관·돌봄 등 보이지 않는 헌신이 큰 분야의 성실함을 깊이 인정합니다.
FIELD_SPECIAL_ACTIONS = {
    "IT/AI·개발": {
        "action": "기술·지식 나눔으로 누군가의 문제 해결 돕기",
        "weight": 18,
        "bonus": 6,
        "note": "기술로 일상의 불편을 덜어내고 배움을 나눈 온기를 기록해요.",
    },
    "공직/공공기관": {
        "action": "보이지 않는 곳에서의 성실한 업무·공익 기여",
        "weight": 20,
        "bonus": 8,
        "note": "드러나지 않는 자리에서도 원칙과 공익을 지켜낸 성실함에 특별 가중치(+8 SPC)를 부여해요.",
    },
    "교육/연구": {
        "action": "누군가의 성장을 응원하는 따뜻한 피드백·배움 나눔",
        "weight": 18,
        "bonus": 6,
        "note": "한 사람의 가능성을 믿고 기다려 준 귀한 온기를 담아요.",
    },
    "예술/창작": {
        "action": "세상에 위로를 더하는 나만의 작은 창작·표현",
        "weight": 18,
        "bonus": 6,
        "note": "고유한 시선으로 마음을 움직이는 기록을 남겼어요.",
    },
    "서비스/자영업": {
        "action": "진심 어린 응대와 이웃과의 따뜻한 연결",
        "weight": 18,
        "bonus": 6,
        "note": "매일 마주하는 사람들에게 건넨 친절이 큰 사회적 자본이 돼요.",
    },
    "보건/돌봄·복지": {
        "action": "타인을 돌본 뒤 나 자신의 마음도 다정히 돌보기",
        "weight": 20,
        "bonus": 8,
        "note": "돌봄의 현장에서 지치기 쉬운 나의 온기를 지켜낸 실천에 특별 가중치(+8 SPC)를 부여해요.",
    },
    "학생/전공 탐색 중": {
        "action": "비교 없이 호기심을 따라 진로·전공 한 걸음 탐색",
        "weight": 16,
        "bonus": 6,
        "note": "남의 속도가 아닌 나만의 방향을 찾아가는 소중한 걸음이에요.",
    },
    "기타·자유 탐색": {
        "action": "나만의 속도로 오늘의 작은 의미 발견하기",
        "weight": 15,
        "bonus": 5,
        "note": "어디에 속해 있든 나만의 온기를 지켜낸 하루를 응원해요.",
    },
}

# 하루 단위 무한 레벨업(Lv.1 -> Lv.2 -> ...) 경험치 단위입니다.
DAILY_LEVEL_SPC_STEP = 35

# 롤(LoL) 티어 구조를 온기 컨셉으로 재해석한 7단계 티어 & 세부 디비전(IV~I) 설정입니다.
# (아이콘, 티어명, 짧은 티어명, 부제, 디비전 목록, 디비전당 필요 SPC, 시작 누적 SPC)
SPC_TIER_DEFINITIONS = (
    {
        "icon": "🌱",
        "tier_name": "브론즈 온기",
        "short_name": "브론즈",
        "subtitle": "씨앗",
        "divisions": ("IV", "III", "II", "I"),
        "step_spc": 100,
        "start_spc": 0,
    },
    {
        "icon": "🌿",
        "tier_name": "실버 온기",
        "short_name": "실버",
        "subtitle": "새싹",
        "divisions": ("IV", "III", "II", "I"),
        "step_spc": 250,
        "start_spc": 400,
    },
    {
        "icon": "🌼",
        "tier_name": "골드 온기",
        "short_name": "골드",
        "subtitle": "꽃망울",
        "divisions": ("IV", "III", "II", "I"),
        "step_spc": 600,
        "start_spc": 1_400,
    },
    {
        "icon": "🔥",
        "tier_name": "플래티넘 온기",
        "short_name": "플래티넘",
        "subtitle": "모닥불",
        "divisions": ("IV", "III", "II", "I"),
        "step_spc": 1_500,
        "start_spc": 3_800,
    },
    {
        "icon": "☀️",
        "tier_name": "다이아 온기",
        "short_name": "다이아",
        "subtitle": "햇살",
        "divisions": ("IV", "III", "II", "I"),
        "step_spc": 3_500,
        "start_spc": 9_800,
    },
    {
        "icon": "🏮",
        "tier_name": "마스터 온기",
        "short_name": "마스터",
        "subtitle": "등대 마스터",
        "divisions": (),
        "step_spc": 26_200,
        "start_spc": 23_800,
    },
    {
        "icon": "🌍",
        "tier_name": "챌린저 온기",
        "short_name": "챌린저",
        "subtitle": "그랜드 온기 거장",
        "divisions": (),
        "step_spc": 0,
        "start_spc": 50_000,
    },
)

# 1개월~10년 장기 미래 시뮬레이터에서 사용하는 사회적 자본가 성장 칭호입니다.
LONG_TERM_SOCIAL_TITLES = (
    (0, "온기 씨앗 기록가"),
    (500, "일상 온기 메이커"),
    (3_000, "마을의 따뜻한 등불"),
    (15_000, "지역사회 온기 리더"),
    (50_000, "지속가능 사회적 자본가"),
    (100_000, "세상을 데우는 온기 거장"),
)

# 현실 자산 & SPC 융합 가계부 시뮬레이터 기본값(단위: 만원) 및 환산 기준입니다.
FINANCE_DEFAULTS = {
    "monthly_income": 320,  # 월 평균 수입(월급)
    "housing_cost": 85,  # 월 주거비용(월세·관리비·대출이자)
    "living_cost": 95,  # 기본 생활비(식비·배달·구독료)
    "variable_cost": 30,  # 월평균 변수 비용(경조사·비상금)
}

SPC_FINANCE_FUSION_RATES = {
    "base_annual_return": 0.035,  # 기본 연 3.5% 저축·복리 수익률
    "spc_max_bonus_rate": 0.015,  # SPC 사회적 신뢰 우대 금리 최대 +1.5%p
    "spc_incentive_manwon": 0.03,  # 1 SPC = 300원(0.03만원) 사회성과 인센티브 환산
}

# 10년 뒤 총가치(현실 자산 + 사회적 자본, 만원)에 따른 융합 성장 레벨입니다.
FINANCE_FUSION_LEVELS = (
    (0, "🌱 온기 가계 씨앗"),
    (3_000, "🌿 안정 생활 온기가"),
    (10_000, "🌼 자립형 사회적 자본가"),
    (25_000, "🔥 지속가능 온기 자산가"),
    (50_000, "☀️ 선순환 웰빙 거장"),
)

# 과시와 경쟁 대신 누적 SPC를 따뜻한 사회적 가치로 환산하는 기준입니다.
SPC_SOCIAL_VALUE_RATES = {
    "briquette_spc_unit": 25.0,  # 25 SPC = 따뜻한 연탄 1장 나눔 환산
    "community_warmth_multiplier": 0.4,  # 1 SPC = 지역사회 온기 기여 0.4 포인트
    "positive_minutes_per_spc": 1.5,  # 1 SPC = 나를 살리는 긍정 시간 1.5분
}

# 타인과의 랭킹 없이 나의 실천과 꾸준함을 기념하는 비경쟁 포지티브 배지 기준입니다.
POSITIVE_BADGE_DEFINITIONS = (
    {
        "id": "first_seed",
        "icon": "🌱",
        "name": "첫 온기 씨앗",
        "description": "첫 번째 온기 기록 남기기",
        "metric": "total_days",
        "target": 1,
        "unit": "일",
    },
    {
        "id": "steady_spark",
        "icon": "🔥",
        "name": "꾸준한 불씨",
        "description": "7일 연속으로 마음 기록 이어가기",
        "metric": "max_streak",
        "target": 7,
        "unit": "일 연속",
    },
    {
        "id": "walk_master",
        "icon": "🚶",
        "name": "산책 마스터",
        "description": "규칙적인 운동·산책 5회 실천하기",
        "metric": "action:규칙적인 운동·산책",
        "target": 5,
        "unit": "회",
    },
    {
        "id": "sharing_ember",
        "icon": "🤝",
        "name": "나눔의 불씨",
        "description": "봉사 템플릿 또는 작은 선행 합산 5회 실천하기",
        "metric": "category:volunteer",
        "target": 5,
        "unit": "회",
    },
    {
        "id": "learning_lantern",
        "icon": "📚",
        "name": "배움의 등불",
        "description": "새로운 지식 학습 5회 실천하기",
        "metric": "action:새로운 지식 학습",
        "target": 5,
        "unit": "회",
    },
    {
        "id": "gratitude_garden",
        "icon": "💌",
        "name": "감사의 정원",
        "description": "밝은 인사·감사·칭찬 한마디 합산 5회 실천하기",
        "metric": "category:micro_warmth",
        "target": 5,
        "unit": "회",
    },
)

# 온기 광장(포지티브 소셜 피드) 공동체 온도계 및 리액션 설정입니다.
COMMUNITY_BASE_SPC = 128_450
COMMUNITY_GOAL_SPC = 200_000
PLAZA_REACTION_SPC_BONUS = 3
PLAZA_POST_SPC_BONUS = 5

PLAZA_REACTIONS = (
    ("warmth", "🔥 온기 더하기"),
    ("invisible_effort", "👏 보이지 않는 노력 응원"),
    ("join", "🌱 나도 동참할래요"),
)

DEFAULT_PLAZA_POSTS = (
    {
        "id": "seed_1",
        "author_badge": "30대 · 직장인 · 공직/공공기관",
        "tier_tag": "🔥 플래티넘 II · Lv.142",
        "action_tag": "보이지 않는 곳에서의 성실한 업무·공익 기여",
        "content": (
            "민원실 마감 직전 서류 작성이 어려우셨던 어르신을 끝까지 도와드리고 조용히 불을 껐어요. "
            "누가 보지 않아도 공익의 자리에 작은 온기를 보탠 하루라 마음이 든든합니다."
        ),
        "created_at": "오늘 오전 09:40",
        "warmth_spc": 42,
        "reactions": {"warmth": 8, "invisible_effort": 11, "join": 4},
    },
    {
        "id": "seed_2",
        "author_badge": "20대 · 취준·학습자 · IT/AI·개발",
        "tier_tag": "🌼 골드 III · Lv.58",
        "action_tag": "기술·지식 나눔으로 누군가의 문제 해결 돕기",
        "content": (
            "오늘 하루 종일 붙잡았던 파이썬 환경 오류 해결법을 보기 좋게 정리해 오픈 노트에 공유했어요. "
            "같은 문제로 막힌 동료 개발자의 시간을 조금이라도 아껴줄 수 있기를 바랍니다."
        ),
        "created_at": "오늘 오전 11:15",
        "warmth_spc": 36,
        "reactions": {"warmth": 7, "invisible_effort": 5, "join": 9},
    },
    {
        "id": "seed_3",
        "author_badge": "60대 · 은퇴 후 · 기타·자유 탐색",
        "tier_tag": "☀️ 다이아 IV · Lv.295",
        "action_tag": "규칙적인 운동·산책",
        "content": (
            "동네 천변 산책길에서 30분 걷기를 하며 벤치 주변 쓰레기를 함께 주웠어요. "
            "건강도 챙기고 우리 동네 길도 환해져서 일석이조의 아침이었습니다."
        ),
        "created_at": "오늘 오후 01:20",
        "warmth_spc": 51,
        "reactions": {"warmth": 12, "invisible_effort": 6, "join": 10},
    },
    {
        "id": "seed_4",
        "author_badge": "40대 · 돌봄·가사 중 · 보건/돌봄·복지",
        "tier_tag": "🔥 플래티넘 IV · Lv.118",
        "action_tag": "타인을 돌본 뒤 나 자신의 마음도 다정히 돌보기",
        "content": (
            "가족과 어르신을 돌보느라 눈코 뜰 새 없었지만, 오후에 딱 10분 따뜻한 차를 마시며 "
            "'오늘도 잘 버텨줘서 고마워'라고 나 자신에게 먼저 인사해 주었어요."
        ),
        "created_at": "오늘 오후 03:05",
        "warmth_spc": 39,
        "reactions": {"warmth": 9, "invisible_effort": 10, "join": 6},
    },
    {
        "id": "seed_5",
        "author_badge": "초/중/고등학생 · 학생 · 학생/전공 탐색 중",
        "tier_tag": "🌿 실버 I · Lv.34",
        "action_tag": "감사 표현",
        "content": (
            "점심시간에 급식실 선생님께 '매일 따뜻한 밥 만들어주셔서 감사합니다!'라고 먼저 인사드렸어요. "
            "환하게 웃어주셔서 오후 수업까지 힘이 났어요."
        ),
        "created_at": "오늘 오후 04:30",
        "warmth_spc": 45,
        "reactions": {"warmth": 11, "invisible_effort": 7, "join": 8},
    },
)

# =========================================================================
# [3~4개월 차 슬롯 B - 파인튜닝 모델 교체]
# QLoRA로 직접 파인튜닝해 Ollama에 등록한 모델(예: "ongi-gemma2-qlora:latest")이
# 준비되면 아래 FINETUNED_OLLAMA_MODEL_NAME 한 줄만 채우면 앱 전체에 즉시 적용됩니다.
# =========================================================================
OLLAMA_BASE_URL = "http://localhost:11434"
BASE_OLLAMA_MODEL_NAME = "gemma2:9b"
FINETUNED_OLLAMA_MODEL_NAME = ""  # 예: "ongi-gemma2-qlora:latest"
OLLAMA_MODEL_NAME = FINETUNED_OLLAMA_MODEL_NAME or BASE_OLLAMA_MODEL_NAME
OLLAMA_TIMEOUT_SECONDS = 8
OLLAMA_REPORT_TIMEOUT_SECONDS = 18

# 밝은 톤 글래스모피즘(Light Glassmorphism) UI 색상 팔레트입니다.
THEME_COLORS = {
    "bg_gradient": "linear-gradient(135deg, #FFFDF7 0%, #FFEFE5 48%, #EBF9F4 100%)",
    "sidebar_bg": "rgba(255, 255, 255, 0.72)",
    "glass_bg": "rgba(255, 255, 255, 0.75)",
    "glass_border": "rgba(255, 255, 255, 0.9)",
    "glass_shadow": "0 10px 30px rgba(30, 41, 59, 0.08)",
    "input_bg": "rgba(255, 255, 255, 0.92)",
    "input_border": "rgba(148, 163, 184, 0.45)",
    "text_heading": "#111827",
    "text_body": "#1E293B",
    "text_muted": "#475569",
    "accent_coral": "#FF7A59",
    "accent_coral_hover": "#F06444",
    "accent_amber": "#F59E0B",
    "accent_gradient": "linear-gradient(135deg, #FF7A59 0%, #F59E0B 100%)",
    "accent_gradient_hover": "linear-gradient(135deg, #F06444 0%, #D97706 100%)",
    "progress_track": "rgba(255, 122, 89, 0.16)",
    "feedback_tint": "rgba(255, 247, 237, 0.9)",
}
