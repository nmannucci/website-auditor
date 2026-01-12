#!/usr/bin/env python3
"""
Website Auditor for Accountant/CPA Firm Websites
Analyzes websites for design, SEO, and conversion opportunities
"""

import os
import re
import json
import base64
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Tuple

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WebsiteAuditor:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.screenshots_dir = Path("screenshots")
        self.reports_dir = Path("reports")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

    def audit_website(self, url: str) -> Dict:
        """Main audit function that coordinates all checks"""
        print(f"\n🔍 Starting audit for: {url}")

        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        audit_results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "audit_sections": {}
        }

        try:
            # Load page and capture data
            page_data = self._load_and_capture_page(url)
            audit_results["page_data"] = page_data

            # Run all audit checks
            audit_results["audit_sections"]["visual_design"] = self._audit_visual_design(page_data)
            audit_results["audit_sections"]["conversion_elements"] = self._audit_conversion_elements(page_data)
            audit_results["audit_sections"]["trust_signals"] = self._audit_trust_signals(page_data)
            audit_results["audit_sections"]["seo_elements"] = self._audit_seo_elements(page_data)
            audit_results["audit_sections"]["technical"] = page_data["technical"]

            # Calculate overall score and recommendation
            audit_results["recommendation"] = self._calculate_recommendation(audit_results)

            # Generate report
            report_path = self._generate_report(audit_results)
            audit_results["report_path"] = str(report_path)

            print(f"\n✅ Audit complete! Report saved to: {report_path}")

        except Exception as e:
            print(f"\n❌ Error during audit: {str(e)}")
            audit_results["error"] = str(e)

        return audit_results

    def _load_and_capture_page(self, url: str) -> Dict:
        """Load the webpage and capture screenshot + HTML"""
        print("📸 Loading page and capturing screenshot...")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            # Navigate and wait for load
            start_time = datetime.now()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except PlaywrightTimeout:
                print("⚠️  Page load timeout, continuing with partial load...")
                page.wait_for_timeout(5000)

            load_time = (datetime.now() - start_time).total_seconds()

            # Capture screenshot
            domain = urlparse(url).netloc.replace('www.', '')
            screenshot_filename = f"{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = self.screenshots_dir / screenshot_filename
            page.screenshot(path=str(screenshot_path), full_page=True)

            # Get HTML content
            html_content = page.content()

            # Check mobile responsiveness
            mobile_page = browser.new_page(viewport={"width": 375, "height": 812})
            mobile_page.goto(url, wait_until="networkidle", timeout=30000)
            mobile_screenshot_path = self.screenshots_dir / f"{domain}_mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            mobile_page.screenshot(path=str(mobile_screenshot_path), full_page=False)

            # Get page title
            title = page.title()

            browser.close()

        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        return {
            "url": url,
            "screenshot_path": str(screenshot_path),
            "mobile_screenshot_path": str(mobile_screenshot_path),
            "html": html_content,
            "soup": soup,
            "title": title,
            "technical": {
                "load_time_seconds": round(load_time, 2),
                "has_viewport_meta": soup.find("meta", {"name": "viewport"}) is not None
            }
        }

    def _audit_visual_design(self, page_data: Dict) -> Dict:
        """Use Claude's vision to assess design quality"""
        print("🎨 Analyzing visual design...")

        # Read screenshot and encode
        with open(page_data["screenshot_path"], "rb") as f:
            screenshot_data = base64.standard_b64encode(f.read()).decode("utf-8")

        prompt = """Analyze this website homepage for an accountant/CPA firm. Evaluate:

1. **Overall Design Quality**: Does it look modern and professional, or outdated?
2. **Visual Hierarchy**: Is the page well-organized with clear sections?
3. **Color Scheme**: Is it professional and appropriate for a financial services firm?
4. **Typography**: Is the text readable and professionally styled?
5. **Imagery**: Are images professional quality and relevant?
6. **White Space**: Is there good use of spacing, or does it feel cluttered?

Provide a brief assessment (2-3 sentences) and a score from 1-10, where:
- 1-3: Severely outdated, unprofessional
- 4-6: Acceptable but could use improvement
- 7-8: Good, modern design
- 9-10: Excellent, highly professional

Format your response as JSON:
{
    "score": <number>,
    "assessment": "<your assessment>",
    "issues": ["<issue 1>", "<issue 2>", ...],
    "strengths": ["<strength 1>", "<strength 2>", ...]
}"""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            # Parse JSON response
            response_text = response.content[0].text
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "score": 5,
                    "assessment": response_text,
                    "issues": [],
                    "strengths": []
                }

            return result

        except Exception as e:
            print(f"⚠️  Error in visual design analysis: {str(e)}")
            return {
                "score": 5,
                "assessment": f"Could not analyze: {str(e)}",
                "issues": ["Analysis failed"],
                "strengths": []
            }

    def _audit_conversion_elements(self, page_data: Dict) -> Dict:
        """Check for conversion elements on homepage"""
        print("📞 Checking conversion elements...")

        soup = page_data["soup"]
        html_lower = page_data["html"].lower()

        results = {
            "has_clear_cta": False,
            "cta_details": "",
            "has_contact_form": False,
            "has_phone_number": False,
            "phone_numbers": [],
            "issues": []
        }

        # Check for CTA buttons
        cta_keywords = ['schedule', 'consult', 'contact us', 'get started', 'book', 'appointment', 'free consultation']
        buttons = soup.find_all(['button', 'a'], class_=re.compile(r'btn|button|cta', re.I))

        cta_found = []
        for btn in buttons:
            text = btn.get_text(strip=True).lower()
            if any(keyword in text for keyword in cta_keywords):
                cta_found.append(btn.get_text(strip=True))

        if cta_found:
            results["has_clear_cta"] = True
            results["cta_details"] = f"Found CTAs: {', '.join(cta_found[:3])}"
        else:
            results["issues"].append("No clear call-to-action button found on homepage")

        # Check for contact form
        forms = soup.find_all('form')
        form_keywords = ['contact', 'email', 'message', 'inquiry', 'name']

        for form in forms:
            form_text = form.get_text().lower()
            inputs = form.find_all(['input', 'textarea'])
            if len(inputs) >= 2 and any(keyword in form_text for keyword in form_keywords):
                results["has_contact_form"] = True
                break

        if not results["has_contact_form"]:
            results["issues"].append("No contact form found on homepage")

        # Check for phone numbers
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_matches = re.findall(phone_pattern, page_data["html"])

        if phone_matches:
            results["has_phone_number"] = True
            results["phone_numbers"] = [''.join(match) for match in phone_matches[:3]]
        else:
            results["issues"].append("No phone number found on homepage")

        # Check for clickable phone links
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if not tel_links and results["has_phone_number"]:
            results["issues"].append("Phone number found but not clickable (no tel: link)")

        return results

    def _audit_trust_signals(self, page_data: Dict) -> Dict:
        """Check for trust signals and credentials"""
        print("🏆 Checking trust signals...")

        soup = page_data["soup"]
        html_lower = page_data["html"].lower()

        results = {
            "has_team_info": False,
            "has_credentials": False,
            "credentials_found": [],
            "has_google_maps": False,
            "issues": []
        }

        # Check for team/about section
        team_keywords = ['our team', 'about us', 'meet our', 'our staff', 'our professionals']
        team_sections = soup.find_all(['section', 'div'], class_=re.compile(r'team|about|staff', re.I))

        if team_sections or any(keyword in html_lower for keyword in team_keywords):
            results["has_team_info"] = True
        else:
            results["issues"].append("No team/about section visible on homepage")

        # Check for credentials
        credential_keywords = ['cpa', 'certified public accountant', 'licensed', 'credential',
                              'certification', 'mba', 'masters', 'bachelor', 'university']

        credentials_found = []
        for keyword in credential_keywords:
            if keyword in html_lower:
                credentials_found.append(keyword.upper())

        if credentials_found:
            results["has_credentials"] = True
            results["credentials_found"] = list(set(credentials_found))
        else:
            results["issues"].append("No professional credentials or licenses mentioned on homepage")

        # Check for Google Maps embed
        if 'maps.google.com' in html_lower or 'google.com/maps/embed' in html_lower:
            results["has_google_maps"] = True
        else:
            results["issues"].append("No Google Maps embed found on homepage")

        return results

    def _audit_seo_elements(self, page_data: Dict) -> Dict:
        """Check SEO elements and NAP consistency"""
        print("🔍 Checking SEO elements...")

        soup = page_data["soup"]

        results = {
            "has_meta_description": False,
            "meta_description": "",
            "title_quality": "",
            "has_h1": False,
            "nap_in_footer": {},
            "issues": []
        }

        # Check meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            results["has_meta_description"] = True
            results["meta_description"] = meta_desc.get("content")[:100]
        else:
            results["issues"].append("Missing meta description tag")

        # Check title tag
        if page_data["title"]:
            results["title_quality"] = f"Present: '{page_data['title'][:60]}...'"
            if len(page_data["title"]) < 30:
                results["issues"].append("Title tag is too short (should be 30-60 characters)")
            elif len(page_data["title"]) > 60:
                results["issues"].append("Title tag is too long (should be 30-60 characters)")
        else:
            results["issues"].append("Missing or empty title tag")

        # Check H1 tag
        h1_tags = soup.find_all("h1")
        if h1_tags:
            results["has_h1"] = True
            if len(h1_tags) > 1:
                results["issues"].append(f"Multiple H1 tags found ({len(h1_tags)}) - should have only one")
        else:
            results["issues"].append("No H1 tag found on page")

        # Check NAP in footer
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text()

            # Extract phone
            phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            phones = re.findall(phone_pattern, footer_text)
            if phones:
                results["nap_in_footer"]["phone"] = ''.join(phones[0])

            # Extract email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, footer_text)
            if emails:
                results["nap_in_footer"]["email"] = emails[0]

            # Check for address keywords
            address_keywords = ['street', 'st.', 'avenue', 'ave.', 'road', 'rd.', 'suite', 'ste.']
            if any(keyword in footer_text.lower() for keyword in address_keywords):
                results["nap_in_footer"]["has_address"] = True

            if not results["nap_in_footer"]:
                results["issues"].append("NAP (Name, Address, Phone) not clearly visible in footer")
        else:
            results["issues"].append("No footer element found")

        return results

    def _calculate_recommendation(self, audit_results: Dict) -> Dict:
        """Calculate overall score and recommendation"""
        print("📊 Calculating recommendation...")

        sections = audit_results["audit_sections"]

        # Scoring system
        score = 0
        max_score = 100
        issues = []
        opportunities = []

        # Visual Design (30 points)
        design_score = sections["visual_design"].get("score", 5)
        score += (design_score / 10) * 30
        if design_score < 7:
            issues.append(f"Design quality rated {design_score}/10 - appears outdated or unprofessional")
            opportunities.append("Website redesign to modernize appearance")

        # Conversion Elements (25 points)
        conv = sections["conversion_elements"]
        if conv["has_clear_cta"]:
            score += 10
        else:
            issues.append("No clear call-to-action on homepage")
            opportunities.append("Add prominent CTA buttons for scheduling consultations")

        if conv["has_contact_form"]:
            score += 8
        else:
            issues.append("No contact form on homepage")
            opportunities.append("Add contact form for easy lead capture")

        if conv["has_phone_number"]:
            score += 7
        else:
            issues.append("No phone number visible on homepage")
            opportunities.append("Add clickable phone number in header")

        # Trust Signals (20 points)
        trust = sections["trust_signals"]
        if trust["has_team_info"]:
            score += 7
        else:
            issues.append("No team/credentials section on homepage")
            opportunities.append("Add team section showcasing credentials and experience")

        if trust["has_credentials"]:
            score += 6
        else:
            issues.append("Professional credentials not prominently displayed")
            opportunities.append("Highlight CPA licenses and certifications")

        if trust["has_google_maps"]:
            score += 7
        else:
            issues.append("No Google Maps embed (important for local SEO)")
            opportunities.append("Embed Google Maps on homepage for SEO boost")

        # SEO (15 points)
        seo = sections["seo_elements"]
        if seo["has_meta_description"]:
            score += 5
        else:
            issues.append("Missing meta description")
            opportunities.append("Add SEO-optimized meta descriptions")

        if seo["has_h1"]:
            score += 5
        else:
            issues.append("Missing H1 tag")
            opportunities.append("Add proper heading structure")

        if seo["nap_in_footer"]:
            score += 5
        else:
            issues.append("NAP not clearly in footer")
            opportunities.append("Ensure consistent NAP in footer for local SEO")

        # Technical (10 points)
        tech = sections["technical"]
        if tech["load_time_seconds"] < 3:
            score += 5
        elif tech["load_time_seconds"] < 5:
            score += 3
            issues.append(f"Page load time is {tech['load_time_seconds']}s (target: under 3s)")
            opportunities.append("Optimize page speed and performance")
        else:
            issues.append(f"Slow page load time: {tech['load_time_seconds']}s")
            opportunities.append("Significant performance optimization needed")

        if tech["has_viewport_meta"]:
            score += 5
        else:
            issues.append("Missing viewport meta tag (mobile optimization)")
            opportunities.append("Add mobile-responsive design")

        # Calculate recommendation
        score = round(score, 1)

        # Grade for prospect-facing report
        if score >= 85:
            grade = "A"
            grade_summary = "Your website is performing well across most areas. Minor optimizations could further enhance your online presence."
        elif score >= 75:
            grade = "B"
            grade_summary = "Your website has a solid foundation with some areas that could be improved to better convert visitors into clients."
        elif score >= 60:
            grade = "C"
            grade_summary = "Your website has several opportunities for improvement that could significantly increase leads and client inquiries."
        else:
            grade = "D"
            grade_summary = "Your website has significant room for improvement. Addressing these issues could substantially grow your online presence and client base."

        # Internal recommendation for batch processing (kept for sorting)
        if score < 60:
            recommendation = "STRONG YES"
        elif score < 75:
            recommendation = "YES"
        elif score < 85:
            recommendation = "MAYBE"
        else:
            recommendation = "NO"

        return {
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "recommendation": recommendation,
            "grade": grade,
            "grade_summary": grade_summary,
            "total_issues": len(issues),
            "issues": issues,
            "opportunities": opportunities
        }

    def _generate_report(self, audit_results: Dict) -> Path:
        """Generate a markdown report"""
        print("📝 Generating report...")

        domain = urlparse(audit_results["url"]).netloc.replace('www.', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"audit_{domain}_{timestamp}.md"
        report_path = self.reports_dir / report_filename

        rec = audit_results["recommendation"]
        sections = audit_results["audit_sections"]

        report = f"""# Website Audit Report

**Website:** {audit_results["url"]}
**Audit Date:** {datetime.now().strftime('%B %d, %Y')}

---

## Overall Grade: {rec["grade"]}

**Score:** {rec["score"]}/{rec["max_score"]} ({rec["percentage"]}%)

{rec["grade_summary"]}

---

## Executive Summary

This audit evaluated your website across five key areas that impact how potential clients find and engage with your firm online:

- **Visual Design** - First impressions and professional appearance
- **Conversion Elements** - How easily visitors can contact you
- **Trust Signals** - Credentials and credibility indicators
- **SEO Fundamentals** - Search engine visibility
- **Technical Performance** - Speed and mobile experience

### Areas Needing Attention: {rec["total_issues"]}
"""

        if rec["issues"]:
            for issue in rec["issues"]:
                report += f"- {issue}\n"
        else:
            report += "- No major issues found\n"

        report += f"\n### Recommended Improvements\n"
        if rec["opportunities"]:
            for i, opp in enumerate(rec["opportunities"], 1):
                report += f"{i}. {opp}\n"

        report += f"\n---\n\n## Detailed Findings\n\n"
        report += f"### Visual Design\n\n"
        design = sections["visual_design"]
        report += f"**Score:** {design['score']}/10\n\n"

        if design.get("issues"):
            report += "**Areas for Improvement:**\n"
            for issue in design["issues"][:3]:
                report += f"- {issue}\n"

        if design.get("strengths"):
            report += "\n**Strengths:**\n"
            for strength in design["strengths"][:3]:
                report += f"- {strength}\n"

        report += f"\n### Conversion Elements\n\n"
        report += f"*These elements help visitors take action and contact your firm.*\n\n"
        conv = sections["conversion_elements"]
        report += f"| Element | Status |\n"
        report += f"|---------|--------|\n"
        report += f"| Clear Call-to-Action | {'Present' if conv['has_clear_cta'] else 'Missing'} |\n"
        report += f"| Contact Form | {'Present' if conv['has_contact_form'] else 'Missing'} |\n"
        report += f"| Phone Number | {'Present' if conv['has_phone_number'] else 'Missing'} |\n"

        report += f"\n### Trust Signals\n\n"
        report += f"*These elements build credibility with potential clients.*\n\n"
        trust = sections["trust_signals"]
        report += f"| Element | Status |\n"
        report += f"|---------|--------|\n"
        report += f"| Team/About Section | {'Present' if trust['has_team_info'] else 'Missing'} |\n"
        report += f"| Credentials Displayed | {'Present' if trust['has_credentials'] else 'Missing'} |\n"
        report += f"| Google Maps Embed | {'Present' if trust['has_google_maps'] else 'Missing'} |\n"

        report += f"\n### SEO Fundamentals\n\n"
        report += f"*These elements affect how easily potential clients can find you online.*\n\n"
        seo = sections["seo_elements"]
        report += f"| Element | Status |\n"
        report += f"|---------|--------|\n"
        report += f"| Meta Description | {'Present' if seo['has_meta_description'] else 'Missing'} |\n"
        report += f"| H1 Heading Tag | {'Present' if seo['has_h1'] else 'Missing'} |\n"
        report += f"| NAP in Footer | {'Complete' if seo['nap_in_footer'] else 'Incomplete'} |\n"

        report += f"\n### Technical Performance\n\n"
        tech = sections["technical"]
        load_rating = "Good" if tech['load_time_seconds'] < 3 else "Needs Improvement" if tech['load_time_seconds'] < 5 else "Slow"
        report += f"| Metric | Value | Status |\n"
        report += f"|--------|-------|--------|\n"
        report += f"| Page Load Time | {tech['load_time_seconds']}s | {load_rating} |\n"
        report += f"| Mobile Optimized | {'Yes' if tech['has_viewport_meta'] else 'No'} | {'Good' if tech['has_viewport_meta'] else 'Needs Attention'} |\n"

        report += f"""
---

## Priority Action Items

Based on this audit, here are the recommended next steps to improve your website's effectiveness:

"""
        if rec["grade"] == "D":
            report += """### High Priority
Your website would benefit significantly from addressing these foundational issues:

1. **Consider a website refresh** - Modernizing your site's design will improve first impressions and build trust with potential clients
2. **Add clear calls-to-action** - Make it easy for visitors to schedule a consultation or contact your firm
3. **Improve local SEO** - Ensure your business information is consistent and visible to help clients find you

### Why This Matters
In today's market, your website is often the first impression potential clients have of your firm. Addressing these issues can directly impact your ability to attract and convert new clients.
"""
        elif rec["grade"] == "C":
            report += """### Recommended Actions
1. **Enhance conversion elements** - Adding contact forms and prominent CTAs can increase client inquiries
2. **Strengthen trust signals** - Showcase your team's credentials and expertise more prominently
3. **Optimize for local search** - Ensure your NAP (Name, Address, Phone) is consistent across your site

### Impact
These improvements can help convert more of your existing website visitors into actual client consultations.
"""
        elif rec["grade"] == "B":
            report += """### Fine-Tuning Opportunities
1. **Polish the details** - Small improvements to design and content can enhance professionalism
2. **Optimize for conversions** - Test different CTAs and form placements to maximize inquiries
3. **Monitor performance** - Regular updates keep your site fresh and maintain search rankings

### Impact
Your site has a solid foundation. These refinements can help you stand out from competitors.
"""
        else:
            report += """### Maintenance Recommendations
1. **Keep content fresh** - Regular updates signal an active, engaged firm
2. **Monitor analytics** - Track which pages drive the most inquiries
3. **Stay current** - Web standards evolve; periodic reviews ensure continued excellence

### Well Done
Your website is performing well. Continue maintaining these high standards to stay ahead of competitors.
"""

        report += f"""
---

## About This Report

This audit was conducted using automated analysis tools that evaluate websites against industry best practices for professional service firms. The findings represent a point-in-time assessment and should be used as a starting point for discussion with your web development team or marketing partner.

For questions about implementing these recommendations, consult with a qualified web developer or digital marketing professional.
"""

        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        return report_path


def main():
    """Main CLI entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python website_auditor.py <url>")
        print("Example: python website_auditor.py https://example-cpa.com")
        sys.exit(1)

    url = sys.argv[1]

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    auditor = WebsiteAuditor()
    results = auditor.audit_website(url)

    if "error" not in results:
        rec = results["recommendation"]
        print(f"\n{'='*60}")
        print(f"Grade: {rec['grade']} | Score: {rec['score']}/{rec['max_score']} ({rec['percentage']}%)")
        print(f"{rec['grade_summary']}")
        print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    main()
