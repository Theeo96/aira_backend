function toNumber(value: unknown): number | null {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function roundEtaMinutes(totalSeconds: number): number {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds >= 30 ? minutes + 1 : minutes;
}

export function parseEtaMinutesFromMessage(message: string): number | null {
  const text = String(message ?? "");

  const minSec = text.match(/(\d+)\s*분(?:\s*(\d+)\s*초)?/);
  if (minSec) {
    const m = Number(minSec[1] ?? 0);
    const s = Number(minSec[2] ?? 0);
    return roundEtaMinutes(m * 60 + s);
  }

  if (/전역\s*도착/.test(text)) return 1;
  if (/진입|도착/.test(text)) return 0;
  return null;
}

export function resolveEtaMinutes(input: {
  seconds: unknown;
  message: unknown;
}): { minutes: number | null; text: string; rawSeconds: number | null } {
  const rawSeconds = toNumber(input.seconds);
  const message = String(input.message ?? "");

  if (rawSeconds != null && rawSeconds > 0) {
    const minutes = roundEtaMinutes(rawSeconds);
    return { minutes, text: `약 ${minutes}분`, rawSeconds };
  }

  const fromMessage = parseEtaMinutesFromMessage(message);
  if (fromMessage != null) {
    return { minutes: fromMessage, text: `약 ${fromMessage}분`, rawSeconds };
  }

  return { minutes: null, text: "도착예정시간 정보 없음", rawSeconds };
}
