# Research and Validation Plan

## Purpose
Validate the product hypothesis without pretending to know any company's private systems or roadmap.

## Questions to answer
1. Which integration patterns are most common among target customers?
2. What transaction fields are realistically available at authorization time?
3. What latency budgets do different use cases tolerate?
4. What data can be shared with an external fraud service?
5. How are false positives reviewed and measured?
6. Which existing products already provide the proposed features?
7. What integration pain points are evidenced in public docs, engineering blogs, job descriptions, standards, or customer interviews?
8. What is the narrowest useful initial buyer/user segment?

## Evidence quality
- Strong: official product/API docs, technical papers, standards, documented customer case studies, direct interviews with consent.
- Medium: credible reporting, job postings, conference talks.
- Weak: anonymous claims, unsourced social posts, speculation.
Record source, date accessed, exact claim supported, confidence, and implication.

## Validation artifacts
- Competitor matrix (features, integration method, deployment, evidence source).
- Problem hypothesis and falsifiable assumptions.
- Synthetic data specification.
- API integration feedback from at least one independent developer.
- Performance and evaluation report.
- Pilot readiness checklist.

## Guardrails
- Do not scrape private systems or attempt unauthorized access.
- Do not use company logos or imply endorsement.
- Do not test against live payment endpoints.
- Do not send sensitive data to third-party models.
- Distinguish documented industry problem from company-specific confirmed need.
