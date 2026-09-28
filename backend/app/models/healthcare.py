import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class ConsultationStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    FINALIZED = "FINALIZED"
    CANCELLED = "CANCELLED"


class DiagnosisType(str, enum.Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    PROVISIONAL = "PROVISIONAL"


class PrescriptionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_DISPENSED = "PARTIALLY_DISPENSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PrescriptionItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPENSED = "DISPENSED"
    CANCELLED = "CANCELLED"


class LabOrderStatus(str, enum.Enum):
    ORDERED = "ORDERED"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    IN_ANALYSIS = "IN_ANALYSIS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ReferralUrgency(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Patient(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        index=True,
        nullable=True,
    )
    primary_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    patient_identifier: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    chronic_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    primary_facility = relationship("Facility")
    user = relationship("User")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    consultations = relationship("Consultation", back_populates="patient", cascade="all, delete-orphan")

    @property
    def facility_id(self) -> uuid.UUID:
        return self.primary_facility_id

    @facility_id.setter
    def facility_id(self, val: uuid.UUID):
        self.primary_facility_id = val

    def __init__(self, **kwargs):
        if "facility_id" in kwargs and "primary_facility_id" not in kwargs:
            kwargs["primary_facility_id"] = kwargs.pop("facility_id")
        super().__init__(**kwargs)


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    token_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        index=True,
        nullable=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default="ROUTINE",
        nullable=False,
    )
    time_slot: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status_enum"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    facility = relationship("Facility")
    doctor = relationship("User")
    consultation = relationship("Consultation", back_populates="appointment", uselist=False)


class Consultation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "consultations"

    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus, name="consultation_status_enum"),
        default=ConsultationStatus.IN_PROGRESS,
        nullable=False,
    )
    triage_vitals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examination_findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    appointment = relationship("Appointment", back_populates="consultation")
    patient = relationship("Patient", back_populates="consultations")
    doctor = relationship("User")
    facility = relationship("Facility")
    diagnoses = relationship("Diagnosis", back_populates="consultation", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="consultation", cascade="all, delete-orphan")
    lab_orders = relationship("LabOrder", back_populates="consultation", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="consultation", cascade="all, delete-orphan")
    vitals_records = relationship("Vitals", back_populates="consultation", cascade="all, delete-orphan")
    amendments = relationship("ClinicalAmendment", back_populates="consultation", cascade="all, delete-orphan")



class Diagnosis(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "diagnoses"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    icd10_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosis_type: Mapped[DiagnosisType] = mapped_column(
        Enum(DiagnosisType, name="diagnosis_type_enum"),
        default=DiagnosisType.PRIMARY,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    consultation = relationship("Consultation", back_populates="diagnoses")


class Prescription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prescriptions"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus, name="prescription_status_enum"),
        default=PrescriptionStatus.ISSUED,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    consultation = relationship("Consultation", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    patient = relationship("Patient")
    doctor = relationship("User")
    facility = relationship("Facility")


class PrescriptionItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    medication_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_prescribed: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_dispensed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medication_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[PrescriptionItemStatus] = mapped_column(
        Enum(PrescriptionItemStatus, name="prescription_item_status_enum"),
        default=PrescriptionItemStatus.PENDING,
        nullable=False,
    )

    prescription = relationship("Prescription", back_populates="items")
    medication = relationship("Medication")



class LabOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_orders"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ordered_by_doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    test_category: Mapped[str] = mapped_column(String(100), nullable=False)
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sample_barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sample_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[LabOrderStatus] = mapped_column(
        Enum(LabOrderStatus, name="lab_order_status_enum"),
        default=LabOrderStatus.ORDERED,
        nullable=False,
    )
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    consultation = relationship("Consultation", back_populates="lab_orders")
    results = relationship("LabResult", back_populates="lab_order", cascade="all, delete-orphan")
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[ordered_by_doctor_id])
    facility = relationship("Facility")


class LabResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_results"

    lab_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    result_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    critical_alert: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    lab_order = relationship("LabOrder", back_populates="results")
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])


class Referral(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "referrals"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    from_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    to_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_facility_name: Mapped[str] = mapped_column(String(255), nullable=False)
    referral_reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[ReferralUrgency] = mapped_column(
        Enum(ReferralUrgency, name="referral_urgency_enum"),
        default=ReferralUrgency.ROUTINE,
        nullable=False,
    )
    clinical_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, name="referral_status_enum"),
        default=ReferralStatus.PENDING,
        nullable=False,
    )
    referred_by_doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    consultation = relationship("Consultation", back_populates="referrals")
    referred_by_doctor = relationship("User")


class Vitals(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vitals"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    systolic_bp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pulse_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spo2_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    triage_level: Mapped[Optional[str]] = mapped_column(String(20), default="ROUTINE", nullable=True)
    triage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    consultation = relationship("Consultation", back_populates="vitals_records")
    recorded_by = relationship("User")


class ClinicalAmendment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "clinical_amendments"

    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amendment_reason: Mapped[str] = mapped_column(Text, nullable=False)
    amendment_notes: Mapped[str] = mapped_column(Text, nullable=False)
    amended_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    consultation = relationship("Consultation", back_populates="amendments")
    amended_by = relationship("User")


class DiagnosisCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "diagnosis_codes"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="ICD-10", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Medication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medications"

    generic_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    strength: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage_form: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def name(self) -> str:
        return self.generic_name

    def __init__(self, **kwargs):
        if "name" in kwargs and "generic_name" not in kwargs:
            kwargs["generic_name"] = kwargs.pop("name")
        if "code" in kwargs:
            if "brand_name" not in kwargs:
                kwargs["brand_name"] = kwargs.pop("code")
            else:
                kwargs.pop("code")
        if "route" not in kwargs:
            kwargs["route"] = "Oral"
        if "unit" not in kwargs:
            kwargs["unit"] = "Unit"
        super().__init__(**kwargs)


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class FeedbackComplaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "feedback_complaints"

    tracking_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # "SERVICE", "FACILITY", "APPOINTMENT", "MEDICINE", "OTHER"
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status_enum"),
        default=ComplaintStatus.SUBMITTED,
        nullable=False,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient")
    facility = relationship("Facility")


class PatientNotification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patient_notifications"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ta: Mapped[str] = mapped_column(String(200), nullable=False)
    message_en: Mapped[str] = mapped_column(Text, nullable=False)
    message_ta: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), default="INFO", nullable=False)  # "APPOINTMENT", "PRESCRIPTION", "HEALTH_TIP", "REMINDER"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    patient = relationship("Patient")


class HealthAwarenessSlide(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "health_awareness_slides"

    category: Mapped[str] = mapped_column(String(50), nullable=False)  # "EXERCISE", "NUTRITION", "HYDRATION_SLEEP", "MENTAL_WELLNESS", "HYGIENE", "DISEASE_PREVENTION", "VACCINATION", "WARNING_SIGNS"
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_ta: Mapped[str] = mapped_column(String(200), nullable=False)
    tip_en: Mapped[str] = mapped_column(Text, nullable=False)
    tip_ta: Mapped[str] = mapped_column(Text, nullable=False)
    motivation_en: Mapped[str] = mapped_column(Text, nullable=False)
    motivation_ta: Mapped[str] = mapped_column(Text, nullable=False)
    action_en: Mapped[str] = mapped_column(Text, nullable=False)
    action_ta: Mapped[str] = mapped_column(Text, nullable=False)
    image_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    ON_DUTY_CAMP = "ON_DUTY_CAMP"


class StaffAttendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "staff_attendance"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status_enum"),
        default=AttendanceStatus.PRESENT,
        nullable=False,
    )
    shift: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)  # "MORNING", "EVENING", "NIGHT", "GENERAL"
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User")
    facility = relationship("Facility")


class ColdChainEquipment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cold_chain_equipments"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    equipment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "ILR", "DEEP_FREEZER", "COLD_BOX"
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_temp_c: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    max_temp_c: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    current_temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_logged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_functional: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_temperature_in_range: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    facility = relationship("Facility")
    logs = relationship("ColdChainLog", back_populates="equipment", cascade="all, delete-orphan")


class ColdChainLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cold_chain_logs"

    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cold_chain_equipments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    is_excursion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    excursion_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    equipment = relationship("ColdChainEquipment", back_populates="logs")
    recorded_by = relationship("User")


class OutreachCamp(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "outreach_camps"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    camp_name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_village: Mapped[str] = mapped_column(String(100), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    supervisor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False)
    target_beneficiaries: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    actual_beneficiaries_served: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    facility = relationship("Facility")
    supervisor = relationship("User")


