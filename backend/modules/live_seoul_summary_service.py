from __future__ import annotations

from datetime import datetime
import re
from typing import Callable
from zoneinfo import ZoneInfo


class LiveSeoulSummaryService:
    def __init__(
        self,
        get_nearby_station: Callable[[float, float], dict | None],
        get_nearby_bus_stop: Callable[[float, float], dict | None],
        estimate_walk_minutes: Callable[[float, float, float | None, float | None], int | None],
        resolve_destination_coords_from_name: Callable[[str], tuple[float | None, float | None]],
        resolve_home_coords: Callable[[], tuple[float | None, float | None]],
        is_schedule_query: Callable[[str | None], bool],
        is_arrival_eta_query: Callable[[str | None], bool],
        extract_schedule_search_dttm: Callable[[str, datetime | None], tuple[str, str]],
        get_transit_route: Callable[..., dict | None],
        parse_tmap_strategy: Callable[[dict | None, str | None, str | None], dict],
        strategy_needs_odsay_backfill: Callable[[dict], bool],
        get_odsay_path: Callable[..., dict | None],
        parse_odsay_strategy: Callable[[dict], dict],
        merge_strategy_with_fallback: Callable[[dict, dict], dict],
        get_weather_and_air: Callable[[float, float], tuple[dict, dict]],
        get_tmap_subway_car_congestion: Callable[[str | None, str | None], dict | None],
        format_eta_phrase: Callable[[int | None], str | None],
        get_subway_arrival: Callable[[str], list[dict]],
        extract_arrival_minutes: Callable[[dict, bool], int | None],
    ):
        self.get_nearby_station = get_nearby_station
        self.get_nearby_bus_stop = get_nearby_bus_stop
        self.estimate_walk_minutes = estimate_walk_minutes
        self.resolve_destination_coords_from_name = resolve_destination_coords_from_name
        self.resolve_home_coords = resolve_home_coords
        self.is_schedule_query = is_schedule_query
        self.is_arrival_eta_query = is_arrival_eta_query
        self.extract_schedule_search_dttm = extract_schedule_search_dttm
        self.get_transit_route = get_transit_route
        self.parse_tmap_strategy = parse_tmap_strategy
        self.strategy_needs_odsay_backfill = strategy_needs_odsay_backfill
        self.get_odsay_path = get_odsay_path
        self.parse_odsay_strategy = parse_odsay_strategy
        self.merge_strategy_with_fallback = merge_strategy_with_fallback
        self.get_weather_and_air = get_weather_and_air
        self.get_tmap_subway_car_congestion = get_tmap_subway_car_congestion
        self.format_eta_phrase = format_eta_phrase
        self.get_subway_arrival = get_subway_arrival
        self.extract_arrival_minutes = extract_arrival_minutes

    def _extract_station_from_text(self, text: str | None) -> str | None:
        t = str(text or "").strip()
        if not t:
            return None
        m = re.search(r"([^\s]{2,24})\s*\uC5ED", t)
        if m:
            return str(m.group(1)).strip() + "\uC5ED"
        return None

    def build_summary(
        self,
        lat: float | None,
        lng: float | None,
        station_name: str | None,
        destination_name: str | None = None,
        prefer_subway: bool = False,
        detailed_subway: bool = False,
        user_text: str | None = None,
    ) -> dict:
        station = station_name.strip() if isinstance(station_name, str) and station_name.strip() else None
        station_lat = None
        station_lng = None

        bus_stop_name = None
        walk_to_bus_stop_min = None

        if lat is not None and lng is not None:
            nearby_subway = self.get_nearby_station(lat, lng)
            if isinstance(nearby_subway, dict):
                if not station:
                    station = nearby_subway.get("name")
                station_lat = nearby_subway.get("lat")
                station_lng = nearby_subway.get("lng")

            nearby_bus = self.get_nearby_bus_stop(lat, lng)
            if isinstance(nearby_bus, dict):
                bus_stop_name = nearby_bus.get("name")
                walk_to_bus_stop_min = self.estimate_walk_minutes(lat, lng, nearby_bus.get("lat"), nearby_bus.get("lng"))

        destination_requested = bool(destination_name and str(destination_name).strip())
        target_lat, target_lng = self.resolve_destination_coords_from_name(destination_name) if destination_requested else (None, None)
        destination_resolved = target_lat is not None and target_lng is not None
        if not destination_requested and (target_lat is None or target_lng is None):
            target_lat, target_lng = self.resolve_home_coords()
            destination_resolved = target_lat is not None and target_lng is not None

        schedule_query = self.is_schedule_query(user_text)
        arrival_query = self.is_arrival_eta_query(user_text)
        search_dttm = None
        search_label = None
        if schedule_query:
            search_dttm, search_label = self.extract_schedule_search_dttm(
                user_text or "",
                datetime.now(ZoneInfo("Asia/Seoul")),
            )

        strategy = {}
        strategy_provider = None
        tmap_ready = False
        if lat is not None and lng is not None and target_lat is not None and target_lng is not None:
            tmap_raw = self.get_transit_route(
                origin={"lat": lat, "lng": lng},
                destination={"lat": target_lat, "lng": target_lng},
                search_dttm=search_dttm,
                count=1,
            )
            tmap_strategy = self.parse_tmap_strategy(
                tmap_raw,
                search_dttm=search_dttm,
                search_label=search_label,
            )
            if isinstance(tmap_strategy, dict) and tmap_strategy:
                strategy = tmap_strategy
                strategy_provider = "tmap"
                tmap_ready = True

                need_odsay_backfill = self.strategy_needs_odsay_backfill(strategy) or (
                    prefer_subway and strategy.get("firstMode") != "subway"
                )
                if need_odsay_backfill:
                    path_type = 1 if prefer_subway else 0
                    path_obj = self.get_odsay_path(sx=lng, sy=lat, ex=target_lng, ey=target_lat, search_path_type=path_type)
                    odsay_strategy = self.parse_odsay_strategy(path_obj) if isinstance(path_obj, dict) else {}
                    if isinstance(odsay_strategy, dict) and odsay_strategy:
                        strategy = self.merge_strategy_with_fallback(strategy, odsay_strategy)
                        strategy_provider = str(strategy.get("provider") or "tmap+odsay")

            if not strategy:
                path_type = 1 if prefer_subway else 0
                path_obj = self.get_odsay_path(sx=lng, sy=lat, ex=target_lng, ey=target_lat, search_path_type=path_type)
                strategy = self.parse_odsay_strategy(path_obj) if isinstance(path_obj, dict) else {}
                if prefer_subway and strategy.get("firstMode") != "subway":
                    fallback_obj = self.get_odsay_path(sx=lng, sy=lat, ex=target_lng, ey=target_lat, search_path_type=0)
                    fallback_strategy = self.parse_odsay_strategy(fallback_obj) if isinstance(fallback_obj, dict) else {}
                    if isinstance(fallback_strategy, dict) and fallback_strategy:
                        strategy = fallback_strategy
                if strategy:
                    strategy_provider = "odsay"

        weather = {}
        air = {}
        if lat is not None and lng is not None:
            weather, air = self.get_weather_and_air(lat, lng)

        first_mode = strategy.get("firstMode")
        first_board = strategy.get("firstBoardName")
        first_direction = strategy.get("firstDirection")
        subway_line = strategy.get("subwayLine")
        bus_numbers = strategy.get("busNumbers") or []
        subway_legs = strategy.get("subwayLegs") or []
        subway_congestion = None

        explicit_station = self._extract_station_from_text(user_text)
        departure_station = (
            explicit_station
            or (first_board if first_mode == "subway" and first_board else None)
            or station
        )
        if first_mode == "subway":
            subway_congestion = self.get_tmap_subway_car_congestion(
                route_name=subway_line,
                station_name=departure_station,
            )
        arrivals = []
        first_eta = None
        next_eta = None
        if not arrival_query:
            first_eta = strategy.get("firstEtaMinutes") if isinstance(strategy, dict) else None
            next_eta = strategy.get("nextEtaMinutes") if isinstance(strategy, dict) else None
            try:
                first_eta = int(first_eta) if first_eta is not None else None
            except Exception:
                first_eta = None
            try:
                next_eta = int(next_eta) if next_eta is not None else None
            except Exception:
                next_eta = None
        if first_eta is not None and next_eta is not None and next_eta <= first_eta:
            next_eta = None

        if arrival_query and departure_station:
            rows = self.get_subway_arrival(str(departure_station))
            if isinstance(rows, list):
                arrivals = [r for r in rows if isinstance(r, dict)]
                if arrivals and not strategy_provider:
                    strategy_provider = "seoul_api"
            rows_for_eta = arrivals
            line_hint = str(subway_line or "").replace(" ", "").strip()
            if line_hint:
                matched = []
                for row in arrivals:
                    train_line_nm = str(row.get("trainLineNm") or "").replace(" ", "")
                    updn_line_nm = str(row.get("updnLine") or "").replace(" ", "")
                    if line_hint and (line_hint in train_line_nm or line_hint in updn_line_nm):
                        matched.append(row)
                if matched:
                    rows_for_eta = matched
            eta_candidates: list[int] = []
            for row in rows_for_eta:
                eta = self.extract_arrival_minutes(row, True)
                if eta is None:
                    continue
                try:
                    eta_n = int(eta)
                except Exception:
                    continue
                if eta_n < 0:
                    continue
                eta_candidates.append(eta_n)
            eta_candidates = sorted(set(eta_candidates))
            if eta_candidates:
                first_eta = eta_candidates[0]
                later = [v for v in eta_candidates[1:] if v > first_eta]
                if later:
                    next_eta = later[0]

        walk_to_departure_min = None
        if lat is not None and lng is not None:
            walk_to_departure_min = self.estimate_walk_minutes(
                lat,
                lng,
                strategy.get("firstStartLat") if strategy else station_lat,
                strategy.get("firstStartLng") if strategy else station_lng,
            )

        decision = None
        if first_mode == "subway":
            if walk_to_departure_min is not None and first_eta is not None:
                if walk_to_departure_min < first_eta:
                    decision = "first"
                else:
                    if next_eta is not None:
                        if walk_to_departure_min < next_eta:
                            decision = "next"
                        else:
                            decision = "after_next"
                    else:
                        decision = "after_next"
            else:
                decision = None

        parts = []

        if destination_requested and not destination_resolved:
            parts.append(f"'{destination_name}' 紐⑹쟻吏瑜???湲곗??쇰줈 李얠? 紐삵뻽?댁슂. ?? ?깆닔?? 媛뺣궓??쿂??留먯???二쇱꽭??")
            if station:
                parts.append(f"?꾩옱 湲곗? 媛??媛源뚯슫 ??? {station}??씠?먯슂.")
        elif arrival_query:
            if not departure_station:
                parts.append("媛源뚯슫 吏?섏쿋??쓣 李얠? 紐삵빐 ?꾩갑 ?쒓컙???뺤씤?????놁뒿?덈떎.")
            else:
                line_text = str(subway_line or "").strip()
                if not line_text and arrivals:
                    row0 = arrivals[0] if isinstance(arrivals[0], dict) else {}
                    line_text = str(row0.get("trainLineNm") or row0.get("updnLine") or "").strip()
                if not line_text:
                    line_text = "해당 노선"
                eta_phrase = self.format_eta_phrase(first_eta)
                if eta_phrase:
                    parts.append(f"{departure_station}??{line_text} 湲곗? ?ㅼ쓬 ?댁감??{eta_phrase}?낅땲??")
                else:
                    parts.append(f"{departure_station}??{line_text} 湲곗? ?ㅼ떆媛??꾩갑 ?덉젙 遺??뺣낫???꾩옱 ?쒓났?섏? ?딆뒿?덈떎.")
                next_phrase = self.format_eta_phrase(next_eta)
                if next_phrase:
                    parts.append(f"洹몃떎???댁감??{next_phrase}?낅땲??")
        elif schedule_query:
            line_text = str(subway_line or "").strip()
            if tmap_ready:
                label = str(strategy.get("searchDttmLabel") or search_label or "").strip()
                if label:
                    parts.append(f"{label} 湲곗? ?댄뻾 ?뺣낫瑜??뺤씤?덉뼱??")
                service_available = strategy.get("serviceAvailable")
                service_known = bool(strategy.get("serviceKnown"))
                if service_known:
                    if service_available is True:
                        parts.append("?대떦 ?쒓컙??먮뒗 ?댄뻾 以묒엯?덈떎.")
                    elif service_available is False:
                        parts.append("?대떦 ?쒓컙??먮뒗 ?댄뻾??醫낅즺??援ш컙???덉뼱??")
                else:
                    parts.append("?댄뻾 ?곹깭 ?몃?媛믪? ?쒓났?섏? ?딆븘 寃쎈줈 湲곗??쇰줈 ?덈궡?⑸땲??")

                if first_mode == "subway":
                    if departure_station and line_text:
                        parts.append(f"{departure_station}??{line_text} 湲곗??쇰줈 ?뺤씤?덉뒿?덈떎.")
                    elif departure_station:
                        parts.append(f"{departure_station}??湲곗??쇰줈 ?뺤씤?덉뒿?덈떎.")
                elif first_mode == "bus":
                    if bus_numbers:
                        parts.append(f"二쇱슂 踰꾩뒪??{', '.join(bus_numbers)}?낅땲??")

                eta_phrase = self.format_eta_phrase(first_eta)
                if eta_phrase:
                    parts.append(f"?꾩옱 湲곗? ?ㅼ쓬 ?댁감??{eta_phrase}?낅땲??")
                elif first_mode:
                    parts.append("?뺥솗???꾩갑 遺??⑥쐞 ?곗씠?곕뒗 ?꾩옱 ?뺤씤?섏? ?딆뒿?덈떎.")
                else:
                    parts.append("?대떦 議곌굔???댄뻾 寃쎈줈瑜?李얠? 紐삵뻽?댁슂.")
            else:
                if strategy_provider == "odsay":
                    parts.append("TMAP ?댄뻾 ?쒓컙???댄뻾 ?쇱젙 ?뺣낫???꾩옱 諛쏆? 紐삵뻽?듬땲??")
                    parts.append("???ODSay 寃쎈줈 湲곗??쇰줈留??덈궡 媛?ν빀?덈떎.")
                else:
                    parts.append("?꾩옱 ?붿껌?섏떊 ?댄뻾 ?쒓컙???댄뻾 ?쇱젙 ?뺣낫瑜?諛쏆쓣 ???놁뒿?덈떎.")
        elif prefer_subway:
            if not departure_station:
                parts.append("吏?섏쿋 異쒕컻??쓣 李얠? 紐삵뻽?댁슂. ???대쫫??留먯???二쇱떆硫?諛붾줈 ?뺤씤???쒕┫寃뚯슂.")
            else:
                line_text = str(subway_line or "?대떦 ?몄꽑")
                direction_text = str(first_direction or "방면 정보 없음")
                parts.append(f"吏?섏쿋濡?媛?쒕젮硫?{departure_station}??뿉??{line_text}????쒕㈃ ?쇱슂.")
                parts.append(f"?묒듅 諛⑸㈃? {direction_text}?낅땲??")
                if walk_to_departure_min is not None:
                    parts.append(f"?꾩옱 ?꾩튂?먯꽌 異쒕컻??퉴吏 ?꾨낫 ??{walk_to_departure_min}遺?嫄몃젮??")
                eta_phrase = self.format_eta_phrase(first_eta)
                if eta_phrase:
                    parts.append(f"?대쾲 ?댁감??{eta_phrase}?댁뿉??")
                else:
                    parts.append("?ㅼ떆媛??댁감 ?꾩갑 ?덉젙 遺??뺣낫???꾩옱 ?쒓났?섏? ?딆뒿?덈떎.")

                if decision == "next" and next_eta is not None:
                    next_phrase = self.format_eta_phrase(next_eta) or f"약 {next_eta}분"
                    parts.append(f"?꾩옱 ?대룞 ?쒓컙 湲곗??쇰줈 ?대쾲 ?댁감???대졄怨? ?ㅼ쓬 ?댁감({next_phrase} ??瑜?沅뚯옣?댁슂.")
                elif decision == "after_next":
                    parts.append("?꾩옱 ?대룞 ?쒓컙 湲곗??쇰줈 ?대쾲/?ㅼ쓬 ?댁감 紐⑤몢 ?대졄?듬땲?? ???꾩갑 ???ㅼ쓬 ?댁감 ?쒓컙???ㅼ떆 ?뺤씤??二쇱꽭??")
                elif decision == "first":
                    parts.append("吏湲?異쒕컻?섎㈃ ?대쾲 ?댁감 ?묒듅 媛?μ꽦???덉뼱??")
                if isinstance(subway_congestion, dict):
                    least_car = str(subway_congestion.get("leastCar") or "").strip()
                    if least_car:
                        parts.append(f"?쇱옟??湲곗??쇰줈??{least_car}移몄씠 媛???ъ쑀濡쒖슫 ?몄엯?덈떎.")

                if detailed_subway and subway_legs:
                    first_leg = subway_legs[0]
                    parts.append(
                        f"?곸꽭 寃쎈줈??{first_leg.get('start')}??뿉??{first_leg.get('line')} "
                        f"{first_leg.get('direction') or '諛⑸㈃'} ?댁감瑜??怨?{first_leg.get('end')}??뿉???대━?쒕㈃ ?쇱슂."
                    )
                    if len(subway_legs) > 1:
                        for idx, leg in enumerate(subway_legs[1:], start=2):
                            parts.append(
                                f"{idx-1}李??섏듅? {leg.get('start')}??뿉??{leg.get('line')} "
                                f"{leg.get('direction') or '諛⑸㈃'}?쇰줈 媛덉븘?怨?{leg.get('end')}??뿉???대━?쒕㈃ ?쇱슂."
                            )

        elif first_mode == "bus":
            parts.append("媛??鍮좊Ⅸ ?以묎탳???쒖옉 援ш컙? 踰꾩뒪?덉슂.")
            if bus_numbers:
                parts.append(f"?묒듅 踰꾩뒪 踰덊샇??{', '.join(bus_numbers)}?낅땲??")
            if first_board:
                parts.append(f"?묒듅 ?뺣쪟?μ? {first_board}?낅땲??")
            if walk_to_departure_min is not None:
                parts.append(f"?꾩옱 ?꾩튂?먯꽌 洹??뺣쪟?κ퉴吏 ?꾨낫 ??{walk_to_departure_min}遺?嫄몃젮??")
            elif bus_stop_name and walk_to_bus_stop_min is not None:
                parts.append(f"媛??媛源뚯슫 ?뺣쪟??{bus_stop_name}源뚯? ?꾨낫 ??{walk_to_bus_stop_min}遺?嫄몃젮??")

        elif first_mode == "subway":
            line_text = str(subway_line or "?대떦 ?몄꽑")
            direction_text = str(first_direction or "방면 정보 없음")
            parts.append(f"吏?섏쿋 湲곗? 媛??鍮좊Ⅸ 寃쎈줈??{departure_station}??뿉??{line_text} ?댁감 ?묒듅?댁뿉??")
            parts.append(f"?묒듅 諛⑸㈃? {direction_text}?낅땲??")

            if walk_to_departure_min is not None:
                parts.append(f"?꾩옱 ?꾩튂?먯꽌 異쒕컻??퉴吏 ?꾨낫 ??{walk_to_departure_min}遺?嫄몃젮??")
            eta_phrase = self.format_eta_phrase(first_eta)
            if eta_phrase:
                parts.append(f"異쒕컻??湲곗? ?대쾲 ?댁감??{eta_phrase}?댁뿉??")
            else:
                parts.append("?ㅼ떆媛??댁감 ?꾩갑 ?덉젙 遺??뺣낫???꾩옱 ?쒓났?섏? ?딆뒿?덈떎.")

            if decision == "next" and next_eta is not None:
                next_phrase = self.format_eta_phrase(next_eta) or f"약 {next_eta}분"
                parts.append(f"吏湲??대룞?섎㈃ ?대쾲 ?댁감???대졄怨? ?ㅼ쓬 ?댁감??{next_phrase} ?꾩삁??")
            elif decision == "after_next":
                parts.append("吏湲??대룞?섎㈃ ?대쾲/?ㅼ쓬 ?댁감 紐⑤몢 ?대졄?듬땲?? ???꾩갑 ???ㅼ쓬 ?댁감 ?쒓컙???ㅼ떆 ?뺤씤??二쇱꽭??")
            elif decision == "first":
                parts.append("吏湲?異쒕컻?섎㈃ ?대쾲 ?댁감 ?묒듅 媛?μ꽦???덉뼱??")
            if isinstance(subway_congestion, dict):
                least_car = str(subway_congestion.get("leastCar") or "").strip()
                if least_car:
                    parts.append(f"?쇱옟??湲곗??쇰줈??{least_car}移몄씠 媛???ъ쑀濡쒖슫 ?몄엯?덈떎.")

            if detailed_subway and subway_legs:
                first_leg = subway_legs[0]
                parts.append(
                    f"?곸꽭 寃쎈줈??{first_leg.get('start')}??뿉??{first_leg.get('line')} "
                    f"{first_leg.get('direction') or '諛⑸㈃'} ?댁감瑜??怨?{first_leg.get('end')}??뿉???대━?쒕㈃ ?쇱슂."
                )
                if len(subway_legs) > 1:
                    for idx, leg in enumerate(subway_legs[1:], start=2):
                        parts.append(
                            f"{idx-1}李??섏듅? {leg.get('start')}??뿉??{leg.get('line')} "
                            f"{leg.get('direction') or '諛⑸㈃'}?쇰줈 媛덉븘?怨?{leg.get('end')}??뿉???대━?쒕㈃ ?쇱슂."
                        )

        else:
            if station:
                parts.append(f"?꾩옱 湲곗? 媛??媛源뚯슫 吏?섏쿋??? {station}??씠?먯슂.")
            if bus_stop_name and walk_to_bus_stop_min is not None:
                parts.append(f"媛??媛源뚯슫 踰꾩뒪 ?뺣쪟?μ? {bus_stop_name}, ?꾨낫 ??{walk_to_bus_stop_min}遺꾩엯?덈떎.")

        if not parts:
            parts.append("?ㅼ떆媛?寃쎈줈 ?뺣낫瑜?異⑸텇??諛쏆? 紐삵뻽?댁슂. 異쒕컻吏? 紐⑹쟻吏瑜??ㅼ떆 ?뺤씤??二쇱꽭??")

        summary = " ".join(parts)

        return {
            "station": station,
            "speechSummary": summary,
            "arrivals": arrivals,
            "decision": decision,
            "firstEtaMinutes": first_eta,
            "nextEtaMinutes": next_eta,
            "walkToStationMinutes": walk_to_departure_min,
            "busStopName": bus_stop_name,
            "walkToBusStopMinutes": walk_to_bus_stop_min,
            "busNumbers": bus_numbers,
            "firstMode": first_mode,
            "firstDirection": first_direction,
            "subwayCongestion": subway_congestion,
            "weather": weather,
            "air": air,
            "homeConfigured": target_lat is not None and target_lng is not None,
            "destinationName": destination_name,
            "destinationRequested": destination_requested,
            "destinationResolved": destination_resolved,
            "routeProvider": strategy_provider,
            "scheduleQuery": schedule_query,
            "arrivalEtaQuery": arrival_query,
            "scheduleSearchDttm": str(search_dttm or "").strip() or None,
        }


