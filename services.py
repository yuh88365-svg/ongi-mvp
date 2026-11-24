"""ONGI의 로컬 저장, SPC 계산, 행복 확률 분석, 샘플 시뮬레이션, AI 피드백 기능을 제공합니다."""

from datetime import date, datetime, timedelta
from http.client import HTTPException
import json
from pathlib import Path
import random
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from config import (
    COMMUNITY_BASE_SPC,
    COMMUNITY_GOAL_SPC,
    DAILY_LEVEL_SPC_STEP,
    DEFAULT_PLAZA_POSTS,
    FIELD_SPECIAL_ACTIONS,
    FINANCE_DEFAULTS,
    FINANCE_FUSION_LEVELS,
    GROWTH_ACTIONS,
    LEGACY_ACTION_WEIGHTS,
    LIFE_CYCLE_RECOMMENDED_ACTIONS,
    LOG_FILE_NAME,
    LONG_TERM_SOCIAL_TITLES,
    MICRO_KINDNESS_ACTIONS,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_NAME,
    OLLAMA_REPORT_TIMEOUT_SECONDS,
    OLLAMA_TIMEOUT_SECONDS,
    PLAZA_FILE_NAME,
    PLAZA_POST_SPC_BONUS,
    PLAZA_REACTION_SPC_BONUS,
    POSITIVE_ACTION_WEIGHTS,
    POSITIVE_BADGE_DEFINITIONS,
    RECOMMENDED_ACTION_BONUS,
    SPC_FINANCE_FUSION_RATES,
    SPC_SOCIAL_VALUE_RATES,
    SPC_TIER_DEFINITIONS,
    STATUS_RECOMMENDED_ACTIONS,
    VOLUNTEER_TEMPLATE_ACTIONS,
)

# 파일은 현재 코드와 같은 폴더에 만들어져 실행 위치에 영향을 받지 않습니다.
LOG_FILE = Path(__file__).with_name(LOG_FILE_NAME)
PLAZA_FILE = Path(__file__).with_name(PLAZA_FILE_NAME)

_SAMPLE_MEMOS = (
    "아침 햇살을 맞으며 가볍게 산책하니 머리가 맑아졌어요.",
    "고마웠던 분께 짧은 감사 인사를 전하니 마음이 따뜻해졌어요.",
    "새로운 개념을 하나 이해해서 작은 성취감을 느꼈어요.",
    "바쁜 하루였지만 잠시 숨을 고르며 나 자신을 다독였어요.",
    "주변 사람을 작게 도와주고 나니 오히려 제가 더 힘을 얻었어요.",
    "좋아하는 음악과 함께 천천히 하루를 마무리했어요.",
    "작은 루틴을 꾸준히 지켜낸 스스로가 대견한 하루였어요.",
    "가족과 따뜻한 식사를 나누며 웃을 수 있어서 좋았어요.",
)


def get_field_special_action(field: str | None = None) -> dict[str, Any] | None:
    """소속 분야·직종에 해당하는 특별 포지티브 행동 정보를 반환합니다."""
    if not field:
        return None
    return FIELD_SPECIAL_ACTIONS.get(field)


def _all_known_action_weights() -> dict[str, int]:
    """일상 온기, 봉사 템플릿, 성장·직종 행동 및 레거시 행동의 전체 가중치 사전을 반환합니다."""
    weights = dict(LEGACY_ACTION_WEIGHTS)
    weights.update(POSITIVE_ACTION_WEIGHTS)
    for spec in FIELD_SPECIAL_ACTIONS.values():
        weights[spec["action"]] = int(spec["weight"])
    return weights


def get_recommended_actions(
    life_cycle: str | None = None,
    current_status: str | None = None,
    field: str | None = None,
) -> tuple[str, ...]:
    """생애 주기·현재 상태·소속 분야에 맞는 추천 포지티브 행동 목록을 반환합니다."""
    ordered: list[str] = []
    special = get_field_special_action(field)
    if special:
        ordered.append(special["action"])
    for action in LIFE_CYCLE_RECOMMENDED_ACTIONS.get(life_cycle or "", ()):
        if action in POSITIVE_ACTION_WEIGHTS and action not in ordered:
            ordered.append(action)
    for action in STATUS_RECOMMENDED_ACTIONS.get(current_status or "", ()):
        if action in POSITIVE_ACTION_WEIGHTS and action not in ordered:
            ordered.append(action)
    return tuple(ordered)


def load_logs() -> list[dict[str, Any]]:
    """로컬 JSON에서 기록을 불러오고, 저장 형식이 잘못되면 명확히 알립니다."""
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open("r", encoding="utf-8") as log_file:
            logs = json.load(log_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{LOG_FILE.name} 파일의 JSON 형식이 올바르지 않습니다."
        ) from error

    if not isinstance(logs, list) or any(
        not isinstance(record, dict) or not isinstance(record.get("date"), str)
        for record in logs
    ):
        raise ValueError(
            f"{LOG_FILE.name} 파일은 날짜가 포함된 기록 목록이어야 합니다."
        )
    return logs


def _write_logs(logs: list[dict[str, Any]]) -> None:
    """기록 목록을 로컬 JSON 파일에 저장합니다."""
    with LOG_FILE.open("w", encoding="utf-8") as log_file:
        json.dump(logs, log_file, ensure_ascii=False, indent=2)


def save_daily_log(record: dict[str, Any]) -> list[dict[str, Any]]:
    """오늘 기록을 저장하며, 같은 날짜의 기록이 있으면 새 내용으로 갱신합니다."""
    log_date = record.get("date")
    if not isinstance(log_date, str):
        raise ValueError("기록에는 YYYY-MM-DD 형식의 날짜가 필요합니다.")

    saved_record = dict(record)
    saved_record["positive_actions"] = list(record.get("positive_actions", []))
    saved_record["daily_spc"] = calculate_daily_spc(
        int(saved_record["happiness"]),
        int(saved_record["energy"]),
        saved_record["positive_actions"],
        life_cycle=saved_record.get("life_cycle"),
        current_status=saved_record.get("current_status"),
        field=saved_record.get("field"),
    )

    # 기존 날짜 기록은 유지하고, 오늘 날짜만 한 건으로 교체합니다.
    logs = [item for item in load_logs() if item["date"] != log_date]
    logs.append(saved_record)
    logs.sort(key=lambda item: item["date"])

    # 쓰기 오류는 호출한 화면에서 확인할 수 있도록 숨기지 않습니다.
    _write_logs(logs)
    return logs


def clear_logs() -> list[dict[str, Any]]:
    """저장된 모든 개인 기록을 초기화합니다."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    if PLAZA_FILE.exists():
        state = load_plaza_state()
        state["user_bonus_spc"] = 0
        _write_plaza_state(state)
    return []


def generate_sample_logs(
    days: int = 30,
    life_cycle: str = "20대",
    current_status: str = "직장인",
    field: str = "IT/AI·개발",
) -> list[dict[str, Any]]:
    """최근 N일간의 일상 온기·세부 봉사 템플릿·성장 행동이 어우러진 샘플 데이터를 생성합니다."""
    rng = random.Random(
        20261124 + sum(ord(ch) for ch in f"{life_cycle}{current_status}{field}")
    )
    recommended = get_recommended_actions(life_cycle, current_status, field)
    special = get_field_special_action(field)

    micro_list = list(MICRO_KINDNESS_ACTIONS.keys())
    volunteer_list = list(VOLUNTEER_TEMPLATE_ACTIONS.keys())
    growth_list = list(GROWTH_ACTIONS.keys())
    if special and special["action"] not in growth_list:
        growth_list.insert(0, special["action"])

    # 행복 나침반에서 뚜렷한 상승 패턴이 나타나도록 핵심 행복 습관을 지정합니다.
    hero_action = recommended[0] if recommended else micro_list[0]

    today = date.today()
    logs: list[dict[str, Any]] = []

    for offset in range(days - 1, -1, -1):
        current_day = today - timedelta(days=offset)
        progress_ratio = (days - 1 - offset) / max(1, days - 1)
        is_weekend = current_day.weekday() >= 5

        selected_actions: list[str] = []

        # 1) 핵심 추천 행동 (높은 빈도)
        if rng.random() < (0.55 + 0.12 * progress_ratio):
            selected_actions.append(hero_action)

        # 2) 일상의 사소한 온기 (매일 1~2개 가볍게 실천)
        micro_pick = rng.choice(micro_list)
        if micro_pick not in selected_actions and rng.random() < 0.78:
            selected_actions.append(micro_pick)
        if rng.random() < 0.35:
            second_micro = rng.choice(micro_list)
            if second_micro not in selected_actions:
                selected_actions.append(second_micro)

        # 3) 성장 & 직종 공헌 (꾸준히 1개 실천)
        growth_pick = rng.choice(growth_list)
        if growth_pick not in selected_actions and rng.random() < 0.52:
            selected_actions.append(growth_pick)

        # 4) 본격 봉사 템플릿 (주말 중심 또는 주 1~2회 현실적인 빈도로 연탄·유기견·무료급식 등 포함)
        volunteer_prob = 0.42 if is_weekend else 0.12
        if rng.random() < volunteer_prob:
            vol_pick = rng.choice(volunteer_list)
            if vol_pick not in selected_actions:
                selected_actions.append(vol_pick)

        # 핵심 행동 및 봉사 실천 여부에 따라 현실적인 행복·에너지 점수를 계산합니다.
        base_happiness = 5.3 + 1.0 * progress_ratio + (0.5 if is_weekend else 0.0)
        base_energy = 5.1 + 0.9 * progress_ratio + (0.4 if is_weekend else -0.2)

        if hero_action in selected_actions:
            base_happiness += rng.uniform(1.5, 2.3)
            base_energy += rng.uniform(1.0, 1.7)
        if any(a in VOLUNTEER_TEMPLATE_ACTIONS for a in selected_actions):
            base_happiness += rng.uniform(0.8, 1.5)
            base_energy += rng.uniform(0.3, 0.9)
        if len(selected_actions) >= 3:
            base_happiness += rng.uniform(0.3, 0.7)

        happiness = max(1, min(10, round(base_happiness + rng.uniform(-0.9, 0.8))))
        energy = max(1, min(10, round(base_energy + rng.uniform(-1.0, 0.9))))
        daily_spc = calculate_daily_spc(
            happiness,
            energy,
            selected_actions,
            life_cycle=life_cycle,
            current_status=current_status,
            field=field,
        )

        logs.append(
            {
                "date": current_day.isoformat(),
                "life_cycle": life_cycle,
                "current_status": current_status,
                "field": field,
                "happiness": happiness,
                "energy": energy,
                "memo": _SAMPLE_MEMOS[(days - offset) % len(_SAMPLE_MEMOS)],
                "positive_actions": selected_actions,
                "daily_spc": daily_spc,
            }
        )

    _write_logs(logs)
    return logs


def calculate_daily_spc(
    happiness: int,
    energy: int,
    positive_actions: list[str],
    life_cycle: str | None = None,
    current_status: str | None = None,
    field: str | None = None,
) -> int:
    """행복·에너지 평균과 긍정 행동 가중치(생애 주기·직종 보너스 포함)를 합쳐 하루 SPC를 계산합니다."""
    if not 1 <= happiness <= 10 or not 1 <= energy <= 10:
        raise ValueError("행복과 에너지는 각각 1점부터 10점까지 입력해야 합니다.")

    all_weights = _all_known_action_weights()
    unknown_actions = set(positive_actions) - set(all_weights)
    if unknown_actions:
        raise ValueError(f"알 수 없는 행동 카테고리입니다: {', '.join(unknown_actions)}")

    recommended = set(get_recommended_actions(life_cycle, current_status, field))
    special = get_field_special_action(field)

    # 감정 점수는 평균으로 반영하고, 선택한 행동의 기본 가중치와 맞춤·분야 특별 보너스를 더합니다.
    wellbeing_points = round((happiness + energy) / 2)
    action_points = 0
    for action in positive_actions:
        base_weight = all_weights[action]
        if special and action == special["action"]:
            bonus = int(special["bonus"])
        elif action in recommended:
            bonus = RECOMMENDED_ACTION_BONUS
        else:
            bonus = 0
        action_points += base_weight + bonus
    return wellbeing_points + action_points


def _build_tier_stages() -> list[dict[str, Any]]:
    """7단계 티어와 세부 디비전(IV~I)을 누적 SPC 오름차순 목록으로 펼칩니다."""
    stages: list[dict[str, Any]] = []
    for tier in SPC_TIER_DEFINITIONS:
        divisions = tier["divisions"]
        start = int(tier["start_spc"])
        step = int(tier["step_spc"])
        if divisions:
            for idx, div in enumerate(divisions):
                div_start = start + idx * step
                div_end = div_start + step
                stages.append(
                    {
                        "icon": tier["icon"],
                        "tier_name": tier["tier_name"],
                        "short_name": tier["short_name"],
                        "subtitle": tier["subtitle"],
                        "division": div,
                        "full_label": f"{tier['icon']} {tier['tier_name']} ({tier['subtitle']} {div})",
                        "short_label": f"{tier['icon']} {tier['short_name']} {div}",
                        "start_spc": div_start,
                        "end_spc": div_end,
                    }
                )
        else:
            stages.append(
                {
                    "icon": tier["icon"],
                    "tier_name": tier["tier_name"],
                    "short_name": tier["short_name"],
                    "subtitle": tier["subtitle"],
                    "division": "",
                    "full_label": f"{tier['icon']} {tier['tier_name']} ({tier['subtitle']})",
                    "short_label": f"{tier['icon']} {tier['short_name']}",
                    "start_spc": start,
                    "end_spc": start + step if step > 0 else None,
                }
            )
    return stages


def _calculate_current_streak(logs: list[dict[str, Any]]) -> int:
    """가장 최근 기록일을 기준으로 현재 이어지고 있는 연속 기록 일수를 계산합니다."""
    parsed_dates: list[date] = []
    for record in logs:
        raw_date = record.get("date")
        if isinstance(raw_date, str):
            try:
                parsed_dates.append(date.fromisoformat(raw_date))
            except ValueError:
                continue

    unique_dates = sorted(set(parsed_dates))
    if not unique_dates:
        return 0

    streak = 1
    for index in range(len(unique_dates) - 1, 0, -1):
        if (unique_dates[index] - unique_dates[index - 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def calculate_spc_summary(
    logs: list[dict[str, Any]], plaza_bonus_spc: int = 0
) -> dict[str, Any]:
    """누적 SPC, 롤 스타일 7단계 티어(IV~I)·LP, 무한 일일 레벨(Lv.), 연속 기록을 계산합니다."""
    log_points = sum(
        int(
            record.get(
                "daily_spc",
                calculate_daily_spc(
                    int(record.get("happiness", 5)),
                    int(record.get("energy", 5)),
                    list(record.get("positive_actions", [])),
                    life_cycle=record.get("life_cycle"),
                    current_status=record.get("current_status"),
                    field=record.get("field"),
                ),
            )
        )
        for record in logs
    )
    total_points = log_points + max(0, int(plaza_bonus_spc))

    # 1) 롤(LoL) 스타일 7단계 티어 & 세부 디비전(IV~I) + LP 계산
    stages = _build_tier_stages()
    current_index = 0
    for idx, stage in enumerate(stages):
        if total_points >= stage["start_spc"]:
            current_index = idx
        else:
            break

    current_stage = stages[current_index]
    if current_index + 1 < len(stages):
        next_stage = stages[current_index + 1]
        span = max(1, next_stage["start_spc"] - current_stage["start_spc"])
        earned_in_stage = total_points - current_stage["start_spc"]
        progress = min(1.0, max(0.0, earned_in_stage / span))
        lp = min(99, int(progress * 100))
        points_to_next = max(0, next_stage["start_spc"] - total_points)
        next_level_name = next_stage["short_label"]
    else:
        progress = 1.0
        lp = 100 + ((total_points - current_stage["start_spc"]) // 50)
        points_to_next = 0
        next_level_name = None

    # 2) 하루 단위 무한 레벨업(Lv. 1 -> Lv. 2 -> ...) 및 연속 기록 계산
    daily_level = (total_points // DAILY_LEVEL_SPC_STEP) + 1
    level_exp_current = total_points % DAILY_LEVEL_SPC_STEP
    level_exp_to_next = DAILY_LEVEL_SPC_STEP - level_exp_current
    level_progress = level_exp_current / DAILY_LEVEL_SPC_STEP
    current_streak = _calculate_current_streak(logs)
    short_tag = f"{current_stage['short_label']} · Lv.{daily_level}"

    return {
        "total_points": total_points,
        "level": current_stage["full_label"],
        "tier_icon": current_stage["icon"],
        "tier_name": current_stage["tier_name"],
        "tier_short": current_stage["short_label"],
        "tier_full": current_stage["full_label"],
        "next_level": next_level_name,
        "progress": progress,
        "lp": lp,
        "points_to_next": points_to_next,
        "daily_level": daily_level,
        "level_exp_current": level_exp_current,
        "level_exp_step": DAILY_LEVEL_SPC_STEP,
        "level_exp_to_next": level_exp_to_next,
        "level_progress": level_progress,
        "current_streak": current_streak,
        "short_tag": short_tag,
    }


# =========================================================================
# [1~2개월 차 슬롯 - 데이터 분석]
# 현재는 행동별 평균 행복 상승률(%)과 고행복(7점 이상) 달성 확률을 계산합니다.
# 1~2개월 차에는 Pandas 상관계수(df.corr())나 Scikit-learn 회귀·분류 모델의
# Feature Importance로 이 함수 내부 로직만 교체하면 행복 나침반이 즉시 고도화됩니다.
# =========================================================================
def analyze_happiness_compass(
    logs: list[dict[str, Any]],
    life_cycle: str | None = None,
    current_status: str | None = None,
    field: str | None = None,
) -> dict[str, Any]:
    """누적 기록을 바탕으로 행동별 행복 상승률(%)과 고행복 확률, 기대 지수를 계산합니다."""
    total_days = len(logs)
    if total_days < 3:
        return {
            "has_enough_data": False,
            "total_days": total_days,
        }

    recommended = set(get_recommended_actions(life_cycle, current_status, field))
    overall_happiness = sum(int(r.get("happiness", 5)) for r in logs) / total_days
    high_threshold = 7

    candidate_actions = list(_all_known_action_weights().keys())
    action_stats: list[dict[str, Any]] = []
    for action in candidate_actions:
        with_action = [
            r for r in logs if action in list(r.get("positive_actions", []))
        ]
        if not with_action:
            continue

        without_action = [
            r for r in logs if action not in list(r.get("positive_actions", []))
        ]

        avg_happiness_with = sum(int(r.get("happiness", 5)) for r in with_action) / len(
            with_action
        )
        avg_energy_with = sum(int(r.get("energy", 5)) for r in with_action) / len(
            with_action
        )
        avg_wellbeing_with = (avg_happiness_with + avg_energy_with) / 2

        baseline_happiness = (
            sum(int(r.get("happiness", 5)) for r in without_action)
            / len(without_action)
            if without_action
            else overall_happiness
        )
        happiness_lift_pct = (
            ((avg_happiness_with - baseline_happiness) / baseline_happiness) * 100
            if baseline_happiness > 0
            else 0.0
        )

        high_days = sum(
            1 for r in with_action if int(r.get("happiness", 5)) >= high_threshold
        )
        high_happiness_prob = round((high_days / len(with_action)) * 100)

        # 기대 온기 지수(100점 만점): 평균 행복·에너지(70%) + 고행복 확률(30%)
        expected_index = round(avg_wellbeing_with * 7.0 + high_happiness_prob * 0.3, 1)

        # 신뢰도 가중치(표본 2회 이상 우선) + 맞춤 추천 가중치
        confidence_factor = 1.0 if len(with_action) >= 2 else 0.85
        profile_bonus = 2.0 if action in recommended else 0.0
        rank_score = (
            (happiness_lift_pct * 0.55 + expected_index * 0.45 + profile_bonus)
            * confidence_factor
        )

        action_stats.append(
            {
                "action": action,
                "count": len(with_action),
                "avg_happiness": round(avg_happiness_with, 1),
                "avg_energy": round(avg_energy_with, 1),
                "happiness_lift_pct": round(happiness_lift_pct, 1),
                "high_happiness_prob": high_happiness_prob,
                "expected_index": expected_index,
                "is_recommended": action in recommended,
                "rank_score": rank_score,
            }
        )

    if not action_stats:
        return {
            "has_enough_data": False,
            "total_days": total_days,
        }

    action_stats.sort(key=lambda item: item["rank_score"], reverse=True)
    best = action_stats[0]

    return {
        "has_enough_data": True,
        "total_days": total_days,
        "best_action": best["action"],
        "happiness_lift_pct": best["happiness_lift_pct"],
        "high_happiness_prob": best["high_happiness_prob"],
        "expected_index": best["expected_index"],
        "avg_happiness": best["avg_happiness"],
        "avg_energy": best["avg_energy"],
        "action_count": best["count"],
        "top_actions": action_stats[:3],
    }


def build_history_dataframe(logs: list[dict[str, Any]]) -> pd.DataFrame:
    """기록을 날짜순으로 정리해 차트에 쓸 행복·에너지·누적 SPC 표를 만듭니다."""
    rows = []
    for record in logs:
        happiness = int(record.get("happiness", 5))
        energy = int(record.get("energy", 5))
        actions = list(record.get("positive_actions", []))
        daily_spc = int(
            record.get(
                "daily_spc",
                calculate_daily_spc(
                    happiness,
                    energy,
                    actions,
                    life_cycle=record.get("life_cycle"),
                    current_status=record.get("current_status"),
                ),
            )
        )
        rows.append(
            {
                "date": record["date"],
                "행복": happiness,
                "에너지": energy,
                "하루 SPC": daily_spc,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["행복", "에너지", "누적 SPC"])

    # 같은 날짜의 기록은 저장 시 최신 기록으로 교체되며, 오래된 입력도 날짜순 정렬합니다.
    history = pd.DataFrame(rows).sort_values("date").set_index("date")
    history["누적 SPC"] = history["하루 SPC"].cumsum()
    return history[["행복", "에너지", "누적 SPC"]]


def _fallback_feedback(record: dict[str, Any]) -> str:
    """Ollama에 연결하지 못했을 때도 오늘의 기록을 격려하는 문장을 돌려줍니다."""
    actions = list(record.get("positive_actions", []))
    if actions:
        return (
            f"오늘 해내신 {', '.join(actions)}이 참 멋져요. "
            "그 작은 온기가 분명 의미 있어요."
        )
    return "오늘의 마음을 기록한 것만으로도 충분히 소중한 한 걸음이에요. 천천히 나만의 온기를 쌓아가요."


def generate_warm_feedback(
    record: dict[str, Any],
    model_name: str = OLLAMA_MODEL_NAME,
) -> str:
    """로컬 Ollama에 따뜻한 피드백을 요청하고, 사용할 수 없으면 응원 문장을 반환합니다."""
    fallback = _fallback_feedback(record)
    prompt = (
        "당신은 ONGI라는 따뜻한 자기성장 파트너입니다. 비교나 평가 없이 "
        "아래 오늘의 기록에 대해 한국어로 다정하고 구체적인 응원 한두 문장을 "
        "작성하세요. 의료적 진단은 하지 마세요.\n"
        f"행복 점수: {record.get('happiness', '미기록')}/10\n"
        f"에너지 점수: {record.get('energy', '미기록')}/10\n"
        f"실천한 행동: {', '.join(record.get('positive_actions', [])) or '없음'}\n"
        f"감정 메모: {record.get('memo', '') or '없음'}"
    )
    request_body = json.dumps(
        {"model": model_name, "prompt": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
        feedback = result.get("response", "").strip()
        return feedback or fallback
    except (
        HTTPError,
        URLError,
        TimeoutError,
        HTTPException,
        json.JSONDecodeError,
        UnicodeDecodeError,
        AttributeError,
        TypeError,
    ):
        # Ollama 연결이나 응답 형식에 문제가 있어도 기록 저장과 기본 응원은 계속됩니다.
        return fallback


def _calculate_max_streak(logs: list[dict[str, Any]]) -> int:
    """기록된 날짜들 중 최장 연속 기록 일수를 계산합니다."""
    parsed_dates: list[date] = []
    for record in logs:
        raw_date = record.get("date")
        if isinstance(raw_date, str):
            try:
                parsed_dates.append(date.fromisoformat(raw_date))
            except ValueError:
                continue

    unique_dates = sorted(set(parsed_dates))
    if not unique_dates:
        return 0

    max_streak = 1
    current_streak = 1
    for index in range(1, len(unique_dates)):
        if (unique_dates[index] - unique_dates[index - 1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    return max_streak


def calculate_social_value_impact(
    logs: list[dict[str, Any]], plaza_bonus_spc: int = 0
) -> dict[str, Any]:
    """누적 SPC와 세부 실천 기록을 생생한 사회적 가치 지표로 환산합니다."""
    summary = calculate_spc_summary(logs, plaza_bonus_spc=plaza_bonus_spc)
    total_spc = summary["total_points"]

    # 실제 기록된 사소한 온기·봉사 횟수도 반영해 더 생동감 있게 환산합니다.
    micro_count = sum(
        1
        for r in logs
        for a in list(r.get("positive_actions", []))
        if a in MICRO_KINDNESS_ACTIONS or a in ("작은 선행", "감사 표현")
    )
    volunteer_count = sum(
        1
        for r in logs
        for a in list(r.get("positive_actions", []))
        if a in VOLUNTEER_TEMPLATE_ACTIONS or a == "봉사·나눔"
    )

    briquettes = round(total_spc / SPC_SOCIAL_VALUE_RATES["briquette_spc_unit"], 1)
    community_warmth = round(
        total_spc * SPC_SOCIAL_VALUE_RATES["community_warmth_multiplier"], 1
    )
    positive_hours = round(
        (total_spc * SPC_SOCIAL_VALUE_RATES["positive_minutes_per_spc"]) / 60.0
        + volunteer_count * 1.5,
        1,
    )
    micro_smiles = micro_count + round(total_spc / 45)

    if total_spc == 0:
        narrative = (
            "첫 기록을 남기면 나의 사소한 인사와 봉사 실천이 세상에 전하는 온기 가치로 환산됩니다."
        )
    else:
        narrative = (
            f"지금까지 차곡차곡 쌓은 {total_spc:,} SPC는 전달된 따뜻한 연탄 {briquettes:,.1f}장, "
            f"유기동물·이웃 돌봄 온기 {positive_hours:,.1f}시간, "
            f"세상을 밝힌 사소한 인사와 미소 {micro_smiles:,}회의 가치와 맞닿아 있어요."
        )

    return {
        "total_spc": total_spc,
        "level": summary["level"],
        "briquettes": briquettes,
        "community_warmth": community_warmth,
        "positive_hours": positive_hours,
        "micro_smiles": micro_smiles,
        "narrative": narrative,
    }


def evaluate_positive_badges(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """누적 기록과 실천 횟수를 바탕으로 비경쟁 포지티브 배지 획득 상태를 계산합니다."""
    total_days = len(logs)
    max_streak = _calculate_max_streak(logs)
    all_weights = _all_known_action_weights()
    action_counts: dict[str, int] = {action: 0 for action in all_weights}

    for record in logs:
        for action in list(record.get("positive_actions", [])):
            if action in action_counts:
                action_counts[action] += 1

    volunteer_keys = set(VOLUNTEER_TEMPLATE_ACTIONS) | {"봉사·나눔", "작은 선행"}
    micro_warmth_keys = {
        "👋 먼저 건네는 밝은 인사·미소",
        "💬 따뜻한 안부·감사·칭찬 한마디",
        "감사 표현",
    }

    badges: list[dict[str, Any]] = []
    for definition in POSITIVE_BADGE_DEFINITIONS:
        metric = definition["metric"]
        if metric == "total_days":
            current = total_days
        elif metric == "max_streak":
            current = max_streak
        elif metric == "category:volunteer":
            current = sum(action_counts.get(name, 0) for name in volunteer_keys)
        elif metric == "category:micro_warmth":
            current = sum(action_counts.get(name, 0) for name in micro_warmth_keys)
        elif metric.startswith("action:"):
            action_name = metric.split(":", 1)[1]
            current = action_counts.get(action_name, 0)
        elif metric.startswith("actions:"):
            names = metric.split(":", 1)[1].split("|")
            current = sum(action_counts.get(name, 0) for name in names)
        else:
            current = 0

        target = int(definition["target"])
        unlocked = current >= target
        progress_pct = min(100, round((current / target) * 100)) if target > 0 else 100
        badges.append(
            {
                "id": definition["id"],
                "icon": definition["icon"],
                "name": definition["name"],
                "description": definition["description"],
                "current": current,
                "target": target,
                "unit": definition["unit"],
                "unlocked": unlocked,
                "progress_pct": progress_pct,
            }
        )
    return badges


def _get_long_term_title(total_spc: int) -> str:
    """장기 누적 SPC에 해당하는 사회적 자본가 성장 칭호를 반환합니다."""
    title = LONG_TERM_SOCIAL_TITLES[0][1]
    for threshold, name in LONG_TERM_SOCIAL_TITLES:
        if total_spc >= threshold:
            title = name
        else:
            break
    return title


def simulate_future_warmth(
    logs: list[dict[str, Any]],
    custom_daily_spc: int | None = None,
    annual_compound_rate: float = 0.04,
) -> dict[str, Any]:
    """현재 온기 누적 속도를 바탕으로 1개월·1년·5년·10년 장기 복리 성장 궤적을 예측합니다."""
    summary = calculate_spc_summary(logs)
    current_total_spc = summary["total_points"]

    if logs:
        observed_daily_spc = max(5, round(current_total_spc / len(logs)))
        has_observed_pace = True
    else:
        observed_daily_spc = 25
        has_observed_pace = False

    daily_spc = (
        max(5, int(custom_daily_spc))
        if custom_daily_spc is not None
        else observed_daily_spc
    )

    def _project_spc_for_days(days: int) -> int:
        # 매일의 실천이 해를 거듭할수록 습관 시너지(연 4% 복리)를 내는 모델입니다.
        years = days / 365.0
        if years <= 1.0:
            added = daily_spc * days
        else:
            annual_base = daily_spc * 365.0
            full_years = int(years)
            rem_fraction = years - full_years
            added = sum(
                annual_base * ((1.0 + annual_compound_rate) ** year_idx)
                for year_idx in range(full_years)
            )
            added += (
                annual_base
                * ((1.0 + annual_compound_rate) ** full_years)
                * rem_fraction
            )
        return round(current_total_spc + added)

    horizons_spec = (
        ("1개월 뒤", 30, "1개월"),
        ("1년 뒤", 365, "1년"),
        ("5년 뒤", 365 * 5, "5년"),
        ("10년 뒤", 365 * 10, "10년"),
    )

    milestones: list[dict[str, Any]] = []
    for label, days, short_label in horizons_spec:
        projected_spc = _project_spc_for_days(days)
        briquettes = round(
            projected_spc / SPC_SOCIAL_VALUE_RATES["briquette_spc_unit"], 1
        )
        positive_hours = round(
            (projected_spc * SPC_SOCIAL_VALUE_RATES["positive_minutes_per_spc"]) / 60.0,
            1,
        )
        community_warmth = round(
            projected_spc * SPC_SOCIAL_VALUE_RATES["community_warmth_multiplier"], 1
        )
        milestones.append(
            {
                "label": label,
                "short_label": short_label,
                "days": days,
                "projected_spc": projected_spc,
                "title": _get_long_term_title(projected_spc),
                "briquettes": briquettes,
                "positive_hours": positive_hours,
                "community_warmth": community_warmth,
            }
        )

    # 1개월 -> 1년 -> 2년 -> ... -> 10년 실제 시간 순서를 엄격히 유지합니다.
    trajectory_rows: list[dict[str, Any]] = []
    chart_points = [("1개월", 30)] + [
        (f"{year}년", year * 365) for year in range(1, 11)
    ]
    ordered_labels = [label for label, _ in chart_points]
    for order_idx, (point_label, days) in enumerate(chart_points):
        proj_spc = _project_spc_for_days(days)
        proj_hours = round(
            (proj_spc * SPC_SOCIAL_VALUE_RATES["positive_minutes_per_spc"]) / 60.0, 1
        )
        trajectory_rows.append(
            {
                "순서": order_idx,
                "시점": point_label,
                "예측 누적 SPC": proj_spc,
                "긍정 에너지(시간)": proj_hours,
            }
        )
    trajectory_df = pd.DataFrame(trajectory_rows)
    trajectory_df["시점"] = pd.Categorical(
        trajectory_df["시점"], categories=ordered_labels, ordered=True
    )

    one_year = milestones[1]
    ten_year = milestones[3]
    headline = (
        f"현재의 온기 속도(하루 평균 {daily_spc:,} SPC)를 유지하면 "
        f"1년 뒤 [{one_year['projected_spc']:,} SPC · {one_year['title']}], "
        f"10년 뒤에는 지역사회에 [{ten_year['positive_hours']:,.0f}시간의 긍정 에너지]를 만든 "
        f"'{ten_year['title']}'로 성장합니다."
    )

    return {
        "current_total_spc": current_total_spc,
        "observed_daily_spc": observed_daily_spc,
        "daily_spc": daily_spc,
        "has_observed_pace": has_observed_pace,
        "annual_compound_rate_pct": round(annual_compound_rate * 100, 1),
        "milestones": milestones,
        "ordered_labels": ordered_labels,
        "trajectory_df": trajectory_df,
        "headline": headline,
    }


def _get_finance_fusion_level(total_value_manwon: float) -> str:
    """현실 자산과 사회적 자본을 합산한 총가치(만원)에 해당하는 융합 레벨을 반환합니다."""
    label = FINANCE_FUSION_LEVELS[0][1]
    for threshold, name in FINANCE_FUSION_LEVELS:
        if total_value_manwon >= threshold:
            label = name
        else:
            break
    return label


def simulate_finance_and_spc_fusion(
    logs: list[dict[str, Any]],
    monthly_income: int = FINANCE_DEFAULTS["monthly_income"],
    housing_cost: int = FINANCE_DEFAULTS["housing_cost"],
    living_cost: int = FINANCE_DEFAULTS["living_cost"],
    variable_cost: int = FINANCE_DEFAULTS["variable_cost"],
    plaza_bonus_spc: int = 0,
) -> dict[str, Any]:
    """월 수입·주거비·생활비·변수 비용과 누적 SPC를 융합해 1개월~10년 자산 흐름을 예측합니다."""
    income = max(0, int(monthly_income))
    housing = max(0, int(housing_cost))
    living = max(0, int(living_cost))
    variable = max(0, int(variable_cost))

    total_expense = housing + living + variable
    monthly_savings = income - total_expense

    housing_ratio = round((housing / income) * 100, 1) if income > 0 else 0.0
    living_ratio = round((living / income) * 100, 1) if income > 0 else 0.0
    variable_ratio = round((variable / income) * 100, 1) if income > 0 else 0.0
    savings_ratio = round((monthly_savings / income) * 100, 1) if income > 0 else 0.0

    # 현재 온기 누적 속도에 비례한 가상의 '사회적 신뢰 우대 금리'(최대 +1.5%p)를 산출합니다.
    spc_summary = calculate_spc_summary(logs, plaza_bonus_spc=plaza_bonus_spc)
    current_spc = spc_summary["total_points"]
    daily_spc = max(10, round(current_spc / len(logs))) if logs else 25
    trust_factor = min(1.0, (daily_spc / 45.0) * 0.7 + min(1.0, current_spc / 3_000) * 0.3)
    base_rate = SPC_FINANCE_FUSION_RATES["base_annual_return"]
    spc_bonus_rate = round(
        SPC_FINANCE_FUSION_RATES["spc_max_bonus_rate"] * max(0.2, trust_factor), 4
    )
    fusion_rate = base_rate + spc_bonus_rate

    def _compound_savings(months: int, annual_rate: float) -> float:
        if monthly_savings <= 0:
            return round(monthly_savings * months, 1)
        monthly_r = annual_rate / 12.0
        if monthly_r <= 0:
            return round(monthly_savings * months, 1)
        fv = monthly_savings * (((1.0 + monthly_r) ** months - 1.0) / monthly_r)
        return round(fv, 1)

    horizons = (
        ("1개월", 1),
        ("2개월", 2),
        ("1년", 12),
        ("2년", 24),
        ("5년", 60),
        ("10년", 120),
    )
    ordered_labels = [label for label, _ in horizons]

    milestones: list[dict[str, Any]] = []
    chart_rows: list[dict[str, Any]] = []

    for label, months in horizons:
        real_assets = _compound_savings(months, base_rate)
        boosted_assets = _compound_savings(months, fusion_rate)
        projected_spc = round(current_spc + daily_spc * (months * 30.4))
        social_incentive = round(
            projected_spc * SPC_FINANCE_FUSION_RATES["spc_incentive_manwon"], 1
        )
        trust_interest_bonus = max(0.0, round(boosted_assets - real_assets, 1))
        spc_capital_value = round(social_incentive + trust_interest_bonus, 1)
        total_fusion_value = round(real_assets + spc_capital_value, 1)

        milestones.append(
            {
                "label": label,
                "months": months,
                "real_assets": real_assets,
                "spc_capital_value": spc_capital_value,
                "total_fusion_value": total_fusion_value,
                "projected_spc": projected_spc,
            }
        )
        chart_rows.append(
            {
                "시점": label,
                "구분": "현실 누적 자산(만원)",
                "금액(만원)": real_assets,
            }
        )
        chart_rows.append(
            {
                "시점": label,
                "구분": "자본+SPC 융합 총가치(만원)",
                "금액(만원)": total_fusion_value,
            }
        )

    trajectory_df = pd.DataFrame(chart_rows)
    trajectory_df["시점"] = pd.Categorical(
        trajectory_df["시점"], categories=ordered_labels, ordered=True
    )

    ten_year = milestones[-1]
    fusion_level = _get_finance_fusion_level(ten_year["total_fusion_value"])

    # 부담 주지 않는 다정한 AI 소비·주거비 밸런스 피드백
    if monthly_savings < 0:
        gentle_feedback = (
            f"이번 달 예상 지출({total_expense:,}만 원)이 수입({income:,}만 원)보다 "
            f"{abs(monthly_savings):,}만 원 정도 앞서가고 있어요. 스스로를 다그치지 마시고, "
            "이번 주에는 배달이나 소소한 구독 중 부담 없는 한두 가지만 잠시 쉬어가며 숨을 골라보는 건 어떨까요?"
        )
    elif housing_ratio >= 35 and living_ratio >= 30:
        gentle_feedback = (
            f"주거비 비중이 {housing_ratio:.0f}%로 묵직한 편인데, 식비·배달 등 기본 생활비({living_ratio:.0f}%)도 "
            "조금 빠른 편이에요. 주거비 예산이 빠듯해질 수 있으니 내일은 따뜻한 집밥이나 홈카페로 "
            "지갑과 마음의 온기를 함께 챙겨보는 건 어떨까요?"
        )
    elif living_ratio >= 35:
        gentle_feedback = (
            f"식비·배달·구독료 등 기본 생활비가 수입의 {living_ratio:.0f}%를 차지하고 있어요. "
            "바쁜 일상에 지쳐 배달이 잦아진 날도 괜찮아요. 이번 주 딱 두 번만 가벼운 집밥으로 바꿔도 "
            "10년 뒤 자산 흐름이 훨씬 든든해진답니다."
        )
    elif housing_ratio >= 35:
        gentle_feedback = (
            f"월 주거비 비중이 {housing_ratio:.0f}%로 다소 높은 환경에서도 매달 {monthly_savings:,}만 원을 "
            "지켜내고 계신 점이 참 대단해요. 변수 비용({variable:,}만 원)만 미리 따로 떼어두면 "
            "마음이 훨씬 편안해질 거예요."
        ).format(variable=variable)
    elif savings_ratio >= 30:
        gentle_feedback = (
            f"수입의 {savings_ratio:.0f}%(월 {monthly_savings:,}만 원)를 차곡차곡 모으는 아주 건강한 밸런스예요! "
            f"여기에 나의 SPC 신뢰 자본(우대 +{spc_bonus_rate * 100:.2f}%p 환산)이 더해져 "
            f"10년 뒤 '{fusion_level}'로 멋지게 성장할 흐름입니다."
        )
    else:
        gentle_feedback = (
            f"매달 {monthly_savings:,}만 원(저축률 {savings_ratio:.0f}%)을 꾸준히 지켜내며 "
            "생활과 저축의 균형을 잘 맞추고 계세요. 오늘의 작은 온기 실천과 함께 "
            "지금의 페이스를 편안하게 이어가 보세요."
        )

    return {
        "monthly_income": income,
        "housing_cost": housing,
        "living_cost": living,
        "variable_cost": variable,
        "total_expense": total_expense,
        "monthly_savings": monthly_savings,
        "housing_ratio": housing_ratio,
        "living_ratio": living_ratio,
        "variable_ratio": variable_ratio,
        "savings_ratio": savings_ratio,
        "base_rate_pct": round(base_rate * 100, 2),
        "spc_bonus_rate_pct": round(spc_bonus_rate * 100, 2),
        "fusion_level": fusion_level,
        "milestones": milestones,
        "ordered_labels": ordered_labels,
        "trajectory_df": trajectory_df,
        "gentle_feedback": gentle_feedback,
    }


def export_logs_to_csv(logs: list[dict[str, Any]]) -> bytes:
    """누적 기록을 엑셀에서도 한글이 깨지지 않는 UTF-8(BOM) CSV 바이트로 변환합니다."""
    if not logs:
        empty_df = pd.DataFrame(
            columns=[
                "날짜",
                "생애주기",
                "현재상태",
                "행복",
                "에너지",
                "포지티브행동",
                "하루SPC",
                "누적SPC",
                "메모",
            ]
        )
        return empty_df.to_csv(index=False).encode("utf-8-sig")

    sorted_logs = sorted(logs, key=lambda item: item.get("date", ""))
    rows: list[dict[str, Any]] = []
    running_spc = 0

    for record in sorted_logs:
        happiness = int(record.get("happiness", 5))
        energy = int(record.get("energy", 5))
        actions = list(record.get("positive_actions", []))
        daily_spc = int(
            record.get(
                "daily_spc",
                calculate_daily_spc(
                    happiness,
                    energy,
                    actions,
                    life_cycle=record.get("life_cycle"),
                    current_status=record.get("current_status"),
                ),
            )
        )
        running_spc += daily_spc
        rows.append(
            {
                "날짜": record.get("date", ""),
                "생애주기": record.get("life_cycle", ""),
                "현재상태": record.get("current_status", ""),
                "소속분야": record.get("field", ""),
                "행복": happiness,
                "에너지": energy,
                "포지티브행동": ", ".join(actions),
                "하루SPC": daily_spc,
                "누적SPC": running_spc,
                "메모": record.get("memo", ""),
            }
        )

    export_df = pd.DataFrame(rows)
    return export_df.to_csv(index=False).encode("utf-8-sig")


def _summarize_recent_trend(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """누적 기록의 평균 행복·에너지와 전반부 대비 후반부 추세를 요약합니다."""
    sorted_logs = sorted(logs, key=lambda item: item.get("date", ""))
    total_days = len(sorted_logs)
    avg_happiness = round(
        sum(int(r.get("happiness", 5)) for r in sorted_logs) / total_days, 1
    )
    avg_energy = round(
        sum(int(r.get("energy", 5)) for r in sorted_logs) / total_days, 1
    )

    midpoint = max(1, total_days // 2)
    early = sorted_logs[:midpoint]
    recent = sorted_logs[midpoint:] or sorted_logs
    early_happiness = sum(int(r.get("happiness", 5)) for r in early) / len(early)
    recent_happiness = sum(int(r.get("happiness", 5)) for r in recent) / len(recent)
    delta = round(recent_happiness - early_happiness, 1)

    if delta >= 0.4:
        trend_label = f"최근 후반부 행복도가 전반부보다 +{delta:.1f}점 높아지며 따뜻한 상승 흐름을 보이고 있어요"
    elif delta <= -0.4:
        trend_label = f"최근 후반부 행복도가 전반부보다 {delta:.1f}점 내려가 잠시 숨 고르기가 필요한 시기예요"
    else:
        trend_label = "전반부와 후반부 모두 흔들림 없이 안정적인 온기를 유지하고 있어요"

    recent_memos = [
        str(r.get("memo", "")).strip()
        for r in sorted_logs[-5:]
        if str(r.get("memo", "")).strip()
    ]
    return {
        "total_days": total_days,
        "avg_happiness": avg_happiness,
        "avg_energy": avg_energy,
        "delta": delta,
        "trend_label": trend_label,
        "recent_memos": recent_memos,
    }


def _build_fallback_coaching_report(
    logs: list[dict[str, Any]],
    life_cycle: str,
    current_status: str,
    summary: dict[str, Any],
    compass: dict[str, Any],
    trend: dict[str, Any],
) -> str:
    """Ollama가 오프라인일 때도 누적 통계를 정교하게 반영한 코칭 편지를 생성합니다."""
    recommended = get_recommended_actions(life_cycle, current_status)
    recommended_text = ", ".join(recommended) if recommended else "작은 선행"
    max_streak = _calculate_max_streak(logs)

    if compass.get("has_enough_data"):
        best_action = compass["best_action"]
        lift = compass["happiness_lift_pct"]
        prob = compass["high_happiness_prob"]
        expected = compass["expected_index"]
        pattern_paragraph = (
            f"특히 데이터 속에서 가장 반짝인 습관은 '{best_action}'이었어요. "
            f"이 행동을 실천하신 날에는 평소보다 행복도가 평균 {lift:+.1f}% 변화했고, "
            f"높은 행복감(7점 이상)을 느낀 확률이 {prob}%(기대 온기 지수 {expected:.1f}점)에 달했습니다."
        )
        next_step = (
            f"앞으로의 한 주는 {life_cycle} · {current_status} 시기에 잘 어울리는 "
            f"'{best_action}'을 주 3회 이상 가볍게 이어가 보시고, "
            f"여유가 되는 날에는 맞춤 추천 행동({recommended_text})도 한 가지 곁들여 보세요."
        )
    else:
        pattern_paragraph = (
            f"아직 {trend['total_days']}일의 소중한 첫걸음을 모으는 단계이지만, "
            f"평균 행복도 {trend['avg_happiness']:.1f}점·에너지 {trend['avg_energy']:.1f}점으로 "
            "나만의 리듬을 만들어 가고 계세요."
        )
        next_step = (
            f"앞으로 3일 이상 꾸준히 기록이 쌓이면 더 정밀한 행복 확률을 분석해 드릴 수 있어요. "
            f"오늘은 {life_cycle} · {current_status} 맞춤 행동인 '{recommended_text}' 중 "
            "부담 없는 하나부터 실천해 보세요."
        )

    return (
        f"안녕하세요, {life_cycle} · {current_status}의 하루를 성실히 살아내고 계신 나에게 ONGI가 편지를 보냅니다.\n\n"
        f"지난 {trend['total_days']}일 동안 총 {summary['total_points']:,} SPC(현재 '{summary['level']}' 레벨, 최장 {max_streak}일 연속 기록)를 "
        f"차곡차곡 쌓아 오셨어요. 전체 평균 행복도는 {trend['avg_happiness']:.1f}/10점, 에너지는 {trend['avg_energy']:.1f}/10점이며, "
        f"{trend['trend_label']}.\n\n"
        f"{pattern_paragraph}\n\n"
        f"{next_step} 누군가와 비교하지 않아도 괜찮아요. 어제의 나보다 조금 더 다정한 오늘의 실천이 가장 큰 성장입니다."
    )


# =========================================================================
# [3~4개월 차 슬롯 A - RAG 연동 후크(Hook)]
# 추후 심리학 회복 가이드, 지역 봉사기관(예: 강남구 가족센터·자원봉사센터) 문서를
# 벡터 DB(Chroma/FAISS)에 인덱싱한 뒤, 이 함수에서 유사도 검색 결과를 반환하도록
# 연결하면 AI 심층 리포트와 AI 온기 파트너 채팅 프롬프트에 자동 주입됩니다.
# =========================================================================
def retrieve_rag_context(
    query: str,
    life_cycle: str = "",
    current_status: str = "",
    field: str = "",
) -> str:
    """외부 심리·지역 봉사 지식 베이스에서 맞춤 컨텍스트를 검색하는 RAG 연결 슬롯입니다."""
    hints: list[str] = []
    if field == "공직/공공기관":
        hints.append(
            "공공·공직 회복 가이드: 성과가 외부로 드러나지 않아도 원칙을 지킨 하루를 스스로 인정하는 '자기 승인 루틴'이 번아웃 예방에 효과적입니다."
        )
    if any(k in query for k in ("봉사", "나눔", "연탄", "유기견", "급식", "지역")):
        hints.append(
            "지역 봉사 연계 팁: 1365 자원봉사포털 및 거주지 가족센터(예: 강남구 가족센터)에서 주말 2시간 단위 생활 봉사를 가볍게 시작할 수 있습니다."
        )
    if any(k in query for k in ("지쳐", "힘들", "번아웃", "불안", "비교", "스트레스")):
        hints.append(
            "긍정심리 회복 가이드: 타인과의 상향 비교가 올라올 때는 5분 산책과 '오늘 내가 통제한 작은 행동 1가지' 기록이 정서 안정에 도움을 줍니다."
        )
    if not hints:
        hints.append(
            f"맞춤 성장 팁({life_cycle or '전 세대'} · {current_status or '일상'}): "
            "거창한 목표보다 매일 반복 가능한 사소한 인사·감사 1회가 장기 행복지수를 가장 안정적으로 높입니다."
        )
    return "\n".join(f"- {item}" for item in hints)


# =========================================================================
# [5개월 차 슬롯 - 멀티 에이전트 선제적 판단]
# 추후 LangGraph 기반 멀티 에이전트(감정 감지 -> 행동 설계 -> 회고 코치)로
# 확장할 때, 이 함수의 반환값을 그래프의 진입 상태(State)와 분기 조건으로 연결합니다.
# =========================================================================
def evaluate_proactive_agent_nudge(
    logs: list[dict[str, Any]],
    life_cycle: str = "",
    current_status: str = "",
    field: str = "",
) -> dict[str, Any]:
    """최근 행복·에너지 저하를 감지해 AI가 먼저 이전 행복 행동을 역제안할지 판단합니다."""
    if len(logs) < 3:
        return {"should_nudge": False, "message": "", "suggested_action": ""}

    sorted_logs = sorted(logs, key=lambda item: item.get("date", ""))
    recent_three = sorted_logs[-3:]
    recent_happiness = sum(int(r.get("happiness", 5)) for r in recent_three) / len(
        recent_three
    )
    recent_energy = sum(int(r.get("energy", 5)) for r in recent_three) / len(
        recent_three
    )
    latest_happiness = int(sorted_logs[-1].get("happiness", 5))

    compass = analyze_happiness_compass(
        logs, life_cycle=life_cycle, current_status=current_status, field=field
    )
    best_action = (
        compass["best_action"]
        if compass.get("has_enough_data")
        else "👋 먼저 건네는 밝은 인사·미소"
    )

    if latest_happiness <= 5 or recent_happiness < 6.2 or recent_energy < 5.8:
        message = (
            f"최근 3일 평균 행복도({recent_happiness:.1f}점)나 에너지({recent_energy:.1f}점)가 "
            f"평소보다 살짝 처져 있어요. 과거 기록에서 기분을 가장 잘 끌어올려 주었던 "
            f"**'{best_action}'**을 오늘 10분만 가볍게 시도해 보시는 건 어떨까요?"
        )
        return {
            "should_nudge": True,
            "message": message,
            "suggested_action": best_action,
            "recent_happiness": round(recent_happiness, 1),
            "recent_energy": round(recent_energy, 1),
        }

    return {
        "should_nudge": False,
        "message": (
            f"최근 3일 평균 행복도 {recent_happiness:.1f}점으로 안정적인 온기를 유지 중이에요! "
            f"오늘도 '{best_action}'으로 기분 좋은 리듬을 이어가 보세요."
        ),
        "suggested_action": best_action,
        "recent_happiness": round(recent_happiness, 1),
        "recent_energy": round(recent_energy, 1),
    }


def generate_deep_coaching_report(
    logs: list[dict[str, Any]],
    life_cycle: str,
    current_status: str,
    field: str = "",
    model_name: str = OLLAMA_MODEL_NAME,
) -> tuple[str, str]:
    """누적 데이터 통계(Mini-RAG 컨텍스트)를 바탕으로 AI 월간 온기 심층 코칭 편지를 생성합니다.

    Returns:
        (report_text, source_label): 리포트 본문과 생성 출처('Ollama AI' 또는 '데이터 통계 코칭')
    """
    if not logs:
        return (
            "아직 분석할 온기 기록이 없어요. 오늘의 마음을 먼저 기록하거나 "
            "사이드바의 '최근 30일 샘플 데이터 채우기'로 심층 코칭 리포트를 체험해 보세요.",
            "안내",
        )

    summary = calculate_spc_summary(logs)
    compass = analyze_happiness_compass(
        logs, life_cycle=life_cycle, current_status=current_status, field=field
    )
    trend = _summarize_recent_trend(logs)
    recommended = get_recommended_actions(life_cycle, current_status, field)
    fallback_report = _build_fallback_coaching_report(
        logs, life_cycle, current_status, summary, compass, trend
    )

    compass_context = (
        f"- 행복 확률 1위 행동: {compass['best_action']} "
        f"(실천 {compass['action_count']}회, 행복 상승률 {compass['happiness_lift_pct']:+.1f}%, "
        f"고행복 달성 확률 {compass['high_happiness_prob']}%, 기대 온기 지수 {compass['expected_index']:.1f}/100)\n"
        if compass.get("has_enough_data")
        else "- 아직 3일 미만 기록이라 행동별 확률 분석 준비 중\n"
    )
    memo_context = (
        "\n".join(f"  * {memo}" for memo in trend["recent_memos"])
        if trend["recent_memos"]
        else "  * 최근 메모 없음"
    )
    rag_context = retrieve_rag_context(
        query=f"{life_cycle} {current_status} {field} 봉사 회복",
        life_cycle=life_cycle,
        current_status=current_status,
        field=field,
    )

    prompt = (
        "당신은 'ONGI'의 따뜻한 AI 심리·습관 성장 코치입니다. "
        "타인과의 비교, 경쟁, 평가, 의료적 진단 없이 아래 사용자의 누적 데이터 컨텍스트를 근거로 "
        "한국어로 다정하고 구체적인 3문단 분량의 '월간 온기 코칭 편지'를 작성하세요.\n"
        "반드시 아래 실제 수치를 자연스럽게 인용하고, 마지막 문단에는 다음 주에 실천할 구체적인 포지티브 스텝을 제안하세요.\n\n"
        f"[사용자 프로필]\n"
        f"- 생애 주기: {life_cycle}\n"
        f"- 현재 상태: {current_status}\n"
        f"- 소속 분야: {field}\n"
        f"- 생애 주기 맞춤 추천 행동: {', '.join(recommended) or '없음'}\n\n"
        f"[누적 온기 통계 컨텍스트]\n"
        f"- 누적 기록 일수: {trend['total_days']}일 (최장 {_calculate_max_streak(logs)}일 연속)\n"
        f"- 현재 온기 티어: {summary['level']} (누적 {summary['total_points']:,} SPC, Lv.{summary['daily_level']})\n"
        f"- 평균 행복도: {trend['avg_happiness']}/10, 평균 에너지: {trend['avg_energy']}/10\n"
        f"- 추세 요약: {trend['trend_label']}\n"
        f"{compass_context}"
        f"- 최근 감정 메모:\n{memo_context}\n\n"
        f"[RAG 참고 지식]\n{rag_context}\n"
    )

    request_body = json.dumps(
        {"model": model_name, "prompt": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=OLLAMA_REPORT_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
        report = result.get("response", "").strip()
        if report:
            return report, f"Ollama ({model_name})"
        return fallback_report, "데이터 통계 맞춤 코칭"
    except (
        HTTPError,
        URLError,
        TimeoutError,
        HTTPException,
        json.JSONDecodeError,
        UnicodeDecodeError,
        AttributeError,
        TypeError,
    ):
        return fallback_report, "데이터 통계 맞춤 코칭 (오프라인)"


def _build_fallback_chat_reply(
    user_message: str,
    logs: list[dict[str, Any]],
    life_cycle: str,
    current_status: str,
    field: str,
    summary: dict[str, Any],
    compass: dict[str, Any],
    finance_context: dict[str, Any] | None = None,
) -> str:
    """Ollama가 꺼져 있어도 사용자 질문 키워드와 누적 통계·자산 밸런스를 조합해 다정한 맞춤 답변을 생성합니다."""
    message = user_message.strip()
    special = get_field_special_action(field)
    recommended = get_recommended_actions(life_cycle, current_status, field)
    top_rec = recommended[0] if recommended else "👋 먼저 건네는 밝은 인사·미소"

    if compass.get("has_enough_data"):
        best_action = compass["best_action"]
        lift = compass["happiness_lift_pct"]
        prob = compass["high_happiness_prob"]
        data_insight = (
            f"최근 {compass['total_days']}일 기록을 보면 **'{best_action}'**을 실천한 날 "
            f"행복도가 평균 **{lift:+.1f}%** 변화했고, 고행복 확률이 **{prob}%**였어요."
        )
    else:
        best_action = top_rec
        data_insight = (
            f"지금은 **{summary['level']}** ({summary['total_points']:,} SPC)로 "
            f"나만의 온기를 차곡차곡 쌓아가는 중이에요."
        )

    if finance_context and any(
        k in message
        for k in ("돈", "월세", "주거", "지출", "소비", "배달", "식비", "저축", "자산", "가계부", "월급", "예산")
    ):
        ten_year = finance_context["milestones"][-1]
        return (
            f"현재 가계 밸런스를 조심스럽게 함께 살펴봤어요.\n\n"
            f"{finance_context['gentle_feedback']}\n\n"
            f"지금의 흐름에 나의 SPC 신뢰 자본이 더해지면 10년 뒤에는 "
            f"**현실 자산 {ten_year['real_assets']:,.0f}만 원 + 사회적 자본 {ten_year['spc_capital_value']:,.0f}만 원 = "
            f"총 {ten_year['total_fusion_value']:,.0f}만 원({finance_context['fusion_level']})**의 "
            "든든한 기반이 만들어져요. 무리하지 말고 내일의 작은 온기부터 챙겨봐요."
        )

    if any(k in message for k in ("지쳐", "피곤", "번아웃", "힘들", "스트레스", "무기력", "우울")):
        field_empathy = (
            f"특히 **{field}** 환경에서는 겉으로 잘 드러나지 않는 에너지가 많이 쓰이기 쉬워요. "
            if field
            else ""
        )
        return (
            f"오늘 많이 애쓰셨네요. {field_empathy}잠시 속도를 늦추고 숨을 고르는 것만으로도 충분해요.\n\n"
            f"{data_insight} 오늘은 큰 목표 대신, 부담 없는 5분짜리 **'{best_action}'**이나 "
            "따뜻한 물 한 잔으로 나 자신을 먼저 다독여 주는 건 어떨까요?"
        )

    if any(k in message for k in ("비교", "불안", "걱정", "뒤처", "조급", "고민", "진로")):
        return (
            f"남들과 나를 비교하게 될 때는 마음이 참 작아지곤 하죠. "
            f"하지만 ONGI가 기록한 **{life_cycle} · {current_status}**의 여정 속에서 "
            f"이미 **{summary['total_points']:,} SPC('{summary['level']}' 레벨)**라는 단단한 온기를 쌓아 오셨어요.\n\n"
            f"{data_insight} 오늘은 타인의 속도가 아니라 어제의 나보다 한 걸음 다정한 **'{best_action}'**에 집중해 봐요."
        )

    if any(k in message for k in ("직장", "업무", "공직", "일", "상사", "동료", "공부", "학교")):
        special_tip = (
            f"**{field}** 분야의 **'{special['action']}'**처럼 보이지 않는 곳에서의 성실함도 "
            "분명 큰 사회적 온기로 쌓이고 있어요."
            if special
            else "오늘 맡은 자리에서 묵묵히 해낸 작은 성실함도 분명 값진 온기예요."
        )
        return (
            f"일과 역할 속에서 마음을 지키는 건 결코 쉬운 일이 아니에요. {special_tip}\n\n"
            f"{data_insight} 퇴근이나 일과 후에 **'{best_action}'**으로 마음의 환기를 챙겨 보시면 "
            "내일의 에너지가 훨씬 부드럽게 회복될 거예요."
        )

    if any(k in message for k in ("추천", "뭐 할", "어떻게", "습관", "계획", "팁", "알려")):
        return (
            f"현재 **{life_cycle} · {current_status} · {field}** 프로필과 누적 기록을 함께 살펴봤어요!\n\n"
            f"{data_insight}\n"
            f"오늘 가장 추천하는 포지티브 스텝은 **'{best_action}'**이고, "
            f"여유가 된다면 **'{top_rec}'**도 가볍게 곁들여 보세요. 작은 실천 하나가 10년 뒤 큰 사회적 자본으로 이어집니다."
        )

    if any(k in message for k in ("행복", "좋아", "뿌듯", "감사", "기뻐", "고마", "성공")):
        return (
            f"와, 오늘 따뜻한 순간을 만나셨군요! 그 기분 좋은 온기를 나눠주셔서 저도 함께 미소가 지어져요.\n\n"
            f"현재 **{summary['level']}** 레벨({summary['total_points']:,} SPC)을 향해 멋지게 걸어가고 계세요. "
            f"{data_insight} 오늘 느낀 그 마음을 '오늘의 온기 기록' 탭에 한 줄로 남겨두시면 나중에 큰 힘이 될 거예요."
        )

    return (
        f"이야기를 들려주셔서 고마워요. **{life_cycle} · {current_status} · {field}**의 하루를 "
        f"묵묵히 걸어가고 있는 지금 이 순간도 충분히 소중해요.\n\n"
        f"{data_insight} 지금 마음에 가장 걸리는 일이나, 오늘 해보고 싶은 작은 실천이 있다면 편하게 더 들려주세요."
    )


def generate_partner_chat_reply(
    user_message: str,
    chat_history: list[dict[str, str]],
    logs: list[dict[str, Any]],
    life_cycle: str,
    current_status: str,
    field: str,
    finance_context: dict[str, Any] | None = None,
    model_name: str = OLLAMA_MODEL_NAME,
) -> tuple[str, str]:
    """사용자 프로필·누적 온기 통계·자산/지출 밸런스를 컨텍스트로 삼아 양방향 AI 파트너 답변을 생성합니다."""
    summary = calculate_spc_summary(logs)
    compass = analyze_happiness_compass(
        logs, life_cycle=life_cycle, current_status=current_status, field=field
    )
    fallback_reply = _build_fallback_chat_reply(
        user_message,
        logs,
        life_cycle,
        current_status,
        field,
        summary,
        compass,
        finance_context=finance_context,
    )

    compass_line = (
        f"행복 확률 1위 행동: {compass['best_action']} "
        f"(행복 상승률 {compass['happiness_lift_pct']:+.1f}%, 고행복 확률 {compass['high_happiness_prob']}%)"
        if compass.get("has_enough_data")
        else "행복 확률 분석: 기록 3일 미만으로 초기 데이터 수집 중"
    )
    finance_line = ""
    if finance_context:
        ten_year = finance_context["milestones"][-1]
        finance_line = (
            f"\n[현재 자산·지출 밸런스]\n"
            f"- 월 수입: {finance_context['monthly_income']:,}만원 / "
            f"주거비: {finance_context['housing_cost']:,}만원({finance_context['housing_ratio']:.0f}%) / "
            f"생활비: {finance_context['living_cost']:,}만원({finance_context['living_ratio']:.0f}%) / "
            f"변수비: {finance_context['variable_cost']:,}만원\n"
            f"- 월 저축 여력: {finance_context['monthly_savings']:+,}만원 (저축률 {finance_context['savings_ratio']:.0f}%)\n"
            f"- 10년 뒤 예측: 현실 자산 {ten_year['real_assets']:,.0f}만원 + SPC 신뢰 자본 {ten_year['spc_capital_value']:,.0f}만원 "
            f"= 총 {ten_year['total_fusion_value']:,.0f}만원 ({finance_context['fusion_level']})\n"
        )

    recent_turns = "\n".join(
        f"{'사용자' if m['role'] == 'user' else 'ONGI'}: {m['content']}"
        for m in chat_history[-6:]
    )
    rag_context = retrieve_rag_context(
        query=user_message,
        life_cycle=life_cycle,
        current_status=current_status,
        field=field,
    )

    prompt = (
        "당신은 'ONGI'의 다정한 AI 친구이자 페이스메이커입니다. "
        "타인과의 비교나 훈계, 다그침, 의료적 진단 없이 사용자의 감정에 먼저 공감하고, "
        "아래 사용자의 프로필·누적 온기 통계·자산/지출 밸런스·참고 지식을 자연스럽게 활용해 한국어로 3~5문장 내외의 따뜻한 답변을 건네세요.\n\n"
        f"[사용자 프로필 및 누적 온기 상태]\n"
        f"- 생애 주기 / 상태 / 분야: {life_cycle} / {current_status} / {field}\n"
        f"- 현재 온기 티어: {summary['level']} (누적 {summary['total_points']:,} SPC, Lv.{summary['daily_level']}, 총 {len(logs)}일 기록)\n"
        f"- {compass_line}\n"
        f"{finance_line}\n"
        f"[RAG 참고 지식]\n{rag_context}\n\n"
        f"[최근 대화]\n{recent_turns or '없음'}\n\n"
        f"[사용자의 새 메시지]\n{user_message}\n\n"
        "ONGI의 답변:"
    )

    request_body = json.dumps(
        {"model": model_name, "prompt": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=OLLAMA_REPORT_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
        reply = result.get("response", "").strip()
        if reply:
            return reply, f"Ollama ({model_name})"
        return fallback_reply, "온기 데이터 맞춤 응답"
    except (
        HTTPError,
        URLError,
        TimeoutError,
        HTTPException,
        json.JSONDecodeError,
        UnicodeDecodeError,
        AttributeError,
        TypeError,
    ):
        return fallback_reply, "온기 데이터 맞춤 응답 (오프라인)"


def _default_plaza_state() -> dict[str, Any]:
    """온기 광장 초기 샘플 게시글과 공동체 온기 상태를 생성합니다."""
    posts = [
        {
            "id": item["id"],
            "author_badge": item["author_badge"],
            "tier_tag": item.get("tier_tag", "🌱 브론즈 IV · Lv.1"),
            "action_tag": item["action_tag"],
            "content": item["content"],
            "created_at": item["created_at"],
            "warmth_spc": int(item["warmth_spc"]),
            "reactions": dict(item["reactions"]),
        }
        for item in DEFAULT_PLAZA_POSTS
    ]
    return {
        "posts": posts,
        "user_bonus_spc": 0,
        "community_extra_spc": 0,
    }


def _write_plaza_state(state: dict[str, Any]) -> None:
    """온기 광장 상태를 로컬 JSON 파일에 저장합니다."""
    with PLAZA_FILE.open("w", encoding="utf-8") as plaza_file:
        json.dump(state, plaza_file, ensure_ascii=False, indent=2)


def load_plaza_state() -> dict[str, Any]:
    """온기 광장 게시글과 리액션 보너스 SPC 상태를 불러옵니다."""
    if not PLAZA_FILE.exists():
        initial_state = _default_plaza_state()
        _write_plaza_state(initial_state)
        return initial_state

    try:
        with PLAZA_FILE.open("r", encoding="utf-8") as plaza_file:
            data = json.load(plaza_file)
    except (json.JSONDecodeError, OSError):
        initial_state = _default_plaza_state()
        _write_plaza_state(initial_state)
        return initial_state

    if not isinstance(data, dict) or not isinstance(data.get("posts"), list):
        initial_state = _default_plaza_state()
        _write_plaza_state(initial_state)
        return initial_state

    data.setdefault("user_bonus_spc", 0)
    data.setdefault("community_extra_spc", 0)
    seed_tags = {item["id"]: item.get("tier_tag", "🌱 브론즈 IV · Lv.1") for item in DEFAULT_PLAZA_POSTS}
    for post in data["posts"]:
        if not post.get("tier_tag"):
            post["tier_tag"] = seed_tags.get(post.get("id", ""), "🌿 실버 IV · Lv.12")
    return data


def add_plaza_post(
    life_cycle: str,
    current_status: str,
    field: str,
    action_tag: str,
    content: str,
    tier_tag: str = "🌱 브론즈 IV · Lv.1",
) -> dict[str, Any]:
    """나의 포지티브 한 줄을 온기 광장에 공유하고 공동체 온기와 개인 보너스를 적립합니다."""
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("공유할 포지티브 한 줄을 입력해 주세요.")

    state = load_plaza_state()
    now_label = datetime.now().strftime("오늘 %H:%M")
    new_post = {
        "id": f"user_{int(datetime.now().timestamp() * 1000)}",
        "author_badge": f"{life_cycle} · {current_status} · {field}",
        "tier_tag": tier_tag,
        "action_tag": action_tag,
        "content": cleaned,
        "created_at": now_label,
        "warmth_spc": PLAZA_POST_SPC_BONUS,
        "reactions": {"warmth": 1, "invisible_effort": 0, "join": 0},
    }
    state["posts"].insert(0, new_post)
    state["user_bonus_spc"] = int(state.get("user_bonus_spc", 0)) + PLAZA_POST_SPC_BONUS
    state["community_extra_spc"] = (
        int(state.get("community_extra_spc", 0)) + PLAZA_POST_SPC_BONUS
    )
    _write_plaza_state(state)
    return state


def react_to_plaza_post(post_id: str, reaction_key: str) -> dict[str, Any]:
    """이웃 게시글에 리액션을 남기고 게시글 온기, 나의 SPC(+3), 공동체 온도계를 함께 올립니다."""
    state = load_plaza_state()
    updated = False
    for post in state["posts"]:
        if post.get("id") == post_id:
            reactions = post.setdefault(
                "reactions", {"warmth": 0, "invisible_effort": 0, "join": 0}
            )
            reactions[reaction_key] = int(reactions.get(reaction_key, 0)) + 1
            post["warmth_spc"] = (
                int(post.get("warmth_spc", 0)) + PLAZA_REACTION_SPC_BONUS
            )
            updated = True
            break

    if updated:
        state["user_bonus_spc"] = (
            int(state.get("user_bonus_spc", 0)) + PLAZA_REACTION_SPC_BONUS
        )
        state["community_extra_spc"] = (
            int(state.get("community_extra_spc", 0)) + PLAZA_REACTION_SPC_BONUS
        )
        _write_plaza_state(state)
    return state


def calculate_community_thermometer(
    logs: list[dict[str, Any]], plaza_state: dict[str, Any]
) -> dict[str, Any]:
    """대한민국 공동체 누적 SPC와 우리 사회 온기 온도계 수치를 계산합니다."""
    user_bonus_spc = int(plaza_state.get("user_bonus_spc", 0))
    user_summary = calculate_spc_summary(logs, plaza_bonus_spc=user_bonus_spc)
    community_extra_spc = int(plaza_state.get("community_extra_spc", 0))

    # 개인 로그 SPC + 광장 활동으로 발생한 추가 온기를 공동체 누적치에 합산합니다.
    user_log_only_spc = max(0, user_summary["total_points"] - user_bonus_spc)
    total_community_spc = COMMUNITY_BASE_SPC + community_extra_spc + user_log_only_spc
    progress = min(1.0, total_community_spc / COMMUNITY_GOAL_SPC)
    temperature = round(progress * 100.0, 1)

    return {
        "total_community_spc": total_community_spc,
        "goal_spc": COMMUNITY_GOAL_SPC,
        "progress": progress,
        "temperature": temperature,
        "user_bonus_spc": user_bonus_spc,
        "post_count": len(plaza_state.get("posts", [])),
    }
