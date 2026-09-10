# Interview verification evidence

Recorded 10 September 2026. This is observed evidence, not a claim that mocked tests validate the live integration.

## Automated checks

- Backend: 99 pytest tests passed, including exact legacy-title matching, all asset payload mappings, and primary commit visibility from a separate Session before simulated Zendesk failure. Two dependency deprecation warnings remain.
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

Each is active with ALL Status less than Solved and no ANY conditions. The proposed narrow change is only an added Brand IS NOT Royal Tyres condition, retaining the existing action/conditions/state/title/order. The owner approved these six exact exclusions. Fresh definitions matched the retained reviewed originals; the existing safeguard service applied only the added exclusion. All thirteen preservation checks passed. Expanded plan fingerprint: `9f2b47863be9da01cbcd8a75b7f27ea12a89d98ed56ec6719ee28f3df253a8aa`.

## Callback and email

Pending was not submitted after the field/tag verification failed. Therefore there is no claimed successful webhook HTTP request, status-change audit or Pending portal synchronization from this run. No email delivery has been confirmed. The connected mail account is not the configured demo receiver; actual delivery remains a receiver-inbox check.

## Hosting issue

Direct GET `/request` returned HTTP 404 while `/` served the application. Render needs a Static Site **Rewrite**, source `/*`, destination `/index.html`, to support SPA deep links and refreshes. The repository's Vercel rewrite file does not configure Render. Existing resources are served before rewrites according to [Render's documented rule matching](https://render.com/docs/redirects-rewrites). The owner signed in and the exact rewrite was saved in Render. Subsequent direct GETs to `/`, `/request`, `/requests/5`, and `/settings` returned HTTP 200 with the React root markup.

## Targeted security review

Basic Auth protects request/setup routes (live unauthenticated request returned 401). Webhook authentication is a separate bearer check. Hosted CORS preflight permits the exact Render frontend origin; tests reject unconfigured origins. Pydantic validates input and suppresses raw values in errors. ORM queries use bound values; the SQL-injection regression treats attack-shaped input as data. React renders user text normally and the browser XSS regression passes. Changed files/docs and frontend environment were checked against configured secret values without printing them. No configured secret was found. Secrets remain server-side; no Authorization values are included in this report.

## Replacement request and remaining stop boundary

The permitted replacement test was made because request 5 failed retention. No other fresh requests were created in this pass.

- React submitted request **6**, HTTP 201; real Zendesk ticket **56**; external ID `royal-tires-asset-6`; asset Other.
- Render PostgreSQL confirms request 6 remains persisted, status `new`, Zendesk status `new`, sync state `synced`, last synced `2026-09-10T21:49:31.906434Z`.
- Brand/group/form and local-ID field remain correct. Asset/source dropdowns and required tags were initially supplied correctly but overwritten by additional automation. `synced` records successful ticket creation, not field-retention validation.
- Ticket 56 audit identifies **Query Type 8 (27650061836572)**, **Issue Type 8 (27695960731292)**, **Request Type 8 (27698470929052)** and **Query Type 7 (2) (28370770616604)** replacing tags. The owner subsequently approved these four exact exclusions; all seventeen read-back preservation checks passed.
- Each has ALL Status less than Solved, no ANY conditions, and one set_tags action. A controlled Pending update then exposed further tag-replacement rules. A complete read-only inventory found thirteen remaining active set_tags rules, each with only Status less than Solved. The owner approved those exact names/IDs, recorded in PROJECT_SPEC.md.
- Email generation/delivery remains unverified. The integration is re-tested below after the final approved exclusions.

The failed Pending attempt changed ticket 56 remotely but the portal remained New because the tag-dependent callback did not match. No additional request was submitted. The final test repairs the same ticket, restores Open (Zendesk rejects resetting to New), and then changes it to Pending.

## Final safeguards and demonstrated callback bug

All thirty explicitly approved safeguards passed preservation/read-back checks; the last plan fingerprint was `85b74616c8fc54b40b0d030c5aa5dc35ca08f94056ef4cd940b6266250577ea1`. Only brand exclusions were added. Original JSON definitions are retained locally outside Git.

Ticket 56 was repaired in place and now retains Brand/Group/Form, all three managed fields, the required portal/request tags and external ID. Its Open-to-Pending audit records both the status-email `External` event and status-sync `WebhookEvent`. That proves trigger execution, not inbox delivery. No third request was created.

Render received POST `/api/webhooks/zendesk` at 21:55:54 and 21:56:20 UTC, but returned 422. Zendesk's invocation-attempt payload showed status `Pending`; the safe response identified the lowercase status literal validation failure. Headers were not inspected or recorded. `WebhookStatus` input normalization now accepts trimmed/case-normalized known labels while rejecting unknown values; regression tests verify Pending reaches the tracking API and invalid values still return 422. Portal/database statuses remain lowercase. Authentication and correlation behavior are unchanged.

The source fix passes all 99 backend tests. The deployed callback must be rechecked after the PR's automatic Render deployment; final CI/deployment/runtime evidence is recorded on PR #19. No successful callback is claimed by this pre-deployment snapshot. New-request email execution was blocked at initial creation and remains unverified; status-email execution is evidenced, actual delivery remains an inbox check.
