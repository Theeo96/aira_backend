import type { SeoulInfoPacket } from "./types";

export function buildSpeechSummary(packet: SeoulInfoPacket): string {
  const parts: string[] = [];

  if (packet.place.originArea) {
    parts.push(`현재 기준 지역은 ${packet.place.originArea}입니다.`);
  }
  if (packet.environment.congestion) {
    parts.push(`혼잡도는 ${packet.environment.congestion}입니다.`);
  }

  if (packet.transit.fastest) {
    parts.push(
      `가장 빠른 열차는 ${packet.transit.fastest.line} ${packet.transit.fastest.message}, ${packet.transit.fastest.etaMinutesText}입니다.`
    );
  }
  if (packet.transit.next) {
    parts.push(`다음 열차는 ${packet.transit.next.etaMinutesText}입니다.`);
  }

  if (packet.transit.totalTimeMinutes != null) {
    parts.push(`최단 경로 총 소요시간은 ${packet.transit.totalTimeMinutes}분입니다.`);
  }
  if (packet.transit.walkToDepartureMinutes != null) {
    parts.push(`출발역까지 도보 ${packet.transit.walkToDepartureMinutes}분입니다.`);
  }

  if (packet.culture.aroundDestination && packet.culture.aroundDestination.eventCount > 0) {
    parts.push(`도착지 주변 문화 이벤트는 ${packet.culture.aroundDestination.eventCount}건입니다.`);
  }

  return parts.join(" ");
}
