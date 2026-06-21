"""
Acoustic Simulator - Standalone Portable App (ONNX 경량 버전)
PyTorch 없이 onnxruntime만으로 동작하는 통합 패키지용 진입점.
"""
import streamlit as st

st.set_page_config(
    page_title="Acoustic Cavity Simulator",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 메인 페이지 (환영 화면)
st.markdown("""
# 🔊 음향 공동 시뮬레이터 & 형상 추정기

**음향 기주공명 기반 용기 형상 역추적 연구 도구**

---

### 📌 사용 방법
왼쪽 사이드바에서 원하는 기능을 선택하세요.

| 페이지 | 기능 |
|---|---|
| **📐 음향 시뮬레이터** | 물채움 시뮬레이션 → 공명 주파수 추적 → CSV 내보내기 |
| **🧠 형상 추정 (AI)** | CSV 업로드 → ONNX 모델로 용기 형상 역추적 |

### 🔄 워크플로우
1. **시뮬레이터**에서 형상을 설정하고 물채움 시뮬레이션 실행
2. 스펙트럼 CSV를 다운로드
3. **형상 추정**에서 CSV를 업로드하여 AI가 형상을 맞추는지 검증
""")

st.divider()
st.caption("Acoustic Cavity Simulator v2.0 — Standalone Portable Edition (ONNX Runtime)")
