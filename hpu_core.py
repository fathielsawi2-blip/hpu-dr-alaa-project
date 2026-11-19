"""
HPU Core — Human Processing Unit
Prototype 0.1

ID, EGO and SUPER-EGO are information sources. They are not processing stages.
HPU evaluates the submitted information against explicit conditions and criteria.
The initial criteria and weights are experimental and must be calibrated through testing.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import json
import re

EXPERIMENTAL_WEIGHTS = {
    "objective_clarity": 0.20,
    "evidence_quality": 0.25,
    "feasibility": 0.20,
    "alignment": 0.15,
    "risk_control": 0.20,
}

@dataclass
class InformationSource:
    source: str
    content: str
    confidence: int = 3
    evidence: str = ""

@dataclass
class Measurement:
    criterion: str
    score: int
    rationale: str
    evidence_found: str = ""

@dataclass
class HPUResult:
    decision_id: str
    created_at: str
    situation: str
    objective: str
    decision: str
    score: float
    confidence: str
    measurements: list
    facts: list
    interpretations: list
    assumptions: list
    missing_information: list
    risks: list
    rationale: list
    next_actions: list
    input_sources: list
    ai_suggestion: str
    ai_evaluation: str

def _has(text: str, terms: list[str]) -> bool:
    t = text.lower()
    return any(term in t for term in terms)

def _extract_numbers(text: str) -> list[str]:
    return re.findall(r'\b\d+(?:[.,]\d+)?%?\b', text)

def _score_sources(sources: list[InformationSource]) -> tuple[int, str]:
    filled = [s for s in sources if s.content.strip()]
    if not filled:
        return 1, "No source information was supplied."
    explicit_evidence = sum(bool(s.evidence.strip()) for s in filled)
    avg_conf = sum(max(1, min(5, s.confidence)) for s in filled) / len(filled)
    score = round((avg_conf / 5) * 3 + (explicit_evidence / len(filled)) * 2)
    return max(1, min(5, score)), f"{len(filled)} source(s) supplied; average self-rated confidence {avg_conf:.1f}/5; {explicit_evidence} source(s) include supporting evidence."

def analyze(
    situation: str,
    objective: str,
    sources: list[InformationSource],
    conditions: str = "",
    constraints: str = "",
    ai_suggestion: str = "",
    weights: dict[str, float] | None = None,
) -> HPUResult:
    """Run transparent, rule-based HPU assessment. Scores are experimental."""
    weights = weights or EXPERIMENTAL_WEIGHTS
    all_text = "\n".join([situation, objective, conditions, constraints] +
                         [s.content + " " + s.evidence for s in sources])
    lower = all_text.lower()
    source_score, source_note = _score_sources(sources)

    objective_score = 5 if len(objective.strip()) >= 25 and _has(objective, ["increase","reduce","create","launch","improve","deliver","achieve","sell","build","complete","test"]) else 3 if objective.strip() else 1
    evidence_score = min(5, source_score + (1 if _extract_numbers(all_text) else 0))
    feasibility_score = 4 if _has(all_text, ["budget","time","team","available","resource","can","already","materials","skills"]) else 2
    feasibility_score = max(1, feasibility_score - (1 if _has(constraints, ["no budget","not enough time","unavailable","cannot","can't"]) else 0))
    alignment_score = 4 if conditions.strip() else 2
    risk_terms = ["risk","backup","safety","approval","test","pilot","review","limit","protect"]
    risk_score = 4 if _has(all_text, risk_terms) else 2
    if _has(constraints, ["unsafe","illegal","harm","privacy breach"]):
        risk_score = 1

    scores = {
        "objective_clarity": objective_score,
        "evidence_quality": evidence_score,
        "feasibility": feasibility_score,
        "alignment": alignment_score,
        "risk_control": risk_score,
    }
    labels = {
        "objective_clarity": ("Objective clarity", "Is the intended result specific enough to assess?"),
        "evidence_quality": ("Evidence quality", source_note),
        "feasibility": ("Feasibility", "Looks for resources, skills, time or practical capability in the submitted information."),
        "alignment": ("Alignment with conditions", "Checks whether decision conditions or success requirements were supplied."),
        "risk_control": ("Risk control", "Looks for risks, safeguards, testing or review arrangements."),
    }
    measurements = [
        asdict(Measurement(labels[k][0], v, labels[k][1], "Score is an initial rule-based estimate, not a validated measurement."))
        for k, v in scores.items()
    ]
    total_weight = sum(weights.values()) or 1
    score = round(sum(scores[k] * weights.get(k, 0) for k in scores) / total_weight * 20, 1)

    facts = []
    if situation.strip(): facts.append("Situation supplied: " + situation.strip())
    nums = _extract_numbers(all_text)
    if nums: facts.append("Numeric details present: " + ", ".join(nums[:12]))
    if any(s.evidence.strip() for s in sources): facts.append("Supporting evidence was entered for at least one information source.")
    interpretations = []
    if any(s.content.strip() for s in sources):
        interpretations.append("The submitted source statements are treated as perspectives or information, not automatically as verified facts.")
    if not nums:
        interpretations.append("No numeric baseline or target was detected; measurement may be less precise.")
    assumptions = [
        "The initial scoring rules are experimental and may not reflect the user's final HPU methodology.",
        "Self-rated source confidence is provisional and has not been independently verified."
    ]
    missing = []
    if not objective.strip(): missing.append("A clear objective or intended outcome.")
    if not conditions.strip(): missing.append("Conditions or success criteria against which HPU should assess the decision.")
    if not any(s.evidence.strip() for s in sources): missing.append("Evidence, examples or records supporting the submitted perspectives.")
    if not constraints.strip(): missing.append("Relevant constraints such as time, budget, people, policy or technical limits.")
    if not nums: missing.append("A measurable baseline, target or quantity, if applicable.")

    risks = []
    if risk_score <= 2: risks.append("Risk controls are not clearly described.")
    if feasibility_score <= 2: risks.append("Practical resources or feasibility need further examination.")
    if not conditions.strip(): risks.append("Without explicit conditions, alignment cannot be assessed reliably.")
    if not risks: risks.append("No high-severity risk was detected by these basic rules; this is not proof that no risk exists.")

    if risk_score == 1:
        decision = "STOP AND REVIEW"
    elif score >= 75 and len(missing) <= 1 and risk_score >= 3:
        decision = "PROCEED TO CONTROLLED IMPLEMENTATION"
    elif score >= 55:
        decision = "RUN A LIMITED PILOT"
    else:
        decision = "REASSESS — MORE INFORMATION NEEDED"

    rationale = [
        f"Experimental weighted score: {score}/100.",
        f"Risk-control measurement: {risk_score}/5.",
        f"Evidence measurement: {evidence_score}/5.",
        f"HPU selected '{decision}' using the current prototype rules."
    ]
    actions = []
    if missing: actions.append("Complete the missing information: " + "; ".join(missing))
    if decision == "RUN A LIMITED PILOT":
        actions.append("Run a small, time-limited pilot with a defined success measure and stop condition.")
    elif decision.startswith("STOP"):
        actions.append("Pause implementation until the identified safety or control concern is reviewed.")
    elif decision.startswith("REASSESS"):
        actions.append("Clarify the objective, conditions, evidence and constraints, then reassess.")
    else:
        actions.append("Proceed in stages and monitor the agreed success measures.")
    actions.append("Record the actual outcome later so the decision can be compared with its result.")

    ai_evaluation = "No AI suggestion supplied. HPU completed its assessment independently."
    if ai_suggestion.strip():
        ai_evaluation = ("AI suggestion recorded as an external input. HPU has not accepted it as authority. "
                         "Compare it against the measurements, evidence, conditions and risks above; "
                         "a human review is required before changing the decision.")

    return HPUResult(
        decision_id=datetime.now(timezone.utc).strftime("HPU-%Y%m%d-%H%M%S-%f"),
        created_at=datetime.now(timezone.utc).isoformat(),
        situation=situation, objective=objective, decision=decision, score=score,
        confidence="LOW" if len(missing) >= 3 or evidence_score <= 2 else "MEDIUM",
        measurements=measurements, facts=facts, interpretations=interpretations,
        assumptions=assumptions, missing_information=missing, risks=risks,
        rationale=rationale, next_actions=actions,
        input_sources=[asdict(s) for s in sources if s.content.strip()],
        ai_suggestion=ai_suggestion, ai_evaluation=ai_evaluation
    )

def result_to_json(result: HPUResult) -> str:
    return json.dumps(asdict(result), ensure_ascii=False, indent=2)
