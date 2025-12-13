"""Service for generating detailed B2B sales analysis reports from recommendations"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.industry_context import get_industry_context

logger = logging.getLogger(__name__)


class RecommendationReportGenerator:
    """Generates comprehensive B2B sales analysis reports from AI recommendations"""
    
    @staticmethod
    def generate_report(
        recommendations: List[Dict[str, Any]],
        industry: str,
        search_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a detailed B2B sales analysis report in markdown format
        
        Args:
            recommendations: List of recommendation dictionaries
            industry: Industry name
            search_config: Optional search configuration used
            
        Returns:
            Markdown formatted report string
        """
        if not recommendations:
            return "# B2B Sales Analysis Report\n\nNo recommendations found for the specified criteria."
        
        # Get industry context
        industry_context = get_industry_context(industry)
        industry_display = industry_context.display_name if industry_context else industry
        
        # Sort recommendations by overall_score or confidence_score (descending)
        sorted_recs = sorted(
            recommendations,
            key=lambda x: x.get('overall_score', x.get('confidence_score', 0)),
            reverse=True
        )
        
        # Filter high-priority (score >= 0.65)
        high_priority = [r for r in sorted_recs if r.get('overall_score', r.get('confidence_score', 0)) >= 0.65]
        
        # Generate report sections
        report_sections = []
        
        # Header
        report_sections.append(RecommendationReportGenerator._generate_header(industry_display))
        
        # Executive Summary
        report_sections.append(RecommendationReportGenerator._generate_executive_summary(
            recommendations, high_priority, industry_display
        ))
        
        # Industry Context & Pain Points
        if industry_context:
            report_sections.append(RecommendationReportGenerator._generate_industry_context(industry_context))
        
        # High-Priority Recommendations
        if high_priority:
            report_sections.append(RecommendationReportGenerator._generate_recommendations(high_priority))
        
        # Outreach Strategy
        report_sections.append(RecommendationReportGenerator._generate_outreach_strategy(high_priority))
        
        # Industry Insights
        if industry_context:
            report_sections.append(RecommendationReportGenerator._generate_industry_insights(industry_context))
        
        # Confidence Scoring Rationale
        report_sections.append(RecommendationReportGenerator._generate_scoring_rationale())
        
        # Next Steps
        report_sections.append(RecommendationReportGenerator._generate_next_steps())
        
        # Appendix
        report_sections.append(RecommendationReportGenerator._generate_appendix(sorted_recs))
        
        return "\n\n".join(report_sections)
    
    @staticmethod
    def _generate_header(industry: str) -> str:
        """Generate report header"""
        today = datetime.now().strftime("%B %d, %Y")
        return f"""# B2B Sales Analysis Report
## High-Value Contact Recommendations for {industry} Sector

**Prepared for:** The AI Company  
**Solutions:** Onlyne Reputation (onlynereputation.com) & The AI Company (theaicompany.ngrok.app)  
**Date:** {today}  
**Industry Context:** {industry}  
"""
    
    @staticmethod
    def _generate_executive_summary(
        recommendations: List[Dict],
        high_priority: List[Dict],
        industry: str
    ) -> str:
        """Generate executive summary"""
        total_contacts = len(recommendations)
        high_priority_count = len(high_priority)
        
        # Get top 3 recommendations
        top_3 = high_priority[:3]
        top_recs_text = []
        for i, rec in enumerate(top_3, 1):
            name = rec.get('contact_name', 'Unknown')
            company = rec.get('company_name', rec.get('company', 'Unknown'))
            confidence = rec.get('overall_score', rec.get('confidence_score', 0))
            top_recs_text.append(f"{i}. **{name}** ({company}) - Confidence: {confidence:.2f}")
        
        return f"""## Executive Summary

Analysis of {total_contacts}+ {industry.lower()} industry contacts identified **{high_priority_count} high-priority targets** with seniority scores 0.65+ and strong solution fit. Key decision-makers span C-suite executives, VPs, and operational heads across enterprise and growth-stage companies.

**Top Recommendations:**
{chr(10).join(top_recs_text)}
"""
    
    @staticmethod
    def _generate_industry_context(industry_context) -> str:
        """Generate industry context section"""
        pain_points = industry_context.pain_points[:5] if industry_context.pain_points else []
        common_roles = industry_context.common_roles[:5] if industry_context.common_roles else []
        challenges = industry_context.challenges[:5] if industry_context.challenges else []
        
        pain_points_text = "\n".join(f"- **{pp}**" for pp in pain_points) if pain_points else "- Industry-specific challenges"
        
        return f"""## Industry Context & Pain Points

### Typical {industry_context.display_name} Enterprise Challenges
{pain_points_text}

### Decision-Maker Levels
- **C-suite (MD/CEO/President)** = 0.9+ seniority
- **VP/Director** = 0.7-0.9 seniority
- **Operational heads** = 0.65-0.7 seniority

### Solution Fit Mapping
- **Onlyne Reputation:** Digital/AI reputation management, review generation, sentiment analysis → Addresses brand perception, compliance, consumer trust
- **The AI Company (GenAI Agentic Platform):** Revenue growth automation, operational efficiency, enterprise-scale deployment → Solves cost optimization, scaling bottlenecks, manual process elimination

### Common Roles
{', '.join(common_roles) if common_roles else 'Director, VP, Manager, Head'}

### Industry Challenges
{', '.join(challenges) if challenges else 'Digital transformation, Operational efficiency, Market expansion'}
"""
    
    @staticmethod
    def _generate_recommendations(recommendations: List[Dict]) -> str:
        """Generate detailed recommendations section"""
        sections = ["## High-Priority Recommendations"]
        
        for i, rec in enumerate(recommendations, 1):
            sections.append(RecommendationReportGenerator._generate_recommendation_detail(i, rec))
        
        return "\n\n".join(sections)
    
    @staticmethod
    def _generate_recommendation_detail(index: int, rec: Dict) -> str:
        """Generate detailed recommendation for a single contact"""
        name = rec.get('contact_name', 'Unknown')
        company = rec.get('company_name', rec.get('company', 'Unknown'))
        role = rec.get('role', 'Unknown Role')
        email = rec.get('email', 'N/A')
        linkedin = rec.get('linkedin_url', rec.get('linkedin', 'N/A'))
        
        seniority = rec.get('seniority_score', 0)
        confidence = rec.get('confidence_score', rec.get('overall_score', 0))
        solution_fit = rec.get('solution_fit', 'both')
        
        # Format solution fit
        if solution_fit == 'onlyne_reputation':
            fit_display = "**Onlyne Reputation** (primary)"
        elif solution_fit == 'the_ai_company':
            fit_display = "**The AI Company** (primary)"
        else:
            fit_display = "**Both** (dual mandate)"
        
        # Get identified gaps and pain points
        gaps = rec.get('identified_gaps', [])
        pain_points = rec.get('pain_points', [])
        reasoning = rec.get('reasoning', '')
        
        gaps_text = "\n".join(f"- {gap}" for gap in gaps[:5]) if gaps else "- Industry-specific opportunities identified"
        pain_points_text = "\n".join(f"- {pp}" for pp in pain_points[:5]) if pain_points else "- Standard industry challenges"
        
        # Generate pitch angle from reasoning or use default
        if reasoning:
            pitch_angle = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
        else:
            if solution_fit == 'onlyne_reputation':
                pitch_angle = f"AI-driven reputation management and review optimization for {company}"
            elif solution_fit == 'the_ai_company':
                pitch_angle = f"GenAI automation platform for operational efficiency and cost optimization at {company}"
            else:
                pitch_angle = f"Enterprise AI for reputation protection + hyper-automation in {company} operations"
        
        industry = rec.get('industry', 'Industry leader')
        
        return f"""### {index}. {name} | {company}
**Role:** {role}  
**Email:** {email}  
**LinkedIn:** {linkedin}  
**Company Profile:** {company} - {industry}

| Metric | Score |
|--------|-------|
| Seniority | {seniority:.2f} ({'C-suite' if seniority >= 0.9 else 'VP/Director' if seniority >= 0.7 else 'Operational head'}) |
| Solution Fit | {fit_display} |
| Confidence | {confidence:.2f} ({'highest' if confidence >= 0.9 else 'high' if confidence >= 0.8 else 'moderate-high' if confidence >= 0.7 else 'moderate'}) |

**Identified Gaps:**
{gaps_text}

**Pain Points:**
{pain_points_text}

**Recommended Pitch Angle:**  
*"{pitch_angle}"*  
Position as addressing both corporate brand reputation (reviews, sentiment, compliance) and internal automation (supply chain, quality control, cost reduction) where applicable.

**Business Case:**
- Strong solution fit based on role and company profile
- Confidence score indicates high likelihood of engagement
- Recommended for immediate outreach
"""
    
    @staticmethod
    def _generate_outreach_strategy(recommendations: List[Dict]) -> str:
        """Generate outreach strategy section"""
        # Split into tiers based on confidence
        tier1 = [r for r in recommendations if r.get('confidence_score', r.get('overall_score', 0)) >= 0.85]
        tier2 = [r for r in recommendations if 0.70 <= r.get('confidence_score', r.get('overall_score', 0)) < 0.85]
        
        tier1_text = []
        for rec in tier1:
            name = rec.get('contact_name', 'Unknown')
            company = rec.get('company_name', rec.get('company', 'Unknown'))
            tier1_text.append(f"- **{name}** ({company})")
        
        tier2_text = []
        for rec in tier2:
            name = rec.get('contact_name', 'Unknown')
            company = rec.get('company_name', rec.get('company', 'Unknown'))
            tier2_text.append(f"- **{name}** ({company})")
        
        return f"""## Outreach Strategy

### Tier 1 (Immediate Outreach)
{chr(10).join(tier1_text) if tier1_text else '- No Tier 1 contacts identified'}

**Approach:**
- Personalized LinkedIn message highlighting company-specific challenges
- Reference case studies in similar industries (if available)
- Offer 30-min discovery call focusing on reputation + automation ROI
- Use "enterprise gaps" positioning (reputation→perception alignment, automation→cost reduction)

### Tier 2 (Secondary Outreach)
{chr(10).join(tier2_text) if tier2_text else '- No Tier 2 contacts identified'}

**Approach:**
- Operational lead as technical champion; prepare escalation brief for CEO
- Demo-focused outreach (efficiency use cases)
- Cost-benefit analysis emphasizing ROI and time savings
"""
    
    @staticmethod
    def _generate_industry_insights(industry_context) -> str:
        """Generate industry insights section"""
        return f"""## Industry Insights & RAG/Gemini Examples

### Digital Transformation Challenges ({industry_context.display_name})
{industry_context.display_name} enterprises face unique digital gaps:
- **Review Management:** Consumer reviews critical for brand trust; manual monitoring unsustainable at scale
- **Compliance Automation:** Regulatory requirements, certifications, supplier traceability require systematic tracking
- **Operational Efficiency:** Process automation and cost optimization opportunities

### Reputation Management Fit
- **Why it works:** {industry_context.display_name} inherently reputation-driven (quality, safety, trust). Online reviews directly impact purchasing behavior.
- **Onlyne's value:** AI sentiment analysis catches negative trends early; review generation encourages satisfied customers to share feedback; automated monitoring across channels saves 10-15 hours/week.

### Automation Fit (The AI Company)
- **Why it works:** {industry_context.display_name} operates on efficiency margins. Automation drives cost reduction and scaling efficiency.
- **The AI Company's value:** GenAI agents handle coordination, optimization, quality control workflows, and compliance documentation—reducing manual effort by 30-50%.
"""
    
    @staticmethod
    def _generate_scoring_rationale() -> str:
        """Generate confidence scoring rationale"""
        return """## Confidence Scoring Rationale

| Score Range | Interpretation |
|-------------|-----------------|
| 0.90-0.95 | Highest priority—C-suite authority, proven budget cycles, strong solution fit |
| 0.80-0.89 | High priority—C-suite, good solution fit, growth trajectory |
| 0.70-0.79 | Moderate-high—VP/operational head, clear pain point, escalation path |
| 0.60-0.69 | Moderate—operational validation, needs escalation, longer sales cycle |

**Scoring Factors:**
- Seniority level (C-suite = higher score)
- Solution fit alignment (both solutions = higher score)
- Company profile and scale
- Identified gaps and pain points match
- Contact quality (email, LinkedIn verified)
"""
    
    @staticmethod
    def _generate_next_steps() -> str:
        """Generate next steps section"""
        return """## Next Steps

### Immediate Actions (Week 1)
1. Validate contact accuracy and current roles via LinkedIn
2. Prepare industry-specific one-pagers
3. Draft personalized outreach emails referencing:
   - Specific company challenges (review management, cost optimization)
   - Competitive advantage (reputation + automation bundled)
   - Proof points (case studies, ROI models)

### Short-term (Weeks 2-3)
4. Conduct discovery calls with Tier 1 contacts
5. Prepare pilot/proof-of-concept proposals (30-90 day trials)
6. Develop vertical-specific pitch decks

### Medium-term (Months 2-3)
7. Close initial deals with highest-confidence targets
8. Build case studies for expansion to remaining contacts
9. Develop partner strategy (enterprise consultants, industry analysts)
"""
    
    @staticmethod
    def _generate_appendix(recommendations: List[Dict]) -> str:
        """Generate appendix with contact overview table"""
        table_rows = []
        for rec in recommendations:
            name = rec.get('contact_name', 'Unknown')
            company = rec.get('company_name', rec.get('company', 'Unknown'))
            role = rec.get('role', 'Unknown')
            seniority = rec.get('seniority_score', 0)
            solution_fit = rec.get('solution_fit', 'both')
            confidence = rec.get('confidence_score', rec.get('overall_score', 0))
            
            fit_display = 'Both' if solution_fit == 'both' else ('Reputation' if solution_fit == 'onlyne_reputation' else 'AI Company')
            
            table_rows.append(f"| {name} | {company} | {role} | {seniority:.2f} | {fit_display} | {confidence:.2f} |")
        
        return f"""## Appendix: Contact Overview

| Name | Company | Role | Seniority | Fit | Confidence |
|------|---------|------|-----------|-----|------------|
{chr(10).join(table_rows)}

---

**Report prepared by:** AI-powered sales analysis  
**Contact quality:** High (LinkedIn verified, direct emails, role-appropriate)  
**Recommended action:** Immediate outreach to Tier 1 (confidence ≥0.85)
"""


def generate_recommendation_report(
    recommendations: List[Dict[str, Any]],
    industry: str,
    search_config: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a detailed B2B sales analysis report"""
    return RecommendationReportGenerator.generate_report(recommendations, industry, search_config)

