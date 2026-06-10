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

   **Start from `boilerplate/settings.html`** in this repo — it is the canonical
   template and includes all mandatory patterns pre-wired (theme sync, wcp:request-theme,
   wcp:theme-apply, .wcpt import, radio-button active-theme sync). Do NOT write
   settings.html from scratch.

   Minimum contents (always include):
   - Port number — displayed prominently so the developer always knows the widget's port
   - Theme selection — the three built-in Penrith Beacon themes, plus the ability to
     upload a `.wcpt` theme file to add any custom theme

   **Critical — theme radio-button sync:** The active theme radio button must reflect
   the dashboard's actual active theme, not just the widget's locally stored preference.
   The host broadcasts `wcp:theme` with a `themeId` field (WCP 2.2.0+). The settings
   page must handle this:
   ```javascript
   window.addEventListener('message', e => {
     if ((e.data?.type === 'wcp:theme' || e.data?.type === 'wcp:context') && (e.data.vars || e.data.theme)) {
       applyTheme(e.data.vars || e.data.theme);
       const hostId = e.data.themeId;
       if (hostId && hostId !== _activeThemeId) {
         _activeThemeId = hostId;
         renderThemeList();  // re-renders radio buttons with correct selection
       }
     }
   });
   ```
   Without this, the radio button always shows the widget's stored default (dark)
   regardless of which theme the dashboard is actually showing.

   **Agent installer download (if companion agent present):** Use `wcp:download-file`
   postMessage — do NOT use `<a href="..." download>`. The `download` attribute is
   blocked in Electron sandboxed iframes. Pattern:
   ```javascript
   async function downloadInstaller(btn) {
     btn.disabled = true;
     const r = await fetch('/widget/agent/installer', {method:'HEAD'});
     if (r.ok) {
       window.parent.postMessage({
         type: 'wcp:download-file',
         data: `${location.protocol}//${location.host}/widget/agent/installer`,
         filename: 'WCP-{WidgetName}-Agent.pkg'
       }, '*');
       setTimeout(() => { btn.textContent = 'Download Agent Installer'; btn.disabled = false; }, 2000);
     } else {
       // Installer not yet bundled — open releases page
       window.parent.postMessage({type:'wcp:open-window', url:'https://github.com/{owner}/{repo-agent}/releases'}, '*');
       btn.disabled = false;
     }
   }
   ```

   If a companion agent was identified for this widget, also include:
   - Agent status indicator — shows whether the companion agent is detected at
     `host.docker.internal:<agent-port>/health`
   - Agent installer download (see pattern above)

   **c) About component** (default size 12×12, separate WCP card):

   **Start from `boilerplate/about.html`** in this repo — it is the canonical template.
   Fill in the `{placeholders}`, delete optional rows not provided, add one `.row`
   per third-party dependency.

   **Mandatory if the widget uses any third-party JS libraries (almost always true).**
   Always offer this component; it is the correct place to document open-source
   attributions. See Step 5b for the full third-party licensing audit requirement.

   Mandatory contents:
   - Widget name
   - Description (1–3 sentences)
   - Version number
   - OCI image path — the full, correctly-formed OCI reference. See **OCI path
     construction** below. Displayed as copyable text. Not a clickable hyperlink.
   - **Open Source Components card** (mandatory when any third-party deps exist — see Step 5b)

   Optional contents — ask the developer for each; include if provided, omit if not:
   - GitHub repository URL
   - Author name
   - Author email address
   - Author website URL

   **Complete About page template** — copy, fill in `{placeholders}`, delete optional rows if not provided:

   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
   <meta charset="UTF-8">
   <title>{Widget Name} — About</title>
   <script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication","name":"{Widget Name}","version":"{{ version }}"}</script>
   <style>
   :root{--wcp-color-bg:#0d1117;--wcp-color-surface:#161b22;--wcp-color-surface-raised:#1c2128;--wcp-color-border:#30363d;--wcp-color-text:#e6edf3;--wcp-color-text-muted:#8b949e;--wcp-color-primary:#f0883e;--wcp-color-success:#3fb950;--wcp-color-danger:#f85149;--wcp-radius-md:8px}
   *{box-sizing:border-box;margin:0;padding:0}
   *::-webkit-scrollbar{width:8px}*::-webkit-scrollbar-track{background:var(--wcp-color-surface)}*::-webkit-scrollbar-thumb{background:var(--wcp-color-border);border-radius:4px}
   html,body{height:100%;background:var(--wcp-color-bg);color:var(--wcp-color-text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}
   .wrap{height:100%;overflow-y:auto;padding:12px}
   .section{background:var(--wcp-color-surface);border:1px solid var(--wcp-color-border);border-radius:var(--wcp-radius-md);padding:14px 16px;margin-bottom:12px}
   .section h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--wcp-color-text-muted);margin-bottom:12px}
   .row{display:flex;justify-content:space-between;align-items:flex-start;padding:5px 0;border-bottom:1px solid var(--wcp-color-border);gap:12px}
   .row:last-child{border-bottom:none}
   .lbl{font-size:12px;color:var(--wcp-color-text-muted);flex-shrink:0}
   .val{font-size:12px;text-align:right;word-break:break-all}
   .oci{font-family:monospace;font-size:11px;background:var(--wcp-color-surface-raised);border:1px solid var(--wcp-color-border);border-radius:4px;padding:6px 10px;margin-top:6px;user-select:all;line-height:1.5;color:var(--wcp-color-text)}
   </style>
   </head>
   <body>
   <div class="wrap">

     <div class="section">
       <h2>Widget</h2>
       <div class="row"><span class="lbl">Name</span><span class="val">{Widget Name}</span></div>
       <div class="row"><span class="lbl">Description</span><span class="val">{1–3 sentence description}</span></div>
       <div class="row"><span class="lbl">Version</span><span class="val">{{ version }}</span></div>
       <div class="row"><span class="lbl">WCP</span><span class="val">{{ wcp_version }}</span></div>
     </div>

     <div class="section">
       <h2>Technical</h2>
       <div class="row"><span class="lbl">Port</span><span class="val">{{ port }}</span></div>
       <div class="row"><span class="lbl">Container</span><span class="val">{container-name}</span></div>
       <div class="row"><span class="lbl">OCI Image</span><span class="val" style="width:100%">
         <div class="oci">{{ oci_path }}</div>
       </span></div>
       <!-- Optional rows — include each only if the developer provides the value -->
       <div class="row"><span class="lbl">GitHub</span>
         <span class="val"><a href="https://github.com/{owner}/{repo}" style="color:var(--wcp-color-primary);text-decoration:none">github.com/{owner}/{repo}</a></span>
       </div>
       <div class="row"><span class="lbl">Author</span><span class="val">{Author Full Name}</span></div>
       <div class="row"><span class="lbl">Author email</span><span class="val"><a href="mailto:{email}" style="color:var(--wcp-color-primary);text-decoration:none">{email}</a></span></div>
       <div class="row"><span class="lbl">Author URL</span><span class="val"><a href="{url}" style="color:var(--wcp-color-primary);text-decoration:none">{url-short}</a></span></div>
     </div>

     <!-- Open Source Components — mandatory when any third-party JS/CSS deps exist -->
     <div class="section">
       <h2>Open Source Components</h2>
       <p style="font-size:12px;color:var(--wcp-color-text-muted);margin-bottom:10px;line-height:1.5">
         This widget uses the following open-source libraries. All are MIT Licensed.
       </p>
       <div class="row"><span class="lbl">{Library} {Version}</span>
         <span class="val" style="color:var(--wcp-color-text-muted)">{Role} · <a href="{url}" style="color:var(--wcp-color-primary);text-decoration:none">{url-short}</a></span>
       </div>
       <!-- one .row per dependency -->
     </div>

   </div>
   <script>
   function applyTheme(t){Object.entries(t).forEach(([k,v])=>document.documentElement.style.setProperty(k,v));}
   window.parent.postMessage({type:'wcp:ready'},'*');
   window.parent.postMessage({type:'wcp:request-theme'},'*');
   (function(){const QK='com.doc.widgetcontextprotocol';const raw=new URLSearchParams(location.search).get(QK)||(location.hash.startsWith('#wcp-theme=')?location.hash.slice(11):null);if(!raw)return;try{const p=JSON.parse(atob(raw));applyTheme(p.vars||p);}catch{}})();
   window.addEventListener('message',e=>{if((e.data?.type==='wcp:theme'||e.data?.type==='wcp:context')&&(e.data.vars||e.data.theme))applyTheme(e.data.vars||e.data.theme);});
   </script>
   </body>
   </html>
   ```

   **Rules:**
   - The WCP version row (`{{ wcp_version }}`) must match the manifest's `wcpVersion` field.
   - The OCI image (`{{ oci_path }}`) is injected by the server from the manifest — display it in a monospace copyable `<div class="oci">` block, never as a hyperlink.
   - Author email must be a `mailto:` link; Author URL must be a full `https://` hyperlink.
   - Delete optional rows (`GitHub`, `Author`, `Author email`, `Author URL`) only if the developer explicitly has no value for them. All four should be offered to the developer — they are part of the standard widget metadata, not truly optional from a QA perspective.

5. Confirm the publisher namespace (Docker Hub username, e.g. `penrithbeacon`).

### OCI path construction

An OCI path is the fully-qualified, protocol-prefixed reference to a container image
as defined by the OCI Distribution Specification. It is NOT a Docker Hub short path
(`namespace/image:tag`) — it includes the protocol scheme and the registry hostname.

**Format:**
```
oci://<registry>/<namespace>/<image-name>:<tag>
```

**Components:**

| Component | What it is | Example |
|-----------|-----------|---------|
| `oci://` | OCI protocol scheme — always this prefix | `oci://` |
| `<registry>` | Registry hostname. For Docker Hub: `docker.io` | `docker.io` |
| `<namespace>` | Docker Hub account or organisation name | `penrithbeacon` |
| `<image-name>` | Repository name within the namespace | `wcp-widget-markdown-editor` |
| `:<tag>` | Version tag (semver for releases; `latest` for tip) | `:1.0.0` |

**Worked example for this widget ecosystem:**
```
oci://docker.io/penrithbeacon/wcp-widget-markdown-editor:1.0.0
```

**Rules:**
- Always include `oci://` — without it the string is a Docker short reference, not an OCI path
- Always use `docker.io` for Docker Hub — `hub.docker.com` is the web UI, not the registry
- The tag for a release is the semantic version (`1.0.0`), not `latest`; `latest` is acceptable
  as an additional tag but the OCI path displayed to users in the About page should be the versioned tag
- The `about.html` template must display this as:
  `oci://docker.io/<namespace>/<image-name>:{{ version }}`
  where `{{ version }}` is the Flask template variable

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

### Step 2b — Instance ID: read from both header AND query parameter

**⛔ Mandatory — without this, multi-instance configuration is completely broken.**

The WCP host passes the instance ID in two different ways:
- **API calls** (fetch from within the iframe): `Wcp-Instance-Id` header
- **Page loads** (iframe src URL): `?wcpInstanceId=` query parameter

Browsers cannot add custom headers to iframe src loads. The host appends `?wcpInstanceId=<uuid>` to the widget URL. Your server-side template renderer will receive this as a query param, not a header.

Your `instance_id_from_request()` function (or equivalent) **must check both**:

```python
def instance_id_from_request():
    return (request.headers.get('Wcp-Instance-Id')
            or request.args.get('wcpInstanceId', 'default'))
```

If you only read the header, every page render uses `'default'` as the instance ID,
configuration is never found, and per-instance state (root folder, settings, etc.)
never loads.

**Also:** when rendering a template, always substitute sensible defaults for unconfigured
values — do not pass empty strings that the frontend then has to re-check:

```python
# Wrong — empty root makes JS think "not configured", sidebar hides:
root=cfg.get('root', '')

# Correct — default to your working directory so the widget works immediately:
root=cfg.get('root', '') or WORKSPACE
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
| `GET /widget/logs` | JSON | WCP logs protocol — self-describing log envelope |
| `POST /widget/bonjour` | JSON | **WCP 2.2.0** — Bonjour port-change notification (see below) |

**`POST /widget/bonjour` — Bonjour agent port-change notification (WCP 2.2.0 mandatory)**

The Bonjour agent calls this endpoint on all registered containers when its own port changes.
Do **not** implement this manually — use the `wcp_bonjour.py` boilerplate module:

```python
# In app.py, after creating the Flask app:
import wcp_bonjour
wcp_bonjour.flask_route(app)   # registers POST /widget/bonjour automatically
```

And at startup (in a daemon thread so it does not block Flask):
```python
import threading
threading.Thread(
    target=wcp_bonjour.init,
    kwargs=dict(
        name="wcp-widget-mywidget",
        port=PORT,
        companion_widget="wcp-widget-mywidget",
        version="1.0.0",
    ),
    daemon=True,
).start()
```

**Copy `boilerplate/wcp_bonjour.py` from this repo into the widget's `src/` directory alongside `app.py`.** It is stdlib-only (no pip dependency). The module handles: port file discovery, in-memory caching, registration with the Bonjour agent (with retry), and the `/widget/bonjour` notification endpoint.

**`GET /widget/wcp` — component `path` must be an absolute URL.**

Each component entry in the manifest must have its `path` as a fully-qualified absolute
URL — not a relative path. The WCP host reads `path` directly and must be able to load it
in an iframe without knowing the widget's base URL separately.

```python
# Correct — absolute URL:
"path": f"http://localhost:{PORT}/widget/"

# Wrong — relative path (will break iframe loading in the host):
"path": "/widget/"
```

The `defaultSize` field uses `cols` and `rows` (not `w` and `h`):

```python
"defaultSize": { "cols": 12, "rows": 12 }   # ✅ WCP 2.x
"defaultSize": { "w": 12, "h": 12 }         # ❌ WCP 1.x — do not use
```

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

### Theme reception — correct implementation

The Penrith Beacon dashboard broadcasts theme vars with `--wcp-color-*` names
(e.g. `--wcp-color-bg`, `--wcp-color-surface`, `--wcp-color-primary`). These are the
**WCP-standard token names** and must be what the widget's CSS also uses.

**Recommended approach:** write widget CSS using `--wcp-color-*` names directly, with
fallback values in `:root` for standalone use. Example:

```css
:root {
  --wcp-color-bg: #1e1e2e;
  --wcp-color-surface: #2a2a3e;
  --wcp-color-primary: #89b4fa;
  /* etc. */
}
html, body { background: var(--wcp-color-bg); color: var(--wcp-color-text); }
```

When the dashboard broadcasts a theme, it overwrites these `:root` values and the widget
re-renders with the host's colour scheme automatically — no mapping needed.

**If the widget uses internal alias names** (e.g. `--bg`, `--accent`, `--surface2`) the
`applyTheme` function must map WCP tokens to those aliases, otherwise theme changes arrive
but nothing in the CSS responds:

```javascript
function applyTheme(t) {
  // Map standard --wcp-color-* tokens to any internal alias vars the widget CSS uses.
  // If your widget CSS uses --wcp-color-* directly, the MAP can be omitted.
  const MAP = {
    '--wcp-color-bg':            '--bg',
    '--wcp-color-surface':       '--surface',
    '--wcp-color-surface-raised':'--surface2',
    '--wcp-color-border':        '--border',
    '--wcp-color-text':          '--text',
    '--wcp-color-text-muted':    '--muted',
    '--wcp-color-primary':       '--accent',
    '--wcp-color-success':       '--green',
    '--wcp-color-danger':        '--red',
    '--wcp-color-warning':       '--yellow',
  };
  Object.entries(t).forEach(([k, v]) => {
    document.documentElement.style.setProperty(k, v);
    const alias = MAP[k]; if (alias) document.documentElement.style.setProperty(alias, v);
  });
}
```

Copy this block verbatim into every `<script>` section:

```javascript
// 1. WCP ready + theme request
// Define applyTheme FIRST (function declaration — hoisted within module scope).
function applyTheme(t) {
  // (include MAP block above if widget CSS uses internal alias var names)
  Object.entries(t).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
}
window.parent.postMessage({ type: 'wcp:ready' }, '*');
window.parent.postMessage({ type: 'wcp:request-theme' }, '*');

// 2. URL-based theme — BOTH forms are mandatory (WCP 2.x)
// Form A: query string  ?com.doc.widgetcontextprotocol=<base64>
// Form B: hash fragment  #wcp-theme=<base64>
// The payload is base64( JSON.stringify({ uuid, name, vars: { '--wcp-color-bg': '#...', ... } }) )
// Extract .vars — do NOT iterate the top-level object directly.
(function(){
  const QK  = 'com.doc.widgetcontextprotocol';
  const raw = new URLSearchParams(location.search).get(QK)
           || (location.hash.startsWith('#wcp-theme=') ? location.hash.slice(11) : null);
  if (!raw) return;
  try { const p = JSON.parse(atob(raw)); applyTheme(p.vars || p); } catch {}
})();

// 3. postMessage theme listener
// The WCP host sends { type: 'wcp:theme', vars: { '--wcp-color-bg': '#...', ... } }
// Always check e.data.vars first; fall back to e.data.theme for legacy hosts.
window.addEventListener('message', e => {
  if ((e.data?.type === 'wcp:theme' || e.data?.type === 'wcp:context') && (e.data.vars || e.data.theme))
    applyTheme(e.data.vars || e.data.theme);
});
```

**Critical — URL theme uses base64 (`atob`), NOT URL-encoding (`decodeURIComponent`).**
The dashboard encodes the theme as `btoa(JSON.stringify(payload))` where `payload` is
`{ uuid, name, vars: { '--wcp-color-*': value, ... } }`. Any template that:
- handles only `#wcp-theme=` hash and not `?com.doc.widgetcontextprotocol=` query string — non-compliant
- uses `decodeURIComponent` instead of `atob` — non-compliant
- uses the old `wcp:theme=` (colon) hash format — non-compliant
- iterates `JSON.parse(atob(...))` directly without extracting `.vars` — sets `uuid` and
  `name` as CSS properties and never sets any colour — broken (silent failure)

All five elements must be present in every template:
1. `wcp:ready` postMessage ✓ (in block above)
2. `wcp:request-theme` postMessage ✓ (in block above)
3. `#wcp-theme=` hash reading — `atob` → extract `.vars` ✓ (in block above)
4. `wcp:context` + `wcp:theme` message listener ✓ (in block above)
5. `applyTheme()` that handles WCP token names ✓ (in block above)

**⚠️ Widget templates run in a sandboxed iframe. This has three mandatory consequences:**

1. **Never use `alert()`, `confirm()`, or `prompt()`** — the WCP host sandbox does not
   include `allow-modals`. **These calls return `false`/`undefined`, not `true`.** This means
   `confirm()` used as a guard (`if (!confirm('Delete?')) return;`) will **always return**,
   permanently blocking the action. Use an in-page toast/notification element for all user
   feedback. Use a two-click confirmation pattern on the button for destructive actions.

2. **`confirm()` returning `false` blocks actions permanently** — any pattern like
   `if (dirty && !confirm('...')) return;` will lock the user out of that feature entirely.
   Replace such guards with auto-save (save then proceed) or toast-based UX.

3. **Use `document.body.appendChild(a); a.click(); document.body.removeChild(a)`** when
   triggering programmatic file downloads — a detached anchor element may not fire in
   all sandbox configurations.

### Step 5b — Audit third-party dependencies (MANDATORY)

Before building the container, list every third-party JavaScript library or framework
referenced in any HTML template (CDN imports, ESM imports, `<script src>`, `import …
from`). For each, identify its licence.

**Why this is mandatory:**
- Permissive licences (MIT, Apache 2.0, BSD) are safe for use in WCP widgets but
  require that the copyright notice is preserved in source distributions.
- Copyleft licences (GPL, LGPL, AGPL) can impose distribution obligations on the
  widget code — these must be escalated to the developer before proceeding.
- Commercial or proprietary licences require explicit permission — stop immediately
  and clarify with the developer.
- Some licences (Creative Commons BY) explicitly require attribution in the product UI.

**Procedure:**

1. List every third-party dependency used in any template. Include:
   - JS frameworks and component libraries (editors, chart libraries, etc.)
   - Utility libraries (parsers, converters, ZIP handlers, etc.)
   - Any CSS frameworks loaded externally
   - Polyfills loaded from CDN

2. For each, state the licence type. The licence is usually visible on the library's
   npm page, GitHub repo, or documentation.

3. **Flag and stop** if any dependency is LGPL, GPL, AGPL, or has a non-standard licence.
   Report to the developer before continuing.

4. **About component is MANDATORY if any third-party dependencies exist** — which in
   practice means almost always. Record all dependencies in an "Open Source Components"
   card in the About page.

**About page — "Open Source Components" card format:**

```html
<div class="section">
  <h2>Open Source Components</h2>
  <p style="font-size:12px;color:var(--wcp-color-text-muted);margin-bottom:10px;line-height:1.5">
    This widget uses the following open-source libraries. {summary licence statement}.
  </p>
  <div class="row"><span class="lbl">{Library} {Version}</span>
    <span class="val" style="color:var(--wcp-color-text-muted)">{Role} · <a href="{url}" style="color:var(--wcp-color-primary);text-decoration:none">{url-short}</a></span>
  </div>
  <!-- one row per dependency -->
</div>
```

Place this card after the Technical card. Group by licence type if mixing licences.

> **Note:** Use `var(--wcp-color-text-muted)` — not `var(--muted)`. The old `--muted`
> alias is not injected by the WCP theme engine. Only full `--wcp-color-*` tokens are
> guaranteed to be present.

**Reference implementation:** `wcp-widget-bonjour/src/templates/about.html`
— "Open Source Components" section listing JSZip, Flask, and Docker SDK (all MIT Licensed).

---

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
