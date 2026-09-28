# AI & Analytics Architecture: Explainable Intelligence & Decision Support

## 1. Architectural Philosophy
Following Sections 27-32 and 58 of the Platform Specification:
- **No Fake AI**: Intelligence operates strictly on real database transactions and observable physical events.
- **Explainability**: Every prediction, risk score, and recommendation includes mathematical basis and natural language explanation.
- **Human-in-the-Loop Oversight**: AI is an advisory decision-support layer, never executing unilateral procurement, transfers, or clinical treatment without human review.
- **Zero Scope Bypass**: AI assistant endpoints enforce user authorization scope (`GLOBAL`, `STATE`, `DISTRICT`, `FACILITY`, `SELF`).

## 2. Core Capabilities

### A. Demand Forecasting & Stockout Risk Prediction
- **Historical Consumption Calculation**: Rolling 30-day dispensing volume from immutable `StockMovement` ledger.
- **Average Daily Consumption**: $\text{Rate} = \frac{\sum \text{Dispensed Quantity}}{30}$.
- **Days of Supply Remaining**: $\text{Days} = \frac{\text{Available Stock}}{\text{Rate}}$.
- **Risk Tiers**:
  - `CRITICAL`: Available quantity is 0 or supply $\le 7$ days.
  - `HIGH`: Supply $\le 15$ days or available quantity $\le$ `minimum_stock_level`.
  - `MEDIUM`: Supply $\le 30$ days or available quantity $\le$ `reorder_level`.
  - `LOW`: Healthy supply buffer $> 30$ days.
- **Confidence Scoring**: Based on historical event density (ranges from 0.40 for sparse data to 0.95 for mature transactional data).

### B. Supply Chain Anomaly Detection
- **Consumption Spikes**: Detects single dispensing transactions $\ge 50$ units or $> 3\times$ typical variance.
- **Unusual Stock Loss**: Flags damage and expiry adjustments exceeding threshold ($\ge 15$ units) with operator notes.

### C. Inter-Facility Transfer Recommendations
- Correlates facilities facing `CRITICAL` or `HIGH` shortage risk with nearby facilities or warehouses maintaining surplus ($> 1.5\times$ reorder level).
- Recommends balanced rebalancing quantities with rationale.

### D. Unified AI Assistant
- Natural language query parser mapping user intent to live data retrieval:
  - `SHORTAGE_RISK`: Low stock and stockout queries.
  - `EXPIRING_BATCHES`: Batches expiring within 60 days for FEFO prioritization.
  - `STOCK_TRANSFERS`: In-transit shipments and transfer statuses.
  - `ANOMALY_DETECTION`: Unusual spikes and loss events.
  - `OPERATIONAL_SUMMARY`: Facility health overview.
- Returns structured JSON with query, intent, answer, evidence payload, confidence score, and clinical advisory disclaimer.

## 3. API Endpoints
- `GET /api/v1/analytics/demand-forecast`: Facility demand forecast and stockout dates.
- `GET /api/v1/analytics/anomalies`: Anomaly detection for spikes and loss.
- `GET /api/v1/analytics/transfer-recommendations`: Automated inter-facility transfer matching.
- `POST /api/v1/ai/assistant/query`: Unified scope-aware conversational assistant.
