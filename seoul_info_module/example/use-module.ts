import {
  buildTransitInfo,
  buildEnvironmentInfo,
  buildCultureInfo,
  buildNewsInfo
} from "../src/index";

async function main() {
  const voiceResponse = await fetch("http://localhost:3000/api/voice-assistant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      utterance: "퇴근하고 광화문 갈건데 빨리 가는 방법 알려줘",
      lat: 37.5899,
      lng: 127.0626
    })
  }).then((r) => r.json());

  const odsayResponse = await fetch(
    "http://localhost:3000/api/odsay-fastest?sx=127.0626&sy=37.5899&ex=126.9769&ey=37.5759"
  ).then((r) => r.json());

  const transit = buildTransitInfo(voiceResponse, odsayResponse);
  const environment = buildEnvironmentInfo(voiceResponse);
  const culture = buildCultureInfo(voiceResponse);
  const news = buildNewsInfo(voiceResponse);

  console.log({ transit, environment, culture, news });
}

void main();
