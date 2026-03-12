from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import articles, test_runs, analysis
from backend.database import db

app = FastAPI(
    title="El País Scraper API",
    description="BrowserStack + Selenium scraping pipeline with Supabase",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router,  prefix="/articles",  tags=["Articles"])
app.include_router(test_runs.router, prefix="/test-runs", tags=["Test Runs"])
app.include_router(analysis.router,  prefix="/analysis",  tags=["Analysis"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status":       "ok",
        "db_connected": db.is_connected(),
        "endpoints": {
            "dashboard": "/dashboard",
            "articles":  "/articles",
            "test_runs": "/test-runs",
            "analysis":  "/analysis/{run_id}",
            "docs":      "/docs",
        }
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "db":     "connected" if db.is_connected() else "disconnected"
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard():
    articles_data = db.get_all_articles()
    runs_data     = db.get_all_test_runs()
    word_freq     = db.get_word_frequency_by_run(runs_data[0]["id"]) if runs_data else []

    run_rows = ""
    for r in runs_data:
        color    = "#27ae60" if r.get("status") == "passed" else "#e74c3c" if r.get("status") == "failed" else "#f39c12"
        emoji    = "✅" if r.get("status") == "passed" else "❌" if r.get("status") == "failed" else "🔄"
        run_rows += f"""
        <tr>
            <td>{r.get('browser', '')}</td>
            <td>{r.get('platform', '')}</td>
            <td><span style="color:{color};font-weight:bold">{emoji} {r.get('status','').upper()}</span></td>
            <td style="font-size:12px">{str(r.get('created_at',''))[:19]}</td>
        </tr>"""

    if not run_rows:
        run_rows = "<tr><td colspan='4' style='text-align:center;color:#999'>No runs yet</td></tr>"

    article_rows = ""
    for a in articles_data:
        img_html = f'<img src="{a.get("image_url","")}" width="80" style="border-radius:4px">' if a.get("image_url") else "—"
        article_rows += f"""
        <tr>
            <td>{img_html}</td>
            <td><strong>{a.get('title_es', '')}</strong></td>
            <td>{a.get('title_en', '')}</td>
            <td style="font-size:12px;max-width:300px;overflow:hidden">{a.get('content_en', '')[:150]}...</td>
            <td style="font-size:12px">{str(a.get('scraped_at',''))[:19]}</td>
        </tr>"""

    if not article_rows:
        article_rows = "<tr><td colspan='5' style='text-align:center;color:#999'>No articles yet — run the scraper first</td></tr>"

    labels = str([w["word"]  for w in word_freq])
    values = str([w["count"] for w in word_freq])

    chart_section = ""
    if word_freq:
        chart_section = f"""
        <div class="card">
            <h2>📊 Word Frequency Analysis</h2>
            <canvas id="wordChart" height="100"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        new Chart(document.getElementById('wordChart'), {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: 'Occurrences',
                    data: {values},
                    backgroundColor: '#3498db',
                    borderRadius: 6
                }}]
            }},
            options: {{
                plugins: {{ legend: {{ display: false }} }},
                scales:  {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }}
            }}
        }});
        </script>"""

    total_articles = len(articles_data)
    total_runs     = len(runs_data)
    passed_runs    = sum(1 for r in runs_data if r.get("status") == "passed")
    failed_runs    = sum(1 for r in runs_data if r.get("status") == "failed")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="30">
        <title>El País Scraper Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f0f2f5;
                color: #333;
            }}

            header {{
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: white;
                padding: 24px 32px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}

            header h1 {{ font-size: 24px; }}
            header p  {{ font-size: 13px; opacity: 0.7; margin-top: 4px; }}

            .live-badge {{
                background: #27ae60;
                color: white;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                animation: pulse 2s infinite;
            }}

            @keyframes pulse {{
                0%   {{ opacity: 1; }}
                50%  {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}

            .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}

            .stats {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }}

            .stat-card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}

            .stat-card .number {{
                font-size: 36px;
                font-weight: bold;
                color: #3498db;
            }}

            .stat-card .label {{
                font-size: 13px;
                color: #888;
                margin-top: 4px;
            }}

            .card {{
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}

            .card h2 {{
                font-size: 18px;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #f0f2f5;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: #f8f9fa;
                padding: 12px;
                text-align: left;
                font-size: 13px;
                color: #666;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            td {{
                padding: 12px;
                border-bottom: 1px solid #f0f2f5;
                font-size: 14px;
                vertical-align: middle;
            }}

            tr:last-child td {{ border-bottom: none; }}
            tr:hover td      {{ background: #fafafa; }}

            footer {{
                text-align: center;
                padding: 24px;
                color: #999;
                font-size: 13px;
            }}

            .refresh-note {{
                text-align: right;
                font-size: 12px;
                color: #999;
                margin-bottom: 16px;
            }}
        </style>
    </head>
    <body>

        <header>
            <div>
                <h1>📰 El País Scraper Dashboard</h1>
                <p>BrowserStack + Selenium + Supabase Pipeline</p>
            </div>
            <div class="live-badge">🟢 LIVE — refreshes every 30s</div>
        </header>

        <div class="container">

            <div class="stats">
                <div class="stat-card">
                    <div class="number">{total_articles}</div>
                    <div class="label">Articles Scraped</div>
                </div>
                <div class="stat-card">
                    <div class="number">{total_runs}</div>
                    <div class="label">BrowserStack Runs</div>
                </div>
                <div class="stat-card">
                    <div class="number" style="color:#27ae60">{passed_runs}</div>
                    <div class="label">Tests Passed</div>
                </div>
                <div class="stat-card">
                    <div class="number" style="color:#e74c3c">{failed_runs}</div>
                    <div class="label">Tests Failed</div>
                </div>
            </div>

            <div class="card">
                <h2>🌐 BrowserStack Test Runs</h2>
                <table>
                    <tr>
                        <th>Browser</th>
                        <th>Platform</th>
                        <th>Status</th>
                        <th>Time</th>
                    </tr>
                    {run_rows}
                </table>
            </div>

            <div class="card">
                <h2>📄 Scraped Articles</h2>
                <table>
                    <tr>
                        <th>Image</th>
                        <th>Spanish Title</th>
                        <th>English Title</th>
                        <th>Content Preview (EN)</th>
                        <th>Scraped At</th>
                    </tr>
                    {article_rows}
                </table>
            </div>

            {chart_section}

        </div>

        <footer>
            Built with Selenium · BrowserStack · Supabase · FastAPI
        </footer>

    </body>
    </html>
    """
    return HTMLResponse(content=html)
