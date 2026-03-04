import urllib.parse
from fastapi import FastAPI, Depends, HTTPException, Request, status, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import models, schemas, crud, auth, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Landpage Admin SaaS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def gerar_wa_link(numero: str, mensagem: str) -> str:
    if not numero:
        return ""
    texto = urllib.parse.quote(mensagem or "")
    # Remove everything that is not a digit from the number for the wa.me link
    numero_limpo = ''.join(filter(str.isdigit, numero))
    return f"https://wa.me/{numero_limpo}?text={texto}"

# --- Admin Auth Endpoints ---

@app.post("/api/admin/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not auth.authenticate_admin(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Admin API Endpoints ---

@app.get("/api/landings", response_model=list[schemas.LandingResponse])
def read_landings(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    return crud.get_landings(db, skip=skip, limit=limit)

@app.get("/api/landings/{landing_id}", response_model=schemas.LandingResponse)
def read_landing(landing_id: int, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    db_landing = crud.get_landing(db, landing_id=landing_id)
    if db_landing is None:
        raise HTTPException(status_code=404, detail="Landing not found")
    return db_landing

@app.post("/api/landings", response_model=schemas.LandingResponse)
def create_landing(landing: schemas.LandingCreate, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    db_landing = crud.get_landing_by_subdomain(db, subdomain=landing.subdomain)
    if db_landing:
        raise HTTPException(status_code=400, detail="Subdomain already registered")
    return crud.create_landing(db=db, landing=landing)

@app.put("/api/landings/{landing_id}", response_model=schemas.LandingResponse)
def update_landing(landing_id: int, landing: schemas.LandingUpdate, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    db_landing = crud.update_landing(db, landing_id=landing_id, landing=landing)
    if db_landing is None:
        raise HTTPException(status_code=404, detail="Landing not found")
    return db_landing

@app.delete("/api/landings/{landing_id}")
def delete_landing(landing_id: int, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    db_landing = crud.delete_landing(db, landing_id=landing_id)
    if db_landing is None:
        raise HTTPException(status_code=404, detail="Landing not found")
    return {"ok": True}

# --- Tracking Endpoints ---

@app.post("/api/t")
async def track_event(event: schemas.TrackingEventCreate, request: Request, db: Session = Depends(database.get_db)):
    """Public endpoint for tracking events. Called by sendBeacon from landing pages."""
    if event.event_type not in ("pageview", "whatsapp_click"):
        return Response(status_code=204)
    # Verify landing exists
    landing = crud.get_landing(db, landing_id=event.landing_id)
    if not landing:
        return Response(status_code=204)
    try:
        crud.create_tracking_event(
            db,
            landing_id=event.landing_id,
            event_type=event.event_type,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
        )
    except Exception:
        pass  # Never fail the visitor experience
    return Response(status_code=204)

@app.get("/api/stats/overview", response_model=schemas.OverviewStats)
def get_overview_stats(db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    return crud.get_overview_stats(db)

@app.get("/api/landings-with-stats")
def read_landings_with_stats(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    """Returns landings list with embedded stats to avoid N+1 queries."""
    landings = crud.get_landings(db, skip=skip, limit=limit)
    all_stats = crud.get_all_stats(db)
    result = []
    for l in landings:
        landing_dict = schemas.LandingResponse.model_validate(l).model_dump()
        stats = all_stats.get(l.id)
        if stats:
            landing_dict["stats"] = stats.model_dump()
        else:
            landing_dict["stats"] = schemas.LandingStats(landing_id=l.id).model_dump()
        result.append(landing_dict)
    return result

@app.get("/api/landings/{landing_id}/stats", response_model=schemas.LandingStats)
def get_landing_stats(landing_id: int, db: Session = Depends(database.get_db), current_admin: str = Depends(auth.get_current_admin)):
    db_landing = crud.get_landing(db, landing_id=landing_id)
    if db_landing is None:
        raise HTTPException(status_code=404, detail="Landing not found")
    return crud.get_landing_stats(db, landing_id=landing_id)

# --- Wildcard Subdomain Handler ---
# This must be the last / route to avoid catching API routes

def injetar_google_tags(html: str, pixel_google: str | None) -> str:
    """Inject Google gtag.js + conversion tracking for WhatsApp clicks."""
    if not pixel_google:
        return html

    gtag_script = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={pixel_google}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{pixel_google}');
    </script>
    """

    conversion_script = f"""
    <!-- Google Ads Conversion Tracking for WhatsApp -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
      document.querySelectorAll('a[href*="wa.me"]').forEach(function(link) {{
        link.addEventListener('click', function() {{
          if (typeof gtag === 'function') {{
            gtag('event', 'conversion', {{
              'send_to': '{pixel_google}/whatsapp_click',
              'event_category': 'engagement',
              'event_label': 'whatsapp_click'
            }});
          }}
        }});
      }});
    }});
    </script>
    """

    if "</head>" in html:
        html = html.replace("</head>", f"{gtag_script}</head>")
    else:
        html = gtag_script + html

    if "</body>" in html:
        html = html.replace("</body>", f"{conversion_script}</body>")
    else:
        html = html + conversion_script

    return html


def injetar_tracker_script(html: str, landing_id: int) -> str:
    """Inject internal tracking script for pageviews and WhatsApp clicks."""
    tracker_script = f"""
    <!-- Internal Tracker -->
    <script>
    (function() {{
      var API = '/api/t';
      var LID = {landing_id};
      function tk(evType) {{
        var data = JSON.stringify({{landing_id: LID, event_type: evType}});
        if (navigator.sendBeacon) {{
          navigator.sendBeacon(API, new Blob([data], {{type: 'application/json'}}));
        }} else {{
          var x = new XMLHttpRequest();
          x.open('POST', API, true);
          x.setRequestHeader('Content-Type', 'application/json');
          x.send(data);
        }}
      }}
      // Track pageview
      tk('pageview');
      // Track WhatsApp clicks
      document.addEventListener('DOMContentLoaded', function() {{
        document.querySelectorAll('a[href*="wa.me"]').forEach(function(link) {{
          link.addEventListener('click', function() {{ tk('whatsapp_click'); }});
        }});
      }});
    }})();
    </script>
    """

    if "</body>" in html:
        html = html.replace("</body>", f"{tracker_script}</body>")
    else:
        html = html + tracker_script

    return html


@app.get("/{full_path:path}")
async def serve_landing(full_path: str, request: Request, db: Session = Depends(database.get_db)):
    host = request.headers.get("host")
    if not host:
        return HTMLResponse(content="<h1>Host header missing</h1>", status_code=400)
    
    parts = host.split(".")
    if len(parts) > 2:
        subdomain = parts[0]
    else:
        subdomain = parts[0]
    
    landing = crud.get_landing_by_subdomain(db, subdomain=subdomain)
    
    if not landing or not landing.active:
        return HTMLResponse("<h1>Página não encontrada ou inativa.</h1>", status_code=404)
        
    html = landing.html_content
    
    # Dynamic WhatsApp Link Injection
    if "{{WHATSAPP_LINK}}" in html:
        wa_link = gerar_wa_link(landing.whatsapp_number, landing.whatsapp_message)
        html = html.replace("{{WHATSAPP_LINK}}", wa_link)
    
    # Google Ads / GA4 pixel injection
    html = injetar_google_tags(html, landing.pixel_google)
    
    # Internal tracker injection
    html = injetar_tracker_script(html, landing.id)
    
    return HTMLResponse(content=html)
