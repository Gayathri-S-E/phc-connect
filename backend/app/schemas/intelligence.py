import uuid
from datetime import date, datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.intelligence import AlertSeverity, AlertType


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    is_acknowledged: bool
    acknowledged_by: Optional[uuid.UUID] = None
    created_at: datetime


class AlertAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: Optional[str] = Field(default=None, max_length=1000)


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: Optional[uuid.UUID] = None
    medication_id: Optional[uuid.UUID] = None
    horizon_days: Literal[30, 60, 90] = 30


class ForecastItem(BaseModel):
    medication_id: uuid.UUID
    medication_name: str
    current_stock: int
    avg_daily_consumption: float
    horizon_days: int
    predicted_consumption: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    projected_shortfall: int
    predicted_stockout_date: Optional[date] = None
    risk_level: str
    confidence: float
    explainability: str


class ForecastResponse(BaseModel):
    facility_id: uuid.UUID
    forecast_date: date
    horizon_days: int
    items: List[ForecastItem]
    disclaimer: str


class RiskAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: Optional[uuid.UUID] = None


class RiskFactor(BaseModel):
    factor: str
    value: float
    weight: float
    contribution: float
    explanation: str


class RiskAnalysisResponse(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    risk_score: float
    risk_level: str
    factors: List[RiskFactor]
    recommendations: List[str]
    generated_at: datetime
    disclaimer: str


class PHCDashboardResponse(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    as_of: datetime
    appointments_today: int
    appointments_by_status: Dict[str, int]
    consultations_today: int
    pending_prescriptions: int
    pending_lab_orders: int
    low_stock_items: int
    stockout_items: int
    batches_expiring_30d: int
    open_shortages: int
    unacknowledged_alerts: int


class FacilityStockSummary(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    district: str
    state: str
    items_tracked: int
    low_stock_items: int
    stockout_items: int
    open_shortages: int


class SupplyChainDashboardResponse(BaseModel):
    as_of: datetime
    scope: str
    facilities_in_scope: int
    total_low_stock_items: int
    total_stockout_items: int
    open_shortages_by_severity: Dict[str, int]
    transfers_by_status: Dict[str, int]
    purchase_orders_by_status: Dict[str, int]
    shipments_by_status: Dict[str, int]
    unacknowledged_alerts: int
    facilities: List[FacilityStockSummary]
