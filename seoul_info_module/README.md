# Seoul Info Module

Portable module for plugging Seoul transit/culture summary logic into another project.

## What this gives you

- Domain-by-domain extractors (use only what you need)
  - `buildTransitInfo`
  - `buildEnvironmentInfo`
  - `buildCultureInfo`
  - `buildNewsInfo`
  - `buildPlaceInfo`
  - `buildSpeechInfo`
- ETA minute rounding rule (30-second threshold)
- Optional all-in-one composer: `buildSeoulInfoPacket`

## Folder

- `src/types.ts`: raw/normalized types
- `src/eta.ts`: ETA parsing and rounding rules
- `src/extractors.ts`: domain extractors + optional packet composer
- `src/speech.ts`: speech-friendly summary text
- `src/index.ts`: public exports

## Quick usage (recommended: pick one domain at a time)

```ts
import {
  buildTransitInfo,
  buildCultureInfo,
  buildNewsInfo
} from "./src/index";

const transit = buildTransitInfo(voiceAssistantPayload, odsayFastestPayload);
const culture = buildCultureInfo(voiceAssistantPayload);
const news = buildNewsInfo(voiceAssistantPayload);
```

## Optional all-in-one

```ts
import { buildSeoulInfoPacket } from "./src/index";

const packet = buildSeoulInfoPacket(voiceAssistantPayload, odsayFastestPayload);
```

## Notes

- This module is framework-agnostic and has no runtime dependencies.
- If upstream fields are missing, values are set to `null` or empty arrays.
- It does not call network APIs directly. You pass raw API responses in.
