import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple
from sqlalchemy import Date, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    AttendanceStatus,
    ClinicalAmendment,
    ComplaintStatus,
    Consultation,
    ConsultationStatus,
    Diagnosis,
    DiagnosisCode,
    FeedbackComplaint,
    HealthAwarenessSlide,
    LabOrder,
    LabOrderStatus,
    LabResult,
    Medication,
    Patient,
    PatientNotification,
    Prescription,
    PrescriptionItem,
    PrescriptionItemStatus,
    PrescriptionStatus,
    Referral,
    ReferralStatus,
    StaffAttendance,
    Vitals,
)


class HealthcareRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Patient Repository ---
    async def get_patient_by_id(self, patient_id: uuid.UUID) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.id == patient_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_patient_by_identifier(self, identifier: str) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.patient_identifier == identifier)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_patient_by_user_id(self, user_id: uuid.UUID) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_patient(self, patient: Patient) -> Patient:
        self.session.add(patient)
        await self.session.flush()
        return patient

    async def update_patient(self, patient: Patient) -> Patient:
        await self.session.flush()
        return patient

    async def search_patients(
        self,
        facility_id: Optional[uuid.UUID] = None,
        query: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[Patient], int]:
        stmt = select(Patient).where(Patient.is_active.is_(True))
        count_stmt = select(func.count(Patient.id)).where(Patient.is_active.is_(True))

        if facility_id:
            stmt = stmt.where(Patient.primary_facility_id == facility_id)
            count_stmt = count_stmt.where(Patient.primary_facility_id == facility_id)

        if query:
            pattern = f"%{query}%"
            filter_expr = or_(
                Patient.patient_identifier.ilike(pattern),
                Patient.phone_number.ilike(pattern),
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        stmt = stmt.order_by(Patient.created_at.desc()).offset(offset).limit(limit)

        records_res = await self.session.execute(stmt)
        count_res = await self.session.execute(count_stmt)

        return records_res.scalars().all(), count_res.scalar() or 0

    # --- Appointment Repository ---
    async def create_appointment(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        await self.session.flush()
        return appointment

    async def get_next_token_number(self, facility_id: uuid.UUID, appt_date: datetime) -> int:
        start_of_day = appt_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = appt_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        stmt = select(func.max(Appointment.token_number)).where(
            Appointment.facility_id == facility_id,
            Appointment.appointment_date >= start_of_day,
            Appointment.appointment_date <= end_of_day,
        )
        res = await self.session.execute(stmt)
        max_token = res.scalar()
        if max_token and max_token >= 501:
            return max_token + 1
        return 501

    async def get_appointment_by_id(self, appointment_id: uuid.UUID) -> Optional[Appointment]:
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_appointments(
        self,
        facility_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
        doctor_id: Optional[uuid.UUID] = None,
        status: Optional[AppointmentStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[Appointment], int]:
        stmt = select(Appointment)
        count_stmt = select(func.count(Appointment.id))

        if facility_id:
            stmt = stmt.where(Appointment.facility_id == facility_id)
            count_stmt = count_stmt.where(Appointment.facility_id == facility_id)
        if patient_id:
            stmt = stmt.where(Appointment.patient_id == patient_id)
            count_stmt = count_stmt.where(Appointment.patient_id == patient_id)
        if doctor_id:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
            count_stmt = count_stmt.where(Appointment.doctor_id == doctor_id)
        if status:
            stmt = stmt.where(Appointment.status == status)
            count_stmt = count_stmt.where(Appointment.status == status)

        stmt = stmt.order_by(Appointment.appointment_date.desc()).offset(offset).limit(limit)

        records_res = await self.session.execute(stmt)
        count_res = await self.session.execute(count_stmt)

        return records_res.scalars().all(), count_res.scalar() or 0

    # --- Consultation Repository ---
    async def create_consultation(self, consultation: Consultation) -> Consultation:
        self.session.add(consultation)
        await self.session.flush()
        return consultation

    async def get_consultation_by_id(self, consultation_id: uuid.UUID) -> Optional[Consultation]:
        stmt = (
            select(Consultation)
            .where(Consultation.id == consultation_id)
            .options(
                selectinload(Consultation.diagnoses),
                selectinload(Consultation.prescriptions).selectinload(Prescription.items),
                selectinload(Consultation.lab_orders).selectinload(LabOrder.results),
                selectinload(Consultation.referrals),
                selectinload(Consultation.vitals_records),
                selectinload(Consultation.amendments),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_consultation_by_appointment(self, appointment_id: uuid.UUID) -> Optional[Consultation]:
        stmt = (
            select(Consultation)
            .where(Consultation.appointment_id == appointment_id)
            .options(
                selectinload(Consultation.diagnoses),
                selectinload(Consultation.prescriptions).selectinload(Prescription.items),
                selectinload(Consultation.lab_orders).selectinload(LabOrder.results),
                selectinload(Consultation.referrals),
                selectinload(Consultation.vitals_records),
                selectinload(Consultation.amendments),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_consultations_by_patient(self, patient_id: uuid.UUID) -> Sequence[Consultation]:
        stmt = (
            select(Consultation)
            .where(Consultation.patient_id == patient_id)
            .options(
                selectinload(Consultation.diagnoses),
                selectinload(Consultation.prescriptions).selectinload(Prescription.items),
                selectinload(Consultation.lab_orders).selectinload(LabOrder.results),
                selectinload(Consultation.referrals),
                selectinload(Consultation.vitals_records),
                selectinload(Consultation.amendments),
            )
            .order_by(Consultation.started_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def add_diagnosis(self, diagnosis: Diagnosis) -> Diagnosis:
        self.session.add(diagnosis)
        await self.session.flush()
        return diagnosis

    # --- Prescription Repository ---
    async def create_prescription(self, prescription: Prescription) -> Prescription:
        self.session.add(prescription)
        await self.session.flush()
        return prescription

    async def get_prescription_by_id(self, prescription_id: uuid.UUID) -> Optional[Prescription]:
        stmt = (
            select(Prescription)
            .where(Prescription.id == prescription_id)
            .options(selectinload(Prescription.items))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_prescriptions(
        self,
        facility_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
        status: Optional[PrescriptionStatus] = None,
        doctor_id: Optional[uuid.UUID] = None,
    ) -> Sequence[Prescription]:
        stmt = select(Prescription).options(
            selectinload(Prescription.items),
            selectinload(Prescription.consultation).selectinload(Consultation.doctor),
        )
        stmt = self._prescription_filters(stmt, facility_id, patient_id, status, doctor_id)
        stmt = stmt.order_by(Prescription.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    def _prescription_filters(stmt, facility_id, patient_id, status, doctor_id):
        if facility_id:
            stmt = stmt.where(Prescription.facility_id == facility_id)
        if patient_id:
            stmt = stmt.where(Prescription.patient_id == patient_id)
        if status:
            stmt = stmt.where(Prescription.status == status)
        if doctor_id:
            stmt = stmt.where(Prescription.doctor_id == doctor_id)
        return stmt

    async def list_prescriptions_paginated(
        self,
        facility_id: Optional[uuid.UUID],
        patient_id: Optional[uuid.UUID],
        status: Optional[PrescriptionStatus],
        doctor_id: Optional[uuid.UUID],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[Prescription], int]:
        base = self._prescription_filters(select(Prescription), facility_id, patient_id, status, doctor_id)
        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        stmt = (
            base.options(selectinload(Prescription.items))
            .order_by(Prescription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all(), total

    # --- Lab Orders Repository ---
    async def create_lab_order(self, order: LabOrder) -> LabOrder:
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_lab_order_by_id(self, order_id: uuid.UUID) -> Optional[LabOrder]:
        stmt = (
            select(LabOrder)
            .where(LabOrder.id == order_id)
            .options(
                selectinload(LabOrder.results),
                selectinload(LabOrder.patient),
                selectinload(LabOrder.doctor),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_lab_orders(
        self,
        facility_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
        status: Optional[LabOrderStatus] = None,
    ) -> Sequence[LabOrder]:
        stmt = select(LabOrder).options(
            selectinload(LabOrder.results),
            selectinload(LabOrder.patient),
            selectinload(LabOrder.doctor),
        )
        if facility_id:
            stmt = stmt.where(LabOrder.facility_id == facility_id)
        if patient_id:
            stmt = stmt.where(LabOrder.patient_id == patient_id)
        if status:
            stmt = stmt.where(LabOrder.status == status)
        stmt = stmt.order_by(LabOrder.ordered_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_lab_orders_paginated(
        self,
        facility_id: Optional[uuid.UUID],
        patient_id: Optional[uuid.UUID],
        status: Optional[LabOrderStatus],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[LabOrder], int]:
        base = select(LabOrder)
        if facility_id:
            base = base.where(LabOrder.facility_id == facility_id)
        if patient_id:
            base = base.where(LabOrder.patient_id == patient_id)
        if status:
            base = base.where(LabOrder.status == status)
        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        stmt = (
            base.options(selectinload(LabOrder.results))
            .order_by(LabOrder.ordered_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all(), total

    async def list_lab_worklist(
        self,
        facility_id: uuid.UUID,
        status: Optional[LabOrderStatus] = None,
        test_category: Optional[str] = None,
    ) -> Sequence[LabOrder]:
        stmt = (
            select(LabOrder)
            .where(LabOrder.facility_id == facility_id)
            .options(
                selectinload(LabOrder.results),
                selectinload(LabOrder.patient),
                selectinload(LabOrder.doctor),
            )
        )
        if status:
            stmt = stmt.where(LabOrder.status == status)
        if test_category:
            stmt = stmt.where(LabOrder.test_category == test_category)
        stmt = stmt.order_by(LabOrder.ordered_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def add_lab_result(self, result: LabResult) -> LabResult:
        self.session.add(result)
        await self.session.flush()
        return result

    # --- Referral Repository ---
    async def create_referral(self, referral: Referral) -> Referral:
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def get_referral_by_id(self, referral_id: uuid.UUID) -> Optional[Referral]:
        stmt = select(Referral).where(Referral.id == referral_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_referrals(
        self,
        from_facility_id: Optional[uuid.UUID] = None,
        to_facility_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
    ) -> Sequence[Referral]:
        stmt = select(Referral)
        if from_facility_id:
            stmt = stmt.where(Referral.from_facility_id == from_facility_id)
        if to_facility_id:
            stmt = stmt.where(Referral.to_facility_id == to_facility_id)
        if patient_id:
            stmt = stmt.where(Referral.patient_id == patient_id)
        stmt = stmt.order_by(Referral.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # --- Vitals Repository ---
    async def create_vitals(self, vitals: Vitals) -> Vitals:
        self.session.add(vitals)
        await self.session.flush()
        return vitals

    async def list_vitals_by_consultation(self, consultation_id: uuid.UUID) -> Sequence[Vitals]:
        stmt = select(Vitals).where(Vitals.consultation_id == consultation_id).order_by(Vitals.recorded_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # --- Clinical Amendment Repository ---
    async def create_amendment(self, amendment: ClinicalAmendment) -> ClinicalAmendment:
        self.session.add(amendment)
        await self.session.flush()
        return amendment

    async def list_amendments_by_consultation(self, consultation_id: uuid.UUID) -> Sequence[ClinicalAmendment]:
        stmt = select(ClinicalAmendment).where(ClinicalAmendment.consultation_id == consultation_id).order_by(ClinicalAmendment.created_at.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # --- Reference Data Repositories ---
    async def create_medication(self, medication: Medication) -> Medication:
        self.session.add(medication)
        await self.session.flush()
        return medication

    async def get_medication_by_id(self, med_id: uuid.UUID) -> Optional[Medication]:
        stmt = select(Medication).where(Medication.id == med_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_medications(self, active_only: bool = True) -> Sequence[Medication]:
        stmt = select(Medication)
        if active_only:
            stmt = stmt.where(Medication.is_active.is_(True))
        stmt = stmt.order_by(Medication.generic_name.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create_diagnosis_code(self, diag_code: DiagnosisCode) -> DiagnosisCode:
        self.session.add(diag_code)
        await self.session.flush()
        return diag_code

    async def get_diagnosis_code_by_code(self, code: str) -> Optional[DiagnosisCode]:
        stmt = select(DiagnosisCode).where(DiagnosisCode.code == code)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # --- Feedback & Complaints Repository ---
    async def create_feedback_complaint(self, complaint: FeedbackComplaint) -> FeedbackComplaint:
        self.session.add(complaint)
        await self.session.flush()
        return complaint

    async def get_feedback_complaint_by_tracking(self, tracking_number: str) -> Optional[FeedbackComplaint]:
        stmt = (
            select(FeedbackComplaint)
            .where(FeedbackComplaint.tracking_number == tracking_number)
            .options(selectinload(FeedbackComplaint.patient), selectinload(FeedbackComplaint.facility))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_feedback_complaint_by_id(self, complaint_id: uuid.UUID) -> Optional[FeedbackComplaint]:
        stmt = (
            select(FeedbackComplaint)
            .where(FeedbackComplaint.id == complaint_id)
            .options(selectinload(FeedbackComplaint.patient), selectinload(FeedbackComplaint.facility))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_feedback_complaints_by_patient(self, patient_id: uuid.UUID) -> Sequence[FeedbackComplaint]:
        stmt = (
            select(FeedbackComplaint)
            .where(FeedbackComplaint.patient_id == patient_id)
            .options(selectinload(FeedbackComplaint.facility))
            .order_by(FeedbackComplaint.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_feedback_complaints(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[ComplaintStatus] = None,
    ) -> Sequence[FeedbackComplaint]:
        stmt = select(FeedbackComplaint).options(
            selectinload(FeedbackComplaint.patient),
            selectinload(FeedbackComplaint.facility),
        )
        if facility_id:
            stmt = stmt.where(FeedbackComplaint.facility_id == facility_id)
        if status:
            stmt = stmt.where(FeedbackComplaint.status == status)
        stmt = stmt.order_by(FeedbackComplaint.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # --- Patient Notifications Repository ---
    async def create_patient_notification(self, notification: PatientNotification) -> PatientNotification:
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def list_patient_notifications(self, patient_id: uuid.UUID) -> Sequence[PatientNotification]:
        stmt = (
            select(PatientNotification)
            .where(PatientNotification.patient_id == patient_id)
            .order_by(PatientNotification.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_patient_notification(
        self, notification_id: uuid.UUID, patient_id: uuid.UUID
    ) -> Optional[PatientNotification]:
        stmt = select(PatientNotification).where(
            PatientNotification.id == notification_id,
            PatientNotification.patient_id == patient_id,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # --- Health Awareness Slides Repository ---
    async def list_health_awareness_slides(
        self, category: Optional[str] = None, active_only: bool = True
    ) -> Sequence[HealthAwarenessSlide]:
        stmt = select(HealthAwarenessSlide)
        if active_only:
            stmt = stmt.where(HealthAwarenessSlide.is_active.is_(True))
        if category:
            stmt = stmt.where(HealthAwarenessSlide.category == category)
        stmt = stmt.order_by(HealthAwarenessSlide.display_order.asc(), HealthAwarenessSlide.created_at.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create_health_awareness_slide(self, slide: HealthAwarenessSlide) -> HealthAwarenessSlide:
        self.session.add(slide)
        await self.session.flush()
        return slide

    # --- Staff Duty Attendance Repository ---
    async def record_staff_check_in(self, attendance: StaffAttendance) -> StaffAttendance:
        self.session.add(attendance)
        await self.session.flush()
        return attendance

    async def get_staff_attendance_by_date(
        self, user_id: uuid.UUID, shift_date: date
    ) -> Optional[StaffAttendance]:
        stmt = select(StaffAttendance).where(
            StaffAttendance.user_id == user_id,
            StaffAttendance.attendance_date == shift_date,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_staff_attendance(
        self, facility_id: uuid.UUID, shift_date: Optional[date] = None
    ) -> Sequence[StaffAttendance]:
        stmt = select(StaffAttendance).where(StaffAttendance.facility_id == facility_id)
        if shift_date:
            stmt = stmt.where(StaffAttendance.attendance_date == shift_date)
        stmt = stmt.order_by(StaffAttendance.check_in_time.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # --- Doctor & Nurse Priority OPD Queue ---
    async def list_opd_queue(
        self,
        facility_id: uuid.UUID,
        target_date: date,
        doctor_id: Optional[uuid.UUID] = None,
        statuses: Optional[List[AppointmentStatus]] = None,
    ) -> Sequence[Appointment]:
        """
        Retrieves priority-triage sorted OPD appointments for doctor/nurse dashboard.
        Triage order: EMERGENCY (1) -> PRIORITY (2) -> ROUTINE (3), then sequential token_number.
        """
        if statuses is None:
            statuses = [
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CHECKED_IN,
                AppointmentStatus.IN_CONSULTATION,
            ]

        priority_order = case(
            (Appointment.priority == "EMERGENCY", 1),
            (Appointment.priority == "PRIORITY", 2),
            else_=3,
        )

        start_of_day = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)

        stmt = (
            select(Appointment)
            .where(
                Appointment.facility_id == facility_id,
                Appointment.appointment_date >= start_of_day,
                Appointment.appointment_date < end_of_day,
                Appointment.status.in_(statuses),
            )
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.consultation).selectinload(Consultation.vitals_records),
            )
        )

        if doctor_id:
            # Allow appointment assigned to this doctor or unassigned (general queue)
            stmt = stmt.where(
                or_(Appointment.doctor_id == doctor_id, Appointment.doctor_id.is_(None))
            )

        stmt = stmt.order_by(priority_order, Appointment.token_number.asc().nullslast(), Appointment.appointment_date.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()


