"""
AstrologyCalculator 단위 테스트
알려진 천문 데이터와 비교하여 계산 정확성을 검증합니다.
"""

import pytest
from astrology_calculator import AstrologyCalculator


@pytest.fixture
def calculator():
    """테스트용 계산기 인스턴스"""
    return AstrologyCalculator()


class TestDatetimeToJulian:
    """율리우스일 변환 테스트"""

    def test_known_date(self, calculator):
        """J2000.0 기준일 (2000-01-01 12:00 UTC) = JD 2451545.0"""
        from datetime import datetime
        import pytz

        dt = datetime(2000, 1, 1, 12, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        assert abs(jd - 2451545.0) < 0.001

    def test_another_known_date(self, calculator):
        """1990-01-01 00:00 UTC = JD 2447892.5"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 0, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        assert abs(jd - 2447892.5) < 0.001


class TestCalculatePlanets:
    """행성 위치 계산 테스트"""

    def test_returns_all_planets(self, calculator):
        """최소 10개 천체 (키론은 ephemeris 파일 의존) 계산되는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)  # 서울 12:00 = UTC 03:00
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        required = {"태양", "달", "수성", "금성", "화성", "목성", "토성", "천왕성", "해왕성", "명왕성"}
        assert required.issubset(set(planets.keys()))
        assert len(planets) >= 10

    def test_planet_data_fields(self, calculator):
        """각 행성 데이터에 필수 필드가 있는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            assert "sign" in data, f"{name}에 sign 필드 없음"
            assert "degree" in data, f"{name}에 degree 필드 없음"
            assert "longitude" in data, f"{name}에 longitude 필드 없음"
            assert "retrograde" in data, f"{name}에 retrograde 필드 없음"
            assert "formatted" in data, f"{name}에 formatted 필드 없음"

    def test_longitude_range(self, calculator):
        """모든 행성 경도가 0~360 범위인지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            assert 0 <= data["longitude"] < 360, f"{name} 경도 범위 오류: {data['longitude']}"

    def test_degree_in_sign_range(self, calculator):
        """별자리 내 도수가 0~30 범위인지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            assert 0 <= data["degree"] < 30, f"{name} 도수 범위 오류: {data['degree']}"

    def test_sign_is_valid(self, calculator):
        """별자리 이름이 유효한지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            assert data["sign"] in calculator.SIGNS, f"{name} 별자리 오류: {data['sign']}"

    def test_sun_in_capricorn_jan1_1990(self, calculator):
        """1990-01-01 태양이 염소자리에 있는지 확인 (알려진 사실)"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        assert planets["태양"]["sign"] == "염소자리"

    def test_retrograde_flag(self, calculator):
        """역행 플래그가 boolean인지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            assert isinstance(data["retrograde"], bool), f"{name} retrograde 타입 오류"

    def test_retrograde_marker_in_formatted(self, calculator):
        """역행 중인 행성의 formatted에 (R) 표시가 있는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)

        for name, data in planets.items():
            if data["retrograde"]:
                assert "(R)" in data["formatted"], f"{name} 역행인데 (R) 표시 없음"
            else:
                assert "(R)" not in data["formatted"], f"{name} 순행인데 (R) 표시 있음"


class TestCalculateHouses:
    """하우스 계산 테스트"""

    def test_houses_return_structure(self, calculator):
        """하우스 데이터 구조 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)

        assert "ascendant" in houses
        assert "midheaven" in houses
        assert "houses" in houses
        assert len(houses["houses"]) == 12

    def test_all_12_houses_present(self, calculator):
        """12하우스 모두 존재하는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)

        for i in range(1, 13):
            assert i in houses["houses"], f"제{i}하우스 없음"

    def test_whole_sign_consecutive(self, calculator):
        """Whole Sign: 12하우스 별자리가 연속적인지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)

        signs = calculator.SIGNS
        first_sign = houses["houses"][1]["sign"]
        first_idx = signs.index(first_sign)

        for i in range(12):
            expected_sign = signs[(first_idx + i) % 12]
            actual_sign = houses["houses"][i + 1]["sign"]
            assert actual_sign == expected_sign, f"제{i+1}하우스: {actual_sign} != {expected_sign}"

    def test_asc_sign_matches_first_house(self, calculator):
        """ASC 별자리와 제1하우스 별자리가 일치하는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)

        assert houses["ascendant"]["sign"] == houses["houses"][1]["sign"]


class TestAssignPlanetsToHouses:
    """행성-하우스 매핑 테스트"""

    def test_all_planets_get_house(self, calculator):
        """모든 행성에 하우스가 배정되는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)
        asc_sign_idx = calculator.SIGNS.index(houses["ascendant"]["sign"])
        calculator._assign_planets_to_houses(planets, asc_sign_idx)

        for name, data in planets.items():
            assert "house" in data, f"{name}에 house 필드 없음"
            assert 1 <= data["house"] <= 12, f"{name} 하우스 범위 오류: {data['house']}"


class TestCalculateNodes:
    """노드 계산 테스트"""

    def test_nodes_structure(self, calculator):
        """노드 데이터 구조 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        nodes = calculator._calculate_nodes(jd)

        assert "north_node" in nodes
        assert "south_node" in nodes

    def test_south_node_opposite_north(self, calculator):
        """South Node가 North Node의 정반대인지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        nodes = calculator._calculate_nodes(jd)

        nn_sign_idx = calculator.SIGNS.index(nodes["north_node"]["sign"])
        sn_sign_idx = calculator.SIGNS.index(nodes["south_node"]["sign"])

        # 정반대 = 6궁 차이
        assert abs(nn_sign_idx - sn_sign_idx) == 6


class TestCalculateAspects:
    """어스펙트 계산 테스트"""

    def test_aspects_return_list(self, calculator):
        """어스펙트가 리스트로 반환되는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)
        aspects = calculator._calculate_aspects(planets)

        assert isinstance(aspects, list)

    def test_aspect_fields(self, calculator):
        """각 어스펙트에 필수 필드가 있는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)
        aspects = calculator._calculate_aspects(planets)

        for asp in aspects:
            assert "planet1" in asp
            assert "planet2" in asp
            assert "aspect" in asp
            assert "angle" in asp
            assert "orb" in asp

    def test_no_self_aspect(self, calculator):
        """같은 행성끼리 어스펙트가 없는지 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)
        aspects = calculator._calculate_aspects(planets)

        for asp in aspects:
            assert asp["planet1"] != asp["planet2"]


class TestPartOfFortune:
    """파트 오브 포춘 테스트"""

    def test_pof_structure(self, calculator):
        """파트 오브 포춘 데이터 구조 확인"""
        from datetime import datetime
        import pytz

        dt = datetime(1990, 1, 1, 3, 0, tzinfo=pytz.utc)
        jd = calculator._datetime_to_julian(dt)
        planets = calculator._calculate_planets(jd)
        houses = calculator._calculate_houses(jd, 37.5665, 126.9780)
        asc_sign_idx = calculator.SIGNS.index(houses["ascendant"]["sign"])
        calculator._assign_planets_to_houses(planets, asc_sign_idx)
        pof = calculator._calculate_part_of_fortune(planets, houses, jd)

        assert "longitude" in pof
        assert "sign" in pof
        assert "degree" in pof
        assert "formatted" in pof
        assert 0 <= pof["longitude"] < 360
        assert pof["sign"] in calculator.SIGNS


class TestCalculateChart:
    """통합 테스트: calculate_chart 전체 흐름"""

    def test_successful_chart(self, calculator):
        """정상 입력 시 성공 반환"""
        result = calculator.calculate_chart(
            birth_date="1990-01-01",
            birth_time="12:00",
            birth_place="Seoul, South Korea"
        )

        assert result["success"] is True
        assert result["chart_data"] is not None
        assert result["error"] is None

    def test_chart_contains_sections(self, calculator):
        """차트 데이터에 모든 섹션이 포함되는지 확인"""
        result = calculator.calculate_chart(
            birth_date="1990-01-01",
            birth_time="12:00",
            birth_place="Seoul, South Korea"
        )

        chart = result["chart_data"]
        assert "행성 배치" in chart
        assert "어스펙트" in chart
        assert "노드" in chart
        assert "하우스 시스템" in chart
        assert "파트 오브 포춘" in chart
        assert "Ascendant" in chart

    def test_invalid_date_format(self, calculator):
        """잘못된 날짜 형식 시 에러"""
        result = calculator.calculate_chart(
            birth_date="not-a-date",
            birth_time="12:00",
            birth_place="Seoul, South Korea"
        )

        assert result["success"] is False
        assert result["error"] is not None

    def test_timezone_applied(self, calculator):
        """서울과 뉴욕의 같은 로컬 시간이 다른 결과를 내는지 확인"""
        result_seoul = calculator.calculate_chart(
            birth_date="1990-06-15",
            birth_time="14:00",
            birth_place="Seoul, South Korea"
        )
        result_ny = calculator.calculate_chart(
            birth_date="1990-06-15",
            birth_time="14:00",
            birth_place="New York, USA"
        )

        # 같은 로컬 시간이지만 시간대가 다르므로 차트가 달라야 함
        assert result_seoul["success"] and result_ny["success"]
        assert result_seoul["chart_data"] != result_ny["chart_data"]


class TestGetCoordinates:
    """지오코딩 테스트"""

    def test_known_city(self, calculator):
        """서울 좌표가 대략 맞는지 확인"""
        lat, lon = calculator.get_coordinates("Seoul, South Korea")
        assert 37.0 < lat < 38.0
        assert 126.0 < lon < 127.5

    def test_error_on_invalid(self, calculator):
        """존재하지 않는 도시는 ValueError 발생"""
        with pytest.raises(ValueError):
            calculator.get_coordinates("xyznonexistentcity12345")
