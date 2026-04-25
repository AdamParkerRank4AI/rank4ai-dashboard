#!/usr/bin/env python3
"""
Check AI citations broken down by query type — matched to page categories.
Tests which types of queries trigger citations for the brand.
"""
import json
import os
from datetime import datetime

import anthropic

OUTPUT_DIR = os.path.expanduser("~/rank4ai-dashboard/src/data/live")

CLIENTS = {
    "rank4ai": {
        "brand": "Rank4AI",
        "domain": "rank4ai.co.uk",
        "competitors": ["YALD", "AEO-REX", "First Answer", "Kaizen", "ClickSlice", "Screaming Frog", "Profound", "Otterly", "Goodie"],
        "query_types": {
            "brand": [
                "What is Rank4AI?",
                "Tell me about Rank4AI",
                "Is Rank4AI a real agency?",
                "Who founded Rank4AI?",
            ],
            "best_of": [
                "Best AI search visibility agencies UK",
                "Top AI SEO agencies in the UK 2026",
                "Best GEO agencies UK",
                "Best AI SEO agencies for law firms UK",
                "Best AI search agencies for B2B SaaS",
                "Best AI visibility consultants UK",
                "Top GEO consultants London",
                "Best AEO agencies UK",
            ],
            "how_to": [
                "How do I get my business found in ChatGPT?",
                "How to optimise for AI search engines",
                "How to get cited by Perplexity AI",
                "How to create an llms.txt file",
                "How to appear in Google AI Overviews",
                "How to optimise for Claude search",
                "How to optimise for Gemini",
                "How to track AI search visibility",
                "How to measure AI citation rate",
                "How to get into ChatGPT search results",
            ],
            "what_is": [
                "What is AI search visibility?",
                "What is GEO generative engine optimization?",
                "What is AEO answer engine optimization?",
                "What is the difference between SEO and GEO?",
                "What is llms.txt?",
                "What is an AI Overview?",
                "What is brand mention monitoring in AI?",
                "What does an AI SEO agency do?",
                "What is entity SEO?",
                "What is a citation in AI search?",
            ],
            "comparison": [
                "SEO vs GEO which is more important?",
                "Traditional SEO vs AI search optimization",
                "Compare AI search agencies UK",
                "GEO vs AEO difference",
                "Profound vs Otterly vs Goodie comparison",
                "Best AI visibility tracker tool",
                "AI SEO agency vs traditional SEO agency",
            ],
            "cost": [
                "How much does AI search optimisation cost UK?",
                "AI SEO agency pricing UK",
                "GEO consultancy fees UK",
                "How much to hire an AI search agency?",
                "AI visibility audit cost UK",
            ],
            "local": [
                "AI search agencies London",
                "AI SEO services near me UK",
                "AI search consultants Manchester",
                "GEO agencies Birmingham",
                "AI visibility specialists Edinburgh",
            ],
            "industry": [
                "AI SEO for law firms",
                "AI search for accountants UK",
                "AI SEO for SaaS companies",
                "AI search optimisation for ecommerce",
                "AI visibility for B2B services",
                "AI SEO for professional services",
            ],
        },
    },
    "market-invoice": {
        "brand": "Market Invoice",
        "domain": "marketinvoice.co.uk",
        "competitors": ["Close Brothers", "Bibby", "Aldermore", "HSBC", "Kriya", "Sonovate", "Lloyds", "Barclays", "NatWest", "RBS", "Skipton", "Pulse Cashflow"],
        "query_types": {
            "brand": [
                "What is Market Invoice?",
                "Tell me about marketinvoice.co.uk",
                "Is Market Invoice the same as MarketFinance?",
                "Is Market Invoice a real comparison site?",
            ],
            "best_of": [
                "Best invoice finance companies UK",
                "Top invoice factoring providers UK",
                "Best invoice finance for small business UK",
                "Best invoice discounting providers UK",
                "Best invoice finance for startups",
                "Top spot factoring providers UK",
                "Best confidential invoice finance UK",
            ],
            "how_to": [
                "How does invoice finance work UK?",
                "How to get set up with invoice factoring",
                "How to choose an invoice finance provider",
                "How to compare invoice finance quotes",
                "How long does invoice finance take to set up?",
                "How to switch invoice finance provider",
                "How to negotiate invoice finance fees",
            ],
            "what_is": [
                "What is invoice factoring?",
                "What is confidential invoice discounting?",
                "What is selective invoice finance?",
                "What is spot factoring?",
                "What is supply chain finance?",
                "What is asset based lending?",
                "What is the difference between factoring and invoice discounting?",
                "What is the BoE base rate impact on invoice finance?",
            ],
            "comparison": [
                "Compare invoice finance providers UK",
                "Invoice finance vs business loan",
                "Factoring vs invoice discounting difference",
                "Close Brothers vs Bibby invoice finance",
                "Aldermore vs HSBC invoice finance",
                "Bank vs independent invoice finance providers",
                "Invoice finance vs overdraft for cash flow",
            ],
            "cost": [
                "How much does invoice finance cost UK?",
                "Invoice finance rates and fees UK",
                "Typical invoice factoring fees UK 2026",
                "Hidden costs of invoice finance",
                "Invoice finance discount rate vs service fee",
            ],
            "industry": [
                "Invoice finance for recruitment agencies UK",
                "Construction invoice finance UK",
                "Invoice finance for NHS suppliers",
                "Invoice finance for manufacturing UK",
                "Transport invoice finance UK",
                "Invoice finance for wholesale businesses",
                "Invoice finance for printers UK",
            ],
            "location": [
                "Invoice finance Manchester",
                "Invoice factoring London",
                "Invoice finance Birmingham",
                "Invoice finance Leeds",
                "Invoice finance Bristol",
                "Invoice factoring Glasgow",
                "Invoice finance Liverpool",
            ],
        },
    },
    "seocompare": {
        "brand": "SEO Compare",
        "domain": "seocompare.co.uk",
        "competitors": ["ClickSlice", "Found", "Propeller", "Aira", "Rise at Seven", "Impression", "Vixen Digital", "Kaizen", "Re:signal", "Footprint Digital"],
        "query_types": {
            "brand": [
                "What is SEO Compare?",
                "Tell me about seocompare.co.uk",
                "Is SEO Compare a real comparison site?",
            ],
            "best_of": [
                "Best SEO agencies UK 2026",
                "Top rated SEO companies UK",
                "Best AI SEO agencies UK",
                "Top SEO agencies London 2026",
                "Best technical SEO agencies UK",
                "Best small business SEO agencies UK",
                "Best ecommerce SEO agencies UK",
                "Best SaaS SEO agencies UK",
                "Top GEO agencies UK 2026",
                "Best AI search agencies for enterprise",
            ],
            "how_to": [
                "How to choose an SEO agency UK",
                "How to compare SEO companies",
                "How to vet an SEO agency",
                "How to spot an SEO agency scam",
                "Questions to ask before hiring an SEO agency",
                "How to evaluate SEO agency case studies",
                "How to switch SEO agencies",
            ],
            "what_is": [
                "What should I look for in an SEO agency?",
                "What is technical SEO?",
                "What is local SEO?",
                "What is AI SEO?",
                "What is GEO?",
                "What does an SEO agency actually do?",
                "What is an SEO retainer?",
            ],
            "comparison": [
                "Compare SEO agencies UK",
                "Freelance SEO vs agency which is better?",
                "Agency vs in-house SEO",
                "Boutique vs large SEO agency",
                "AI SEO agency vs traditional SEO agency",
                "DIY SEO vs hiring an agency",
                "Compare AI search agencies UK",
            ],
            "cost": [
                "How much does an SEO agency cost UK?",
                "SEO agency monthly retainer fees UK",
                "Typical SEO project cost UK 2026",
                "AI SEO agency pricing UK",
                "Average SEO consultant day rate UK",
            ],
            "industry": [
                "Best SEO agencies for law firms UK",
                "Best SEO agencies for accountants UK",
                "Best SEO for healthcare providers UK",
                "Best SEO for property companies UK",
                "Best SEO for nonprofits UK",
            ],
            "location": [
                "SEO agencies London",
                "SEO agencies Manchester",
                "SEO agencies Birmingham",
                "SEO agencies Edinburgh",
                "SEO agencies Bristol",
                "SEO agencies Leeds",
                "SEO agencies Glasgow",
            ],
        },
    },
    "rochellemarashi": {
        "brand": "Rochelle Marashi",
        "domain": "rochellemarashi.pages.dev",
        "competitors": ["BACP", "UKCP", "Counselling Directory", "Psychology Today", "Welldoing"],
        "query_types": {
            "brand": [
                "Who is Rochelle Marashi?",
                "Tell me about Rochelle Marashi therapist",
                "Is Rochelle Marashi a qualified psychotherapist?",
            ],
            "best_of": [
                "Best psychotherapists in London",
                "Best therapists for coercive control",
                "Best trauma therapists UK",
                "Best psychotherapists Hampstead",
                "Best psychotherapists for stalking victims",
                "Best UK therapists for narcissistic abuse",
            ],
            "how_to": [
                "How to find a psychotherapist UK",
                "How to choose a therapist for trauma",
                "How to know if you need therapy",
                "How to recognise coercive control",
                "How to leave a coercively controlling relationship",
                "How to find a therapist who specialises in stalking",
            ],
            "what_is": [
                "What is psychotherapy?",
                "What is coercive control?",
                "What is the difference between counselling and psychotherapy?",
                "What is trauma-informed therapy?",
                "What is online therapy UK?",
                "What does a UKCP psychotherapist do?",
            ],
            "comparison": [
                "Counselling vs psychotherapy difference",
                "CBT vs psychodynamic therapy",
                "Online therapy vs in-person therapy UK",
                "BACP vs UKCP therapist accreditation",
            ],
            "cost": [
                "How much does private therapy cost UK?",
                "Average psychotherapy session cost London",
                "Is private therapy worth the cost UK?",
            ],
            "conditions": [
                "Therapy for anxiety London",
                "Therapy for trauma survivors UK",
                "Therapy for relationship abuse",
                "Therapy for PTSD UK",
                "Therapy for stalking survivors",
                "Therapy for narcissistic abuse recovery",
                "Therapy for complex trauma UK",
                "Therapy for domestic abuse survivors UK",
                "Therapy for gaslighting recovery",
            ],
            "location": [
                "Psychotherapist Hampstead",
                "Therapist London NW3",
                "Online psychotherapist UK",
                "Psychotherapist North London",
                "Trauma therapist Camden",
                "Private therapist Highgate",
            ],
            "process": [
                "What happens in a first therapy session?",
                "How long does psychotherapy take to work?",
                "How often should I see a therapist?",
                "Is therapy confidential UK?",
                "What's the difference between BACP and UKCP?",
                "Can I get therapy on the NHS for trauma?",
                "How to prepare for your first therapy session",
            ],
        },
    },
}


def check_query(api_client, query, brand, domain, competitors):
    """Query Claude and check for brand + competitor mentions."""
    try:
        message = api_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": query}],
        )
        response = message.content[0].text
        response_lower = response.lower()
        brand_lower = brand.lower()
        domain_lower = domain.lower()

        brand_mentioned = brand_lower in response_lower or domain_lower in response_lower

        competitor_mentions = []
        for comp in competitors:
            if comp.lower() in response_lower:
                competitor_mentions.append(comp)

        return {
            "query": query,
            "brand_mentioned": brand_mentioned,
            "competitors_mentioned": competitor_mentions,
            "response_preview": response[:300],
        }
    except Exception as e:
        return {"query": query, "brand_mentioned": False, "error": str(e)[:100]}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        return

    api_client = anthropic.Anthropic(api_key=api_key)
    all_results = {}

    for client_id, config in CLIENTS.items():
        print(f"\n{'='*50}")
        print(f"{config['brand']}")
        print(f"{'='*50}")

        type_results = {}
        total_cited = 0
        total_queries = 0

        for query_type, queries in config["query_types"].items():
            print(f"\n  [{query_type.upper()}]")
            results = []

            for query in queries:
                result = check_query(api_client, query, config["brand"], config["domain"], config["competitors"])
                results.append(result)
                total_queries += 1

                status = "CITED" if result.get("brand_mentioned") else "not cited"
                comps = ", ".join(result.get("competitors_mentioned", [])[:3])
                comp_str = f" | Competitors: {comps}" if comps else ""
                print(f"    {status}: {query[:50]}...{comp_str}")

                if result.get("brand_mentioned"):
                    total_cited += 1

            cited_in_type = sum(1 for r in results if r.get("brand_mentioned"))
            type_results[query_type] = {
                "queries": len(queries),
                "cited": cited_in_type,
                "rate": round(cited_in_type / max(len(queries), 1) * 100, 1),
                "results": results,
            }

        overall_rate = round(total_cited / max(total_queries, 1) * 100, 1)

        # Aggregate competitor data
        all_comps = {}
        for qt in type_results.values():
            for r in qt["results"]:
                for c in r.get("competitors_mentioned", []):
                    all_comps[c] = all_comps.get(c, 0) + 1
        top_comps = sorted(all_comps.items(), key=lambda x: -x[1])

        all_results[client_id] = {
            "brand": config["brand"],
            "tested_at": datetime.now().isoformat(),
            "total_queries": total_queries,
            "total_cited": total_cited,
            "overall_rate": overall_rate,
            "by_type": type_results,
            "top_competitors": [{"name": n, "mentions": c} for n, c in top_comps[:10]],
        }

        print(f"\n  Overall: {total_cited}/{total_queries} ({overall_rate}%)")
        print(f"  By type:")
        for qt, data in type_results.items():
            print(f"    {qt}: {data['cited']}/{data['queries']} ({data['rate']}%)")

    output_file = os.path.join(OUTPUT_DIR, "citations_by_type.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()
