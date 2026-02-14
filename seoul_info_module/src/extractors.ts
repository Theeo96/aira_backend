import { resolveEtaMinutes } from "./eta";
import type {
  CultureInfo,
  CultureSummary,
  EnvironmentInfo,
  NewsInfo,
  PlaceInfo,
  RawOdsayFastestPayload,
  RawVoiceAssistantPayload,
  SeoulInfoPacket,
  SpeechInfo,
  TransitInfo
} from "./types";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function toStringOrNull(value: unknown): string | null {
  if (value == null) return null;
  const s = String(value).trim();
  return s.length > 0 ? s : null;
}

function toNumberOrNull(value: unknown): number | null {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function parseCulture(input: unknown): CultureSummary | null {
  const r = asRecord(input);
  const area = toStringOrNull(r.area);
  if (!area) return null;

  const eventPreview = asArray(r.event_preview).map((v) => String(v));
  const cultureNewsPreview = asArray(r.culture_news_preview).map((row) => {
    const item = asRecord(row);
    return {
      title: String(item.title ?? "-"),
      date: String(item.date ?? "-")
    };
  });

  return {
    area,
    eventCount: toNumberOrNull(r.event_count) ?? 0,
    eventPreview,
    cultureNewsCount: toNumberOrNull(r.culture_news_count) ?? 0,
    cultureNewsPreview
  };
}

function parseTrain(input: unknown) {
  const r = asRecord(input);
  if (Object.keys(r).length === 0) return null;

  const line = String(r.trainLineNm ?? r.line ?? "-");
  const message = String(r.arvlMsg2 ?? r.arrivalMessage ?? "-");
  const seconds = r.barvlDt ?? r.arrivalSeconds;
  const eta = resolveEtaMinutes({ seconds, message });

  return {
    line,
    message,
    etaMinutes: eta.minutes,
    etaMinutesText: eta.text,
    rawSeconds: eta.rawSeconds
  };
}

function getVoiceContext(voicePayload: RawVoiceAssistantPayload | null | undefined) {
  const voice = asRecord(voicePayload);
  const observations = asRecord(voice.observations);
  const culture = asRecord(voice.culture);
  const news = asRecord(voice.news);
  const resolvedArea = asRecord(voice.resolved_area);
  return { voice, observations, culture, news, resolvedArea };
}

export function buildPlaceInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined
): PlaceInfo {
  const { observations, resolvedArea } = getVoiceContext(voicePayload);
  return {
    originArea: toStringOrNull(resolvedArea.areaName),
    destinationArea: toStringOrNull(observations.destination_area),
    destinationStation: toStringOrNull(observations.destination_station)
  };
}

export function buildTransitInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined,
  odsayPayload?: RawOdsayFastestPayload | null
): TransitInfo {
  const { observations } = getVoiceContext(voicePayload);
  const odsay = asRecord(odsayPayload);
  const fastestPath = asRecord(odsay.fastestPath);
  const walk = asRecord(odsay.walkToDepartureStation);

  return {
    fastest: parseTrain(observations.subway_fastest),
    next: parseTrain(observations.subway_next),
    totalTimeMinutes: toNumberOrNull(fastestPath.totalTimeMinutes),
    transferCount: toNumberOrNull(fastestPath.transferCount),
    walkToDepartureMinutes: toNumberOrNull(walk.minutes),
    walkExact:
      typeof walk.exactFromCurrentOnly === "boolean"
        ? (walk.exactFromCurrentOnly as boolean)
        : null
  };
}

export function buildEnvironmentInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined
): EnvironmentInfo {
  const { observations } = getVoiceContext(voicePayload);
  return {
    congestion: toStringOrNull(observations.area_congestion),
    weatherTemp: toNumberOrNull(observations.weather_temp),
    bikeParkingTotal: toNumberOrNull(observations.bike_parking_total),
    bikeRackTotal: toNumberOrNull(observations.bike_rack_total),
    bikeOccupancyPct: toNumberOrNull(observations.bike_occupancy_pct)
  };
}

export function buildCultureInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined
): CultureInfo {
  const { observations, culture } = getVoiceContext(voicePayload);
  return {
    aroundOrigin: parseCulture(culture.around_origin ?? observations.origin_culture),
    aroundDestination: parseCulture(
      culture.around_destination ?? observations.destination_culture
    )
  };
}

export function buildNewsInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined
): NewsInfo {
  const { news } = getVoiceContext(voicePayload);
  return {
    latest: asArray(news.items)
      .slice(0, 2)
      .map((row) => {
        const item = asRecord(row);
        return {
          title: String(item.title ?? ""),
          date: String(item.pubDate ?? ""),
          link: String(item.originallink ?? item.link ?? "")
        };
      })
  };
}

export function buildSpeechInfo(
  voicePayload: RawVoiceAssistantPayload | null | undefined
): SpeechInfo {
  const { voice } = getVoiceContext(voicePayload);
  return {
    summary: toStringOrNull(voice.speak_text) ?? "요약 정보가 없습니다.",
    followUp:
      toStringOrNull(voice.follow_up_question) ?? "원하시는 조건으로 다시 안내할까요?"
  };
}

export function buildSeoulInfoPacket(
  voicePayload: RawVoiceAssistantPayload | null | undefined,
  odsayPayload?: RawOdsayFastestPayload | null
): SeoulInfoPacket {
  const voice = asRecord(voicePayload);
  const odsay = asRecord(odsayPayload);

  return {
    meta: {
      source: {
        voiceAssistant: Object.keys(voice).length > 0,
        odsayFastest: Object.keys(odsay).length > 0
      }
    },
    place: buildPlaceInfo(voicePayload),
    transit: buildTransitInfo(voicePayload, odsayPayload),
    environment: buildEnvironmentInfo(voicePayload),
    culture: buildCultureInfo(voicePayload),
    news: buildNewsInfo(voicePayload),
    speech: buildSpeechInfo(voicePayload)
  };
}
