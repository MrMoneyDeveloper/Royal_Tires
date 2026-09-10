# Interview verification evidence

Recorded 10 September 2026. This is observed evidence, not a claim that mocked tests validate the live integration.

## Automated checks

- Backend: 70 pytest tests passed, including exact legacy-title matching, all asset payload mappings, and primary commit visibility from a separate Session before simulated Zendesk failure. Two dependency deprecation warnings remain.
- Frontend: 11 Node unit tests passed; Vite production build passed.
- Playwright: 8 desktop/mobile Chromium tests passed. These intercept API responses and do not call the live sandbox.
- CI and merge status are recorded in the pull request; passing local tests alone is not CI evidence.

## Governed configuration

- Hosted connection test returned HTTP 200 with an admin identity; no credentials are recorded here.
- All 12 managed resources were REUSE. Hosted approved apply returned HTTP 200 and read-back PASS for all 12.
- Six original legacy safeguards were already protected and verified unchanged.
- Discovery proved the seventh actual title is `hello world`, ID `28978973387036`, rather than `hello world?`. The owner explicitly approved that correction and its single Brand IS NOT Royal Tyres exclusion.
- The corrected existing safeguard service was run from the reviewed branch with a freshly compared plan and retained original definitions. All seven preservation checks passed. Guard plan fingerprint: `91b7aaed226bafcdf705952b3a6deb0c64b59ceaf6c89393c1dba5b70a8f806d`.
- The currently deployed older allowlist still reports the question-mark title as SKIP; the corrected code is in the final PR. No unlisted trigger was changed.
- Managed read-back checks IDs; the subsequent ticket audit supplies evidence about actual field/tag behavior.

## One fresh hosted request

| Evidence | Result |
| --- | --- |
| Frontend | Render Static Site, entered through `/` |
| Creation | HTTP 201 at 21:33:28 UTC |
| Local request ID | 5 |
| Zendesk ticket ID | 55 |
| External ID | `royal-tires-asset-5` |
| Asset | Other |
| PostgreSQL | `royal_tires` database confirms persisted request 5 |
| Portal/Zendesk status | new / new |
| Sync state | synced (ticket creation succeeded; this is not field-verification status) |
| Last synced | 2026-09-10T21:33:28.059817Z |
| Audit | REQUEST_CREATED at 21:33:26.994250Z; ZENDESK_TICKET_CREATED at 21:33:28.063014Z |
| Render logs | Matching `event=REQUEST_CREATED request_id=5` and `event=ZENDESK_TICKET_CREATED request_id=5` |
| Browser | In-app navigation to `/requests/5` worked; no page errors or browser Zendesk requests |
| Brand/group/form | Correct Royal Tyres IDs retained |
| Custom fields/tags | Initially submitted correctly; subsequently overwritten by other sandbox triggers |

The timestamped SQL records and audit confirm primary persistence. The regression test separately verifies that a different Session sees the primary commit before the Zendesk call fails.

## Unexpected configuration: stop boundary

Ticket 55's Zendesk audit identifies these additional rules replacing tags. They are outside the original seven-title allowlist. Live changes stopped rather than silently expanding scope.

| Exact title | ID | Existing action |
| --- | --- | --- |
| Issue Category 2 2 | 27601293620508 | set_tags: billing |
| Request Type 5 | 27625845148444 | set_tags: equipment_fault |
| Query Type 7 | 27650068343452 | set_tags: hnw_withdrawal |
| Issue Type 7 | 27695967421724 | set_tags: missing_parcel |
| Request Type 7 | 27698487674012 | set_tags: emergency_maintenance |
| Query Type 6 (2) | 28370722368028 | set_tags: customer_complaint |

Each is active with ALL Status less than Solved and no ANY conditions. The proposed narrow change is only an added Brand IS NOT Royal Tyres condition, retaining the existing action/conditions/state/title/order. Separate owner approval is required.

## Callback and email

Pending was not submitted after the field/tag verification failed. Therefore there is no claimed successful webhook HTTP request, status-change audit or Pending portal synchronization from this run. No email delivery has been confirmed. The connected mail account is not the configured demo receiver; actual delivery remains a receiver-inbox check.

## Hosting issue

Direct GET `/request` returned HTTP 404 while `/` served the application. Render needs a Static Site **Rewrite**, source `/*`, destination `/index.html`, to support SPA deep links and refreshes. The repository's Vercel rewrite file does not configure Render. Existing resources are served before rewrites according to [Render's documented rule matching](https://render.com/docs/redirects-rewrites). Dashboard access is required to apply this rule with the available tools.

## Targeted security review

Basic Auth protects request/setup routes (live unauthenticated request returned 401). Webhook authentication is a separate bearer check. Hosted CORS preflight permits the exact Render frontend origin; tests reject unconfigured origins. Pydantic validates input and suppresses raw values in errors. ORM queries use bound values; the SQL-injection regression treats attack-shaped input as data. React renders user text normally and the browser XSS regression passes. Changed files/docs and frontend environment were checked against configured secret values without printing them. No configured secret was found. Secrets remain server-side; no Authorization values are included in this report.
