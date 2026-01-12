#!/usr/bin/env python3
"""
Batch Website Auditor
Processes multiple CPA/accountant websites from a CSV file
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from website_auditor import WebsiteAuditor


class BatchAuditor:
    def __init__(self):
        self.auditor = WebsiteAuditor()
        self.results_dir = Path("batch_results")
        self.results_dir.mkdir(exist_ok=True)

    def process_csv(self, csv_path: str) -> List[Dict]:
        """Process all URLs from a CSV file"""

        if not os.path.exists(csv_path):
            print(f"❌ Error: CSV file not found: {csv_path}")
            return []

        # Read URLs from CSV
        urls = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'url' in row and row['url'].strip():
                    urls.append({
                        'url': row['url'].strip(),
                        'company_name': row.get('company_name', '').strip(),
                        'notes': row.get('notes', '').strip()
                    })

        if not urls:
            print("❌ No URLs found in CSV file")
            print("Make sure your CSV has a 'url' column")
            return []

        print(f"\n{'='*70}")
        print(f"🚀 BATCH AUDIT STARTED")
        print(f"{'='*70}")
        print(f"Total websites to audit: {len(urls)}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # Process each URL
        results = []
        for idx, site_info in enumerate(urls, 1):
            url = site_info['url']
            company_name = site_info['company_name'] or url

            print(f"\n{'─'*70}")
            print(f"[{idx}/{len(urls)}] Processing: {company_name}")
            print(f"URL: {url}")
            print(f"{'─'*70}")

            try:
                audit_result = self.auditor.audit_website(url)

                # Add company info to results
                audit_result['company_name'] = company_name
                audit_result['input_notes'] = site_info['notes']

                results.append(audit_result)

                # Show quick summary
                if 'error' not in audit_result:
                    rec = audit_result['recommendation']
                    print(f"\n✅ Complete: {rec['recommendation']} - Score: {rec['score']}/100")
                else:
                    print(f"\n⚠️  Error: {audit_result['error']}")

            except Exception as e:
                print(f"\n❌ Failed to audit {url}: {str(e)}")
                results.append({
                    'url': url,
                    'company_name': company_name,
                    'error': str(e)
                })

            # Progress update
            remaining = len(urls) - idx
            if remaining > 0:
                print(f"\n📊 Progress: {idx}/{len(urls)} complete, {remaining} remaining")

        # Generate summary report
        summary_path = self._generate_summary_report(results, csv_path)

        print(f"\n{'='*70}")
        print(f"✅ BATCH AUDIT COMPLETE")
        print(f"{'='*70}")
        print(f"Total audited: {len(results)}")
        print(f"Summary saved to: {summary_path}")
        print(f"{'='*70}\n")

        return results

    def _generate_summary_report(self, results: List[Dict], input_csv: str) -> Path:
        """Generate CSV and Markdown summary of batch results"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # CSV Summary
        csv_summary_path = self.results_dir / f"summary_{timestamp}.csv"

        with open(csv_summary_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'company_name',
                'url',
                'recommendation',
                'score',
                'percentage',
                'total_issues',
                'has_clear_cta',
                'has_contact_form',
                'has_phone_number',
                'has_team_info',
                'has_credentials',
                'has_google_maps',
                'design_score',
                'load_time_seconds',
                'report_path',
                'error'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                if 'error' in result and 'recommendation' not in result:
                    # Error case
                    writer.writerow({
                        'company_name': result.get('company_name', ''),
                        'url': result.get('url', ''),
                        'error': result.get('error', 'Unknown error')
                    })
                else:
                    # Successful audit
                    rec = result['recommendation']
                    sections = result['audit_sections']

                    writer.writerow({
                        'company_name': result.get('company_name', ''),
                        'url': result['url'],
                        'recommendation': rec['recommendation'],
                        'score': rec['score'],
                        'percentage': rec['percentage'],
                        'total_issues': rec['total_issues'],
                        'has_clear_cta': sections['conversion_elements']['has_clear_cta'],
                        'has_contact_form': sections['conversion_elements']['has_contact_form'],
                        'has_phone_number': sections['conversion_elements']['has_phone_number'],
                        'has_team_info': sections['trust_signals']['has_team_info'],
                        'has_credentials': sections['trust_signals']['has_credentials'],
                        'has_google_maps': sections['trust_signals']['has_google_maps'],
                        'design_score': sections['visual_design']['score'],
                        'load_time_seconds': sections['technical']['load_time_seconds'],
                        'report_path': result.get('report_path', ''),
                        'error': ''
                    })

        # Markdown Summary
        md_summary_path = self.results_dir / f"summary_{timestamp}.md"

        with open(md_summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# Batch Audit Summary Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Input File:** {input_csv}\n")
            f.write(f"**Total Sites Audited:** {len(results)}\n\n")

            # Categorize results
            strong_yes = [r for r in results if r.get('recommendation', {}).get('recommendation') == 'STRONG YES']
            yes = [r for r in results if r.get('recommendation', {}).get('recommendation') == 'YES']
            maybe = [r for r in results if r.get('recommendation', {}).get('recommendation') == 'MAYBE']
            no = [r for r in results if r.get('recommendation', {}).get('recommendation') == 'NO']
            errors = [r for r in results if 'error' in r and 'recommendation' not in r]

            f.write(f"## 📊 Overview\n\n")
            f.write(f"| Category | Count | Percentage |\n")
            f.write(f"|----------|-------|------------|\n")
            f.write(f"| 🔥 STRONG YES | {len(strong_yes)} | {len(strong_yes)/len(results)*100:.1f}% |\n")
            f.write(f"| ✅ YES | {len(yes)} | {len(yes)/len(results)*100:.1f}% |\n")
            f.write(f"| 🤔 MAYBE | {len(maybe)} | {len(maybe)/len(results)*100:.1f}% |\n")
            f.write(f"| ❌ NO | {len(no)} | {len(no)/len(results)*100:.1f}% |\n")
            if errors:
                f.write(f"| ⚠️ ERRORS | {len(errors)} | {len(errors)/len(results)*100:.1f}% |\n")

            # Top Prospects
            if strong_yes or yes:
                f.write(f"\n## 🎯 Top Prospects (STRONG YES & YES)\n\n")

                top_prospects = strong_yes + yes
                # Sort by score (lowest first = most opportunity)
                top_prospects.sort(key=lambda x: x.get('recommendation', {}).get('score', 100))

                for result in top_prospects:
                    rec = result['recommendation']
                    company = result.get('company_name', result['url'])

                    f.write(f"### {company}\n\n")
                    f.write(f"- **URL:** {result['url']}\n")
                    f.write(f"- **Recommendation:** {rec['recommendation']}\n")
                    f.write(f"- **Score:** {rec['score']}/100 ({rec['percentage']}%)\n")
                    f.write(f"- **Issues Found:** {rec['total_issues']}\n")
                    f.write(f"- **Reason:** {rec['reason']}\n")

                    # Top 3 opportunities
                    if rec['opportunities']:
                        f.write(f"- **Top Opportunities:**\n")
                        for opp in rec['opportunities'][:3]:
                            f.write(f"  - {opp}\n")

                    f.write(f"- **Full Report:** [{result.get('report_path', 'N/A')}]({result.get('report_path', '')})\n")
                    f.write(f"\n---\n\n")

            # Maybe prospects
            if maybe:
                f.write(f"\n## 🤔 Moderate Prospects (MAYBE)\n\n")
                for result in maybe:
                    rec = result['recommendation']
                    company = result.get('company_name', result['url'])
                    f.write(f"- **{company}** - Score: {rec['score']}/100 - [{result.get('report_path', 'Report')}]({result.get('report_path', '')})\n")

            # Low priority
            if no:
                f.write(f"\n## ❌ Low Priority (NO)\n\n")
                for result in no:
                    rec = result['recommendation']
                    company = result.get('company_name', result['url'])
                    f.write(f"- **{company}** - Score: {rec['score']}/100 - Well optimized\n")

            # Errors
            if errors:
                f.write(f"\n## ⚠️ Failed Audits\n\n")
                for result in errors:
                    company = result.get('company_name', result.get('url', 'Unknown'))
                    f.write(f"- **{company}** - Error: {result.get('error', 'Unknown error')}\n")

            # Export info
            f.write(f"\n## 📁 Files Generated\n\n")
            f.write(f"- **CSV Summary:** {csv_summary_path}\n")
            f.write(f"- **Individual Reports:** See `reports/` directory\n")
            f.write(f"- **Screenshots:** See `screenshots/` directory\n\n")

        print(f"📄 CSV summary: {csv_summary_path}")
        print(f"📄 Markdown summary: {md_summary_path}")

        return md_summary_path


def main():
    """CLI entry point for batch processing"""

    if len(sys.argv) < 2:
        print("Usage: python batch_auditor.py <csv_file>")
        print("Example: python batch_auditor.py prospects.csv")
        print("\nCSV file should have columns: url, company_name (optional), notes (optional)")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    batch_auditor = BatchAuditor()
    results = batch_auditor.process_csv(csv_path)

    # Show final summary
    if results:
        strong_yes = sum(1 for r in results if r.get('recommendation', {}).get('recommendation') == 'STRONG YES')
        yes_count = sum(1 for r in results if r.get('recommendation', {}).get('recommendation') == 'YES')

        print(f"\n🎯 ACTION ITEMS:")
        print(f"   - {strong_yes} STRONG YES prospects (high priority)")
        print(f"   - {yes_count} YES prospects (good priority)")
        print(f"   - Check batch_results/ folder for detailed summaries\n")


if __name__ == "__main__":
    main()
