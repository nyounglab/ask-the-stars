"""
Swiss Ephemeris를 사용한 점성술 차트 계산 모듈
생년월일시와 위치로 정확한 천체 위치를 계산합니다.
"""

import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import pytz


class AstrologyCalculator:
    """점성술 차트 계산 클래스"""

    # 행성 이름 (한국어)
    PLANETS = {
        swe.SUN: "태양",
        swe.MOON: "달",
        swe.MERCURY: "수성",
        swe.VENUS: "금성",
        swe.MARS: "화성",
        swe.JUPITER: "목성",
        swe.SATURN: "토성",
        swe.URANUS: "천왕성",
        swe.NEPTUNE: "해왕성",
        swe.PLUTO: "명왕성",
        swe.CHIRON: "키론",
    }

    # 별자리 이름 (한국어)
    SIGNS = [
        "양자리", "황소자리", "쌍둥이자리", "게자리",
        "사자자리", "처녀자리", "천칭자리", "전갈자리",
        "사수자리", "염소자리", "물병자리", "물고기자리"
    ]

    # 하우스 의미 (간단)
    HOUSE_MEANINGS = {
        1: "자아, 외모, 인상",
        2: "재산, 가치관",
        3: "소통, 형제자매, 단거리 여행",
        4: "가정, 뿌리, 부모",
        5: "사랑, 창조성, 자녀",
        6: "건강, 일상, 봉사",
        7: "파트너십, 결혼, 타인",
        8: "변화, 공유 자원, 성",
        9: "철학, 장거리 여행, 고등교육",
        10: "경력, 명성, 사회적 지위",
        11: "친구, 희망, 공동체",
        12: "잠재의식, 영성, 고독"
    }

    # 한글 도시명 → 영문 매핑 (주요 도시)
    CITY_MAP = {
        "서울": "Seoul, South Korea",
        "부산": "Busan, South Korea",
        "인천": "Incheon, South Korea",
        "대구": "Daegu, South Korea",
        "대전": "Daejeon, South Korea",
        "광주": "Gwangju, South Korea",
        "울산": "Ulsan, South Korea",
        "수원": "Suwon, South Korea",
        "성남": "Seongnam, South Korea",
        "고양": "Goyang, South Korea",
        "용인": "Yongin, South Korea",
        "창원": "Changwon, South Korea",
        "청주": "Cheongju, South Korea",
        "전주": "Jeonju, South Korea",
        "천안": "Cheonan, South Korea",
        "제주": "Jeju, South Korea",
        "포항": "Pohang, South Korea",
        "김해": "Gimhae, South Korea",
        "평택": "Pyeongtaek, South Korea",
        "안산": "Ansan, South Korea",
        "안양": "Anyang, South Korea",
        "남양주": "Namyangju, South Korea",
        "화성": "Hwaseong, South Korea",
        "의정부": "Uijeongbu, South Korea",
        "파주": "Paju, South Korea",
        "김포": "Gimpo, South Korea",
        "광명": "Gwangmyeong, South Korea",
        "군포": "Gunpo, South Korea",
        "하남": "Hanam, South Korea",
        "오산": "Osan, South Korea",
        "이천": "Icheon, South Korea",
        "양주": "Yangju, South Korea",
        "구리": "Guri, South Korea",
        "안성": "Anseong, South Korea",
        "포천": "Pocheon, South Korea",
        "의왕": "Uiwang, South Korea",
        "여주": "Yeoju, South Korea",
        "동두천": "Dongducheon, South Korea",
        "과천": "Gwacheon, South Korea",
        "춘천": "Chuncheon, South Korea",
        "원주": "Wonju, South Korea",
        "강릉": "Gangneung, South Korea",
        "속초": "Sokcho, South Korea",
        "동해": "Donghae, South Korea",
        "삼척": "Samcheok, South Korea",
        "태백": "Taebaek, South Korea",
        "충주": "Chungju, South Korea",
        "제천": "Jecheon, South Korea",
        "공주": "Gongju, South Korea",
        "보령": "Boryeong, South Korea",
        "아산": "Asan, South Korea",
        "서산": "Seosan, South Korea",
        "논산": "Nonsan, South Korea",
        "당진": "Dangjin, South Korea",
        "군산": "Gunsan, South Korea",
        "익산": "Iksan, South Korea",
        "정읍": "Jeongeup, South Korea",
        "남원": "Namwon, South Korea",
        "김제": "Gimje, South Korea",
        "목포": "Mokpo, South Korea",
        "여수": "Yeosu, South Korea",
        "순천": "Suncheon, South Korea",
        "나주": "Naju, South Korea",
        "광양": "Gwangyang, South Korea",
        "경주": "Gyeongju, South Korea",
        "김천": "Gimcheon, South Korea",
        "안동": "Andong, South Korea",
        "구미": "Gumi, South Korea",
        "영주": "Yeongju, South Korea",
        "영천": "Yeongcheon, South Korea",
        "상주": "Sangju, South Korea",
        "문경": "Mungyeong, South Korea",
        "경산": "Gyeongsan, South Korea",
        "진주": "Jinju, South Korea",
        "통영": "Tongyeong, South Korea",
        "사천": "Sacheon, South Korea",
        "밀양": "Miryang, South Korea",
        "거제": "Geoje, South Korea",
        "양산": "Yangsan, South Korea",
        "세종": "Sejong, South Korea",
    }

    def __init__(self):
        """Swiss Ephemeris 초기화"""
        # Ephemeris 파일 경로 설정 (기본 경로 사용)
        swe.set_ephe_path(None)
        self.geolocator = Nominatim(user_agent="astrology_app")
        self.timezone_finder = TimezoneFinder()

    def _normalize_location(self, location: str) -> str:
        """한글 도시명을 영문으로 변환 (매핑에 있으면 변환, 없으면 원본 유지)"""
        normalized = location.strip()
        # 딕셔너리에서 정확히 매칭되는 한글 도시명 확인
        if normalized in self.CITY_MAP:
            return self.CITY_MAP[normalized]
        # "서울특별시", "부산광역시" 등에서 행정구역 접미사 제거
        for suffix in ["특별시", "광역시", "특별자치시", "특별자치도"]:
            stripped = normalized.replace(suffix, "").strip()
            if stripped in self.CITY_MAP:
                return self.CITY_MAP[stripped]
        return normalized

    def get_coordinates(self, location: str) -> tuple[float, float]:
        """
        위치 이름으로 위도/경도 찾기 (한글 도시명 지원)

        Args:
            location: 도시명 (예: "서울", "Seoul, South Korea")

        Returns:
            (위도, 경도) 튜플

        Raises:
            ValueError: 위치를 찾을 수 없을 때
        """
        normalized = self._normalize_location(location)
        try:
            location_data = self.geolocator.geocode(normalized, timeout=10)
            if location_data:
                return (location_data.latitude, location_data.longitude)
            raise ValueError(f"'{location}'의 위치를 찾을 수 없습니다. 도시명을 확인해주세요. (예: 서울, Seoul)")
        except ValueError:
            raise
        except Exception:
            raise ValueError("위치 검색에 실패했습니다. 잠시 후 다시 시도해주세요.")

    def calculate_chart(
        self,
        birth_date: str,  # YYYY-MM-DD
        birth_time: str,  # HH:MM
        birth_place: str
    ) -> dict:
        """
        점성술 차트 계산

        Args:
            birth_date: 생년월일 (YYYY-MM-DD)
            birth_time: 출생 시간 (HH:MM)
            birth_place: 출생 장소

        Returns:
            차트 데이터 딕셔너리
        """
        try:
            # 1. 위치 좌표 획득
            lat, lon = self.get_coordinates(birth_place)

            # 2. 날짜/시간 파싱 → 출생지 시간대 기반으로 UTC 변환
            dt_str = f"{birth_date} {birth_time}"
            dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

            tz_name = self.timezone_finder.timezone_at(lat=lat, lng=lon)
            if tz_name:
                local_tz = pytz.timezone(tz_name)
                dt_local = local_tz.localize(dt_naive)
                dt_utc = dt_local.astimezone(pytz.utc)
            else:
                dt_utc = pytz.utc.localize(dt_naive)

            julian_day = self._datetime_to_julian(dt_utc)

            # 3. 행성 위치 계산
            planets_data = self._calculate_planets(julian_day)

            # 4. 하우스 계산 (Whole Sign)
            houses_data = self._calculate_houses(julian_day, lat, lon)

            # 5. 행성-하우스 매핑 (Whole Sign)
            asc_sign_idx = self.SIGNS.index(houses_data['ascendant']['sign'])
            self._assign_planets_to_houses(planets_data, asc_sign_idx)

            # 6. 노드 계산 (카르마/전생)
            nodes_data = self._calculate_nodes(julian_day)

            # 7. 어스펙트 계산
            aspects_data = self._calculate_aspects(planets_data)

            # 8. 파트 오브 포춘 계산
            pof_data = self._calculate_part_of_fortune(
                planets_data, houses_data, julian_day
            )

            # 9. 포맷팅
            formatted_data = self._format_chart_data(
                planets_data,
                houses_data,
                nodes_data,
                aspects_data,
                pof_data,
                birth_place,
                lat,
                lon
            )

            return {
                "success": True,
                "chart_data": formatted_data,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "chart_data": None,
                "error": f"차트 계산 오류: {str(e)}"
            }

    def _datetime_to_julian(self, dt: datetime) -> float:
        """날짜/시간을 율리우스일로 변환"""
        return swe.julday(
            dt.year,
            dt.month,
            dt.day,
            dt.hour + dt.minute / 60.0
        )

    def _calculate_planets(self, julian_day: float) -> dict:
        """행성 위치 계산"""
        planets_data = {}

        for planet_id, planet_name in self.PLANETS.items():
            # 행성 위치 계산
            try:
                position, retro = swe.calc_ut(julian_day, planet_id)
            except swe.Error:
                # 소행성(키론 등)은 ephemeris 파일이 없으면 건너뜀
                continue

            # 황도 경도 (0-360도)
            longitude = position[0]

            # 역행 여부 (일일 이동 속도가 음수면 역행)
            is_retrograde = position[3] < 0

            # 별자리 (0-11)
            sign_num = int(longitude / 30)
            sign_name = self.SIGNS[sign_num]

            # 별자리 내 도수 (0-30도)
            degree_in_sign = longitude % 30

            retro_mark = " (R)" if is_retrograde else ""
            planets_data[planet_name] = {
                "sign": sign_name,
                "degree": round(degree_in_sign, 2),
                "longitude": round(longitude, 2),
                "retrograde": is_retrograde,
                "formatted": f"{sign_name} {int(degree_in_sign)}°{int((degree_in_sign % 1) * 60)}'{retro_mark}"
            }

        return planets_data

    def _calculate_houses(
        self,
        julian_day: float,
        lat: float,
        lon: float
    ) -> dict:
        """하우스 계산 (Whole Sign 시스템)"""
        # Placidus로 먼저 계산하여 상승점 획득
        houses, ascmc = swe.houses(julian_day, lat, lon, b'P')

        # 상승점 (Ascendant)
        asc_longitude = ascmc[0]
        asc_sign_num = int(asc_longitude / 30)
        asc_degree = asc_longitude % 30

        # 중천 (MC - Midheaven)
        mc_longitude = ascmc[1]
        mc_sign_num = int(mc_longitude / 30)
        mc_degree = mc_longitude % 30

        # Whole Sign 하우스: 상승 별자리가 1하우스, 순서대로
        house_cusps = {}
        for i in range(12):
            house_num = i + 1
            house_sign_num = (asc_sign_num + i) % 12
            house_cusps[house_num] = {
                "sign": self.SIGNS[house_sign_num],
                "meaning": self.HOUSE_MEANINGS[house_num]
            }

        return {
            "ascendant": {
                "sign": self.SIGNS[asc_sign_num],
                "degree": round(asc_degree, 2),
                "formatted": f"{self.SIGNS[asc_sign_num]} {int(asc_degree)}°{int((asc_degree % 1) * 60)}'"
            },
            "midheaven": {
                "sign": self.SIGNS[mc_sign_num],
                "degree": round(mc_degree, 2),
                "formatted": f"{self.SIGNS[mc_sign_num]} {int(mc_degree)}°{int((mc_degree % 1) * 60)}'"
            },
            "houses": house_cusps
        }

    def _assign_planets_to_houses(self, planets_data: dict, asc_sign_num: int):
        """Whole Sign 시스템에서 각 행성의 하우스를 결정"""
        for planet_name, data in planets_data.items():
            planet_sign_num = int(data['longitude'] / 30)
            house_num = ((planet_sign_num - asc_sign_num) % 12) + 1
            data['house'] = house_num

    # 어스펙트 정의: (정확한 각도, 기본 허용 오차)
    ASPECTS = {
        "합(Conjunction)": (0, 8),
        "육합(Sextile)": (60, 6),
        "사각(Square)": (90, 7),
        "삼합(Trine)": (120, 8),
        "충(Opposition)": (180, 8),
        "퀸컨스(Quincunx)": (150, 3),
    }

    # 발광체(태양/달)는 넓은 오브, 외행성은 좁은 오브
    _LUMINARIES = {"태양", "달"}
    _INNER_PLANETS = {"수성", "금성", "화성"}

    def _get_effective_orb(self, planet1: str, planet2: str, base_orb: float) -> float:
        """행성 쌍에 따라 오브 조정 (발광체 +2, 외행성 -2)"""
        if planet1 in self._LUMINARIES or planet2 in self._LUMINARIES:
            return base_orb + 2
        if planet1 not in self._INNER_PLANETS and planet2 not in self._INNER_PLANETS:
            return max(base_orb - 2, 1)
        return base_orb

    def _calculate_aspects(self, planets_data: dict) -> list:
        """행성 간 어스펙트(각도 관계) 계산 (행성별 오브 차등 적용)"""
        aspects = []
        planet_list = list(planets_data.items())

        for i, (name1, data1) in enumerate(planet_list):
            for name2, data2 in planet_list[i + 1:]:
                angle = abs(data1['longitude'] - data2['longitude'])
                if angle > 180:
                    angle = 360 - angle

                for aspect_name, (exact_angle, base_orb) in self.ASPECTS.items():
                    effective_orb = self._get_effective_orb(name1, name2, base_orb)
                    diff = abs(angle - exact_angle)
                    if diff <= effective_orb:
                        aspects.append({
                            'planet1': name1,
                            'planet2': name2,
                            'aspect': aspect_name,
                            'angle': round(angle, 2),
                            'orb': round(diff, 2),
                        })
        return aspects

    def _calculate_part_of_fortune(
        self, planets_data: dict, houses_data: dict, julian_day: float
    ) -> dict:
        """파트 오브 포춘 계산 (주간: ASC + Moon - Sun, 야간: ASC + Sun - Moon)"""
        sun_lon = planets_data["태양"]["longitude"]
        moon_lon = planets_data["달"]["longitude"]
        # ASC 경도 복원: sign 시작 + degree
        asc_sign_idx = self.SIGNS.index(houses_data["ascendant"]["sign"])
        asc_lon = asc_sign_idx * 30 + houses_data["ascendant"]["degree"]

        # 주간/야간 판별: 태양이 ASC~DSC 사이(지평선 위)에 있으면 주간
        dsc_lon = (asc_lon + 180) % 360
        if asc_lon < dsc_lon:
            is_daytime = asc_lon <= sun_lon < dsc_lon
        else:
            is_daytime = sun_lon >= asc_lon or sun_lon < dsc_lon

        if is_daytime:
            pof_lon = (asc_lon + moon_lon - sun_lon) % 360
        else:
            pof_lon = (asc_lon + sun_lon - moon_lon) % 360

        sign_num = int(pof_lon / 30)
        degree_in_sign = pof_lon % 30

        return {
            "longitude": round(pof_lon, 2),
            "sign": self.SIGNS[sign_num],
            "degree": round(degree_in_sign, 2),
            "formatted": f"{self.SIGNS[sign_num]} {int(degree_in_sign)}°{int((degree_in_sign % 1) * 60)}'",
            "meaning": "행운과 물질적 풍요의 지점",
        }

    def _calculate_nodes(self, julian_day: float) -> dict:
        """노드 계산 (North/South Node - 카르마)"""
        # True Node 계산
        north_node, _ = swe.calc_ut(julian_day, swe.TRUE_NODE)
        nn_longitude = north_node[0]
        nn_sign_num = int(nn_longitude / 30)
        nn_degree = nn_longitude % 30

        # South Node는 North Node + 180도
        sn_longitude = (nn_longitude + 180) % 360
        sn_sign_num = int(sn_longitude / 30)
        sn_degree = sn_longitude % 30

        return {
            "north_node": {
                "sign": self.SIGNS[nn_sign_num],
                "degree": round(nn_degree, 2),
                "formatted": f"{self.SIGNS[nn_sign_num]} {int(nn_degree)}°{int((nn_degree % 1) * 60)}'",
                "meaning": "이번 생의 목표, 발전해야 할 방향"
            },
            "south_node": {
                "sign": self.SIGNS[sn_sign_num],
                "degree": round(sn_degree, 2),
                "formatted": f"{self.SIGNS[sn_sign_num]} {int(sn_degree)}°{int((sn_degree % 1) * 60)}'",
                "meaning": "전생의 재능, 극복해야 할 패턴"
            }
        }

    def _format_chart_data(
        self,
        planets: dict,
        houses: dict,
        nodes: dict,
        aspects: list,
        pof: dict,
        location: str,
        lat: float,
        lon: float
    ) -> str:
        """차트 데이터를 텍스트로 포맷팅"""
        output = []

        output.append("=" * 60)
        output.append("📊 출생 차트 데이터")
        output.append("=" * 60)

        # 위치 정보
        output.append(f"\n📍 출생 장소: {location}")
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        output.append(f"   좌표: {abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}")

        # 상승/중천
        output.append(f"\n🌅 상승 (Ascendant): {houses['ascendant']['formatted']}")
        output.append(f"🏔️  중천 (Midheaven): {houses['midheaven']['formatted']}")

        # 행성 (하우스 매핑 + 역행 포함)
        output.append("\n" + "=" * 60)
        output.append("🌟 행성 배치")
        output.append("=" * 60)
        for planet_name, data in planets.items():
            house_info = f"(제{data['house']}하우스)" if 'house' in data else ""
            output.append(f"{planet_name:8s}: {data['formatted']:24s} {house_info}")

        # 어스펙트
        if aspects:
            output.append("\n" + "=" * 60)
            output.append("🔗 어스펙트 (행성 간 각도)")
            output.append("=" * 60)
            for asp in aspects:
                output.append(
                    f"{asp['planet1']} {asp['aspect']} {asp['planet2']}"
                    f"  (오브: {asp['orb']}°)"
                )

        # 노드
        output.append("\n" + "=" * 60)
        output.append("🔮 노드 (카르마/전생)")
        output.append("=" * 60)
        output.append(f"North Node (용머리): {nodes['north_node']['formatted']}")
        output.append(f"  → {nodes['north_node']['meaning']}")
        output.append(f"\nSouth Node (용꼬리): {nodes['south_node']['formatted']}")
        output.append(f"  → {nodes['south_node']['meaning']}")

        # 파트 오브 포춘
        output.append(f"\n🍀 파트 오브 포춘: {pof['formatted']}")
        output.append(f"  → {pof['meaning']}")

        # 하우스
        output.append("\n" + "=" * 60)
        output.append("🏠 하우스 시스템 (Whole Sign)")
        output.append("=" * 60)
        for house_num in range(1, 13):
            house_data = houses['houses'][house_num]
            # 해당 하우스에 있는 행성 목록
            planets_in_house = [
                name for name, pdata in planets.items()
                if pdata.get('house') == house_num
            ]
            planets_str = f" ← {', '.join(planets_in_house)}" if planets_in_house else ""
            output.append(
                f"제{house_num:2d}하우스: {house_data['sign']:12s} - {house_data['meaning']}{planets_str}"
            )

        output.append("\n" + "=" * 60)

        return "\n".join(output)
