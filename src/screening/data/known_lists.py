"""
Known company lists for screening gates.

Contains:
- DEFENSE_PRIMES: Known defense/intelligence prime contractors
- CLEARANCE_KEYWORDS: Security clearance requirement keywords in JDs
- GOV_EMPLOYER_SIGNALS: Government employer signals
- STAFFING_AGENCIES: Known staffing/consulting placement firms
- STAFFING_SIGNALS: Staffing agency signals in JDs
- HARD_EXCLUDE_COMPANIES: Companies to always exclude regardless of role
"""

# ── Defense Prime Contractors ────────────────────────────────────────
# Matches against company name (lowercased). Substring match.

DEFENSE_PRIMES = {
    "lockheed martin", "raytheon", "northrop grumman", "general dynamics",
    "bae systems", "l3harris", "l3 harris", "leidos", "saic",
    "booz allen hamilton", "booz allen", "caci international", "caci",
    "mantech", "science applications international", "parsons",
    "peraton", "amentum", "jacobs engineering",
    "general atomics", "textron", "huntington ingalls",
    "elbit systems", "leonardo drs", "curtiss-wright",
    "mercury systems", "aerojet rocketdyne", "kratos defense",
    "maxar technologies", "palantir", "anduril",
}

# ── Security Clearance Keywords ──────────────────────────────────────
# Found in JD text. If any appear, the job requires clearance.

CLEARANCE_KEYWORDS = {
    "security clearance", "top secret", "ts/sci", "secret clearance",
    "ts clearance", "sci clearance", "public trust",
    "clearance required", "active clearance", "dod clearance",
    "polygraph", "ci poly", "full scope poly", "lifestyle poly",
    "interim clearance", "eligibility for clearance",
    "must be clearable", "ability to obtain clearance",
    "current clearance", "classified environment",
    "classified information", "noforn", "sci eligible",
}

# ── Government Employer Signals ──────────────────────────────────────
# Company name or JD signals suggesting government/DOD employer.

GOV_EMPLOYER_SIGNALS = {
    "department of defense", "department of energy", "dod ",
    "nsa", "cia", "dia", "nro", "nga", "fbi", "dhs",
    "national security agency", "central intelligence agency",
    "defense intelligence agency", "national reconnaissance office",
    "national geospatial", "department of homeland",
    "usaf", "us army", "us navy", "us marine",
    "space force", "darpa", "iarpa", "naval research",
    "army research", "air force research",
    "intelligence community", "ic contractor",
    "fema", "federal emergency management",
    "department of veterans", "department of justice",
    "department of state", "department of treasury",
    "department of interior", "department of labor",
    "department of education", "department of agriculture",
    "department of commerce", "department of transportation",
    "department of health", "department of housing",
}

# ── Staffing Agencies ────────────────────────────────────────────────
# Known staffing/consulting placement firms. Substring match on company name.

STAFFING_AGENCIES = {
    "robert half", "randstad", "adecco", "manpower", "kelly services",
    "hays", "michael page", "kforce", "insight global", "teksystems",
    "tek systems", "apex systems", "cybercoders", "dice",
    "staffing", "recruiting", "talent acquisition",
    "consultants", "consulting group", "solutions group",
    "workforce", "personnel", "temporary", "contract staffing",
    "aerotek", "brooksource", "collabera", "cognizant",
    "infosys", "wipro", "tata consultancy", "hcl technologies",
    "accenture federal", "deloitte consulting",
}

# ── Staffing Signals in JD ───────────────────────────────────────────
# Text patterns in job descriptions suggesting staffing/contract placement.
#
# Deliberate omissions:
#   "vendor management" alone — too broad; product companies mention managing
#   SaaS vendors / supplier relationships. Use "vendor management system" only,
#   which is specific to the staffing-industry VMS platform concept.

STAFFING_SIGNALS = {
    "w2 only", "w-2 only", "corp to corp", "c2c",
    # "our client" alone is too broad — matches "our clients" on product company JDs.
    # Use staffing-specific multi-word patterns that cannot appear in product JDs.
    "placed at our client", "working at our client", "work at our client",
    "our client is looking", "our client requires",
    "on behalf of our client", "end client",
    "client site", "client location",
    "contract-to-hire", "contract to hire", "c2h",
    "right to represent", "rtr", "submission to",
    "vendor management system",          # specific VMS platform reference (not generic "vendor mgmt")
    "third-party staffing", "third party staffing",
    "consulting engagement", "engagement period",
}


# ── Direct-Hire Allowlist ─────────────────────────────────────────────
# Product companies confirmed as direct employers that were false-flagged by
# staffing-signal substring matches in their JD text.  Substring match on
# lowercased company name — bypasses all staffing checks in Gate 0C.

DIRECT_HIRE_ALLOWLIST = {
    # Food-service SaaS / e-commerce — mentions "vendor management" for supplier ops
    "webstaurantstore",
    # AI news startup — direct employer, not a placement firm
    "haystack news",
    # Veterinary practice management SaaS — direct employer
    "vetcor",
    # Data engineering product company
    "navina",
    # Collaboration SaaS
    "hive",
    # Health data / analytics platform
    "cotiviti",
}

# ── Hard Exclude Companies ───────────────────────────────────────────
# Companies to always exclude regardless of role, compensation, or stack.
# Add companies with well-documented toxic culture, ethical concerns, etc.

HARD_EXCLUDE_COMPANIES = {
    "amazon",
}
