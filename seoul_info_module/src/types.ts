export type RawVoiceAssistantPayload = Record<string, unknown>;
export type RawOdsayFastestPayload = Record<string, unknown>;

export type NormalizedTrain = {
  line: string;
  message: string;
  etaMinutes: number | null;
  etaMinutesText: string;
  rawSeconds: number | null;
};

export type CultureSummary = {
  area: string;
  eventCount: number;
  eventPreview: string[];
  cultureNewsCount: number;
  cultureNewsPreview: Array<{ title: string; date: string }>;
};

export type PlaceInfo = {
  originArea: string | null;
  destinationArea: string | null;
  destinationStation: string | null;
};

export type TransitInfo = {
  fastest: NormalizedTrain | null;
  next: NormalizedTrain | null;
  totalTimeMinutes: number | null;
  transferCount: number | null;
  walkToDepartureMinutes: number | null;
  walkExact: boolean | null;
};

export type EnvironmentInfo = {
  congestion: string | null;
  weatherTemp: number | null;
  bikeParkingTotal: number | null;
  bikeRackTotal: number | null;
  bikeOccupancyPct: number | null;
};

export type CultureInfo = {
  aroundOrigin: CultureSummary | null;
  aroundDestination: CultureSummary | null;
};

export type NewsInfo = {
  latest: Array<{
    title: string;
    date: string;
    link: string;
  }>;
};

export type SpeechInfo = {
  summary: string;
  followUp: string;
};

export type SeoulInfoPacket = {
  meta: {
    source: {
      voiceAssistant: boolean;
      odsayFastest: boolean;
    };
  };
  place: PlaceInfo;
  transit: TransitInfo;
  environment: EnvironmentInfo;
  culture: CultureInfo;
  news: NewsInfo;
  speech: SpeechInfo;
};
