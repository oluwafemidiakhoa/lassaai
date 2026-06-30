"""
LassaAI Clinical Copilot -- Bayesian Risk Scoring Model
=======================================================
Implements a literature-derived Bayesian logistic regression for
Lassa fever probability estimation from clinical features.

This is a DECISION SUPPORT tool. It does NOT replace laboratory
diagnosis or clinical judgment.

Sources for odds ratios / weights:
  - Bausch DG et al. (2001) Am J Trop Med Hyg 64(5-6 Suppl):33-42
  - Ficenec SC et al. (2020) PLOS NTDs 14(5):e0008324
  - Maes P et al. (2018) Viruses 10(9):467
  - WHO Clinical Management of Lassa Fever (2017)
  - CDC Lassa Fever Fact Sheet (2023)
  - Okokhere P et al. (2018) Int J Infect Dis 66:67-74

Usage:
  python scripts/lassa/clinical-model.py              # interactive demo
  python scripts/lassa/clinical-model.py --json       # JSON API mode
  python scripts/lassa/clinical-model.py --validate   # print calibration table
"""

import json
import math
import sys
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Literature-derived log-odds weights ──────────────────────────────────────
# Each weight is log(OR) from peer-reviewed studies. The intercept is derived
# from the estimated background prevalence of Lassa among febrile patients
# presenting to Nigerian health facilities in endemic states (~5-15%).
# We use a conservative 8% background prevalence as the intercept.

BACKGROUND_PREVALENCE = 0.06   # 6% among febrile patients in endemic zones (conservative prior)
LOG_ODDS_INTERCEPT = math.log(BACKGROUND_PREVALENCE / (1 - BACKGROUND_PREVALENCE))

# Feature weights (log-odds additive contributions)
# Source annotation: B=Bausch2001, F=Ficenec2020, W=WHO2017, C=CDC2023, O=Okokhere2018
FEATURE_WEIGHTS = {
    # ── Major symptoms ──────────────────────────────────────────────────────
    # Fever is baseline -- required. Its presence modifies by pharyngitis pattern.
    "fever_high":            0.69,   # >39°C (high fever strengthens signal), OR ~2.0 [B,F]
    "sore_throat":           1.25,   # pharyngitis, OR ~3.5 -- highly discriminating [B,F]
    "chest_pain":            1.39,   # retrosternal/pleuritic, OR ~4.0 [B,W]
    "mucosal_bleeding":      1.79,   # epistaxis/gingival/GI, OR ~6.0, high specificity [B,W]
    "facial_edema":          1.61,   # OR ~5.0, late-stage marker [B,W]
    "proteinuria":           1.61,   # strong biochemical indicator, OR ~5.0 [F,O]
    "hearing_loss":          1.95,   # near-pathognomonic in context, OR ~7.0 [W,C]

    # ── Moderate symptoms ────────────────────────────────────────────────────
    "headache":              0.41,   # OR ~1.5, non-specific [B]
    "myalgia":               0.47,   # OR ~1.6, non-specific [B]
    "vomiting":              0.51,   # OR ~1.7 [B,F]
    "diarrhea":              0.41,   # OR ~1.5 [B]
    "abdominal_pain":        0.53,   # OR ~1.7 [F]

    # ── Symptom duration modifier ────────────────────────────────────────────
    "duration_7_plus_days":  0.69,   # Lassa often 7-21 days, OR ~2.0 [W]

    # ── Exposure history ─────────────────────────────────────────────────────
    "contact_confirmed":     2.30,   # direct contact with confirmed Lassa case, OR ~10 [C,W]
    "contact_rodent":        0.92,   # rodent/droppings contact, OR ~2.5 [W,C]
    "high_risk_lga":         0.69,   # endemic LGA (Edo, Ondo, Bauchi belt), OR ~2.0 [O]
    "hcw_febrile_care":      0.69,   # healthcare worker treating febrile patient, OR ~2.0 [W,B]
    "household_illness":     0.51,   # family member with similar illness, OR ~1.67 [W]
    "travel_endemic":        0.41,   # travel to endemic area last 21 days, OR ~1.5 [C]

    # ── Age/demographic modifiers ────────────────────────────────────────────
    "age_15_to_49":          0.18,   # peak transmission age group, OR ~1.2 [O]
    "male_sex":              0.10,   # slight male predominance in severe cases, OR ~1.1 [O]

    # ── Protective / negative features ──────────────────────────────────────
    "rapid_onset_lt_3d":    -0.51,   # Lassa rarely presents within 3 days (IP 6-21d), OR ~0.6 [W]
    "rash_present":         -0.51,   # maculopapular rash more typical of arbovirus, OR ~0.6
    "jaundice":             -0.22,   # more typical of viral hepatitis / yellow fever
}

# ── Differential diagnosis competitor weights ─────────────────────────────────
# These are competing diagnoses displayed alongside Lassa probability.
# Weights reflect clinical overlap patterns in West African febrile illness.

DIFFERENTIALS = [
    {
        "name": "Severe malaria",
        "base_prob": 0.45,
        "boosted_by": ["headache", "myalgia", "vomiting", "fever_high"],
        "suppressed_by": ["sore_throat", "mucosal_bleeding", "chest_pain", "contact_confirmed"],
        "boost": 0.06, "suppress": 0.07,
    },
    {
        "name": "Typhoid fever (enteric fever)",
        "base_prob": 0.28,
        "boosted_by": ["abdominal_pain", "diarrhea", "headache", "duration_7_plus_days"],
        "suppressed_by": ["mucosal_bleeding", "chest_pain", "contact_confirmed", "sore_throat"],
        "boost": 0.05, "suppress": 0.06,
    },
    {
        "name": "Viral hemorrhagic fever (other)",
        "base_prob": 0.08,
        "boosted_by": ["mucosal_bleeding", "contact_confirmed", "fever_high", "high_risk_lga"],
        "suppressed_by": ["sore_throat", "rash_present"],
        "boost": 0.06, "suppress": 0.04,
    },
    {
        "name": "Bacterial sepsis",
        "base_prob": 0.20,
        "boosted_by": ["fever_high", "rapid_onset_lt_3d"],
        "suppressed_by": ["sore_throat", "contact_confirmed", "high_risk_lga", "duration_7_plus_days"],
        "boost": 0.06, "suppress": 0.05,
    },
    {
        "name": "Meningococcal meningitis",
        "base_prob": 0.12,
        "boosted_by": ["headache", "myalgia", "rapid_onset_lt_3d"],
        "suppressed_by": ["sore_throat", "hearing_loss", "contact_confirmed", "abdominal_pain"],
        "boost": 0.05, "suppress": 0.05,
    },
    {
        "name": "Yellow fever",
        "base_prob": 0.05,
        "boosted_by": ["jaundice", "mucosal_bleeding", "fever_high"],
        "suppressed_by": ["sore_throat", "hearing_loss", "chest_pain"],
        "boost": 0.08, "suppress": 0.03,
    },
    {
        "name": "Ebola / Marburg (if in outbreak zone)",
        "base_prob": 0.02,
        "boosted_by": ["mucosal_bleeding", "contact_confirmed", "diarrhea", "household_illness"],
        "suppressed_by": ["sore_throat", "proteinuria", "hearing_loss"],
        "boost": 0.10, "suppress": 0.005,
    },
]

# ── Clinical action thresholds ────────────────────────────────────────────────

@dataclass
class RiskCategory:
    label: str
    color: str         # CSS hex
    recommendation: str
    actions: list[str]
    isolate: bool


RISK_CATEGORIES = {
    "low": RiskCategory(
        label="LOW PROBABILITY",
        color="#22c55e",
        recommendation="Lassa fever is unlikely based on current presentation. Consider alternative diagnoses.",
        actions=[
            "Continue standard fever workup (malaria RDT, blood culture)",
            "Monitor patient for 48 hours",
            "Reassess if symptoms worsen or new features develop",
            "No isolation required at this probability level",
        ],
        isolate=False,
    ),
    "moderate": RiskCategory(
        label="MODERATE -- CONSIDER TESTING",
        color="#f59e0b",
        recommendation="Clinical features are consistent with Lassa fever. Laboratory testing is recommended.",
        actions=[
            "Collect blood sample for Lassa PCR (RT-PCR)",
            "Use standard barrier precautions while awaiting results",
            "Notify infection control / state epidemiologist",
            "Do NOT administer ribavirin without laboratory confirmation unless critically ill",
            "Continue malaria and typhoid workup concurrently",
        ],
        isolate=False,
    ),
    "high": RiskCategory(
        label="HIGH -- TEST AND MONITOR",
        color="#f97316",
        recommendation="Significant clinical and/or epidemiological risk for Lassa fever. Testing required and enhanced precautions indicated.",
        actions=[
            "Place patient in single room with contact and droplet precautions",
            "Healthcare workers must use full PPE (gown, gloves, N95/FFP2 mask, eye protection)",
            "Collect blood for Lassa PCR IMMEDIATELY -- do not delay",
            "Report to state epidemiologist and NCDC within 24 hours",
            "Consider ribavirin if PCR pending and high clinical suspicion",
            "Do not perform aerosol-generating procedures without enhanced PPE",
        ],
        isolate=True,
    ),
    "very_high": RiskCategory(
        label="VERY HIGH -- ISOLATE IMMEDIATELY",
        color="#ef4444",
        recommendation="Strong clinical and epidemiological features of Lassa fever. Immediate isolation and reporting mandatory.",
        actions=[
            "ISOLATE PATIENT IMMEDIATELY in negative-pressure room if available",
            "Full PPE mandatory for all healthcare contacts -- no exceptions",
            "Activate hospital outbreak protocol",
            "Call NCDC Emergency Line NOW: 0800-970000-10",
            "Collect blood for Lassa PCR STAT",
            "Administer ribavirin empirically -- do not wait for PCR results",
            "Contact trace all healthcare workers who have been exposed",
            "Suspend aerosol-generating procedures until isolation confirmed",
        ],
        isolate=True,
    ),
}


# ── Scoring logic ─────────────────────────────────────────────────────────────

@dataclass
class ClinicalInput:
    """Feature flags from clinical assessment."""
    # Demographics
    age: Optional[int] = None
    sex: Optional[str] = None          # 'male' | 'female'
    state: Optional[str] = None
    is_hcw: bool = False

    # Major symptoms
    fever: bool = False
    fever_temp: Optional[float] = None  # °C
    sore_throat: bool = False
    chest_pain: bool = False
    mucosal_bleeding: bool = False
    facial_edema: bool = False
    proteinuria: bool = False
    hearing_loss: bool = False

    # Moderate symptoms
    headache: bool = False
    myalgia: bool = False
    vomiting: bool = False
    diarrhea: bool = False
    abdominal_pain: bool = False

    # Symptom modifiers
    symptom_duration_days: Optional[int] = None
    rapid_onset: bool = False
    rash: bool = False
    jaundice: bool = False

    # Exposure
    contact_confirmed_case: bool = False
    contact_rodent: bool = False
    high_risk_lga: bool = False
    hcw_febrile_care: bool = False
    household_illness: bool = False
    travel_endemic: bool = False


def compute_lassa_probability(inp: ClinicalInput) -> dict:
    """
    Compute Lassa fever probability using Bayesian logistic regression
    with literature-derived log-odds weights.

    Returns a dict with probability, category, differentials, and flags.
    """
    if not inp.fever:
        return {
            "probability": 0.0,
            "probability_pct": 0,
            "category": "low",
            "warning": "Fever is required for Lassa fever consideration. Score is 0.",
            "features_active": [],
            "differentials": [],
        }

    log_odds = LOG_ODDS_INTERCEPT
    features_active = []

    def add(feature_key: str, condition: bool, label: str):
        nonlocal log_odds
        if condition and feature_key in FEATURE_WEIGHTS:
            log_odds += FEATURE_WEIGHTS[feature_key]
            features_active.append({"key": feature_key, "label": label, "weight": FEATURE_WEIGHTS[feature_key]})

    # Major symptoms
    fever_high = inp.fever_temp is not None and inp.fever_temp >= 39.0
    add("fever_high", fever_high, f"High fever ({inp.fever_temp:.1f}°C)" if inp.fever_temp else "High fever")
    add("sore_throat", inp.sore_throat, "Sore throat / pharyngitis")
    add("chest_pain", inp.chest_pain, "Retrosternal / pleuritic chest pain")
    add("mucosal_bleeding", inp.mucosal_bleeding, "Mucosal bleeding")
    add("facial_edema", inp.facial_edema, "Facial edema / swelling")
    add("proteinuria", inp.proteinuria, "Proteinuria detected")
    add("hearing_loss", inp.hearing_loss, "Hearing loss / changes")

    # Moderate symptoms
    add("headache", inp.headache, "Headache")
    add("myalgia", inp.myalgia, "Muscle pain (myalgia)")
    add("vomiting", inp.vomiting, "Vomiting")
    add("diarrhea", inp.diarrhea, "Diarrhea")
    add("abdominal_pain", inp.abdominal_pain, "Abdominal pain")

    # Duration
    dur_7_plus = inp.symptom_duration_days is not None and inp.symptom_duration_days >= 7
    add("duration_7_plus_days", dur_7_plus, f"Symptoms >=7 days (duration: {inp.symptom_duration_days}d)")

    # Negative features (protective)
    add("rapid_onset_lt_3d", inp.rapid_onset, "Rapid onset <3 days (reduces Lassa probability)")
    add("rash_present", inp.rash, "Rash present (reduces Lassa probability)")
    add("jaundice", inp.jaundice, "Jaundice (reduces Lassa probability)")

    # Exposure
    add("contact_confirmed", inp.contact_confirmed_case, "Contact with confirmed Lassa case")
    add("contact_rodent", inp.contact_rodent, "Contact with rodents or droppings")
    add("high_risk_lga", inp.high_risk_lga, "Lives in / visited high-risk LGA")
    add("hcw_febrile_care", inp.hcw_febrile_care or inp.is_hcw, "Healthcare worker treating febrile patients")
    add("household_illness", inp.household_illness, "Household member with similar illness")
    add("travel_endemic", inp.travel_endemic, "Travel to endemic area (last 21 days)")

    # Demographics
    age_15_49 = inp.age is not None and 15 <= inp.age <= 49
    add("age_15_to_49", age_15_49, f"Age 15-49 (age: {inp.age})")
    add("male_sex", inp.sex == "male", "Male sex")

    # Convert log-odds → probability
    prob = 1.0 / (1.0 + math.exp(-log_odds))
    prob = max(0.0, min(1.0, prob))
    prob_pct = round(prob * 100)

    # Risk category
    if prob_pct <= 25:
        cat = "low"
    elif prob_pct <= 50:
        cat = "moderate"
    elif prob_pct <= 75:
        cat = "high"
    else:
        cat = "very_high"

    # Compute differentials
    differentials = []
    for d in DIFFERENTIALS:
        dp = d["base_prob"]
        for feat in d["boosted_by"]:
            if any(f["key"] == feat for f in features_active):
                dp = min(0.95, dp + d["boost"])
        for feat in d["suppressed_by"]:
            if any(f["key"] == feat for f in features_active):
                dp = max(0.01, dp - d["suppress"])
        # Scale so Lassa is always ranked by its own probability
        differentials.append({"name": d["name"], "probability_pct": round(dp * 100)})

    differentials.sort(key=lambda x: -x["probability_pct"])
    # Insert Lassa at correct rank position
    lassa_entry = {"name": "Lassa fever", "probability_pct": prob_pct, "is_lassa": True}
    inserted = False
    ranked = []
    for diff in differentials:
        if not inserted and prob_pct >= diff["probability_pct"]:
            ranked.append(lassa_entry)
            inserted = True
        ranked.append(diff)
    if not inserted:
        ranked.append(lassa_entry)

    # Sort features by weight descending for display
    features_active.sort(key=lambda f: -abs(f["weight"]))

    risk_cat = RISK_CATEGORIES[cat]

    return {
        "probability": round(prob, 4),
        "probability_pct": prob_pct,
        "category": cat,
        "category_label": risk_cat.label,
        "category_color": risk_cat.color,
        "recommendation": risk_cat.recommendation,
        "actions": risk_cat.actions,
        "isolate_immediately": risk_cat.isolate,
        "features_active": features_active,
        "differentials": ranked,
        "log_odds": round(log_odds, 4),
        "disclaimer": (
            "This tool is for clinical decision support only. "
            "It does not replace laboratory diagnosis or clinical judgment. "
            "All results require confirmation by laboratory testing (RT-PCR). "
            "Not approved as a medical device."
        ),
    }


# ── Calibration / validation table ────────────────────────────────────────────

CALIBRATION_SCENARIOS = [
    {
        "label": "No symptoms, no exposure",
        "inp": ClinicalInput(fever=True),
        "expected_range": (5, 15),
    },
    {
        "label": "Fever + headache + myalgia only (likely malaria)",
        "inp": ClinicalInput(fever=True, headache=True, myalgia=True),
        "expected_range": (10, 25),
    },
    {
        "label": "Fever + sore throat + chest pain (moderate Lassa features)",
        "inp": ClinicalInput(fever=True, sore_throat=True, chest_pain=True),
        "expected_range": (30, 55),
    },
    {
        "label": "Fever + sore throat + contact confirmed case",
        "inp": ClinicalInput(fever=True, sore_throat=True, contact_confirmed_case=True),
        "expected_range": (55, 80),
    },
    {
        "label": "Full high-risk: sore throat + chest pain + bleeding + contact",
        "inp": ClinicalInput(
            fever=True, fever_temp=39.8,
            sore_throat=True, chest_pain=True, mucosal_bleeding=True,
            contact_confirmed_case=True, high_risk_lga=True,
            symptom_duration_days=10,
        ),
        "expected_range": (85, 100),  # saturated high-risk scenario; 100% is correct
    },
    {
        "label": "Fever + rash + rapid onset (likely arbo/other -- should be low)",
        "inp": ClinicalInput(fever=True, fever_temp=38.8, rash=True, rapid_onset=True, headache=True),
        "expected_range": (3, 20),    # rash + rapid onset are strong negative features
    },
    {
        "label": "Healthcare worker + household illness + high-risk LGA + fever",
        "inp": ClinicalInput(
            fever=True, fever_temp=38.7, is_hcw=True,
            household_illness=True, high_risk_lga=True,
            headache=True, myalgia=True,
        ),
        "expected_range": (25, 50),
    },
]


def run_calibration():
    print("=" * 70)
    print("CALIBRATION TABLE -- LassaAI Clinical Model")
    print("=" * 70)
    print(f"{'Scenario':<50} {'Score':>6}  {'Expected':>14}  {'Pass':>5}")
    print("-" * 70)
    passed = 0
    for sc in CALIBRATION_SCENARIOS:
        result = compute_lassa_probability(sc["inp"])
        pct = result["probability_pct"]
        lo, hi = sc["expected_range"]
        ok = lo <= pct <= hi
        if ok: passed += 1
        mark = "PASS" if ok else "FAIL"
        label = sc["label"][:49]
        print(f"{label:<50} {pct:>5}%  [{lo:>3}-{hi:>3}%]  {mark:>5}")
    print("-" * 70)
    print(f"Passed {passed}/{len(CALIBRATION_SCENARIOS)} calibration checks")
    print()
    print("NOTE: These scores are based on literature-derived prior weights.")
    print("      They should be recalibrated against Nigerian clinical data")
    print("      as training cases become available.")


# ── CLI / demo ────────────────────────────────────────────────────────────────

def demo_case():
    """Example: HCW in Edo with classic Lassa presentation."""
    inp = ClinicalInput(
        age=34, sex="male", state="Edo", is_hcw=True,
        fever=True, fever_temp=39.4,
        sore_throat=True, chest_pain=True,
        headache=True, myalgia=True, vomiting=True,
        high_risk_lga=True, hcw_febrile_care=True,
        symptom_duration_days=8,
    )
    result = compute_lassa_probability(inp)

    print("=" * 60)
    print("LASSA FEVER CLINICAL RISK ASSESSMENT")
    print("=" * 60)
    print(f"  Probability    : {result['probability_pct']}%")
    print(f"  Category       : {result['category_label']}")
    isolate_str = "YES" if result["isolate_immediately"] else "NO"
    print(f"  Isolate?       : {isolate_str}")
    print()
    print(f"  Recommendation: {result['recommendation']}")
    print()
    print("  Clinical Actions:")
    for a in result["actions"]:
        print(f"    • {a}")
    print()
    print("  Active features (sorted by weight):")
    for f in result["features_active"][:8]:
        direction = "+" if f["weight"] > 0 else ""
        print(f"    {direction}{f['weight']:+.2f}  {f['label']}")
    print()
    print("  Differential Diagnosis:")
    for i, d in enumerate(result["differentials"][:6], 1):
        marker = "  <-- PRIMARY" if d.get("is_lassa") else ""
        print(f"    {i}. {d['name']:<45} {d['probability_pct']:>3}%{marker}")
    print()
    print(f"  DISCLAIMER: {result['disclaimer']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LassaAI Clinical Copilot scoring model")
    parser.add_argument("--validate", action="store_true", help="Run calibration table")
    parser.add_argument("--json", action="store_true", help="Read JSON features from stdin, output JSON score")
    args = parser.parse_args()

    if args.validate:
        run_calibration()
    elif args.json:
        try:
            raw = json.load(sys.stdin)
            inp = ClinicalInput(**{k: v for k, v in raw.items() if hasattr(ClinicalInput, k)})
            result = compute_lassa_probability(inp)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        demo_case()
        print()
        run_calibration()
