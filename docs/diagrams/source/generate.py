"""Regenerate the eight documentation SVGs using only Python's standard library.
Run from any directory: python docs/diagrams/source/generate.py
Coordinates and labels below are the editable source; no runtime imports or secrets.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
RED, DARK, INK, GRAY = '#d71920', '#1b1b1b', '#111111', '#f3f4f5'
GREEN, AMBER = '#187343', '#925700'

class Diagram:
    def __init__(self, number, title, subtitle, height=1000):
        self.number, self.height = number, height
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}. Royal Tyres IT Asset Request Tool. Read the accompanying README for implementation notes.</desc>
<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0,0 L9,4.5 L0,9 Z" fill="{DARK}"/></marker></defs>
<rect width="1200" height="{height}" fill="white"/>
<g font-family="Arial, Helvetica, sans-serif" fill="{INK}">
<rect x="40" y="34" width="7" height="73" fill="{RED}"/>
<text x="64" y="52" font-size="16" font-weight="700" letter-spacing="1.2">ROYAL TYRES IT ASSET REQUEST TOOL</text>
<text x="64" y="87" font-size="30" font-weight="700">{escape(title)}</text>
<text x="64" y="115" font-size="18" fill="#52565b">{escape(subtitle)}</text>
<text x="1145" y="75" text-anchor="end" font-size="28" font-weight="700" fill="{RED}">{number:02}</text>''']
    def text(self,x,y,lines,size=19,color=INK,bold=False,anchor='start'):
        if isinstance(lines,str): lines=[lines]
        for i,line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{y+i*(size+8)}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(line)}</text>')
    def box(self,x,y,w,h,title,lines=(),kind='normal'):
        fill,stroke,tc = {'normal':('white','#bec3c8',INK),'dark':(DARK,DARK,'white'),'red':('#fff2f3',RED,INK),'success':('#eff9f2',GREEN,INK),'warning':('#fff7e9',AMBER,INK),'muted':(GRAY,'#d9dde0',INK)}[kind]
        self.parts.append(f'<g data-card="{escape(title)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        self.text(x+20,y+31,title,21,tc,True)
        self.text(x+20,y+60,lines,18,tc)
        self.parts.append('</g>')
    def arrow(self,*pts,dashed=False):
        coords=' '.join(f'{x},{y}' for x,y in pts)
        self.parts.append(f'<polyline points="{coords}" fill="none" stroke="{DARK}" stroke-width="2" stroke-linejoin="round" marker-end="url(#arrow)"'+(' stroke-dasharray="6 5"' if dashed else '')+'/>')
    def group(self,x,y,w,h,label):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{GRAY}" stroke="#d9dde0"/>')
        self.text(x+18,y+28,label,16,'#52565b',True)
    def foot(self,lines):
        self.parts.append(f'<path d="M40 {self.height-89} H1160" stroke="#d9dde0"/>')
        self.text(44,self.height-59,lines,18,'#52565b')
    def save(self,name):
        self.parts.append('</g></svg>')
        (OUT/name).write_text('\n'.join(self.parts)+'\n',encoding='utf-8')

# 01: One backend/database repeated as labeled callback destinations, not extra services.
d=Diagram(1,'System Architecture','Hosted components and the direction of integration calls',1040)
d.box(440,155,320,78,'User',['Employee / service desk'])
d.box(370,280,460,98,'React / Vite Frontend',['Render Static Site','Browser HTTP service: api.js'])
d.arrow((600,233),(600,280));d.arrow((600,378),(600,450));d.text(620,409,['HTTPS / JSON','Basic Auth'],17)
d.box(370,450,460,90,'FastAPI Backend',['Render · Controllers → Services'],kind='dark')
d.arrow((470,540),(470,580),(250,580),(250,625))
d.arrow((730,540),(730,580),(960,580),(960,625));d.text(760,568,'OUTBOUND → Zendesk REST',17,RED,True)
d.box(40,625,470,205,'Render PostgreSQL',['Primary local system of record','asset_requests','audit_logs','zendesk_connection'],kind='red')
d.box(750,625,410,80,'Zendesk REST API',['Ticket creation / configuration'])
d.arrow((955,705),(955,745));d.box(750,745,410,75,'Zendesk Trigger',['Status-change event'])
d.arrow((955,820),(955,885),(645,885));d.text(670,866,'INBOUND callback',17,RED,True)
d.box(40,855,605,65,'Webhook → FastAPI → PostgreSQL',[],kind='dark')
d.foot(['Inbound: POST JSON + separate bearer secret to the same FastAPI backend.','Frontend never calls Zendesk directly. SQLite is local development/testing only.']);d.save('01-system-architecture.svg')

# 02: Controller box is the route boundary; schema validation precedes its body.
d=Diagram(2,'Application Code Flow','MVC-style layered mental model — not traditional ASP.NET MVC',1250)
d.group(330,335,525,345,'')
d.text(890,390,['HTTP pipeline','Middleware wraps','request / response'],18)
rows=[('React View / Component','VIEW · what the user sees.'),('frontend/src/services/api.js','Browser → FastAPI HTTP boundary.'),('FastAPI Controller boundary','CONTROLLER · HTTP route and dependencies.'),('Pydantic Schema','SCHEMA · validates the API data contract.'),('Service','SERVICE · business workflow / execution order.'),('Repository','REPOSITORY · how ORM queries/persistence occur.'),('SQLAlchemy Model','MODEL · persisted entity / SQL table mapping.'),('Session / Engine','DATA · unit of work / database connectivity.'),('PostgreSQL','Primary system of record.')]
for i,(title,line) in enumerate(rows):
 y=160+i*110;d.box(350,y,485,80,title,[line],kind='dark' if i==4 else 'normal')
 if i: d.arrow((592, y-30),(592,y))
d.box(40,430,255,145,'Core',['Settings','Security','Logging'],kind='muted')
for y in [420,640,970]:d.arrow((295,505),(315,505),(315,y),(350,y),dashed=True)
d.box(895,600,265,80,'ZendeskService',['External HTTP / payloads'])
d.arrow((835,640),(895,640));d.box(895,745,265,80,'Zendesk REST API',['External helpdesk'])
d.arrow((1027,680),(1027,745));d.text(895,890,['Middleware returns the','response through safe','logging / header policy.'],18)
d.foot(['Schema validation happens before the Controller route body runs. Arrows show the mental model.','Repositories receive the shared Session. Services choose transaction boundaries.']);d.save('02-code-layer-flow.svg')

# 03: The second half cannot begin until the primary transaction commits.
d=Diagram(3,'Create Request','End-to-end execution sequence · local persistence first',1240)
d.box(40,160,320,95,'Employee → Form',['AssetRequestForm','Frontend validation'])
d.box(430,160,320,95,'frontend api.js',['POST /api/requests','Basic Auth + JSON'])
d.box(820,160,340,95,'RequestController',['AssetRequestCreate validation','before the route body'])
d.arrow((360,202),(430,202));d.arrow((750,202),(820,202));d.arrow((990,255),(990,275),(600,275),(600,305))
d.box(365,305,470,78,'RequestService',['Owns sequencing and the shared Session'],kind='dark')
d.arrow((480,383),(480,413),(265,413),(265,443));d.arrow((720,383),(720,413),(940,413),(940,443))
d.box(40,443,450,105,'RequestRepository',['AssetRequest Model → Session flush','Local ID allocated; not yet committed'])
d.box(710,443,450,105,'AuditRepository',['AuditLog: REQUEST_CREATED','Same transaction; links to local ID'])
d.arrow((265,548),(265,590),(600,590),(600,620));d.arrow((935,548),(935,590),(600,590))
d.box(190,620,820,112,'POSTGRESQL COMMIT',['PRIMARY REQUEST IS COMMITTED BEFORE CALLING ZENDESK','AssetRequest + AuditLog are now durable.'],kind='red')
d.arrow((600,732),(600,772));d.box(240,772,720,83,'RequestService → ZendeskService',['Zendesk Tickets API receives the already-committed request'])
d.arrow((415,855),(415,900),(300,900),(300,932));d.arrow((785,855),(785,900),(900,900),(900,932))
d.box(40,932,530,170,'SUCCESS · ticket ID returned',['Store zendesk_ticket_id and status','Mark synced; write audit event','Commit integration outcome locally'],kind='success')
d.box(630,932,530,170,'FAILURE · ZendeskError',['KEEP local AssetRequest','Mark sync_failed; write audit event','Commit failure state locally'],kind='warning')
d.foot(['Controller returns the saved request DTO (HTTP 201). External failure cannot undo the first commit.','If integration is not configured, the request stays saved with sync_pending.']);d.save('03-create-request-sequence.svg')

# 04: All numbers are illustrative, even when they resemble a prior live test.
d=Diagram(4,'Identifiers and Audit Relationship','EXAMPLE VALUES ONLY · database keys versus integration identifiers',1050)
d.box(40,170,460,190,'LOCAL DATABASE · AssetRequest',['id = 6  (local primary key)','status = pending','zendesk_ticket_id = 56','Table: asset_requests'],kind='dark')
d.box(690,170,470,142,'Zendesk Ticket #56',['Generated by Zendesk','Stored locally on AssetRequest','External ticket ID, not a local foreign key'])
d.arrow((500,240),(690,240));d.text(520,222,'links to',17)
d.box(690,360,470,220,'external_id',['royal-tires-asset-6','Built deterministically from local ID','Sent to Zendesk for correlation','NOT encryption · NOT a hash','NOT the database primary key'],kind='red')
d.arrow((500,280),(600,280),(600,415),(690,415))
d.arrow((265,360),(265,400))
d.box(40,400,460,130,'LOCAL REQUEST ID · 6',['Generated by PostgreSQL / local DB','Primary identifier in the portal','One AssetRequest → many AuditLog rows'])
d.arrow((265,530),(265,640));d.text(290,589,'one → many',18,RED,True)
d.box(40,640,530,175,'Persisted workflow history',['AuditLog #1 · REQUEST_CREATED','AuditLog #2 · ZENDESK_TICKET_CREATED','AuditLog #3 · ZENDESK_STATUS_CHANGED','Each event has request_id = 6'])
d.box(690,640,470,175,'FOREIGN KEY',['audit_logs.request_id','↓','asset_requests.id','Links each event to its parent request'],kind='muted')
d.arrow((570,725),(690,725))
d.box(40,855,1120,75,'AuditLog is chronological workflow history',['It is NOT authentication or session state.'])
d.foot(['Local ID and Zendesk ID are generated by different systems; external_id ties them together.']);d.save('04-identifiers-audit.svg')

# 05: Schema/body-auth order and optional external correlation match the implementation.
d=Diagram(5,'Zendesk Status Synchronization','Event-driven webhook flow · external event to local state',1220)
d.box(40,160,330,110,'Zendesk Agent',['Changes ticket status','Open → Pending'])
d.box(435,160,330,110,'Zendesk Trigger',['Royal Tyres portal tag matches','Status changed / ticket update'])
d.box(830,160,330,110,'Zendesk Webhook',['POST JSON','Separate bearer authentication'])
d.arrow((370,215),(435,215));d.arrow((765,215),(830,215));d.arrow((995,270),(995,305),(600,305),(600,345))
d.box(230,345,740,133,'WebhookController · /api/webhooks/zendesk',['Webhook schema normalizes / validates: “Pending” → “pending”','FastAPI validates before route body; Controller checks bearer secret','Portal Basic Auth is NOT webhook authentication.'],kind='red')
d.arrow((600,478),(600,520))
d.box(230,520,740,155,'WebhookService',['RequestRepository: find local Model by zendesk_ticket_id','Verify supplied external_id with request_identity.py','Then update the Session-tracked AssetRequest status / sync timestamp'])
d.arrow((600,675),(600,715));d.box(230,715,740,110,'AuditRepository → AuditLog → PostgreSQL COMMIT',['Status and audit commit together in the shared Session','ZENDESK_STATUS_CHANGED (or receipt event if unchanged)'],kind='dark')
d.arrow((600,825),(600,865));d.box(230,865,740,100,'Local API → RequestDetailView / Dashboard',['Tracking polls every 10 seconds; Dashboard loads / refreshes','Both display persisted local state; neither calls Zendesk directly.'])
d.box(40,1000,530,105,'NORMAL API CALL',['Our application initiates the HTTP request.'])
d.box(630,1000,530,105,'WEBHOOK',['Zendesk initiates HTTP after an event.'])
d.foot(['Both use HTTP. external_id is optional in the schema and checked when supplied; event ordering is not implemented.']);d.save('05-zendesk-webhook-flow.svg')

# 06: Names only; no environment values are loaded by this generator.
d=Diagram(6,'Runtime Configuration and Security','Environment names only · secrets stay on the server',1510)
d.box(40,155,1120,195,'Render Environment Variables',['DATABASE_URL     APP_USERNAME     APP_PASSWORD     FRONTEND_URL','ZENDESK_SUBDOMAIN     ZENDESK_EMAIL     ZENDESK_API_TOKEN','ZENDESK_WEBHOOK_SECRET     ZENDESK_NOTIFICATION_EMAIL','RENDER_EXTERNAL_URL'],kind='muted')
d.arrow((600,350),(600,385));d.box(210,385,780,105,'backend/app/core/config.py',['Pydantic BaseSettings → typed Settings object','Host supplies runtime values; source code contains no deployed secrets.'],kind='dark')
# Fan-out bus keeps arrows out of the cards.
d.arrow((600,490),(600,525))
centers=[148,374,600,826,1052]
for x in centers:d.arrow((600,525),(x,525),(x,565))
cards=[('DATABASE_URL',['Data / Engine /','Session','→ PostgreSQL']),('APP_USERNAME',['+ APP_PASSWORD','Basic Auth →','protected API routes']),('FRONTEND_URL',['CORS allowed origins','Browser policy only']),('ZENDESK_*',['ZendeskService','→ Zendesk REST','URL/email configure','callback/notification']),('WEBHOOK AUTH',['Webhook secret','→ separate bearer','authentication'])]
for i,(title,lines) in enumerate(cards):d.box(40+i*226,565,216,195,title,lines)
d.text(44,789,'RENDER_EXTERNAL_URL → callback endpoint · ZENDESK_NOTIFICATION_EMAIL → email target',18)
security=[('PYDANTIC',['Validates incoming API data.']),('SQLALCHEMY',['Uses bound / parameterized values.','No user-input SQL concatenation.']),('REACT',['Renders user data as text.','No dangerouslySetInnerHTML','for user-controlled content.']),('CORS',['Browser-origin policy.','NOT authentication.']),('BASIC AUTH',['Assignment-required demo login.','Credentials on protected requests.']),('SECRETS',['Injected at runtime.','Not hard-coded into GitHub.']),('SQL INJECTION',['Input must not become','executable SQL syntax.']),('XSS',['Input must not become executable','browser HTML / JavaScript.'])]
for i,(title,lines) in enumerate(security):d.box(40+(i%2)*570,805+(i//2)*140,550,125,title,lines,kind='muted')
d.foot(['HTTPS protects transport. CORS and input validation do not replace authentication.']);d.save('06-environment-security.svg')

# 07: Versions, commands, triggers and concurrency mirror ci.yml.
d=Diagram(7,'Continuous Integration','GitHub Actions · .github/workflows/ci.yml',1330)
d.box(240,155,720,105,'Code change → GitHub Actions',['Pull request targeting main OR push to main','Workflow/ref concurrency cancels superseded runs.'],kind='dark')
d.arrow((420,260),(420,295),(300,295),(300,335));d.arrow((780,260),(780,295),(900,295),(900,335))
d.group(40,335,520,555,'BACKEND JOB · ubuntu-latest · backend directory')
d.group(640,335,520,715,'FRONTEND JOB · ubuntu-latest · frontend directory')
backend=[('Checkout','actions/checkout@v4'),('Set up Python 3.13','actions/setup-python@v5 · pip cache'),('Install requirements','python -m pip install -r requirements.txt'),('Backend tests','python -m pytest')]
frontend=[('Checkout','actions/checkout@v4'),('Set up Node 22.12.0','actions/setup-node@v4 · npm cache'),('Install dependencies','npm ci'),('Frontend unit tests','npm test'),('Vite production build','npm run build'),('Install Chromium','npx playwright install --with-deps chromium'),('Playwright E2E','npm run test:e2e')]
for col,rows in [(80,backend),(680,frontend)]:
 for i,(title,line) in enumerate(rows):
  y=385+i*86;d.box(col,y,440,70,title,[line])
  if i:d.arrow((col+220,y-16),(col+220,y))
d.box(80,785,440, 70,'PASS / FAIL',['Automated verification result'],kind='muted')
d.arrow((300,713),(300,785));d.box(680,995,440, 42,'PASS / FAIL',[],kind='muted');d.arrow((900,971),(900,995))
d.box(40,1100,1120,105,'SEPARATE DEPLOYMENT MECHANISM',['Main branch change → Render Auto Deploy → Backend + Frontend','CI validates; it does not deploy. No branch-protection enforcement is assumed.'],kind='red')
d.foot(['CI = automated verification. Render deployment is separate. No manual deploy is needed for these diagrams.']);d.save('07-ci-pipeline.svg')

# 08: App preserves current route at login and holds credentials in memory.
d=Diagram(8,'Frontend Page and Navigation Flow','App.jsx composes routes · api.js owns browser HTTP',1210)
d.box(40,160,390,110,'LOGIN · AuthLayout',['Enter credentials matching server','APP_USERNAME / APP_PASSWORD'])
d.box(600,160,560,110,'frontend/src/services/api.js',['Basic Auth probe against FastAPI','GET /api/requests?limit=1&offset=0'])
d.arrow((430,215),(600,215));d.arrow((880,160),(880,140),(235,140),(235,160));d.text(540,133,'401 → remain Login',17,RED,True)
d.arrow((880,270),(880,310),(600,310),(600,350));d.text(900,305,'success',18,GREEN,True)
d.box(325,350,550,100,'AppLayout · shared page shell',['App.jsx selects the View for the browser path','Credentials remain in memory; refresh signs out.'],kind='dark')
for x in [225,600,975]:d.arrow((600,450),(600,485),(x,485),(x,525))
d.box(40,525,350,165,'New Request · /request',['RequestView','AssetRequestForm component','Client validation → api.js POST','Saved request → Track link'])
d.box(425,525,350,165,'Dashboard · /dashboard',['DashboardView','Latest 100 local requests','Search / filter / manual refresh','Select request row'])
d.box(810,525,350,165,'Settings · /settings',['SettingsView','Account / developer tools','ZendeskSetupView','Governed setup through api.js'])
d.arrow((215,690),(215,730),(600,730),(600,780));d.arrow((600,690),(600,780))
d.box(300,780,530,130,'RequestDetailView · /requests/:id',['Local status · Zendesk status · sync state','Polls local API every 10 seconds','Manual refresh reads local data'])
d.arrow((985,690),(985,780));d.box(865,780,295,130,'Swagger / API docs',['Opens FastAPI /docs','Backend-generated','OpenAPI documentation'])
d.box(40,955,1120,140,'READ THE UI BY RESPONSIBILITY',['App.jsx: route / composition · Layouts: shared page shells · Views: page-level UI','Components: smaller reusable pieces · api.js: browser → FastAPI HTTP boundary','No View calls Zendesk directly.'],kind='muted')
d.foot(['Aliases: / and /request/ → New Request; /requests → Dashboard; /zendesk-setup → Settings.']);d.save('08-frontend-page-flow.svg')
print('Generated 8 SVG diagrams in',OUT)
