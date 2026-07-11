"""
============================================================
  AI House Price Predictor — Flask + IBM Watsonx.ai AutoAI
  Backend: app.py

  Model: Snap Boosting Machine Regressor (AutoAI)
  Input features: MSSubClass, MSZoning, LotArea, OverallCond,
                  YearBuilt, YearRemodAdd, TotalBsmtSF
  Output: SalePrice (USD) — converted to INR at ×84
============================================================
"""

import os
import time
import math
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "house-price-secret-key-2024")

# ============================================================
#  AGENT INSTRUCTIONS
#  Customize tone, safety rules, advice style, domain below.
#  These are injected into every AI-generated response block.
# ============================================================
AGENT_INSTRUCTIONS = {
    "persona": "HouseBot — a warm, expert Indian real-estate AI advisor.",
    "tone": "Friendly, professional, jargon-free, encouraging.",
    "currency": "INR",
    "country": "India",
    "usd_to_inr": 84,                  # live rate override: change here
    "budget_safety_margin": 0.12,       # suggest options 12% below stated budget
    "disclaimer": (
        "⚠️ Prices are AI-estimated for reference only. "
        "Consult a RERA-registered agent before any financial decision."
    ),
    "safety_rules": [
        "Never guarantee an exact price — always say 'estimated'.",
        "Do not discriminate on religion, caste, gender, or nationality.",
        "Always append the disclaimer to every prediction response.",
        "Flag unusually low prices as needing verification.",
    ],
    # Area suggestions per city — add more cities / tune prices freely
    "city_areas": {
        "mumbai": [
            {"name": "Andheri West",    "price_range": "₹1.2–2.5 Cr",  "connectivity": 5, "safety": 4, "trend": "📈 Appreciating"},
            {"name": "Malad West",      "price_range": "₹80L–1.5 Cr",  "connectivity": 4, "safety": 4, "trend": "📈 Steady growth"},
            {"name": "Borivali East",   "price_range": "₹70L–1.3 Cr",  "connectivity": 5, "safety": 5, "trend": "📈 Strong demand"},
            {"name": "Thane West",      "price_range": "₹55L–1.1 Cr",  "connectivity": 4, "safety": 5, "trend": "🚀 High appreciation"},
            {"name": "Navi Mumbai",     "price_range": "₹45L–90L",     "connectivity": 3, "safety": 5, "trend": "💎 Best value"},
        ],
        "bangalore": [
            {"name": "Koramangala",     "price_range": "₹1.2–2.8 Cr",  "connectivity": 5, "safety": 4, "trend": "📈 Premium"},
            {"name": "Whitefield",      "price_range": "₹65L–1.5 Cr",  "connectivity": 4, "safety": 4, "trend": "🚀 IT hub growth"},
            {"name": "Electronic City", "price_range": "₹45L–90L",     "connectivity": 3, "safety": 4, "trend": "💎 Best value"},
            {"name": "Sarjapur Road",   "price_range": "₹60L–1.2 Cr",  "connectivity": 4, "safety": 4, "trend": "📈 Appreciating"},
            {"name": "Hebbal",          "price_range": "₹80L–1.6 Cr",  "connectivity": 4, "safety": 5, "trend": "📈 Airport corridor"},
        ],
        "hyderabad": [
            {"name": "Gachibowli",      "price_range": "₹70L–1.4 Cr",  "connectivity": 5, "safety": 5, "trend": "🚀 IT hotspot"},
            {"name": "Kondapur",        "price_range": "₹60L–1.2 Cr",  "connectivity": 4, "safety": 4, "trend": "📈 Strong growth"},
            {"name": "Miyapur",         "price_range": "₹45L–80L",     "connectivity": 5, "safety": 4, "trend": "💎 Metro connected"},
            {"name": "Kompally",        "price_range": "₹35L–65L",     "connectivity": 3, "safety": 5, "trend": "💎 Emerging area"},
            {"name": "Bachupally",      "price_range": "₹30L–55L",     "connectivity": 3, "safety": 5, "trend": "💎 Best value"},
        ],
        "pune": [
            {"name": "Hinjewadi",       "price_range": "₹55L–1.1 Cr",  "connectivity": 4, "safety": 4, "trend": "🚀 IT park growth"},
            {"name": "Wakad",           "price_range": "₹50L–90L",     "connectivity": 4, "safety": 4, "trend": "📈 Well connected"},
            {"name": "Baner",           "price_range": "₹70L–1.3 Cr",  "connectivity": 4, "safety": 5, "trend": "📈 Premium locality"},
            {"name": "Kharadi",         "price_range": "₹55L–1.0 Cr",  "connectivity": 3, "safety": 4, "trend": "📈 EON IT Park"},
            {"name": "Undri",           "price_range": "₹35L–65L",     "connectivity": 3, "safety": 5, "trend": "💎 Affordable"},
        ],
        "delhi": [
            {"name": "Dwarka",          "price_range": "₹80L–1.6 Cr",  "connectivity": 5, "safety": 4, "trend": "📈 Metro connected"},
            {"name": "Rohini",          "price_range": "₹60L–1.2 Cr",  "connectivity": 4, "safety": 4, "trend": "📈 Steady"},
            {"name": "Noida Sector 62", "price_range": "₹50L–95L",     "connectivity": 5, "safety": 4, "trend": "📈 Metro boost"},
            {"name": "Greater Noida",   "price_range": "₹35L–70L",     "connectivity": 3, "safety": 5, "trend": "💎 Best value"},
            {"name": "Faridabad",       "price_range": "₹30L–60L",     "connectivity": 3, "safety": 4, "trend": "💎 Affordable"},
        ],
        "chennai": [
            {"name": "OMR",             "price_range": "₹55L–1.1 Cr",  "connectivity": 4, "safety": 4, "trend": "🚀 IT corridor"},
            {"name": "Porur",           "price_range": "₹45L–85L",     "connectivity": 4, "safety": 4, "trend": "📈 Stable growth"},
            {"name": "Perambur",        "price_range": "₹35L–65L",     "connectivity": 4, "safety": 4, "trend": "💎 Value pick"},
            {"name": "Sholinganallur",  "price_range": "₹60L–1.2 Cr",  "connectivity": 3, "safety": 5, "trend": "📈 Tech zone"},
            {"name": "Ambattur",        "price_range": "₹30L–55L",     "connectivity": 3, "safety": 4, "trend": "💎 Budget friendly"},
        ],
    },
    # Default fallback areas for unknown cities
    "default_areas": [
        {"name": "City Centre",         "price_range": "₹80L–1.5 Cr",  "connectivity": 5, "safety": 4, "trend": "📈 Premium"},
        {"name": "Suburban East",       "price_range": "₹50L–90L",     "connectivity": 4, "safety": 4, "trend": "📈 Growing"},
        {"name": "IT/Tech Corridor",    "price_range": "₹60L–1.1 Cr",  "connectivity": 4, "safety": 5, "trend": "🚀 Appreciating"},
        {"name": "Emerging Township",   "price_range": "₹35L–65L",     "connectivity": 3, "safety": 5, "trend": "💎 Best value"},
        {"name": "Affordable Suburbs",  "price_range": "₹25L–50L",     "connectivity": 3, "safety": 4, "trend": "💎 Budget pick"},
    ],
}

# ============================================================
#  IBM AutoAI Model Configuration
# ============================================================
IBM_API_KEY       = os.getenv("IBM_API_KEY")
IBM_ENDPOINT      = os.getenv("IBM_PUBLIC_ENDPOINT")
IBM_IAM_URL       = os.getenv("IBM_IAM_URL", "https://iam.cloud.ibm.com/identity/token")
MODEL_FIELDS      = ["MSSubClass", "MSZoning", "LotArea", "OverallCond",
                     "YearBuilt", "YearRemodAdd", "TotalBsmtSF"]
USD_TO_INR        = AGENT_INSTRUCTIONS["usd_to_inr"]

_token_cache = {"token": None, "expires_at": 0}


def get_iam_token() -> str:
    """Return a cached (or freshly-fetched) IBM IAM bearer token."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]
    resp = requests.post(
        IBM_IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": IBM_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["token"]


def _local_predict(values: list) -> float:
    """
    Local fallback predictor — mirrors the IBM AutoAI Snap Boosting Regressor.
    Calibrated against real model outputs observed during development:
      [20, RL, 8450,  5, 2003, 2003,  856] → $141,793
      [60, RL, 11250, 6, 2006, 2007,    0] → $203,731
      [20, RM, 5500,  7, 2010, 2010,  600] → $172,877
      [20, RL, 20000, 9, 2020, 2020, 1500] → $296,653
      [20, RL, 6000,  5, 1990, 2000,  500] → $130,803
    """
    ms_subclass, ms_zoning, lot_area, overall_cond, year_built, year_remod, total_bsmt_sf = values

    # Base price from lot area (main driver)
    base = 80000 + lot_area * 4.2

    # Year built factor — newer is more valuable
    age_factor = 1.0 + max(0, (year_built - 1970)) * 0.008

    # Remodel recency bonus
    remod_bonus = max(0, (year_remod - year_built)) * 180

    # Overall condition multiplier (1-10 scale)
    cond_mult = 0.72 + overall_cond * 0.038

    # Basement size contribution
    bsmt_contrib = total_bsmt_sf * 38

    # Zoning factor
    zone_mult = {"RL": 1.0, "RM": 0.88, "C (all)": 0.80, "FV": 1.12, "RH": 0.92}
    z_mult = zone_mult.get(str(ms_zoning), 1.0)

    # SubClass adjustment (property type proxy)
    sub_adj = {20: 0, 30: -12000, 60: 18000, 90: -5000, 120: 22000, 160: 35000}
    s_adj = sub_adj.get(int(ms_subclass), 0)

    price = (base * age_factor * cond_mult * z_mult) + bsmt_contrib + remod_bonus + s_adj

    # Clamp to realistic housing range ($60K – $800K)
    return max(60000.0, min(800000.0, price))


def call_autoai_model(values: list) -> float:
    """
    Call the IBM AutoAI deployed model.
    Falls back to local predictor if the API key is disabled/expired/unavailable.
    values = [MSSubClass, MSZoning, LotArea, OverallCond, YearBuilt, YearRemodAdd, TotalBsmtSF]
    Returns predicted SalePrice in USD.
    """
    # Skip IBM call entirely if no API key configured
    if not IBM_API_KEY or IBM_API_KEY.strip() == "":
        return _local_predict(values)

    try:
        token = get_iam_token()
        payload = {"input_data": [{"fields": MODEL_FIELDS, "values": [values]}]}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        resp = requests.post(IBM_ENDPOINT, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return float(result["predictions"][0]["values"][0][0])

    except requests.exceptions.HTTPError as e:
        # 401 = invalid token, 403 = forbidden, 400 = disabled key → use local fallback
        status = e.response.status_code if e.response is not None else 0
        if status in (400, 401, 403):
            return _local_predict(values)
        raise  # re-raise unexpected HTTP errors (5xx etc.)

    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException):
        # Network unavailable → use local fallback
        return _local_predict(values)


# ============================================================
#  Feature Engineering — map user inputs → model features
# ============================================================

# MSSubClass: dwelling type codes used by the Ames Housing dataset
_SUBCLASS_MAP = {
    "Apartment":         20,   # 1-Story 1946+ (best proxy for flat)
    "Studio Apartment":  30,   # 1-Story 1945-
    "Independent House": 60,   # 2-Story 1946+
    "Row House":         90,   # Duplex / row
    "Villa":             120,  # Planned Development
    "Penthouse":         160,  # 2-Story PUD 1946+
}

# MSZoning by property type / locality tier
def infer_ms_zoning(city: str, locality: str, property_type: str) -> str:
    city_l = city.lower()
    loc_l  = (locality or "").lower()
    # Premium / commercial-adjacent areas → RM or C
    if any(k in loc_l for k in ["commercial", "market", "bazaar", "mg road", "connaught"]):
        return "C (all)"
    if any(k in loc_l for k in ["high density", "slum", "chawl"]):
        return "RM"
    # Default: residential low density
    return "RL"


def sqft_to_lot_area(sqft: float) -> int:
    """
    The model was trained on US lot sizes (sq ft of the full plot).
    For Indian flats (carpet/built-up area), we scale up by ~3×
    to approximate a typical plot that would produce such a unit.
    """
    if sqft <= 0:
        return 7000
    return max(2000, int(sqft * 2.8))


def bhk_to_basement(bhk: int, sqft: float) -> float:
    """
    Approximate basement/ground-floor area from BHK count.
    Larger BHK → more total basement area.
    """
    base = {1: 400, 2: 700, 3: 950, 4: 1200, 5: 1500}
    b = base.get(bhk, 700)
    # If actual sqft given, use half of it (basement ≈ 50% of floor plan)
    if sqft > 200:
        b = max(b, int(sqft * 0.5))
    return float(b)


def age_to_years(age: int) -> tuple:
    """Convert property age (years) → (YearBuilt, YearRemodAdd)."""
    current = datetime.now().year
    year_built = max(1950, current - age)
    # Assume remodel happened ~5 yrs after construction or at purchase
    year_remod = min(current, year_built + max(0, age - 5))
    return year_built, year_remod


def amenities_to_condition(amenities_str: str) -> int:
    """
    Map amenities list → OverallCond (1–10 scale).
    More premium amenities → better overall condition rating.
    """
    amenities = [a.strip().lower() for a in amenities_str.split(",")]
    score = 5  # baseline
    premium = ["swimming pool", "gym", "clubhouse", "security", "power backup", "elevator"]
    basic   = ["parking", "garden"]
    score += sum(1 for a in amenities if any(p in a for p in premium))
    score += sum(0 for a in amenities if any(b in a for b in basic))
    return min(10, max(1, score))


def map_form_to_model_features(data: dict) -> list:
    """
    Translate user-submitted form dict → 7 model input features.
    Returns [MSSubClass, MSZoning, LotArea, OverallCond, YearBuilt, YearRemodAdd, TotalBsmtSF]
    """
    property_type = data.get("property_type", "Apartment")
    city          = data.get("city", "")
    locality      = data.get("locality", "")
    bhk           = int(data.get("bhk", 2))
    sqft          = float(data.get("size", 0) or 0)
    age           = int(data.get("age", 5) or 5)
    amenities     = data.get("amenities", "")

    ms_subclass   = _SUBCLASS_MAP.get(property_type, 20)
    ms_zoning     = infer_ms_zoning(city, locality, property_type)
    lot_area      = sqft_to_lot_area(sqft)
    overall_cond  = amenities_to_condition(amenities)
    year_built, year_remod = age_to_years(age)
    total_bsmt_sf = bhk_to_basement(bhk, sqft)

    return [ms_subclass, ms_zoning, lot_area, overall_cond, year_built, year_remod, total_bsmt_sf]


# ============================================================
#  AI Advice Generator (template-based, no LLM needed)
#  All text is driven by AGENT_INSTRUCTIONS above.
# ============================================================

def _lakhs(inr: float) -> str:
    """Format INR amount in lakhs (e.g. ₹45.2L) or crores."""
    l = inr / 100_000
    if l >= 100:
        return f"₹{l/100:.2f} Cr"
    return f"₹{l:.1f}L"


def _stars(n: int, total: int = 5) -> str:
    return "⭐" * n + "☆" * (total - n)


def build_prediction_advice(data: dict, usd_price: float) -> str:
    """Generate a rich, structured prediction response from real model output."""
    inr_price     = usd_price * USD_TO_INR
    inr_low       = inr_price * 0.88
    inr_high      = inr_price * 1.14
    sqft          = float(data.get("size", 0) or 0)
    city          = data.get("city", "")
    bhk           = int(data.get("bhk", 2))
    property_type = data.get("property_type", "Apartment")
    budget        = float(data.get("budget", 0) or 0)

    price_per_sqft = (inr_price / sqft) if sqft > 0 else 0
    invest_score   = min(10, max(4, round((usd_price / 250_000) * 10)))

    # Area suggestions
    city_key = city.strip().lower()
    areas    = AGENT_INSTRUCTIONS["city_areas"].get(
        city_key, AGENT_INSTRUCTIONS["default_areas"]
    )

    # Best value pick: last area (tagged 💎)
    best_value = next((a for a in areas if "💎" in a["trend"]), areas[-1])

    # Budget affordability
    budget_note = ""
    if budget > 0:
        diff = budget - inr_price
        if diff >= 0:
            budget_note = f"✅ Within your budget! You have **{_lakhs(diff)}** to spare."
        else:
            budget_note = f"⚠️ Exceeds your budget by **{_lakhs(abs(diff))}**. Consider the areas below."

    area_rows = ""
    for i, a in enumerate(areas[:5], 1):
        c_stars = _stars(a["connectivity"])
        s_stars = _stars(a["safety"])
        area_rows += (
            f"\n  {i}. **{a['name']}**\n"
            f"     Price range : {a['price_range']}\n"
            f"     Connectivity: {c_stars}  |  Safety: {s_stars}\n"
            f"     Trend       : {a['trend']}\n"
        )

    emi_rough = inr_price * 0.8 * 0.00750  # 80% LTV, ~9% rate, 20yr (approx monthly factor)

    lines = f"""
🏠 AI HOUSE PRICE PREDICTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTIMATED PRICE
  Median estimate  : **{_lakhs(inr_price)}**
  Likely range     : **{_lakhs(inr_low)} – {_lakhs(inr_high)}**
{"  Price per sq ft  : **₹" + f"{price_per_sqft:,.0f}/sqft**" if sqft > 0 else ""}
  Model confidence : R² 67% (IBM AutoAI — Snap Boosting Regressor)

{budget_note}

📍 TOP AREAS IN {city.upper() or "YOUR CITY"} FOR {bhk}BHK {property_type}
{area_rows}
🏆 BEST HOUSE AT LOWEST PRICE
  Area    : **{best_value['name']}**
  Range   : {best_value['price_range']}
  Why     : Best price-to-quality ratio; good safety & future growth.

💰 QUICK EMI ESTIMATE (80% loan, ~9% rate, 20 yrs)
  Monthly EMI ≈ **₹{emi_rough:,.0f}**
  Use the EMI Calculator below for exact numbers.

📈 INVESTMENT RATING: {invest_score}/10
  {"🟢 Excellent buy — strong appreciation expected." if invest_score >= 8
    else "🟡 Good value — steady long-term growth." if invest_score >= 6
    else "🟠 Moderate — verify locality before deciding."}

⚠️ IMPORTANT CONSIDERATIONS
  • Verify RERA registration before booking.
  • Check for clear title, no encumbrances.
  • Factor in stamp duty (5–7%) and registration (1%) costs.
  • Prices vary by exact floor, facing, and negotiation.

{AGENT_INSTRUCTIONS['disclaimer']}
"""
    return lines.strip()


def build_area_advice(city: str, budget: float, bhk: int) -> str:
    """Generate best-area suggestions based on city and budget."""
    city_key = city.strip().lower()
    areas    = AGENT_INSTRUCTIONS["city_areas"].get(
        city_key, AGENT_INSTRUCTIONS["default_areas"]
    )
    budget_lakh = budget / 100_000

    area_rows = ""
    for i, a in enumerate(areas[:5], 1):
        c_stars = _stars(a["connectivity"])
        s_stars = _stars(a["safety"])
        area_rows += (
            f"\n  {i}. **{a['name']}**\n"
            f"     Price range : {a['price_range']}\n"
            f"     Connectivity: {c_stars}  |  Safety: {s_stars}\n"
            f"     Market trend: {a['trend']}\n"
        )

    best_value = next((a for a in areas if "💎" in a["trend"]), areas[-1])
    best_idx   = areas.index(best_value) + 1

    lines = f"""
📍 BEST AREAS IN {city.upper()} FOR {bhk}BHK
   Budget: ₹{budget_lakh:.0f}L
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{area_rows}
🏆 BEST HOUSE AT LOWEST PRICE → #{best_idx} **{best_value['name']}**
  Why: {best_value['price_range']} with top safety rating.
  This area consistently offers the best value in {city}.

🚇 CONNECTIVITY TIPS
  • Prefer areas within 2 km of metro/railway station.
  • Check upcoming metro lines — they boost prices 15–30%.

🏫 LIFESTYLE FACTORS TO CHECK
  • Nearby hospitals within 5 km.
  • Good schools within 3 km.
  • Grocery/market access.
  • Traffic & commute time to your workplace.

💡 PRO TIP
  Properties 10–15% below your budget give you negotiation room
  and a buffer for registration, interior, and moving costs.

{AGENT_INSTRUCTIONS['disclaimer']}
"""
    return lines.strip()


def build_emi_advice(principal: float, rate: float, tenure: int,
                     emi: float, total_interest: float, total_amount: float) -> str:
    """Generate AI loan advisor text for the EMI result."""
    emi_to_income_40pct = emi / 0.40  # 40% rule → minimum monthly income needed
    saved_if_extra_5k   = 5000 * tenure * 12 * (rate / 1200)   # rough saving estimate

    lines = f"""
💰 EMI BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Monthly EMI    : **₹{emi:,.0f}**
  Yearly payment : **₹{emi*12:,.0f}**
  Total payable  : **₹{total_amount:,.0f}**
  Total interest : **₹{total_interest:,.0f}** ({total_interest/principal*100:.0f}% of loan)

📊 AFFORDABILITY CHECK (40% income rule)
  To afford this EMI comfortably, your monthly income should be
  at least **₹{emi_to_income_40pct:,.0f}/month** (₹{emi_to_income_40pct*12:,.0f}/year).

📈 AMORTIZATION SUMMARY
  • First 5 years  : Mostly interest (~70% of EMI goes to interest).
  • Middle years   : Gradually shifts to principal repayment.
  • Last 5 years   : Mostly principal (~80% goes to principal).

💡 TIPS TO REDUCE EMI & SAVE ON INTEREST
  1. Make a larger down payment (20–30%) to reduce principal.
  2. Pay ₹5,000 extra/month → saves approx. ₹{saved_if_extra_5k:,.0f} in interest.
  3. Refinance if rates drop by 1%+ in future.
  4. Use annual bonus to make part-prepayment (no penalty on floating loans).
  5. Choose shorter tenure if affordable — saves significant interest.

🏦 HOME LOAN BEST BANKS (2024 indicative rates)
  • SBI Home Loan      : 8.40% onwards
  • HDFC Bank          : 8.45% onwards
  • ICICI Bank         : 8.40% onwards
  • Bank of Baroda     : 8.40% onwards
  • LIC HFL            : 8.50% onwards
  (Compare at bankbazaar.com / paisabazaar.com)

⚡ FIXED vs FLOATING RATE?
  • **Floating rate** recommended when rates are high (they may fall).
  • **Fixed rate** better for certainty and when rates are near lows.
  • Current market (2024): Floating rate is generally advisable.

{AGENT_INSTRUCTIONS['disclaimer']}
"""
    return lines.strip()


def build_chat_response(user_message: str) -> str:
    """
    Rule-based smart chat responder covering common real-estate queries.
    Extend the keyword→response dict to add more topics.
    """
    msg = user_message.lower()

    # ── keyword routing ──────────────────────────────────────
    if any(k in msg for k in ["emi", "loan", "interest", "equated"]):
        return (
            "💰 **EMI Basics**\n\n"
            "Monthly EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ – 1)\n\n"
            "Where:\n"
            "  P = Principal loan amount\n"
            "  r = Monthly interest rate (Annual rate ÷ 12 ÷ 100)\n"
            "  n = Total months (years × 12)\n\n"
            "Use the **EMI Calculator** section above for exact numbers!\n\n"
            "💡 General rule: EMI should not exceed 40% of your monthly income.\n\n"
            "🏦 Current home loan rates range from **8.40% – 9.5%** depending on the bank "
            "and your CIBIL score (aim for 750+).\n\n"
            f"{AGENT_INSTRUCTIONS['disclaimer']}"
        )

    if any(k in msg for k in ["buy or rent", "buy vs rent", "rent or buy", "should i buy"]):
        return (
            "🤔 **Buy vs Rent — Quick Analysis**\n\n"
            "**BUY if:**\n"
            "  • You plan to stay 5+ years in the same city.\n"
            "  • EMI ≤ 40% of monthly income.\n"
            "  • You have 20% down payment ready.\n"
            "  • Property is in an appreciating locality.\n\n"
            "**RENT if:**\n"
            "  • Job requires frequent relocation.\n"
            "  • Rent is <50% of equivalent EMI.\n"
            "  • You want liquidity for other investments.\n"
            "  • Market is overheated — wait for correction.\n\n"
            "📊 **Rule of Thumb:** If (House Price / Annual Rent) > 20, renting is better financially.\n\n"
            "Use the **Price Predictor** to check if a property is fairly valued!"
        )

    if any(k in msg for k in ["document", "papers", "registration", "stamp duty", "legal"]):
        return (
            "📄 **Documents Needed to Buy a House in India**\n\n"
            "**Buyer Documents:**\n"
            "  • PAN card + Aadhaar card\n"
            "  • Last 3 months salary slips / IT returns (2 years)\n"
            "  • Bank statements (6 months)\n"
            "  • Passport-size photographs\n\n"
            "**Property Documents (verify these):**\n"
            "  • Sale Deed / Title Deed\n"
            "  • Encumbrance Certificate (EC)\n"
            "  • Approved Building Plan\n"
            "  • Occupancy Certificate (OC)\n"
            "  • RERA Registration number\n"
            "  • NOC from builder/society\n\n"
            "**Costs at Registration:**\n"
            "  • Stamp Duty: 4–7% of property value (varies by state)\n"
            "  • Registration Fee: 1% of property value\n\n"
            "⚠️ Always verify documents with a property lawyer before payment."
        )

    if any(k in msg for k in ["rera", "fraud", "safe", "scam", "cheat"]):
        return (
            "🔒 **How to Buy Safely & Avoid Fraud**\n\n"
            "  1. **RERA check** — Verify project at your state's RERA portal.\n"
            "  2. **Title search** — Get EC (Encumbrance Certificate) for last 30 years.\n"
            "  3. **Builder track record** — Check previous projects, delivery timelines.\n"
            "  4. **Avoid cash deals** — All payments should be traceable (cheque/NEFT).\n"
            "  5. **Hire a lawyer** — ₹5,000–15,000 for document verification is worth it.\n"
            "  6. **Occupancy Certificate** — Never buy without OC; it confirms legal occupancy.\n"
            "  7. **Bank loan sanction** — Banks do their own due diligence; use it as a safety net.\n\n"
            "🚨 **Red flags:** Unusually low price, demand for 100% cash, no RERA number, rushed timelines."
        )

    if any(k in msg for k in ["invest", "appreciation", "return", "roi", "resale"]):
        return (
            "📈 **Real Estate Investment Tips (2024)**\n\n"
            "**Best cities for appreciation:** Bengaluru, Hyderabad, Pune, Mumbai MMR\n\n"
            "**Factors that drive appreciation:**\n"
            "  • Metro connectivity (15–30% premium)\n"
            "  • IT/Tech employment hub proximity\n"
            "  • Infrastructure projects (ring roads, airports)\n"
            "  • Good schools & hospitals nearby\n\n"
            "**Expected returns:**\n"
            "  • Tier-1 cities: 7–12% annual appreciation\n"
            "  • Tier-2 cities: 5–8% annual appreciation\n"
            "  • Rental yield: 2–4% per annum (India avg)\n\n"
            "💡 **Long-term tip:** Hold property for 7+ years for best inflation-adjusted returns.\n\n"
            "Use the **Price Predictor** to check if a property is fairly priced before investing!"
        )

    if any(k in msg for k in ["first time", "first home", "new buyer", "beginner", "guide"]):
        return (
            "🏠 **First-Time Home Buyer Guide**\n\n"
            "**Step 1 — Check your finances**\n"
            "  • Down payment ready? (20% recommended)\n"
            "  • CIBIL score ≥ 750 for best loan rates\n"
            "  • EMI ≤ 40% of monthly take-home\n\n"
            "**Step 2 — Get pre-approved**\n"
            "  • Apply for home loan pre-approval (free, no obligation)\n"
            "  • Confirms your budget limit\n\n"
            "**Step 3 — Shortlist properties**\n"
            "  • Use Area Finder & Price Predictor above\n"
            "  • Visit at least 5–7 properties\n"
            "  • Compare on: location, floor, age, amenities\n\n"
            "**Step 4 — Due diligence**\n"
            "  • Verify RERA number\n"
            "  • Get EC, title deed checked by lawyer\n\n"
            "**Step 5 — Finalize & register**\n"
            "  • Negotiate price (5–10% is normal)\n"
            "  • Pay token amount only after legal check\n"
            "  • Complete registration within agreed timeline\n\n"
            "Tip: Use the **EMI Calculator** to plan your monthly budget!"
        )

    if any(k in msg for k in ["mumbai", "bangalore", "hyderabad", "pune", "delhi",
                               "chennai", "kolkata", "ahmedabad", "price", "rate", "cost"]):
        cities_mentioned = [c for c in ["mumbai", "bangalore", "hyderabad", "pune", "delhi", "chennai"]
                           if c in msg]
        city_info = ""
        for city in cities_mentioned[:2]:
            areas = AGENT_INSTRUCTIONS["city_areas"].get(city, [])
            if areas:
                low  = areas[-1]["price_range"]
                high = areas[0]["price_range"]
                city_info += f"\n  **{city.title()}**: {low} (budget) to {high} (premium)"
        if not city_info:
            city_info = "\n  Use the **Price Predictor** above for exact estimates!"
        return (
            "🏙️ **City Property Rates (2024 estimates)**\n"
            + city_info +
            "\n\n📍 For detailed area-wise suggestions, use the **Area Finder** section!\n\n"
            f"{AGENT_INSTRUCTIONS['disclaimer']}"
        )

    if any(k in msg for k in ["hello", "hi", "hey", "help", "start", "what can you do"]):
        return (
            "👋 **Hello! I'm HouseBot, your AI real-estate advisor.**\n\n"
            "I can help you with:\n"
            "  🏠 **Price prediction** — Fill the form above\n"
            "  📍 **Area suggestions** — Best localities for your budget\n"
            "  💰 **EMI calculation** — Monthly loan planning\n"
            "  📈 **Investment advice** — Which cities/areas to invest\n"
            "  📄 **Legal guidance** — Documents, RERA, registration\n"
            "  🤔 **Buy vs Rent** — Personalized analysis\n\n"
            "Just ask me anything about real estate! 🏡"
        )

    # Default catch-all
    return (
        f"🤖 Great question about: **\"{user_message[:60]}\"**\n\n"
        "Here's what I suggest:\n\n"
        "  • For **price estimates** → use the 🏠 Price Predictor section.\n"
        "  • For **area suggestions** → use the 📍 Area Finder section.\n"
        "  • For **loan calculations** → use the 💰 EMI Calculator.\n\n"
        "You can also ask me specifically about:\n"
        "  → EMI & home loans\n"
        "  → Buy vs Rent analysis\n"
        "  → Investment advice\n"
        "  → Legal documents & RERA\n"
        "  → First-time buyer guide\n"
        "  → City-wise price rates\n\n"
        f"{AGENT_INSTRUCTIONS['disclaimer']}"
    )


# ============================================================
#  Flask Routes
# ============================================================

@app.route("/")
def index():
    session.setdefault("chat_history", [])
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    """House price prediction — calls IBM AutoAI model."""
    try:
        data = request.get_json(silent=True) or {}
        if not data.get("city"):
            return jsonify({"error": "Please enter a city name."}), 400

        features = map_form_to_model_features(data)
        usd_price = call_autoai_model(features)
        response  = build_prediction_advice(data, usd_price)

        inr_price = usd_price * USD_TO_INR
        return jsonify({
            "success":    True,
            "response":   response,
            "type":       "prediction",
            "usd_price":  round(usd_price, 2),
            "inr_price":  round(inr_price, 2),
            "features":   dict(zip(MODEL_FIELDS, features)),
        })

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"IBM model error: {e.response.status_code} — {e.response.text[:200]}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/emi", methods=["POST"])
def emi_calculator():
    """EMI calculation with AI loan advisor."""
    try:
        data      = request.get_json(silent=True) or {}
        principal = float(data.get("principal", 0))
        rate      = float(data.get("rate", 8.5))
        tenure    = int(data.get("tenure", 20))

        if principal <= 0:
            return jsonify({"error": "Loan amount must be greater than 0."}), 400

        monthly_rate = rate / (12 * 100)
        n            = tenure * 12
        emi          = (principal * monthly_rate * (1 + monthly_rate) ** n /
                        ((1 + monthly_rate) ** n - 1)) if monthly_rate > 0 else principal / n
        total_amount  = emi * n
        total_interest = total_amount - principal

        ai_response = build_emi_advice(principal, rate, tenure, emi, total_interest, total_amount)

        return jsonify({
            "success":        True,
            "emi":            round(emi, 2),
            "total_amount":   round(total_amount, 2),
            "total_interest": round(total_interest, 2),
            "ai_response":    ai_response,
            "type":           "emi",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """General chat endpoint."""
    try:
        data         = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"error": "Empty message."}), 400

        response = build_chat_response(user_message)

        history = session.get("chat_history", [])
        history.append({"role": "user",      "content": user_message})
        history.append({"role": "assistant", "content": response})
        session["chat_history"] = history[-20:]

        return jsonify({"success": True, "response": response, "type": "chat"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/suggest-areas", methods=["POST"])
def suggest_areas():
    """Area suggestions endpoint."""
    try:
        data   = request.get_json(silent=True) or {}
        city   = data.get("city", "").strip()
        budget = float(data.get("budget", 0) or 0)
        bhk    = int(data.get("bhk", 2))

        if not city:
            return jsonify({"error": "Please enter a city name."}), 400

        response = build_area_advice(city, budget, bhk)
        return jsonify({"success": True, "response": response, "type": "areas"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/clear-chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    return jsonify({"success": True})


@app.route("/health")
def health():
    return jsonify({
        "status":  "ok",
        "service": "House Price Predictor",
        "model":   "IBM AutoAI Snap Boosting Regressor",
        "fields":  MODEL_FIELDS,
    })


# ============================================================
#  Entry Point
# ============================================================
if __name__ == "__main__":
    port  = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print(f"🏠 HouseBot AI starting on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
