#!/usr/bin/env python3
"""
Generate a branded PDF report for a client.
Pulls all dashboard data and creates a professional report.

Usage:
  python3 generate_report.py rank4ai
  python3 generate_report.py market-invoice
  python3 generate_report.py all
"""
import json
import os
import sys
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
LIVE_DIR = os.path.join(PROJECT_DIR, "src", "data", "live")
OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/reports")


def load(filename):
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def generate_html_report(client_id):
    """Generate HTML report from dashboard data."""
    clients = load(os.path.join(PROJECT_DIR, "src", "data", "clients.json"))
    if isinstance(clients, list):
        client = next((c for c in clients if c["id"] == client_id), None)
    else:
        client = None

    if not client:
        print(f"Unknown client: {client_id}")
        return None

    # Load all data
    crawl = load(f"crawl_{client_id}.json")
    uptime = load("uptime.json").get(client_id, {})
    ga4 = load("ga4.json").get(client_id, {})
    gsc = load("gsc.json").get(client_id, {})
    bing = load("bing.json").get(client_id, {})
    audit = load("ai_audit.json").get(client_id, {})
    citations = load("citations_by_type.json").get(client_id, {})
    pagespeed = load("pagespeed.json").get(client_id, {})
    competitors = load("competitor_serp.json").get(client_id, {})
    kg = load("knowledge_graph.json").get(client_id, {})
    entities = load("nlp_entities.json").get(client_id, {})
    crawl_activity = load("crawl_activity.json").get(client_id, {})
    serp = load("serp_data.json").get(client_id, {})
    snapshot = None
    snap_dir = os.path.join(PROJECT_DIR, "src", "data", "snapshots", client_id)
    baseline_file = os.path.join(snap_dir, "baseline.json")
    if os.path.exists(baseline_file):
        with open(baseline_file) as f:
            snapshot = json.load(f)

    today = datetime.now().strftime("%d %B %Y")
    brand = client["name"]
    domain = client["domain"]

    # Build sections
    def score_color(score, good=70, warn=40):
        if score >= good: return "#22c55e"
        if score >= warn: return "#eab308"
        return "#ef4444"

    def metric_row(label, value, color=None):
        c = f' style="color: {color}"' if color else ""
        return f'<tr><td style="padding: 8px 16px; color: #6b7280; font-size: 13px;">{label}</td><td style="padding: 8px 16px; font-weight: 600; font-size: 13px;"{c}>{value}</td></tr>'

    sections = []

    # Executive Summary
    summary_items = []
    if audit: summary_items.append(f"AI Readiness Score: <strong>{audit.get('overall_score', '--')}/100</strong> ({audit.get('readiness', '')})")
    if citations: summary_items.append(f"AI Citation Rate: <strong>{citations.get('overall_rate', 0)}%</strong> across {citations.get('total_queries', 0)} queries")
    if ga4.get('overview'): summary_items.append(f"Traffic: <strong>{ga4['overview'].get('active_users', 0):,}</strong> users in the last 30 days")
    if crawl: summary_items.append(f"Site Health: <strong>{crawl.get('pages_crawled', 0)}</strong> pages crawled, <strong>{crawl.get('total_issues', 0)}</strong> issues found")
    if competitors: summary_items.append(f"Search Visibility: <strong>{competitors.get('client_visibility_pct', 0)}%</strong> of target queries")
    if kg: summary_items.append(f"Google Knowledge Graph: <strong>{'Known Entity' if kg.get('is_known_entity') else 'Not Found'}</strong>")

    sections.append(f"""
    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
      <h2 style="color: #15803d; font-size: 16px; margin: 0 0 12px;">Executive Summary</h2>
      <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 13px; line-height: 1.8;">
        {''.join(f'<li>{item}</li>' for item in summary_items)}
      </ul>
    </div>
    """)

    # AI Readiness
    if audit:
        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">AI Search Readiness</h2>
        <div style="display: flex; gap: 16px; margin-bottom: 16px;">
          <div style="text-align: center; padding: 16px; background: #f9fafb; border-radius: 8px; flex: 1;">
            <div style="font-size: 32px; font-weight: 700; color: {score_color(audit.get('overall_score', 0))};">{audit.get('overall_score', 0)}/100</div>
            <div style="font-size: 11px; color: #6b7280;">Overall Score</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #f9fafb; border-radius: 8px; flex: 1;">
            <div style="font-size: 20px; font-weight: 600;">{audit.get('scores', {}).get('schema', 0)}/100</div>
            <div style="font-size: 11px; color: #6b7280;">Schema</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #f9fafb; border-radius: 8px; flex: 1;">
            <div style="font-size: 20px; font-weight: 600;">{audit.get('scores', {}).get('eeat', 0)}/100</div>
            <div style="font-size: 11px; color: #6b7280;">E-E-A-T</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #f9fafb; border-radius: 8px; flex: 1;">
            <div style="font-size: 20px; font-weight: 600;">{audit.get('scores', {}).get('citation_potential', 0)}/100</div>
            <div style="font-size: 11px; color: #6b7280;">Citation Potential</div>
          </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          {metric_row('llms.txt', 'Present' if audit.get('llms_txt', {}).get('exists') else 'Missing', '#22c55e' if audit.get('llms_txt', {}).get('exists') else '#ef4444')}
          {metric_row('AI Crawlers Blocked', str(audit.get('robots_txt', {}).get('blocked_count', 0)), '#22c55e' if audit.get('robots_txt', {}).get('blocked_count', 0) == 0 else '#ef4444')}
          {metric_row('Pages Audited', str(audit.get('pages_audited', 0)))}
        </table>
        """)

    # AI Citations
    if citations:
        comp_rows = ""
        for c in citations.get("top_competitors", [])[:5]:
            comp_rows += f'<tr><td style="padding: 6px 16px; font-size: 12px;">{c["name"]}</td><td style="padding: 6px 16px; font-size: 12px; font-weight: 600;">{c["mentions"]} mentions</td></tr>'

        type_rows = ""
        for qt, qd in citations.get("by_type", {}).items():
            color = "#22c55e" if qd["rate"] > 50 else "#eab308" if qd["rate"] > 0 else "#ef4444"
            type_rows += metric_row(qt.replace("_", " ").title(), f'{qd["rate"]}% ({qd["cited"]}/{qd["queries"]})', color)

        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">AI Citation Tracking</h2>
        <p style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">Tested across Claude (Anthropic). Shows whether AI models cite {brand} when asked industry queries.</p>
        <div style="display: flex; gap: 16px; margin-bottom: 16px;">
          <div style="text-align: center; padding: 16px; background: #fef2f2; border-radius: 8px; flex: 1;">
            <div style="font-size: 32px; font-weight: 700; color: {score_color(citations.get('overall_rate', 0), 50, 10)};">{citations.get('overall_rate', 0)}%</div>
            <div style="font-size: 11px; color: #6b7280;">Citation Rate</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #f9fafb; border-radius: 8px; flex: 1;">
            <div style="font-size: 20px; font-weight: 600;">{citations.get('total_cited', 0)}/{citations.get('total_queries', 0)}</div>
            <div style="font-size: 11px; color: #6b7280;">Queries Cited</div>
          </div>
        </div>
        <h3 style="font-size: 13px; color: #374151; margin: 16px 0 8px;">By Query Type</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">{type_rows}</table>
        {"<h3 style='font-size: 13px; color: #374151; margin: 16px 0 8px;'>Who Gets Mentioned Instead</h3><table style='width: 100%; border-collapse: collapse; margin-bottom: 24px;'>" + comp_rows + "</table>" if comp_rows else ""}
        """)

    # Traffic
    if ga4.get("overview"):
        o = ga4["overview"]
        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Traffic (Last 30 Days)</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          {metric_row('Active Users', f'{o.get("active_users", 0):,}')}
          {metric_row('Sessions', f'{o.get("sessions", 0):,}')}
          {metric_row('Pageviews', f'{o.get("pageviews", 0):,}')}
          {metric_row('Bounce Rate', f'{o.get("bounce_rate", 0)}%')}
        </table>
        """)

    # SEO Health
    if crawl:
        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">SEO Health</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          {metric_row('Pages Crawled', str(crawl.get('pages_crawled', 0)))}
          {metric_row('Issues Found', str(crawl.get('total_issues', 0)), '#eab308' if crawl.get('total_issues', 0) > 0 else '#22c55e')}
          {metric_row('Pages with Schema', str(crawl.get('pages_with_schema', 0)))}
          {metric_row('Avg Word Count', str(crawl.get('avg_word_count', 0)))}
          {metric_row('Orphan Pages', str(crawl.get('orphan_pages', 0)))}
        </table>
        """)

    # Site Speed
    if pagespeed.get("avg_scores"):
        s = pagespeed["avg_scores"]
        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Site Speed (Mobile)</h2>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          {metric_row('Performance', f'{s.get("performance", 0)}/100', score_color(s.get('performance', 0), 80, 50))}
          {metric_row('SEO Score', f'{s.get("seo", 0)}/100', score_color(s.get('seo', 0)))}
          {metric_row('Accessibility', f'{s.get("accessibility", 0)}/100', score_color(s.get('accessibility', 0)))}
          {metric_row('Best Practices', f'{s.get("best-practices", 0)}/100')}
        </table>
        """)

    # Competitor Comparison
    if competitors and competitors.get("competitors"):
        comp_table = ""
        for c in competitors["competitors"][:8]:
            comp_table += f'<tr><td style="padding: 6px 16px; font-size: 12px;">{c["domain"]}</td><td style="padding: 6px 16px; font-size: 12px; font-weight: 600;">{c["visibility_pct"]}%</td><td style="padding: 6px 16px; font-size: 12px;">#{c["avg_position"]}</td></tr>'

        sections.append(f"""
        <h2 style="color: #1a3a4a; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Search Visibility vs Competitors</h2>
        <p style="font-size: 12px; color: #6b7280; margin-bottom: 12px;">Based on {competitors.get('total_queries', 0)} target queries in Google (UK).</p>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          <tr style="background: #f0fdf4;"><td style="padding: 6px 16px; font-size: 12px; font-weight: 600; color: #15803d;">{domain} (you)</td><td style="padding: 6px 16px; font-size: 12px; font-weight: 700; color: #15803d;">{competitors.get('client_visibility_pct', 0)}%</td><td style="padding: 6px 16px; font-size: 12px; color: #15803d;">{f'#{competitors["client_avg_position"]}' if competitors.get('client_avg_position') else '--'}</td></tr>
          {comp_table}
        </table>
        """)

    # Build full HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{brand} — AI Search Visibility Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; color: #1f2937; }}
    @page {{ size: A4; margin: 20mm; }}
  </style>
</head>
<body>
  <div style="background: linear-gradient(135deg, #1a3a4a, #2d5a6b); color: white; padding: 32px; margin-bottom: 24px;">
    <div style="font-size: 12px; opacity: 0.7;">Prepared by Rank4AI Ltd</div>
    <h1 style="margin: 8px 0 4px; font-size: 24px;">{brand} — AI Search Visibility Report</h1>
    <div style="font-size: 13px; opacity: 0.8;">{domain} · {today}</div>
  </div>

  <div style="max-width: 700px; margin: 0 auto; padding: 0 24px;">
    {''.join(sections)}

    <div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; text-align: center; color: #9ca3af; font-size: 11px;">
      <p>Generated by Rank4AI Dashboard · rank4ai.co.uk</p>
      <p>Report date: {today}</p>
    </div>
  </div>
</body>
</html>"""

    return html


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if len(sys.argv) < 2:
        print("Usage: python3 generate_report.py <client_id|all>")
        return

    target = sys.argv[1]
    clients_file = os.path.join(PROJECT_DIR, "src", "data", "clients.json")
    with open(clients_file) as f:
        clients = json.load(f)
    client_ids = [c["id"] for c in clients]

    targets = client_ids if target == "all" else [target]

    for client_id in targets:
        if client_id not in client_ids:
            print(f"Unknown client: {client_id}")
            continue

        print(f"Generating report for {client_id}...")
        html = generate_html_report(client_id)
        if not html:
            continue

        # Save HTML
        today = datetime.now().strftime("%Y-%m-%d")
        html_file = os.path.join(OUTPUT_DIR, f"{client_id}-report-{today}.html")
        with open(html_file, "w") as f:
            f.write(html)
        print(f"  HTML: {html_file}")

        # Try to generate PDF
        try:
            from weasyprint import HTML
            pdf_file = os.path.join(OUTPUT_DIR, f"{client_id}-report-{today}.pdf")
            HTML(string=html).write_pdf(pdf_file)
            print(f"  PDF: {pdf_file}")
        except Exception as e:
            print(f"  PDF generation failed: {e}")
            print(f"  HTML report is still available at {html_file}")


if __name__ == "__main__":
    main()
