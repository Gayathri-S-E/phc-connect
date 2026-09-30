"""Compact, minimised views of clinical records for the model. Shared by Patient and Doctor assistants.

Only fields the assistant needs are exposed: no phone numbers, addresses or emergency contacts.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso(dt: Optional[datetime]) -> Optional[str]:
    return aware(dt).isoformat() if dt else None


def _vitals(v: Any) -> Dict[str, Any]:
    return {
        "recorded_at": iso(v.recorded_at), "bp": f"{v.systolic_bp}/{v.diastolic_bp}" if v.systolic_bp and v.diastolic_bp else None,
        "pulse": v.pulse_rate, "temperature_c": v.temperature_celsius, "resp_rate": v.respiratory_rate,
        "spo2_percent": v.spo2_percent, "weight_kg": v.weight_kg, "height_cm": v.height_cm, "bmi": v.bmi,
    }


def _lab(order: Any) -> Dict[str, Any]:
    return {
        "test": order.test_category, "status": order.status.value, "ordered_at": iso(order.ordered_at),
        "completed_at": iso(order.completed_at),
        "results": [{
            "test": r.test_name, "value": r.result_value, "unit": r.unit, "reference_range": r.reference_range,
            "flagged_abnormal_by_lab": r.is_abnormal, "verified_by_lab_staff": r.verified_by_id is not None,
        } for r in order.results],
    }


def consultation_view(c: Any, *, with_gaps: bool = False) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "consultation_id": str(c.id), "date": iso(c.started_at), "status": c.status.value,
        "chief_complaint": c.chief_complaint, "clinical_notes": c.clinical_notes,
        "examination_findings": c.examination_findings,
        "diagnoses": [{"icd10": d.icd10_code, "name": d.condition_name, "type": d.diagnosis_type.value} for d in c.diagnoses],
        "vitals": [_vitals(v) for v in c.vitals_records],
        "lab_orders": [_lab(o) for o in c.lab_orders],
        "prescriptions": [{
            "prescription_id": str(p.id), "status": p.status.value, "notes": p.notes,
            "items": [{"medicine": i.medication_name, "dosage": i.dosage, "frequency": i.frequency,
                       "duration_days": i.duration_days, "instructions": i.instructions} for i in p.items],
        } for p in c.prescriptions],
        "referrals": [{"referral_id": str(r.id), "to": r.to_facility_name, "reason": r.referral_reason,
                       "urgency": r.urgency.value, "status": r.status.value} for r in c.referrals],
    }
    if with_gaps:
        gaps: List[str] = []
        if not c.clinical_notes:
            gaps.append("clinical_notes")
        if not c.examination_findings:
            gaps.append("examination_findings")
        if not c.diagnoses:
            gaps.append("diagnoses")
        if not c.vitals_records and not c.triage_vitals:
            gaps.append("vitals")
        out["missing_fields"] = gaps
    return out
