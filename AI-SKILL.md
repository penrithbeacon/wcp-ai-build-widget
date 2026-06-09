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
- ➡ Documentation, audit, deployment — hand off to wcp-ai-automation when complete

**Prerequisite reading:** This skill references patterns and standards from:
- [wcp-ai-build AI-SKILL.md Section 2](https://github.com/penrithbeacon/wcp-ai-build/blob/main/AI-SKILL.md) — Technology Negotiation Pattern
- [WIDGET-BUILD-SPEC.md](https://github.com/penrithbeacon/wcp-ai-automation/blob/main/standards/WIDGET-BUILD-SPEC.md) — what every WCP widget must implement

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
   - What is a reasonable default card size? (columns × rows in the dashboard grid)

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

Read [WIDGET-BUILD-SPEC.md](https://github.com/penrithbeacon/wcp-ai-automation/blob/main/standards/WIDGET-BUILD-SPEC.md)
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
README.md                      ← placeholder — filled by wcp-ai-automation
DOCKER.md                      ← placeholder — filled by wcp-ai-automation
specification.md               ← generated in Step 4 below
audit.md                       ← empty — filled before first release
```

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

### Step 4 — Implement optional endpoints

Based on Phase D decisions:
- Publish to Web: `POST /widget/publish`, `DELETE /widget/publish`, `GET /`
- WCP export: `GET /widget/export.wcp`
- Configuration: `POST /widget/configure`
- Widget-specific data endpoints: whatever the widget's Phase C requirements demand

### Step 5 — Implement HTML templates

Every HTML template must include all five WCP theme reception elements
(see WIDGET-BUILD-SPEC.md Section H):
1. `wcp:ready` postMessage
2. `wcp:request-theme` postMessage
3. `#wcp-theme=` hash reading
4. `wcp:context` + `wcp:theme` message listener
5. Theme variable application (`setProperty` loop)

### Step 6 — Build and verify

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

---

## 5. Skill: Generate the Specification

Use [templates/specification.md](https://github.com/penrithbeacon/wcp-ai-automation/blob/main/templates/specification.md)
from wcp-ai-automation to produce a completed `specification.md` for the widget repo.

Populate it with the decisions made in Section 3 (Design) and the endpoints implemented
in Section 4 (Build). The specification records the design intent alongside the technical
implementation — it is the authoritative reference for all future changes to this widget.

---

## 6. Handoff to Deployment

The widget is built, running, and verified. Now hand off to wcp-ai-automation:

> _"Read https://github.com/penrithbeacon/wcp-ai-automation/blob/main/AI-SKILL.md
> and use it to create documentation for this widget and prepare it for release."_

The automation skill will:
- Generate `README.md` and `DOCKER.md` from the running container
- Run the full pre-release audit against every WCP requirement
- Walk through the Docker Hub deployment workflow
