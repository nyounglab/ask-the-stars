# 점성술 자동화 웹 애플리케이션

<img src="frontend/og.png" width="400"/>

생년월일시를 입력하면 **Swiss Ephemeris**로 정확한 점성술 차트를 계산하고, **Google Gemini AI**가 전생까지 포함한 상세한 해석을 제공하는 웹 서비스입니다.

## 주요 기능

- 생년월일, 시간, 장소만 입력하면 자동 분석
- Swiss Ephemeris로 천체 위치 직접 계산 (출생지 시간대 자동 변환)
- Whole Sign 하우스 시스템 사용
- Google Gemini API를 통한 한국어 해석
- 노드(North/South Node)를 통한 카르마적 관점 제시
- 반응형 디자인

## 기술 스택

- **백엔드**: Python, FastAPI
- **프론트엔드**: HTML, CSS, JavaScript
- **천문 계산**: Swiss Ephemeris (pyswisseph)
- **시간대 처리**: timezonefinder, pytz
- **위치 처리**: Geopy (Nominatim)
- **AI**: Google Gemini API (google-generativeai)

## 설치 방법

### 1. Python 가상환경 생성 및 활성화

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 3. Google API 키 발급

[Google AI Studio](https://aistudio.google.com/app/apikey)에서 API 키를 발급받습니다.

## 실행 방법

```bash
GOOGLE_API_KEY={your-api-key} venv/bin/python -m uvicorn main:app \
  --host 0.0.0.0 --port 8000 --reload \
  --app-dir backend
```

브라우저에서 `http://localhost:8000`을 방문하세요.

## 사용 방법

1. **정보 입력**: 이름, 생년월일, 출생 시간, 출생 장소를 입력합니다.
   - 출생 시간을 정확히 모르면 12:00으로 입력하세요.
   - 출생 장소는 영문으로 입력하세요 (예: Seoul, South Korea).

2. **분석 시작**: "운명 분석하기" 버튼을 클릭합니다.

3. **대기**: 약 10-20초 정도 소요됩니다.
   - Swiss Ephemeris로 차트 계산
   - Gemini AI가 해석 작성

4. **결과 확인**:
   - 원본 차트 데이터 (접을 수 있음)
   - AI의 상세한 해석 (전생 포함)

## 프로젝트 구조

```
astrology-app/
├── backend/
│   ├── main.py                # FastAPI 서버
│   ├── astrology_calculator.py # Swiss Ephemeris 차트 계산
│   ├── ai_interpreter.py      # Gemini API 해석
│   └── requirements.txt       # Python 의존성
├── frontend/
│   ├── index.html             # 메인 페이지
│   ├── styles.css             # 스타일
│   └── script.js              # 프론트엔드 로직
├── .gitignore
└── README.md
```

## 테스트

### 차트 계산 단독 테스트

```bash
cd backend
python astrology_calculator.py
```

### AI 인터프리터 단독 테스트

```bash
cd backend
python ai_interpreter.py
```

### API 엔드포인트 테스트

서버 실행 후:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트",
    "birthdate": "1990-01-01",
    "birthtime": "12:00",
    "birthplace": "Seoul, South Korea"
  }'
```

## 주의사항

### API 비용

Gemini API는 무료 티어가 있지만, 사용량에 따라 과금될 수 있습니다.

### 점성술은 참고용

점성술은 재미와 통찰을 위한 도구입니다. AI가 생성한 해석이며, 중요한 인생 결정의 근거로 사용하지 마세요.

## 문제 해결

### 서버가 시작되지 않을 때

- Python 가상환경이 활성화되었는지 확인
- 의존성이 모두 설치되었는지 확인: `pip install -r requirements.txt`
- `GOOGLE_API_KEY` 환경 변수가 설정되었는지 확인

### CORS 에러

`backend/main.py`의 CORS 설정을 확인하세요.

## 향후 개선 계획

- [ ] 어스펙트(행성 간 각도) 계산 추가
- [ ] 역행(Retrograde) 표시
- [ ] 사용자 인증 및 이력 저장
- [ ] 데이터베이스 추가 (캐싱)

## 라이선스

개인 사용을 위한 프로젝트입니다.


## GCP Cloud Run 배포

### 1. 사전 준비

**Secret Manager에 API 키 등록**

```bash
gcloud secrets create GOOGLE_API_KEY --replication-policy="automatic"
echo -n "your-api-key-here" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-
```

**서비스 계정 생성 및 권한 부여**

```bash
# 서비스 계정 생성
gcloud iam service-accounts create ${SA_NAME} --display-name="Astrology App SA"

# 권한 부여
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

**Cloud Build 기본 서비스 계정 권한 부여** (Compute Engine 기본 SA)

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.admin"
```

### 2. 배포

소스 코드에서 직접 빌드하여 배포합니다 (`--source .` 방식).

```bash
gcloud run deploy ${RUN_NAME} \
  --source . \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-secrets GOOGLE_API_KEY=${SECRET_NAME}:${SECRET_VERSION} \
  --service-account=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
  --clear-base-image
```

| 변수 | 설명 |
|------|------|
| `RUN_NAME` | Cloud Run 서비스 이름 |
| `REGION` | 배포 리전 (예: `asia-northeast3`) |
| `SECRET_NAME` | Secret Manager에 등록한 시크릿 이름 |
| `SECRET_VERSION` | 시크릿 버전 (예: `latest` 또는 `1`) |
| `SA_NAME` | 생성한 서비스 계정 이름 |
| `PROJECT_ID` | GCP 프로젝트 ID |