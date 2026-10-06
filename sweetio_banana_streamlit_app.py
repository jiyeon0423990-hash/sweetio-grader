import re
import streamlit as st

st.set_page_config(page_title="스위티오 바나나 광고 자동 채점", page_icon="🍌", layout="wide")

# -----------------------------
# 1. 문항/채점 기준 설정
# -----------------------------
QUESTIONS = {
    "q1": {
        "title": "문항1. 광고에 등장하는 대상은 무엇인가요?",
        "model_answers": [
            "스위티오 바나나와 광고 모델 안유진"
        ],
        "required_groups": [
            ["스위티오 바나나", "스위티오", "dole 스위티오", "돌 스위티오"],
        ],
        "optional_groups": [
            ["안유진", "광고 모델", "모델"]
        ],
        "wrong_patterns": [
            ["dole만", "돌만"],
        ],
        "rule_note": "핵심 광고 대상인 '스위티오 바나나'를 파악하면 통과. 안유진까지 쓰면 완전 답안."
    },
    "q2": {
        "title": "문항2. 광고에서 선택된 내용은 무엇인가요?",
        "model_answers": [
            "해발 500m 재배, 높은 당도, 긴 재배 기간, 170년 노하우 등 바나나의 우수한 품질을 보여 주는 내용"
        ],
        "required_any": [
            ["해발 500m", "500m", "고지대", "높은 곳에서 재배"],
            ["높은 당도", "당도가 높", "달다", "단맛"],
            ["긴 재배 기간", "오랜 재배 기간", "오래 재배"],
            ["170년 노하우", "170년", "오랜 노하우", "축적된 노하우"],
        ],
        "wrong_only_groups": [
            ["가격", "비싸다", "싸다", "다른 바나나와 비교", "타 바나나 비교", "경쟁 제품 비교"]
        ],
        "rule_note": "선택된 구체적 내용 중 1개 이상이 의미상 드러나면 통과. 숫자 자체보다 의미를 우선."
    },
    "q3": {
        "title": "문항3. 광고에서 배제된 내용은 무엇인가요?",
        "model_answers": [
            "바나나의 가격과 다른 바나나와의 구체적인 비교 내용"
        ],
        "required_any": [
            ["가격", "얼마", "판매가", "비용"],
            ["다른 바나나와의 비교", "다른 바나나와 비교", "타 바나나 비교", "경쟁 제품 비교", "구체적 비교"]
        ],
        "wrong_only_groups": [
            ["해발 500m", "500m", "높은 당도", "당도", "긴 재배 기간", "170년 노하우", "170년"]
        ],
        "rule_note": "가격 또는 타 바나나와의 구체적 비교가 빠졌다는 의미가 드러나면 통과."
    },
    "q4": {
        "title": "문항4. 제작자의 관점은 무엇인가요?",
        "model_answers": [
            "스위티오 바나나는 품질이 검증된 프리미엄 바나나이며, 라벨은 그 우수한 품질을 보증해 주는 표시라고 본다."
        ],
        "viewpoint_groups": [
            ["프리미엄", "고급", "특별한 바나나", "일반 바나나보다 우수", "우수한 바나나"],
            ["품질이 검증", "품질이 좋", "품질이 뛰어", "좋은 품질", "우수한 품질"],
            ["라벨이 품질을 보증", "라벨은 품질 보증", "라벨로 품질을 보증", "라벨이 신뢰", "라벨은 신뢰"]
        ],
        "intent_only_patterns": [
            ["구매", "사게", "사도록", "구매하도록", "구매 유도", "설득하려"],
        ],
        "rule_note": "대상을 '어떻게 보는가'가 드러나야 통과. 구매 유도만 쓰면 오답. 관점+의도가 함께 있어도 관점이 명확하면 통과."
    },
    "q5": {
        "title": "문항5. 제작자의 의도는 무엇인가요?",
        "model_answers": [
            "소비자가 스위티오 바나나를 품질이 좋은 프리미엄 상품으로 인식하게 하여 구매하도록 설득하려는 것이다.",
            "소비자가 스위티오 바나나를 일반 바나나와 차별화된 고품질·프리미엄 상품으로 인식하게 하려는 것이다."
        ],
        "intent_groups": [
            ["구매", "사게", "사도록", "구매하도록", "구매 유도", "사고 싶게"],
            ["프리미엄으로 인식", "고급으로 인식", "좋은 바나나라고 생각", "품질이 좋다고 생각", "특별한 바나나라고 생각"],
            ["차별화", "다른 바나나와 다르게", "일반 바나나와 다르게", "특별하게 인식"],
            ["품질을 강조", "우수성을 강조", "좋은 품질을 알리"]
        ],
        "viewpoint_only_patterns": [
            ["프리미엄 바나나이다", "고급 바나나이다", "품질이 좋다", "품질이 뛰어나다", "특별한 바나나이다"]
        ],
        "rule_note": "소비자에게 어떤 인식·행동을 유도하려는지가 드러나야 통과. 제품 특성 진술만 있으면 오답."
    }
}

# 향후 '선택지가 있는 문항'을 추가할 때 사용할 구조 예시.
# 현재 스위티오 바나나 1~5번은 선택지가 없는 문항이므로 실제로는 비워 둔다.
OPTION_MODEL_ANSWERS = {
    # "q6": {
    #     "A": ["선택지 A의 모범 답안 1", "선택지 A의 모범 답안 2"],
    #     "B": ["선택지 B의 모범 답안 1"]
    # }
}


# -----------------------------
# 2. 텍스트 정규화 및 의미 판정
# -----------------------------
def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\"'“”‘’.,!?·:/()\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: str, expressions) -> bool:
    t = normalize(text)
    return any(normalize(expr) in t for expr in expressions)


def matches_group(text: str, group) -> bool:
    return contains_any(text, group)


def count_matching_groups(text: str, groups) -> int:
    return sum(1 for group in groups if matches_group(text, group))


# -----------------------------
# 3. 문항별 자동 채점 로직
# -----------------------------
def grade_q1(answer: str):
    if not answer.strip():
        return False, "답안이 비어 있습니다."

    has_product = any(matches_group(answer, g) for g in QUESTIONS["q1"]["required_groups"])
    has_model = any(matches_group(answer, g) for g in QUESTIONS["q1"]["optional_groups"])

    if has_product and has_model:
        return True, "핵심 대상인 스위티오 바나나와 광고 모델 안유진을 모두 제시했습니다."
    if has_product:
        return True, "핵심 광고 대상인 스위티오 바나나를 정확히 파악했습니다. 안유진까지 쓰면 더 완전한 답안입니다."
    return False, "광고의 핵심 대상인 '스위티오 바나나'가 드러나야 합니다."


def grade_q2(answer: str):
    if not answer.strip():
        return False, "답안이 비어 있습니다."

    correct_count = count_matching_groups(answer, QUESTIONS["q2"]["required_any"])
    wrong_count = count_matching_groups(answer, QUESTIONS["q2"]["wrong_only_groups"])

    # 결론 방향 확인: 선택된 실제 장점을 최소 1개는 포함해야 함
    if correct_count >= 1:
        return True, f"광고에서 실제로 선택된 특징을 {correct_count}개 의미상 정확히 제시했습니다."

    if wrong_count >= 1:
        return False, "가격이나 타 제품 비교는 '선택된 내용'이 아니라 '배제된 내용'입니다."

    return False, "해발 500m 재배, 높은 당도, 긴 재배 기간, 170년 노하우 중 하나 이상의 의미가 드러나야 합니다."


def grade_q3(answer: str):
    if not answer.strip():
        return False, "답안이 비어 있습니다."

    correct_count = count_matching_groups(answer, QUESTIONS["q3"]["required_any"])
    wrong_count = count_matching_groups(answer, QUESTIONS["q3"]["wrong_only_groups"])

    # 결론 방향 확인: 실제 배제 요소가 최소 1개 필요
    if correct_count >= 1:
        return True, "광고에서 배제된 현실적 정보가 의미상 정확히 드러납니다."

    if wrong_count >= 1:
        return False, "해발 500m, 높은 당도, 긴 재배 기간, 170년 노하우는 '배제된 내용'이 아니라 광고가 선택한 내용입니다."

    return False, "가격 또는 다른 바나나와의 구체적 비교가 배제되었다는 의미가 드러나야 합니다."


def grade_q4(answer: str):
    if not answer.strip():
        return False, "답안이 비어 있습니다."

    viewpoint_count = count_matching_groups(answer, QUESTIONS["q4"]["viewpoint_groups"])
    intent_only = count_matching_groups(answer, QUESTIONS["q4"]["intent_only_patterns"]) >= 1

    # 오개념 방지:
    # 구매 유도라는 '의도'만 있고 대상에 대한 평가/관점이 없으면 오답.
    if viewpoint_count >= 1:
        if intent_only:
            return True, "제작자의 관점이 분명하며, 의도 표현이 함께 포함되어 있어도 관점이 확인되므로 인정합니다."
        return True, "스위티오를 고품질·프리미엄 상품으로 보는 제작자의 관점이 드러납니다."

    if intent_only:
        return False, "이 답안은 '구매하게 하려는 의도'만 설명합니다. 문항4에서는 제작자가 스위티오를 어떤 상품으로 보는지가 드러나야 합니다."

    return False, "스위티오를 품질이 좋은/검증된/프리미엄 상품으로 본다는 의미가 필요합니다."


def grade_q5(answer: str):
    if not answer.strip():
        return False, "답안이 비어 있습니다."

    intent_count = count_matching_groups(answer, QUESTIONS["q5"]["intent_groups"])
    viewpoint_only = count_matching_groups(answer, QUESTIONS["q5"]["viewpoint_only_patterns"]) >= 1

    # 결론 방향 확인:
    # 단순한 제품 특성 진술이 아니라 소비자의 인식/행동을 유도하려는 목적이 드러나야 함.
    if intent_count >= 1:
        return True, "소비자의 인식 또는 구매 행동을 유도하려는 제작자의 의도가 드러납니다."

    if viewpoint_only:
        return False, "이 답안은 제품을 어떻게 보는지에 관한 '관점'에 머뭅니다. 소비자에게 무엇을 인식시키거나 하게 하려는지가 필요합니다."

    return False, "프리미엄·고품질 이미지 형성, 차별화, 품질 강조, 구매 유도 중 하나 이상의 의도가 의미상 드러나야 합니다."


GRADERS = {
    "q1": grade_q1,
    "q2": grade_q2,
    "q3": grade_q3,
    "q4": grade_q4,
    "q5": grade_q5,
}


# -----------------------------
# 4. 공통 채점 함수
# -----------------------------
def grade_answer(question_id: str, answer: str):
    passed, feedback = GRADERS[question_id](answer)
    return {
        "question_id": question_id,
        "passed": passed,
        "result": "통과" if passed else "재검토",
        "feedback": feedback,
        "model_answers": QUESTIONS[question_id]["model_answers"],
        "rule_note": QUESTIONS[question_id]["rule_note"],
    }


# -----------------------------
# 5. Streamlit UI
# -----------------------------
st.title("🍌 스위티오 바나나 광고 학습활동 자동 채점")
st.caption(
    "문자열 완전 일치가 아니라, 학습지에서 허용한 의미가 답안에 드러나는지를 중심으로 판정합니다."
)

with st.expander("채점 원칙 보기"):
    st.markdown(
        """
- **용어가 없어도 의미가 같으면 인정**합니다.
- 학생이 특정 개념을 설명할 때에는 **그 개념의 핵심 특성**이 실제 답안에 드러나야 합니다.
- **선택된 내용 ↔ 배제된 내용**, **관점 ↔ 의도**를 뒤바꾸면 오답 처리합니다.
- 단, 관점 문항에 의도가 함께 적힌 경우처럼 **정답 핵심이 분명하면서 부가 설명이 섞인 경우는 인정**합니다.
- 문항이 요구하는 **결론 방향**이 명확히 드러나야 통과합니다.
- 현재 1~5번은 선택지가 없는 문항입니다. 선택형 문항을 추가할 경우 `OPTION_MODEL_ANSWERS`에 선택지별 모범 답안을 등록하도록 설계했습니다.
        """
    )

answers = {}

for qid, q in QUESTIONS.items():
    st.subheader(q["title"])
    answers[qid] = st.text_area(
        "학생 답안",
        key=f"answer_{qid}",
        height=90,
        placeholder="학생 답안을 입력하세요."
    )

    if st.button("이 문항 채점", key=f"btn_{qid}"):
        result = grade_answer(qid, answers[qid])

        if result["passed"]:
            st.success(f"✅ {result['result']}")
        else:
            st.error(f"❌ {result['result']}")

        st.write(result["feedback"])

        with st.expander("모범 답안 및 판정 기준"):
            st.markdown("**모범 답안**")
            for i, model in enumerate(result["model_answers"], 1):
                st.write(f"{i}. {model}")
            st.markdown("**판정 기준**")
            st.write(result["rule_note"])

    st.divider()


# -----------------------------
# 6. 전체 채점
# -----------------------------
st.header("전체 채점")

if st.button("1~5번 전체 채점", type="primary"):
    total = 0

    for qid in QUESTIONS:
        result = grade_answer(qid, answers[qid])
        if result["passed"]:
            total += 1
            st.success(f"{QUESTIONS[qid]['title']} → 통과")
        else:
            st.error(f"{QUESTIONS[qid]['title']} → 재검토")
        st.caption(result["feedback"])

    st.metric("통과 문항 수", f"{total} / {len(QUESTIONS)}")


# -----------------------------
# 7. 교사용 테스트 도구
# -----------------------------
with st.expander("교사용 테스트 도구"):
    st.write("경계 답안을 직접 넣어 채점 규칙을 점검할 수 있습니다.")

    test_q = st.selectbox(
        "문항 선택",
        options=list(QUESTIONS.keys()),
        format_func=lambda x: QUESTIONS[x]["title"]
    )
    test_answer = st.text_input("테스트 답안")

    if st.button("테스트 판정"):
        result = grade_answer(test_q, test_answer)
        st.json(result)
