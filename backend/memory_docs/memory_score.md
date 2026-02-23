# Emotion Scoring (Rule-Based) — README

이 문서는 `confidence / intensity / valence / arousal` 점수를 **LLM 자기평가가 아니라 룰 기반(결정론적)**으로 산출하기 위한 기준을 정리합니다.  
목표는 **주간 리포트/증감 알림/히트맵**에서 점수의 **일관성(재현성)**을 확보하는 것입니다.

---

## 1) 입력 데이터(현재 JSONL 스키마)

현재 JSONL(예: `synthetic_emotion_32labels_2560.jsonl`)에는 아래 필드만 존재합니다.

- top-level: `source`, `seed_id`, `relation`, `speaker_text`, `listener_text`, `label`, `scores`, `meta`
- `label`: `id`, `label_ko`, `group`
- `scores`: `confidence`, `intensity`, `valence`, `arousal`
- `meta`: `seed_situation`

이 README는 **(A) 기존 scores를 그대로 쓸 수도 있고**, **(B) 동일한 구조의 scores를 룰로 재계산**할 수도 있게 설계합니다.

---

## 2) 결정: LLM vs 룰 기반

- **분류(label.id / group)**: LLM or 분류기 가능
- **점수(scores)**: 리포트/지표 안정성을 위해 **룰 기반 권장**
  - 같은 문장에 대해 점수가 흔들리면(LLM 자기평가) 주간 리포트의 변화량이 불안정해짐
  - QA/디버깅/재현이 어려움

권장 운영:
- LLM: 감정 라벨 + 근거(evidence) 생성
- 룰: `confidence/intensity/valence/arousal` 산출

---

## 3) 고정 맵(기본값)

아래 맵은 32 감정 `label.id`를 기준으로 기본값을 제공합니다.

### 3.1 valence_map (-1 ~ +1)

```json
{
  "E01_JOY": 0.75,
  "E02_HAPPINESS": 0.90,
  "E03_EXCITEMENT": 0.85,
  "E04_SATISFACTION": 0.70,
  "E05_GRATITUDE": 0.80,
  "E06_PRIDE": 0.75,

  "E07_LOVE": 0.90,
  "E08_AFFECTION": 0.80,
  "E09_FLUTTER": 0.85,
  "E10_CLOSENESS": 0.75,

  "E11_SADNESS": -0.75,
  "E12_DEPRESSED": -0.85,
  "E13_LONELY": -0.80,
  "E14_HURT": -0.85,
  "E15_REGRET": -0.75,
  "E16_GUILT": -0.80,

  "E17_ANGER": -0.90,
  "E18_IRRITATION": -0.80,
  "E19_UNFAIRNESS": -0.85,
  "E20_HATRED": -0.95,
  "E21_CONTEMPT": -0.90,

  "E22_ANXIETY": -0.75,
  "E23_FEAR": -0.85,
  "E24_TENSION": -0.65,
  "E25_PRESSURE": -0.60,

  "E26_SURPRISE": 0.00,
  "E27_EMBARRASSED": -0.35,
  "E28_CONFUSION": -0.20,
  "E29_DISAPPOINTED": -0.70,

  "E30_DISGUST": -0.90,
  "E31_AVERSION": -0.85,

  "E32_NEUTRAL": 0.00
}
```

### 3.2 arousal_map (0 ~ 1)

```json
{
  "E01_JOY": 0.65,
  "E02_HAPPINESS": 0.55,
  "E03_EXCITEMENT": 0.85,
  "E04_SATISFACTION": 0.45,
  "E05_GRATITUDE": 0.40,
  "E06_PRIDE": 0.60,

  "E07_LOVE": 0.55,
  "E08_AFFECTION": 0.45,
  "E09_FLUTTER": 0.75,
  "E10_CLOSENESS": 0.35,

  "E11_SADNESS": 0.35,
  "E12_DEPRESSED": 0.20,
  "E13_LONELY": 0.25,
  "E14_HURT": 0.45,
  "E15_REGRET": 0.40,
  "E16_GUILT": 0.45,

  "E17_ANGER": 0.85,
  "E18_IRRITATION": 0.75,
  "E19_UNFAIRNESS": 0.80,
  "E20_HATRED": 0.80,
  "E21_CONTEMPT": 0.60,

  "E22_ANXIETY": 0.80,
  "E23_FEAR": 0.90,
  "E24_TENSION": 0.75,
  "E25_PRESSURE": 0.65,

  "E26_SURPRISE": 0.85,
  "E27_EMBARRASSED": 0.75,
  "E28_CONFUSION": 0.55,
  "E29_DISAPPOINTED": 0.40,

  "E30_DISGUST": 0.60,
  "E31_AVERSION": 0.55,

  "E32_NEUTRAL": 0.30
}
```

### 3.3 base_intensity_map (0 ~ 1)

```json
{
  "E01_JOY": 0.60,
  "E02_HAPPINESS": 0.65,
  "E03_EXCITEMENT": 0.80,
  "E04_SATISFACTION": 0.55,
  "E05_GRATITUDE": 0.50,
  "E06_PRIDE": 0.60,

  "E07_LOVE": 0.70,
  "E08_AFFECTION": 0.55,
  "E09_FLUTTER": 0.75,
  "E10_CLOSENESS": 0.50,

  "E11_SADNESS": 0.60,
  "E12_DEPRESSED": 0.70,
  "E13_LONELY": 0.60,
  "E14_HURT": 0.75,
  "E15_REGRET": 0.60,
  "E16_GUILT": 0.65,

  "E17_ANGER": 0.85,
  "E18_IRRITATION": 0.75,
  "E19_UNFAIRNESS": 0.80,
  "E20_HATRED": 0.90,
  "E21_CONTEMPT": 0.75,

  "E22_ANXIETY": 0.75,
  "E23_FEAR": 0.85,
  "E24_TENSION": 0.70,
  "E25_PRESSURE": 0.65,

  "E26_SURPRISE": 0.70,
  "E27_EMBARRASSED": 0.70,
  "E28_CONFUSION": 0.55,
  "E29_DISAPPOINTED": 0.65,

  "E30_DISGUST": 0.80,
  "E31_AVERSION": 0.70,

  "E32_NEUTRAL": 0.35
}
```

---

## 4) 룰 기반 보정 규칙(텍스트 신호)

### 4.1 원칙
- 기본값은 위 맵을 사용
- `speaker_text + listener_text`를 합친 텍스트에서 신호를 검출하여 보정
- 최종은 `clamp`로 범위를 제한

### 4.2 신호와 가중치(권장 기본)

#### 강화(+)
- `!` : intensity +0.06 (최대 3개 반영), arousal +0.05
- `?` : arousal +0.04 (최대 3개 반영)
- `ㅋ{2,}` : intensity +0.06 (최대 2회 반영)
- `[ㅠㅜ]{2,}` : intensity +0.08 (최대 2회 반영)
- 강조어(예: `너무/진짜/완전/겁나/개/대박/미친`) : intensity +0.05, arousal +0.03 (최대 3회 반영)
- 비속어(팀 룰에 맞는 리스트 기반): intensity +0.10, arousal +0.05 (각 최대 2회 반영)

#### 완화(-)
- 완화어(예: `좀/약간/그냥/조금/왠지/어느 정도`) : intensity -0.05 (최대 3회 반영)
- 불확실(예: `아마/같아/듯/모르겠/헷갈`) : confidence 중심 -0.10 (최대 2회 반영)

#### 길이 조정
- 너무 짧음(<=10자): intensity -0.05, confidence -0.08
- 충분히 구체적(>=80자): intensity +0.03, confidence +0.05

#### 각성도 감소 신호
- `...` 또는 `…` : arousal -0.04 (매치당)

---

## 5) JS 구현 예시(결정론적)

```js
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

const VALENCE = /* valence_map */;
const AROUSAL_BASE = /* arousal_map */;
const INT_BASE = /* base_intensity_map */;

const RE = {
  exclaim: /!/g,
  question: /\?/g,
  laugh: /ㅋ{2,}/g,
  cry: /[ㅠㅜ]{2,}/g,
  ellipsis: /\.{3,}|…{1,}/g,
  intensifiers: /(너무|진짜|완전|겁나|개|대박|미친)/g,
  mitigators: /(좀|약간|그냥|조금|왠지|어느\s?정도)/g,
  uncertainty: /(아마|같아|듯|모르겠|헷갈)/g
};

// 팀 룰에 맞게 리스트 확장 가능
const SWEAR = /(씨발|ㅅㅂ|좆|존나|병신)/g;

function countMatches(text, re) {
  const m = text.match(re);
  return m ? m.length : 0;
}

export function scoreText(labelId, speakerText, listenerText) {
  const text = `${speakerText ?? ""} ${listenerText ?? ""}`.trim();
  const len = text.length;

  const ex = Math.min(countMatches(text, RE.exclaim), 3);
  const qu = Math.min(countMatches(text, RE.question), 3);
  const laugh = Math.min(countMatches(text, RE.laugh), 2);
  const cry = Math.min(countMatches(text, RE.cry), 2);
  const ints = Math.min(countMatches(text, RE.intensifiers), 3);
  const mits = Math.min(countMatches(text, RE.mitigators), 3);
  const unc = Math.min(countMatches(text, RE.uncertainty), 2);
  const sw = Math.min(countMatches(text, SWEAR), 2);

  // intensity
  let intensity = (INT_BASE[labelId] ?? 0.5)
    + ex * 0.06
    + ints * 0.05
    + sw * 0.10
    + laugh * 0.06
    + cry * 0.08
    - mits * 0.05;

  if (len <= 10) intensity -= 0.05;
  if (len >= 80) intensity += 0.03;
  intensity = clamp(intensity, 0.05, 1.0);

  // arousal
  let arousal = (AROUSAL_BASE[labelId] ?? 0.5)
    + ex * 0.05
    + qu * 0.04
    + ints * 0.03
    + sw * 0.05
    - countMatches(text, RE.ellipsis) * 0.04;

  arousal = clamp(arousal, 0.05, 1.0);

  // valence: label 고정 맵
  const valence = clamp((VALENCE[labelId] ?? 0.0), -1.0, 1.0);

  // confidence: 명확성 기반
  let clarity =
    0.40
    + (ints > 0 ? 0.10 : 0)
    + (ex > 0 ? 0.06 : 0)
    + (sw > 0 ? 0.08 : 0)
    + (cry > 0 || laugh > 0 ? 0.05 : 0)
    - mits * 0.06
    - unc * 0.10;

  if (len <= 10) clarity -= 0.08;
  if (len >= 80) clarity += 0.05;

  clarity = clamp(clarity, 0.0, 1.0);

  // confidence 범위: 0.70~0.97
  const confidence = clamp(0.70 + 0.27 * clarity, 0.70, 0.97);

  return { confidence, intensity, valence, arousal };
}
```

---

## 6) 운영용 임계치(리포트/알림)

권장 기본 (상황에 따라 조정):

- 알림/요약(Top 변화) 집계 포함 조건:
  - `confidence >= 0.78`
  - `intensity >= 0.65`
- 히트맵에는 더 넓게 포함:
  - `confidence >= 0.70` (또는 전부 포함 후 시각적으로 투명도 처리)

---

## 7) 점수 안정성 검증(팀 설득용)

### 7.1 검증 목표
- 동일 입력에 대해 scores가 **항상 동일**하게 나오는지(재현성)
- 특정 감정 그룹에서 intensity/arousal이 직관과 크게 어긋나지 않는지(타당성)
- 리포트 지표(최근 7일 vs 이전 28일)가 점수 흔들림 없이 유지되는지

### 7.2 최소 검증 절차(추천)
1. JSONL 전체에 룰 스코어를 계산하고 `scores`를 교체한 버전 생성
2. 감정별 `intensity/arousal/confidence` 평균/표준편차를 출력
3. 상위 10개 감정의 변화량(최근 vs 이전)을 2회 실행해도 동일한지 확인

---

## 8) 빠른 체크리스트

- [ ] label.id는 반드시 32개 중 하나로 들어오는가?
- [ ] 텍스트 전처리(공백/특수문자) 후에도 동일 결과가 나오는가?
- [ ] confidence 컷(예: 0.78) 적용 시 알림 수가 과도하게 줄지 않는가?
- [ ] 욕설/강조어 사전은 팀 룰에 맞게 관리되는가?

---

## 9) 파일 위치

- 이 README는 프로젝트 루트에 `README.md`로 저장되어야 합니다.