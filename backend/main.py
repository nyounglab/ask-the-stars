"""
FastAPI 백엔드 서버
점성술 자동화 웹 애플리케이션의 메인 서버
"""

import asyncio
import threading
import time
from functools import lru_cache, partial

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from datetime import datetime
import os
import logging
from pathlib import Path


# 구조화 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from astrology_calculator import AstrologyCalculator
from ai_interpreter import AstrologyInterpreter

# FastAPI 앱 생성
app = FastAPI(
    title="점성술 자동화 API",
    description="생년월일시 입력으로 점성술 차트 분석 및 AI 해석 제공",
    version="1.0.0"
)

# CORS 설정
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# 인메모리 Rate Limiter (주기적 정리 포함)
_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()
RATE_LIMIT_MAX = 5  # 최대 요청 수
RATE_LIMIT_WINDOW = 60  # 초 단위 윈도우
_RATE_LIMIT_CLEANUP_THRESHOLD = 500


def _check_rate_limit(client_ip: str) -> bool:
    """IP 기반 rate limit 체크. 초과 시 True 반환. 주기적으로 오래된 IP 정리."""
    now = time.time()
    with _rate_limit_lock:
        # 스토어가 일정 크기 이상이면 오래된 IP 엔트리 정리
        if len(_rate_limit_store) > _RATE_LIMIT_CLEANUP_THRESHOLD:
            stale = [ip for ip, ts in _rate_limit_store.items()
                     if not ts or now - max(ts) > RATE_LIMIT_WINDOW]
            for ip in stale:
                del _rate_limit_store[ip]
        timestamps = _rate_limit_store.get(client_ip, [])
        _rate_limit_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
            return True
        _rate_limit_store[client_ip].append(now)
        return False


# 리버스 프록시 뒤에서 운영 시 True (예: BEHIND_PROXY=true)
_BEHIND_PROXY = os.getenv("BEHIND_PROXY", "false").lower() in ("true", "1", "yes")


def _get_client_ip(req: Request) -> str:
    """클라이언트 IP 추출 (프록시 환경에서만 X-Forwarded-For 신뢰)"""
    if _BEHIND_PROXY:
        forwarded = req.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return req.client.host if req.client else "unknown"


print("CWD:", os.getcwd())
print("DIRS:", os.listdir(".."))



# 정적 파일 서빙 (프론트엔드)
app.mount("/:D", StaticFiles(directory="../frontend", html=True), name=":D")



# Pydantic 검증 에러를 일관된 형식으로 반환
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        messages.append(error.get("msg", "입력값이 올바르지 않습니다"))
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(messages)}
    )


# 요청 모델
class BirthInfoRequest(BaseModel):
    """출생 정보 요청 모델"""
    name: str
    birthdate: str  # YYYY-MM-DD
    birthtime: str  # HH:MM
    birthplace: str

    @field_validator('birthdate')
    @classmethod
    def validate_birthdate(cls, v: str) -> str:
        """생년월일 형식 및 범위 검증"""
        try:
            parsed = datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('생년월일은 YYYY-MM-DD 형식이어야 합니다')
        if parsed.year < 1900:
            raise ValueError('1900년 이후의 날짜를 입력해주세요')
        if parsed > datetime.now():
            raise ValueError('미래 날짜는 입력할 수 없습니다')
        return v

    @field_validator('birthtime')
    @classmethod
    def validate_birthtime(cls, v: str) -> str:
        """출생 시간 형식 검증"""
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('출생 시간은 HH:MM 형식이어야 합니다')

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """이름 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('이름을 입력해주세요')
        stripped = v.strip()
        if len(stripped) > 50:
            raise ValueError('이름은 50자 이내로 입력해주세요')
        return stripped

    @field_validator('birthplace')
    @classmethod
    def validate_birthplace(cls, v: str) -> str:
        """출생 장소 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('출생 장소를 입력해주세요')
        stripped = v.strip()
        if len(stripped) > 100:
            raise ValueError('출생 장소는 100자 이내로 입력해주세요')
        return stripped


# 응답 모델
class AnalysisResponse(BaseModel):
    """분석 결과 응답 모델"""
    success: bool
    chart_data: str | None = None
    interpretation: str | None = None
    error: str | None = None


# 계산기 초기화 (인터프리터는 lazy init - API 키 없이도 서버 시작 가능)
calculator = AstrologyCalculator()
_interpreter = None
_interpreter_lock = threading.Lock()


@lru_cache(maxsize=128)
def _cached_calculate_chart(birth_date: str, birth_time: str, birth_place: str) -> tuple:
    """차트 계산 결과 캐싱 (동일 입력 → 동일 결과)"""
    result = calculator.calculate_chart(birth_date, birth_time, birth_place)
    # lru_cache는 dict를 캐싱할 수 없으므로 tuple로 변환
    return (result["success"], result.get("chart_data"), result.get("error"))


def get_interpreter() -> AstrologyInterpreter:
    """AstrologyInterpreter를 lazy initialization으로 반환 (thread-safe)"""
    global _interpreter
    if _interpreter is None:
        with _interpreter_lock:
            if _interpreter is None:
                _interpreter = AstrologyInterpreter()
    return _interpreter


@app.get("/")
async def root():
    """루트 → 프론트엔드로 리다이렉트"""
    return RedirectResponse(url="/:D/")

@app.get("/health")
async def health_check():
    """서버 상태 체크"""
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_chart(request: BirthInfoRequest, req: Request):
    """
    점성술 차트 분석 엔드포인트

    사용자의 생년월일시 정보를 받아:
    1. Swiss Ephemeris로 차트 데이터 계산
    2. Gemini API로 해석 생성
    3. 결과 반환
    """
    # Rate limit 체크
    client_ip = _get_client_ip(req)
    if _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )

    try:
        loop = asyncio.get_event_loop()

        # 1. Swiss Ephemeris로 차트 계산 (블로킹 → 스레드풀 위임, 캐싱 적용)
        safe_name = request.name.replace('\n', ' ').replace('\r', ' ')
        logger.info("차트 계산 시작: %s", safe_name)
        success, chart_data, calc_error = await loop.run_in_executor(
            None,
            partial(
                _cached_calculate_chart,
                birth_date=request.birthdate,
                birth_time=request.birthtime,
                birth_place=request.birthplace,
            ),
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"차트 계산 실패: {calc_error}"
            )
        logger.info("차트 계산 완료")

        # 2. Gemini API로 해석 생성 (블로킹 → 스레드풀 위임)
        logger.info("AI 해석 시작")
        interpretation_result = await loop.run_in_executor(
            None,
            partial(
                get_interpreter().interpret_chart,
                chart_data=chart_data,
                user_name=request.name,
            ),
        )

        if interpretation_result["error"]:
            raise HTTPException(
                status_code=500,
                detail=f"AI 해석 실패: {interpretation_result['error']}"
            )

        interpretation = interpretation_result["interpretation"]
        logger.info("AI 해석 완료")

        # 3. 결과 반환
        return AnalysisResponse(
            success=True,
            chart_data=chart_data,
            interpretation=interpretation,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("분석 중 에러 발생: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="분석 중 에러가 발생했습니다. 입력 정보를 확인하고 다시 시도해주세요."
        )


# 개발 서버 실행 (직접 실행 시)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
