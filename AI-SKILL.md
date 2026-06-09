# WCP AI Build — Widget AI Skill

> **Version 1.0.0** | For consumption by any AI engine building a WCP widget.
> Source of truth: [github.com/penrithbeacon/wcp-ai-build-widget](https://github.com/penrithbeacon/wcp-ai-build-widget)

---

## 1. What This Skill Does

This skill walks a developer through the complete **design and build** of a WCP widget —
from first question to a running Docker container with all mandatory WCP endpoints
responding correctly.

**Scope of this skill:**
- ✅ Widget design — intent, components, data, features
- ✅ Technology choice — language, framework, container runtime
- ✅ Widget build — source code, Dockerfile, docker-compose.yml, WCP endpoints
- ✅ Specification document — completed `specification.md`
- ➡ Documentation, audit, deployment — hand off to wcp-ai-release when complete

**Prerequisite reading:** This skill references patterns and standards from:
- [wcp-ai-build AI-SKILL.md Section 2](https://github.com/penrithbeacon/wcp-ai-build/blob/main/AI-SKILL.md) — Technology Negotiation Pattern
- [WIDGET-BUILD-SPEC.md](https://github.com/penrithbeacon/wcp-ai-release/blob/main/standards/WIDGET-BUILD-SPEC.md) — what every WCP widget must implement

---

## 2. Technology Negotiation

Follow the **Technology Negotiation Pattern** defined in
[wcp-ai-build AI-SKILL.md Section 2](https://github.com/penrithbeacon/wcp-ai-build/blob/main/AI-SKILL.md).

For WCP widgets, the technology decision is: **container runtime language and web framework.**

At the time of writing, industry-standard options include:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Python + Flask** | Synchronous micro-framework, minimal boilerplate | ★ AI default — used by all 9 reference WCP widgets; largest community; trivially containerisable |
| Python + FastAPI | Async framework with automatic OpenAPI documentation | Growing enterprise adoption; slightly more complex setup |
| Node.js + Express | JavaScript runtime with mature HTTP framework | Large ecosystem; good for event-driven or real-time widgets |
| Go + net/http or Gin | Compiled, statically typed; minimal container image size | Excellent performance; steeper learning curve; less community tooling |

**AI default: Python + Flask**

_Research current options at build time_ — this table reflects the landscape at version 1.0.0
of these standards. Apply the Technology Negotiation Pattern: ask the developer first, present
options if no preference, proceed with the default on deferral.

---

## 3. Skill: Design the Widget

### Arriving with context

You may arrive here having already gathered information from the developer in
wcp-ai-build — specifically their full description of what they want to build. If so:

- Treat that description as pre-answered design context
- Work through the phases below, but **skip any question that is already clearly answered**
  by the description you were given
- Where the description is partial (e.g. mentions components but not data sources), ask
  only for what is missing
- Do not ask the developer to repeat themselves — acknowledge what you already know and
  confirm your interpretation, then ask only for the gaps

### Docker capability inference

Before asking design questions, apply these inference rules to the developer's description.
Record the inferences and confirm them — do not ask the developer to re-state things you
can already determine.

| If the description mentions… | Infer… |
|-------------------------------|--------|
| Creating, saving, or persisting files | A Docker volume is required. Ask for the mount path in Phase E. |
| A user-configurable root folder or working directory | The volume mount path is set at container start via `docker-compose.yml`. The settings UI configures which subdirectory within the mount is the active root. |
| Browsing or picking ANY folder on the host file system at runtime | A companion agent is required. A running container cannot see beyond its mounted volume. The agent exposes a host filesystem browser endpoint. |
| Reading host system data (processes, installed tools, OS config) | A companion agent is required. |
| Running commands on the host machine | A companion agent is required. |
| External HTTP APIs, computed data, or in-container state only | No agent required. |
| A WYSIWYG or rich text editor | A JavaScript rich text editor library is required in the frontend. Apply the Technology Negotiation Pattern for this choice separately from the backend language choice. |
| A code editor or syntax-highlighted editor | A JavaScript code editor library is required (e.g. CodeMirror, Monaco). Apply Technology Negotiation. |

**If a companion agent is inferred as needed:**
1. Announce it to the developer: _"Based on what you've described, this widget will need a companion agent running on the host machine. I'll be designing both in parallel."_
2. Read [wcp-ai-build-agent AI-SKILL.md](https://github.com/penrithbeacon/wcp-ai-build-agent/blob/main/AI-SKILL.md) and run that pipeline alongside this one within the same conversation.
3. At integration points (port assignment, data contract, `host.docker.internal` reference), ask questions that cover both widget and agent together.
4. The widget should degrade gracefully when the agent is not present — detect availability at startup via a health check to `host.docker.internal:<agent-port>/health` and adjust the UI accordingly.

### Design phases

Work through these phases in order. The developer may answer in abstract terms (features,
use cases, intended outcome) or technical terms — both are fine. Abstract answers are
translated into technical decisions as the phases progress.

### Phase A — Intent

Ask:
1. What does this widget do? _(1–3 sentence description)_
2. Who will use it? What problem does it solve?
3. Is this similar to any existing tool or service the developer is familiar with?

The answers to Phase A inform everything that follows. If the developer is uncertain,
help them articulate the desired outcome in terms of: **what the user sees** and **what
the user can do.**

### Phase B — Components

WCP widgets can have multiple visual components, each rendered in its own iframe card.

Ask:
1. How many visual components does this widget need?
   - A single main view is the most common (and simplest) case
   - Multiple components make sense when different views serve different contexts:
     e.g. a compact dashboard card + a full-page control panel
2. For each component:
   - What does it display?
   - What is its role? (`widget` = main card, `ancillary` = secondary panel, `banner` = top strip, `coda` = bottom strip)
   - What is the default card size? (columns × rows in the dashboard grid)

**⛔ Default size gateway — mandatory before proceeding.**

For every component (including Settings and About if included), you must obtain an
explicit `cols` × `rows` confirmation from the developer before writing any code.
Do not assume or carry forward a vague description — record exact integers.

After the developer answers, repeat the table back to confirm:

> _"Before I build, confirming the default sizes:_
> | Component | cols | rows |
> |-----------|------|------|
> | {name}    | {n}  | {n}  |
> | Settings  | {n}  | {n}  |
> | About     | {n}  | {n}  |
> _Is that correct?"_

These exact values go directly into the widget manifest (`defaultSize` in each
component entry of `GET /widget/wcp`) and **must not change** between design and
implementation. The pre-release audit verifies the live manifest matches these values.

### Phase C — Data and Behaviour

Ask:
1. Does the widget need data from outside itself?
   - External HTTP API (e.g. weather service, GitHub API, financial data)?
   - Local host data (requires an agent — if yes, check whether one exists or needs building)?
   - Static or computed data only (no external dependency)?
2. If an external API is required:
   - Which API?
   - Does it require credentials (API key, OAuth token)?
   - How frequently should data refresh?
3. Does the widget need to remember settings or state between sessions?
   - If yes: a named Docker volume is needed
4. Does the widget accept configuration from the dashboard (e.g. user sets a city for a weather widget)?
   - If yes: `POST /widget/configure` endpoint required
5. Can multiple independent instances of this widget run simultaneously in different cards?
   - Multi-instance: each instance has its own state keyed by `Wcp-Instance-Id`
   - Single-instance: one shared state across all cards

### Phase D — Advanced Features

Ask (these are optional — include only if the developer wants them):
1. **Publish to Web** — should the widget be able to generate a standalone SPA HTML file
   that can be served publicly, independent of the WCP dashboard?
   (Adds `POST /widget/publish` and `DELETE /widget/publish` endpoints)
2. **WCP export** — should the widget be exportable as a `.wcp` package for sharing
   with other WCP users?
   (Adds `GET /widget/export.wcp` endpoint)

### Phase E — Infrastructure

1. Apply the **Technology Negotiation Pattern** for language and framework (Section 2 above).
   If a WYSIWYG or code editor was identified in the Docker inference step, apply a
   **separate** Technology Negotiation for the frontend JavaScript library.

2. Port assignment:
   - Ask the developer if they have a preferred port.
   - If not: suggest the next available port above those in the occupied port set
     recorded in wcp-ai-build Step 1 (from Bonjour query or developer-provided list).

3. **Widget naming and namespace conflict check:**
   - Widget repository and image names follow the pattern: `wcp-widget-<name>`
   - Confirm the name with the developer.
   - Using the stored GitHub PAT, check whether `<github-username>/wcp-widget-<name>`
     already exists on GitHub.
   - Using the stored Docker Hub token, check whether `<dockerhub-username>/wcp-widget-<name>`
     already exists on Docker Hub.
   - If either exists: flag the conflict and ask the developer to choose a different name.
   - Record the confirmed widget name and full repository/image paths.

4. **Standard components — always offer these three:**

   Every widget build must include the following components unless the developer explicitly
   declines. Offer all three and build whichever are accepted.

   **a) The primary component** — the main widget card the developer has described.
   Default size: whatever was agreed in Phase B.

   **b) Settings component** (always offer — default size 12×12, separate WCP card):

   Minimum contents (always include):
   - Port number — displayed prominently so the developer always knows the widget's port
   - Theme selection — the three built-in Penrith Beacon themes, plus the ability to
     upload a `.wcpt` theme file to add any custom theme
   - Root folder path — a text input (or, if a companion agent is present, a folder
     picker) for configuring the widget's working directory

   If a companion agent was identified for this widget, also include:
   - Agent status indicator — shows whether the companion agent is detected at
     `host.docker.internal:<agent-port>/health`
   - Agent installer download — a button/link that downloads the companion agent
     installer directly from the widget container (e.g. `GET /widget/agent/installer`).
     The installer file is bundled inside the Docker image. Include platform detection
     where possible (e.g. offer macOS `.pkg` if the browser user-agent indicates macOS).
     Display installation instructions alongside the download link.

   **c) About component** (always offer — default size 12×12, separate WCP card):

   Mandatory contents:
   - Widget name
   - Description (1–3 sentences)
   - Version number
   - OCI image path — the full Docker Hub image reference (e.g.
     `yourname/wcp-widget-example:1.0.0`). Displayed as copyable text. Not a clickable
     hyperlink at this time.

   Optional contents — ask the developer for each; include if provided, omit if not:
   - GitHub repository URL
   - Author name
   - Author email address
   - Author website URL

5. Confirm the publisher namespace (Docker Hub username, e.g. `penrithbeacon`).

6. **Carry forward to all subsequent pipeline stages:**
   - GitHub username + PAT
   - Docker Hub username + access token
   - Credentials file path
   - Widget name (`wcp-widget-<name>`)
   - Full GitHub repository path
   - Full Docker Hub image path

---

## 4. Skill: Build the Widget

Once all design decisions are complete, build the widget.

### Step 1 — Read the build standard

Read [WIDGET-BUILD-SPEC.md](https://github.com/penrithbeacon/wcp-ai-release/blob/main/standards/WIDGET-BUILD-SPEC.md)
for the complete implementation specification. Key sections:
- **Section A** — Dockerfile and docker-compose.yml structure
- **Section B** — Server application structure (CORS, WCP headers, app runner)
- **Section C** — WCP discovery protocol (`GET /wcp`, `GET /widget/wcp`)
- **Section D** — WCP manifest structure (all required fields)
- **Section E** — Mandatory endpoints (every widget must implement all of these)
- **Section H** — WCP theme reception (every HTML template must implement all five elements)

### Step 2 — Generate the file structure

Create these files (paths relative to the widget repo root):

```
Dockerfile
docker-compose.yml
.dockerignore
.gitignore
{dependency manifest}          ← e.g. requirements.txt, package.json, go.mod
src/
  {entry-point file}           ← e.g. app.py, index.js, main.go
  templates/                   ← HTML templates (or equivalent for chosen framework)
    widget.html                ← compact dashboard view (GET /widget/)
    index.html                 ← widget index page (GET /widget/index)
    {additional-components}.html
  installers/                  ← companion agent installer files (only if agent present)
    {agent-name}.pkg           ← macOS installer — copied into image at build time
README.md                      ← placeholder — filled by wcp-ai-release
DOCKER.md                      ← placeholder — filled by wcp-ai-release
specification.md               ← generated in Step 4 below
audit.md                       ← empty — filled before first release
```

**Companion agent installer bundling:**
If a companion agent was identified for this widget, the agent's compiled installer
(`.pkg` on macOS, equivalent on other platforms) must be physically copied into the
Docker image at build time so that `GET /widget/agent/installer` has a file to serve.

Add to `Dockerfile`:
```dockerfile
COPY src/installers/ ./src/installers/
```

The installer file is placed in `src/installers/` in the source tree before building
the image. During the release pipeline (`wcp-ai-release`), the agent's installer is
built first, then copied here before the widget image is built. This ensures the
installer served from the widget is always the version that shipped with this image.

If the installer is not yet available at widget build time, the endpoint should return
`503 Service Unavailable` with a body pointing to the agent's GitHub Releases page,
rather than a `404` — this signals "not yet available" rather than "does not exist".

### Step 3 — Implement all mandatory WCP endpoints

Every widget must implement all of these. Refer to WIDGET-BUILD-SPEC.md for the exact
response format of each:

| Endpoint | Returns | Notes |
|----------|---------|-------|
| `GET /wcp` | JSON | Container Directory — discovery |
| `GET /widget/wcp` | JSON | Widget Manifest + `web.published` status |
| `OPTIONS /wcp` | 204 | CORS preflight (covers all widget routes) |
| `GET /widget/` | HTML | Compact dashboard view |
| `GET /widget/index` | HTML | Widget Index — lists all controls |
| `GET /widget/health` | JSON | `{ "status": "ok", "name": "...", "container": "..." }` |
| `GET /widget/icon.svg` | SVG | Widget icon |
| `GET /widget/api/guids` | JSON | Component UUIDs for orchestration binding |
| `GET /widget/logs` | JSON | WCP logs protocol — self-describing log envelope |

**WCP logs protocol** — the `/widget/logs` response must follow this structure:

```json
{
  "schema": "wcp-logs/1.0",
  "container": "<container-name>",
  "entries": [
    { "ts": "<ISO8601Z>", "level": "info|warn|error", "msg": "..." }
  ]
}
```

Support optional query parameters: `?limit=N`, `?level=info|warn|error`, `?since=<ISO8601Z>`.
Entries are held in an in-memory ring buffer (suggested max 500 entries). The endpoint
always returns 200 with an empty `entries` array if no logs have been recorded.

### Step 4 — Implement optional endpoints

Based on Phase D decisions:
- Publish to Web: `POST /widget/publish`, `DELETE /widget/publish`, `GET /`
- WCP export: `GET /widget/export.wcp`
- Configuration: `POST /widget/configure`
- Widget-specific data endpoints: whatever the widget's Phase C requirements demand

### Step 5 — Implement HTML templates

Every HTML template must include all five WCP theme reception elements.
**Do not reference an external document for these — implement exactly as shown below.**
Copy this block verbatim into every `<script>` section, immediately after the
`wcp:request-theme` postMessage line:

```javascript
// 1. WCP ready + theme request
window.parent.postMessage({ type: 'wcp:ready' }, '*');
window.parent.postMessage({ type: 'wcp:request-theme' }, '*');

// 2. #wcp-theme= hash reading (WCP 2.x standard — base64 encoded)
if (window.location.hash.startsWith('#wcp-theme=')) {
  try {
    const _fvars = JSON.parse(atob(window.location.hash.slice(11)));
    for (const [k, v] of Object.entries(_fvars)) document.documentElement.style.setProperty(k, v);
  } catch {}
}

// 3. postMessage theme listener
window.addEventListener('message', e => {
  if ((e.data?.type === 'wcp:theme' || e.data?.type === 'wcp:context') && e.data.theme)
    Object.entries(e.data.theme).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
});
```

**Critical — `#wcp-theme=` uses base64 (`atob`), NOT URL-encoding (`decodeURIComponent`).**
The dashboard encodes the theme as `btoa(JSON.stringify(themeVars))`. Any template that
uses `decodeURIComponent` or the old `wcp:theme=` (colon) hash format is non-compliant.

All five elements must be present in every template:
1. `wcp:ready` postMessage ✓ (in block above)
2. `wcp:request-theme` postMessage ✓ (in block above)
3. `#wcp-theme=` hash reading — `atob` base64 decode ✓ (in block above)
4. `wcp:context` + `wcp:theme` message listener ✓ (in block above)
5. Theme variable application — `setProperty` loop ✓ (in block above)

### Step 6 — Build and verify

**Important — docker-compose.yml must include `build: .`**

The generated `docker-compose.yml` must include a `build:` directive so that
`docker compose build` works for local development. Without it, the `image:` key
references the Docker Hub image and `docker compose build` reports "No services
to build". The correct pattern is both together:

```yaml
services:
  wcp-widget-{widget-id}:
    build: .
    image: {dockerhub-username}/wcp-widget-{widget-id}:latest
```

With `build: .` present, `docker build` and `docker compose build` both work
locally, while `docker compose up` (without a prior build) will pull from Docker Hub
if no local image exists.

```bash
# Build and start the container
docker build -t wcp-widget-{widget-id}:local .
docker compose up -d

# Verify mandatory endpoints
PORT={port}
curl -s http://localhost:$PORT/wcp | python3 -m json.tool
curl -s http://localhost:$PORT/widget/wcp | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://localhost:$PORT/wcp
curl -s http://localhost:$PORT/widget/health | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/widget/
curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/widget/index
```

All mandatory endpoints must return 200 (or 204 for OPTIONS) before proceeding.

**Verify `defaultSize` matches the Phase B confirmed values:**

```bash
curl -s http://localhost:$PORT/widget/wcp | python3 -c "
import sys,json
d=json.load(sys.stdin)
for c in d['components']:
    print(c['name'], '->', c['defaultSize'])
"
```

Compare the output against the table confirmed with the developer in Phase B.
If any `cols` or `rows` value differs from what was confirmed, fix the manifest
before proceeding. The developer cannot add the widget with the correct size
unless the manifest carries the right values.

**Always tell the developer the port and manifest URL at this point.** The developer
cannot add the widget to an orchestration without knowing these. After the container
starts and all endpoints pass, say:

> _"The widget is running. To add it to an orchestration in your WCP host studio:_
> _- Port: **{port}**_
> _- Manifest URL: **http://localhost:{port}/widget/wcp**_
> _Paste the manifest URL into the Add Widget dialog."_

---

## 5. Skill: Generate the Specification

Use [templates/specification.md](https://github.com/penrithbeacon/wcp-ai-release/blob/main/templates/specification.md)
from wcp-ai-release to produce a completed `specification.md` for the widget repo.

Populate it with the decisions made in Section 3 (Design) and the endpoints implemented
in Section 4 (Build). The specification records the design intent alongside the technical
implementation — it is the authoritative reference for all future changes to this widget.

---

## 6. Mandatory Handoff to Release Pipeline

> ⛔ **The build is not complete until the release pipeline passes its audit gate.**
> A widget that starts with `docker compose up` is *built*. A widget that has passed
> the wcp-ai-release audit and is published on Docker Hub is *released*. These are
> not the same. Do not consider this work done until the release pipeline completes.

### Before handing off — confirm all of the following:

- [ ] All mandatory endpoints return 200 / 204 (Step 6 verification curls pass)
- [ ] `GET /widget/logs` returns a valid WCP logs envelope
- [ ] If a companion agent is present: `GET /widget/api/agent/status` is implemented
- [ ] If a companion agent is present: `src/installers/` contains the agent `.pkg`
      (or the endpoint returns 503 with a GitHub Releases URL in the body)
- [ ] `specification.md` has been generated (Section 5 above)

### Alpha kiosk stage — human QA (required before first release)

Before running the release pipeline, the widget must be tested in a real dashboard
environment. This is a **human-driven stage** — the AI's role is advisory (debug,
implement feature requests, answer questions). There is no scripted endpoint; the
developer decides when the widget is ready to graduate to beta.

In your WCP host studio:

1. Create a new orchestration
2. Add the widget card(s) to the orchestration layout
3. Mark the orchestration as an application
4. Launch it from the **alpha kiosk**
5. Verify the widget works as expected — layout, theme reception, all interactions,
   Settings component, About component, agent status (if applicable)
6. Iterate: fix bugs, add features, adjust layout — until satisfied with the result

> **What is an alpha kiosk?**
> WCP hosts support three kiosk stages that mirror a standard software release cycle:
> - **Alpha kiosk** — development and internal QA; local only; no public release
> - **Beta kiosk** — pre-release testing; first public publication; beta tag on Docker Hub
> - **Release kiosk** — production; stable tag on Docker Hub; ready to ship
>
> The alpha kiosk is the appropriate environment for initial testing. The widget is
> not published publicly at this stage. When the developer is satisfied, they graduate
> it to beta — which is where the release pipeline first runs.

### Dry run during orchestration building — offer this proactively

Building the first orchestration in the WCP host studio takes a few minutes. This is
a natural opportunity for the AI to run a **dry-run beta release in parallel** — it
validates the full release pipeline (all WCP spec endpoints, documentation generation,
audit gate) without publishing anything publicly.

**At the point where you hand the developer over to the studio, say:**

> _"While you're building the orchestration, I can run a dry-run release right now in
> parallel. It validates all WCP spec requirements, generates the documentation, and
> reports exactly what a live release would do — without pushing anything to Docker Hub
> or GitHub. This often catches endpoint path issues or spec gaps early, while you have
> something productive to do in the studio. Want me to run the dry run now?"_

If the developer agrees, read
[wcp-ai-release AI-SKILL.md](https://github.com/penrithbeacon/wcp-ai-release/blob/main/AI-SKILL.md)
with stage = **beta** and mode = **dry run**. Report the full dry-run result when the
developer returns from the studio. Fix any issues found before proceeding to a live release.

### Hand off

Tell the developer:

> _"The widget is verified locally and ready for alpha kiosk testing. Add it to an
> orchestration in your WCP host studio, launch it from the alpha kiosk, and complete
> your QA. When you're satisfied and ready to make your first public (beta) release,
> read https://github.com/penrithbeacon/wcp-ai-release/blob/main/AI-SKILL.md
> and follow it."_

**Carry forward to wcp-ai-release:**
- Widget name (`wcp-widget-<name>`)
- Full GitHub repository path
- Full Docker Hub image path (`<dockerhub-username>/wcp-widget-<name>`)
- Widget port
- Credentials file path
- Whether a companion agent is present (name and port if so)
- Release stage: **beta** (first release from alpha kiosk) or **release** (graduating from beta kiosk)
