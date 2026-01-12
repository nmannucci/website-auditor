# CPA Website Auditor

An automated tool that audits accountant and CPA firm websites to identify prospects for design and SEO services.

## What It Does

This tool analyzes CPA/accountant websites and provides a detailed audit covering:

- **Visual Design**: Uses AI vision to assess if the site looks modern and professional
- **Conversion Elements**: Checks for CTAs, contact forms, phone numbers
- **Trust Signals**: Looks for team credentials, licenses, Google Maps embed
- **SEO**: Analyzes meta tags, heading structure, NAP consistency in footer
- **Technical**: Measures page load speed and mobile optimization

It then gives you a clear **recommendation** (STRONG YES, YES, MAYBE, or NO) on whether to reach out to them as a prospect.

## Installation

1. **Clone or download this project**

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

4. **Set up your API key**:
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Usage

Run the auditor with any website URL:

```bash
python website_auditor.py https://example-cpa-firm.com
```

Or without the https:
```bash
python website_auditor.py example-cpa-firm.com
```

## What You Get

After running an audit, you'll receive:

1. **Console Summary**: Quick overview of the recommendation and score
2. **Detailed Report**: Markdown file saved in `reports/` folder with:
   - Overall recommendation (STRONG YES / YES / MAYBE / NO)
   - Score out of 100
   - Complete breakdown of all issues found
   - List of improvement opportunities
   - Next steps for outreach

3. **Screenshots**: Saved in `screenshots/` folder:
   - Full desktop screenshot
   - Mobile screenshot

## Example Output

```
🔍 Starting audit for: https://example-cpa.com
📸 Loading page and capturing screenshot...
🎨 Analyzing visual design...
📞 Checking conversion elements...
🏆 Checking trust signals...
🔍 Checking SEO elements...
📊 Calculating recommendation...
📝 Generating report...

✅ Audit complete! Report saved to: reports/audit_example-cpa.com_20260109_143022.md

============================================================
RECOMMENDATION: STRONG YES
Score: 45.5/100 (45.5%)
This website has significant improvement opportunities across design, conversion, and SEO. Excellent prospect.
============================================================
```

## Understanding the Scoring

The tool scores websites across these categories:

- **Visual Design** (30 points): Professional appearance, modern look
- **Conversion Elements** (25 points): CTA buttons, contact forms, phone numbers
- **Trust Signals** (20 points): Team info, credentials, Google Maps
- **SEO** (15 points): Meta tags, heading structure, NAP in footer
- **Technical** (10 points): Load speed, mobile optimization

**Score Ranges**:
- **0-60**: STRONG YES - Major opportunities, excellent prospect
- **60-75**: YES - Notable improvements needed, good prospect
- **75-85**: MAYBE - Some opportunities, moderate prospect
- **85-100**: NO - Well-optimized, limited opportunity

## Batch Processing Multiple Sites

### Using CSV Files (Recommended)

The easiest way to audit multiple sites is using a CSV file:

1. **Create a CSV file** with your prospect list (see `prospects_example.csv`):
```csv
url,company_name,notes
https://example-cpa-firm1.com,Smith & Associates CPA,Found on Google - local firm
https://example-accounting2.com,Johnson Accounting Services,Referral from LinkedIn
https://example-tax-services3.com,Martinez Tax & Consulting,Cold prospect - seems outdated
```

2. **Run the batch auditor**:
```bash
python batch_auditor.py prospects.csv
```

3. **Get comprehensive results**:
   - Individual detailed reports for each site (in `reports/` folder)
   - Summary CSV file with all scores and metrics (in `batch_results/` folder)
   - Summary Markdown report categorizing prospects by priority
   - All screenshots saved in `screenshots/` folder

### What You Get from Batch Processing

The batch auditor generates:

1. **CSV Summary** (`batch_results/summary_TIMESTAMP.csv`):
   - Sortable spreadsheet with all key metrics
   - Columns: company name, URL, recommendation, score, all individual checks
   - Perfect for importing into your CRM or filtering in Excel

2. **Markdown Summary Report** (`batch_results/summary_TIMESTAMP.md`):
   - Organized by priority: STRONG YES, YES, MAYBE, NO
   - Top prospects listed first with their main issues
   - Quick overview of opportunity breakdown
   - Direct links to individual detailed reports

3. **Individual Reports**: Full audit report for each site in `reports/` folder

4. **Screenshots**: Desktop and mobile screenshots for every site

### Example Batch Output

```
======================================================================
🚀 BATCH AUDIT STARTED
======================================================================
Total websites to audit: 15
Timestamp: 2026-01-09 14:30:22
======================================================================

[1/15] Processing: Smith & Associates CPA
URL: https://example-cpa-firm1.com
...
✅ Complete: STRONG YES - Score: 42/100

[2/15] Processing: Johnson Accounting Services
...

======================================================================
✅ BATCH AUDIT COMPLETE
======================================================================
Total audited: 15
Summary saved to: batch_results/summary_20260109_143500.md
======================================================================

🎯 ACTION ITEMS:
   - 8 STRONG YES prospects (high priority)
   - 4 YES prospects (good priority)
   - Check batch_results/ folder for detailed summaries
```

### Using Python Script (Advanced)

You can also create a custom Python script:

```python
from website_auditor import WebsiteAuditor

urls = [
    "example-cpa1.com",
    "example-cpa2.com",
    "example-cpa3.com"
]

auditor = WebsiteAuditor()

for url in urls:
    print(f"\n{'='*60}")
    print(f"Auditing: {url}")
    print(f"{'='*60}")
    results = auditor.audit_website(url)

    if "error" not in results:
        rec = results["recommendation"]
        print(f"Result: {rec['recommendation']} - {rec['score']}/100")
```

## Tips for Best Results

1. **Check robots.txt**: Some sites may block automated access
2. **Run during off-hours**: Avoid peak traffic times for accurate load time measurements
3. **Review screenshots**: The AI design analysis is good, but your expert eye can catch nuances
4. **Check Google Business Profile**: The tool notes if NAP is in footer, but you should manually verify it matches their GBP

## Troubleshooting

**"Error: ANTHROPIC_API_KEY not found"**
- Make sure you created a `.env` file with your API key

**"Timeout loading page"**
- Some sites are slow or block automation. The tool will continue with partial data.

**"No module named playwright"**
- Run: `pip install -r requirements.txt`
- Then: `playwright install chromium`

## Project Structure

```
Website Auditor/
├── website_auditor.py      # Main script for single site audits
├── batch_auditor.py        # Batch processing from CSV files
├── prospects_example.csv   # Example CSV template
├── requirements.txt        # Python dependencies
├── .env                    # Your API key (create this)
├── .env.example           # Template
├── screenshots/           # Generated screenshots
├── reports/              # Individual audit reports
├── batch_results/        # Batch summary reports (CSV + Markdown)
└── README.md            # This file
```

## Cost Estimates

Using Claude API for vision analysis:
- ~$0.01-0.02 per audit
- Batch of 50 audits: ~$0.50-1.00

This is incredibly cost-effective for lead generation!

## Next Steps

After identifying good prospects:

1. Review the detailed report
2. Look at the screenshots to see the site yourself
3. Use the "opportunities" list to customize your outreach
4. Reference specific issues when reaching out: "I noticed your site doesn't have a Google Maps embed, which could really help with local SEO..."

## License

Free to use for your business!
