# Domain discovery for x402 services

Technical proposal — 21 September 2026

## What a developer publishes

Start with the OpenAPI description of your API. Add payment annotations to the operations that accept x402, then publish a small entry document at `/.well-known/x402` pointing to that OpenAPI description. The entry document locates the API contract; it does not repeat endpoints, schemas, or prices.

```text
GET /.well-known/x402  -->  GET /openapi.json  -->  API operation
                            inputs and outputs
                            authentication
                            payment annotations
```

There are two valid ways to produce the final OpenAPI file: generate the annotations directly from application/SDK configuration, or apply an authorized provider's overlay during the build. Agents receive the final description in either case. The merchant authorizes publication and can delegate generation or hosting. Using a facilitator does not require using an overlay.

**This is a proposed publication profile.** Neither the well-known entry format nor the `x-x402` OpenAPI extension below is an adopted x402 standard. Their precise definitions are included here so developers and WG reviewers can implement and assess the proposal.

## The x402 file: a small pointer

For the StableTravel example, the proposed response from `https://stabletravel.dev/.well-known/x402` is the complete JSON below:

```json
{
  "discoveryVersion": "1",
  "openapi": ["https://stabletravel.dev/openapi.json"]
}
```

The public URL ends in `x402`, without `.json`. The server returns JSON with `Content-Type: application/json`. A framework can implement this as a GET route or map a static file to that URL. The filename in this repository is only a fixture name.

| Entry field | Type | Rule in this proposed profile |
| --- | --- | --- |
| `discoveryVersion` | String | Required; `"1"` for this proposed discovery format. |
| `openapi` | Array of URL strings | Required, nonempty. Each URL identifies a final OpenAPI 3.1 description. |

`discoveryVersion` identifies the entry-document format and the discovery field definitions in this profile. It is independent of `x402Version`, which identifies the payment protocol. Clients must not interpret a missing or unsupported discovery version as version `"1"`; they should report unsupported discovery and avoid parsing it under this profile. The value `"1"` names this proposed format, not an adopted WG standard.

Serve the entry and descriptions without payment or credentials over HTTPS. For this first profile, the entry, final descriptions, and effective API server URLs share an origin. Validate redirects against the same rule. Publish updates to OpenAPI before updating the entry to point to them.

The sample is something StableTravel **could publish**. It is not a claim that StableTravel has deployed our entry format or approved this proposal. The full service would list all its paid, unpaid, and authenticated operations; the repository contains only selected operations for review.

The [independent x402 discovery Internet-Draft](https://www.ietf.org/ietf-ftp/internet-drafts/draft-hawkins-x402-dns-discovery-03.html) uses this same path with another manifest format. Compare it and [Agentic Resource Discovery (ARD)](https://github.com/ards-project/ard-spec/blob/main/spec/ard.md) before adopting the entry schema. Compatibility is not assumed.

## Developer walkthrough with a real data endpoint

The main example is StableTravel's `GET /api/seats-aero/routes?source=united`. It returns airline origin/destination pairs covered by a mileage program. This is flight data, not API routing information and not a flight purchase.

### 1. Generate the normal OpenAPI document

Keep the real operation path, query parameters, and response schema. The captured operation requires `source`, a nonempty string such as `united` or `aeroplan`. Its response is an array of records with fields including `OriginAirport`, `DestinationAirport`, `Distance`, and `NumDaysOut`.

This example record comes from the service's live 402 Bazaar metadata, not a purchased response:

```json
{
  "ID": "route_123",
  "Source": "united",
  "OriginAirport": "SFO",
  "DestinationAirport": "FRA",
  "OriginRegion": "North America",
  "DestinationRegion": "Europe",
  "Distance": 5685,
  "NumDaysOut": 365
}
```

`examples/stabletravel.source.openapi.json` retains the selected published operation and all its inline input/output schemas. No response fields were invented or removed. No referenced component schemas are needed for this operation.

### 2. Add the x402 annotation to the operation

In OpenAPI, the location is `paths["/api/seats-aero/routes"].get["x-x402"]`. It is a sibling of `summary`, `description`, `parameters`, and `responses`. It is not inside the success-response schema and not in `/.well-known/x402`.

[OpenAPI specification extensions](https://spec.openapis.org/oas/v3.1.1.html#specification-extensions) use names beginning with `x-`. That permits this extension syntactically; this proposal defines its meaning. Ordinary OpenAPI tools can ignore it. A discovery client implementing this profile reads it.

For this endpoint, the proposed discovery annotation is:

```json
"x-x402": {
  "x402Version": 2,
  "price": {
    "currency": "USD",
    "min": "0.010000",
    "max": "0.010000"
  },
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:8453",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "payTo": "0xDd257723b86B4947483905cdAcBbBC70fACF2ec0",
    "payToType": "address"
  }]
}
```

The optional price summary advertises USD 0.01; equal bounds mean a fixed advertised price. The optional payment option describes the observed Base scheme, network, asset, and recipient. The publisher can omit price, payment options, or both when they cannot advertise them reliably. Omission never means free access.

The price comes from the service's published documentation. The Base option comes from a live unsigned request on 21 September 2026 that returned HTTP 402; no payment was made. The live challenge also advertised Solana. The selected option is not an exhaustive list, and the USD display price is not a token payment instruction.

For their own service, developers generate these discovery fields from their own payment configuration. Do not copy StableTravel's recipient into another service or maintain independent payment constants in documentation.

### 3. Describe the challenge and the operation

Document the operation's HTTP 402 response. Under `responses["402"].headers`, describe the x402 v2 `PAYMENT-REQUIRED` header as a string containing a base64-encoded `PaymentRequired` object. The overlay example adds this header documentation to the existing response without replacing the success schema.

Use the existing OpenAPI operation `description` for service behavior and charging conditions that need explanation. Keep its meaning consistent with runtime `resource.description`. Our example copies the observed resource description; it does not invent charges for empty results or refunds.

No billing `unit`, `kind`, `quantity`, or separate billing-description field is introduced. OpenAPI describes the input/output structure; prose explains any additional charging conditions.

### 4. Validate and publish

Validate the OpenAPI document, check the proposed annotation against `x-x402.schema.json`, and compare it with the deployed payment configuration. Publish the final result at the URL listed in the well-known entry. Keep unpaid and authenticated follow-up operations in the production description as well.

An SDK does not automatically publish this profile. A developer needs an OpenAPI generator extension, a small build step, or an overlay to add these annotations. This repository demonstrates the build step; it does not change the x402 SDK.

## Proposed discovery fields: the contract

This proposal defines **one operation-level extension: `x-x402`**. The same object is added directly to OpenAPI or through an overlay's `update`. It includes optional price information; it does not require a second pricing extension.

| Field | Type | Rule in this proposed profile |
| --- | --- | --- |
| `x402Version` | Integer | Required; `2`. Advertises x402 v2 support. |
| `price` | Object | Optional advertised price range for the operation. Omit when unknown or unsuitable. |
| `price.currency` | String | Required if price is present. ISO 4217 currency code, such as `USD`. |
| `price.min` | Decimal string | Required if price is present. Nonnegative advertised lower bound in major currency units. |
| `price.max` | Decimal string | Required if price is present. Nonnegative advertised upper bound; must be at least `min`. |
| `accepts` | Array of objects | Optional, nonempty when present. Non-exhaustive advertised x402 payment options. |
| `accepts[].scheme` | String | Required in each advertised option. Native scheme identifier, such as `exact`, `upto`, or `batch-settlement`. Open string; future identifiers are allowed. |
| `accepts[].network` | String | Required in each advertised option. Native CAIP-2 network identifier. |
| `extensions` | Array of strings | Optional, nonempty list of unique extension identifiers supported for this operation, such as `sign-in-with-x`. |
| `accepts[].asset` | String | Optional. Native asset identifier, if known in advance. |
| `accepts[].payTo` | String | Optional. Native recipient identifier, only if suitable for public discovery. Requires `payToType`. |
| `accepts[].payToType` | String | Optional payout declaration: `address`, `role`, or `stealth`. `address` and `role` require `payTo`; `stealth` omits it. |

**Price itself is optional, including fixed prices.** When present, both bounds use the same currency. Equal bounds express a fixed advertised price; unequal bounds express a range. The minimal valid annotation is `{"x402Version": 2}`. There is no separate `mode`, billing unit, quantity, or billing-description field. Use the operation's existing `description` for conditions that need explanation.

A range summarizes advertised pricing across the operation's supported inputs; it is not a quote for a particular request, an authorization ceiling, or permission to charge. If a publisher cannot provide meaningful bounds, it omits `price`. Clients must not interpret an omitted price as zero or the advertised maximum as a guaranteed spending cap.

`price` and this discovery container are new definitions in this proposal. `scheme`, `network`, `asset`, and `payTo` reuse the names and value meanings from x402 v2. The discovery `accepts` entries are summaries, **not complete runtime PaymentRequirements objects**. They must never be passed directly to payment-signing code.

The live [x402 v2 PaymentRequired message](https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md#51-paymentrequired-schema) still supplies `amount` in atomic asset units, `maxTimeoutSeconds`, and any required mechanism `extra` fields. Those are not fields of this discovery annotation. A USD discovery price does not establish an asset exchange rate. A range does not imply the `upto` scheme.

The JSON Schema in `x-x402.schema.json` defines allowed fields, types, and required fields. Publishers also check that the currency code is valid and `min <= max`; the example checker performs the bound comparison. The schema does not verify ownership, deployed payment support, or price accuracy.

Do not include request-bound nonces, blockhashes, signatures, or authorizations in static discovery. Clients always obtain fresh payment requirements and apply their own spending policy. Optional `payTo` is an advertised recipient, not proof of ownership. `payToType` is a proposed discovery field: `address` identifies a public wallet address, `role` a scheme-defined recipient role, and `stealth` signals that address-based attribution must not assume one reusable public recipient. A `stealth` declaration omits `payTo`; the applicable payment mechanism must provide the actual recipient at runtime. It does not itself implement stealth payments or assert that every mechanism supports them. If payout information is unknown, omit both fields. Absence implies no recipient policy.

## Payment schemes and extensions

Use `accepts[].scheme` for the payment mechanism. It is an open identifier, not an enum limited to current schemes. Advertise separate options for supported scheme/network combinations. Clients must not treat an unknown scheme as `exact`; they need an implementation of the selected scheme and fresh runtime requirements.

[`batch-settlement`](https://docs.x402.org/schemes/batch-settlement) belongs here alongside `exact` and `upto`. It uses escrow and off-chain vouchers with later batched redemption. Its deposit and channel parameters come from the live mechanism, not from the advertised price range.

Use the proposed `extensions` list for operation-level capability discovery. Reuse the exact identifiers used as keys in runtime x402 extension objects. This list contains names only; it is not the runtime `extensions` object and must not be sent as one. Omission means support is unspecified, not that no extensions exist. An advertised extension need not apply to every payment option or request. The live exchange determines applicability and required data; clients must not assume an unknown extension is safe to ignore when the live flow requires it.

For illustration, a publisher that supports all three schemes and SIWX could add the following annotation. This is a contract example, not a claim about either Stable service:

```json
"x-x402": {
  "x402Version": 2,
  "accepts": [
    {"scheme": "exact", "network": "eip155:8453"},
    {"scheme": "upto", "network": "eip155:8453"},
    {"scheme": "batch-settlement", "network": "eip155:8453"}
  ],
  "extensions": ["sign-in-with-x"]
}
```

[Sign-In-With-X](https://docs.x402.org/extensions/sign-in-with-x) is wallet authentication, not a payment scheme. It can allow access to previously purchased content or protect auth-only routes. Keep authentication requirements in OpenAPI `security` and `components.securitySchemes`, with charging and alternative-access conditions in the operation description. An extension-support hint does not require a signature on every request or establish entitlement. Never publish nonces, signatures, or expiring authentication challenges in the discovery annotation.

An auth-only operation may use `x-x402` to advertise the integration version and `extensions` while omitting `price` and `accepts`; its security declaration and description must explain access. Presence of `x-x402` alone does not establish a payment requirement. The StableStudio polling example retains the captured SIWX security declaration without adding an extension identifier that was not captured as x402 runtime metadata.

## Same output through an overlay

A managed provider can supply an [OpenAPI Overlay](https://spec.openapis.org/overlay/v1.1.0.html) that adds the operation description, `x-x402`, and payment-header documentation. Its target for this example is:

```json
"target": "$['paths']['/api/seats-aero/routes']['get']"
```

The complete `examples/stabletravel.overlay.json` contains the updates. In this demo, the build first removes source-specific payment metadata from the captured base, then applies the overlay and serves only the final OpenAPI result. That source conversion is example preparation, not an Overlay requirement. An overlay is an optional build input, not another document the agent has to compose.

Overlay updates merge objects and append arrays. Validate conflicts and duplicate options before publication. This example rejects missing targets as an extra build safeguard; standard Overlay processing treats a target with no matches as a no-op. The example composer supports only the exact object-member targets used here, not the complete JSONPath or Overlay feature set.

A provider supplies the behavior it owns, while the authorized publisher validates and releases the final description. Open Graph link-preview tags have no role in payment terms or OpenAPI composition.

## Variable pricing: a second real Stable operation

`POST https://stablestudio.dev/api/generate/nano-banana-pro/generate` accepts a prompt, aspect ratio, and image size. Its documented response returns a job ID and polling URL. The selected example also retains `GET /api/jobs/{jobId}` and its SIWX security scheme, so the paid operation does not leave the client without the documented follow-up operation.

The proposed annotation for this operation is:

```json
"x-x402": {
  "x402Version": 2,
  "price": {
    "currency": "USD",
    "min": "0",
    "max": "10.00"
  }
}
```

The range values are taken from the captured service documentation and expressed using **our proposed fields**. No runtime amount is fabricated from them. Payment options are omitted because this capture does not establish a reusable option for the operation. The client obtains actual terms for its prompt and image settings at runtime.

The polling operation retains its authentication declaration and receives no payment annotation merely because its authentication response uses HTTP 402.

The source's polling path omits its required `jobId` path-parameter declaration. The example build adds that string parameter and records the correction. It preserves the source's response schemas, including the unconstrained `result` field, rather than inventing a stronger result contract.

A varying price does not imply `upto`. Under `exact`, the server can calculate an amount for a particular request. Under `upto`, the initial amount is an authorization ceiling and settlement can be lower. A displayed min/max range is neither of those instructions. This follows [Coinbase's payment flow](https://docs.cdp.coinbase.com/x402/how-it-works) and the [x402 upto specification](https://github.com/x402-foundation/x402/blob/main/specs/schemes/upto/scheme_upto.md).

The source captures remain unchanged as evidence. The build removes the source-specific `x-payment-info` block before adding our proposed discovery fields. Published example outputs do not contain that block. This is a deliberately scoped x402 publication example; omitting the source's MPP documentation does not mean the real service stopped supporting MPP. Other payment protocols can define their own annotations without changing OpenAPI input/output schemas.

## Publication and endpoint lifecycle

Publication is opt-in: a merchant chooses which operations to advertise for discovery. Include unpaid and authenticated follow-up operations needed to use an advertised service. Aggregator registration warnings, ranking, crawling, and identity verification remain outside this publication profile; an incomplete schema is not silently treated as a complete API contract.

Use OpenAPI's existing `deprecated: true` for an operation being retired. Describe a replacement in its existing description when known. Deprecation does not itself mean an operation is unavailable. Remove withdrawn operations from the next published description, and let HTTP responses remain authoritative about current availability.

Regenerate the final description when application routes, provider payment settings, or advertised prices change. An authorized provider can trigger the merchant's build through a webhook or CI workflow; agents still fetch one composed description. Precise caching and withdrawal timing remain unresolved, so a directory must not treat a cached entry as proof that an endpoint or price is still available. Tax calculation and identity/ownership verification are separate work; this draft defines no tax or ownership-proof fields.

## Run and inspect the examples

From the repository root:

```sh
python3 proposals/openapi-publication/check_examples.py --write
```

This writes the developer-facing artifacts under `proposals/openapi-publication/build/`:

```text
stabletravel/.well-known/x402
stabletravel/openapi.json
stablestudio/.well-known/x402
stablestudio/openapi.json
```

For a developer's own service, publish the corresponding files on their own origin and use their own routes and payment configuration. These example outputs refer to real Stable services for review; running the command does not publish anything to those services or make a payment.

The offline check compares direct generation with overlay composition for StableTravel, verifies captured operation hashes and local references, preserves input/output schemas, checks both proposed price ranges and omission semantics, rejects inverted bounds and source-field leakage, checks the authentication correction, and rejects a missing overlay target. The full selected source schemas appear once in the tracked package; final artifacts are generated, not duplicated as large fixtures.

## Evidence and remaining work

The selected operations come from [StableTravel OpenAPI](https://stabletravel.dev/openapi.json) and [StableStudio OpenAPI](https://stablestudio.dev/openapi.json), captured on 21 September 2026. `examples/evidence.json` records source and operation hashes. `examples/stabletravel.challenge-excerpt.json` records the observed Base payment option and the server-supplied output example. It is evidence, not a reusable authorization or a successful paid response.

The remaining decisions are the well-known format/path compatibility, the proposed discovery field contract and refresh/failure rules. The optional price range is defined in this draft; it is not delegated to a vendor extension or left unspecified. A full implementation also needs standard OpenAPI/Overlay tooling and validation against deployed behavior. The walkthrough makes the proposed developer contract concrete without claiming WG adoption or merchant endorsement.
