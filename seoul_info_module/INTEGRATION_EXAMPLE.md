# Integration Example

## 1) Copy folder

Copy `seoul_info_module` into your target project.

## 2) Import only needed domains

```ts
import {
  buildTransitInfo,
  buildEnvironmentInfo,
  buildCultureInfo,
  buildNewsInfo
} from "./seoul_info_module/src/index";
```

## 3) Extract per use-case

```ts
const transit = buildTransitInfo(voiceAssistantPayload, odsayFastestPayload);
const environment = buildEnvironmentInfo(voiceAssistantPayload);
const culture = buildCultureInfo(voiceAssistantPayload);
const news = buildNewsInfo(voiceAssistantPayload);
```

## 4) Optional combined packet

```ts
import { buildSeoulInfoPacket } from "./seoul_info_module/src/index";

const packet = buildSeoulInfoPacket(voiceAssistantPayload, odsayFastestPayload);
```

## 5) If ODSay payload is not available

```ts
const transit = buildTransitInfo(voiceAssistantPayload, null);
```

The module will still return safe defaults.
