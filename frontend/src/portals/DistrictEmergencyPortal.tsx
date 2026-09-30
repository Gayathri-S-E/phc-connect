import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, AlertTriangle, CheckCircle, Clock, 
  Plus, Users, MapPin, Send, FileText, ChevronRight, 
  Activity, Truck, Check, HelpCircle, AlertOctagon, Flame
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function DistrictEmergencyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'dashboard' | 'incidents' | 'tasks' | 'resources' => {
    if (path.includes('/incidents')) return 'incidents';
    if (path.includes('/tasks')) return 'tasks';
    if (path.includes('/resources')) return 'resources';
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState<'dashboard' | 'incidents' | 'tasks' | 'resources'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'dashboard' | 'incidents' | 'tasks' | 'resources') => {
    setActiveTab(tab);
    if (tab === 'dashboard') navigate('/emergency');
    else navigate(`/emergency/${tab}`);
  };
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Emergency Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);

  // New Incident Declaration State
  const [isDeclareModalOpen, setIsDeclareModalOpen] = useState(false);
  const [declareTitle, setDeclareTitle] = useState('');
  const [declareCategory, setDeclareCategory] = useState('DISEASE_CLUSTER');
  const [declareSeverity, setDeclareSeverity] = useState('MAJOR');
  const [declareArea, setDeclareArea] = useState('District South Sub-division');
  const [declareDescription, setDeclareDescription] = useState('');

  // Priority Setting State
  const [isPriorityModalOpen, setIsPriorityModalOpen] = useState(false);
  const [priorityLevel, setPriorityLevel] = useState('CRITICAL');
  const [priorityReason, setPriorityReason] = useState('');

  // Status Update State
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [incidentStatus, setIncidentStatus] = useState('CONTAINED');
  const [statusNotes, setStatusNotes] = useState('');

  // Task Creation State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskAssignedTo, setTaskAssignedTo] = useState('');

  // Emergency Resource Request State
  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false);
  const [resourceMedId, setResourceMedId] = useState('');
  const [resourceQty, setResourceQty] = useState(100);
  const [resourceReason, setResourceReason] = useState('');
  const [medications, setMedications] = useState<any[]>([]);

  // Resolution State
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionSummary, setResolutionSummary] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchEmergencyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, incRes, medsRes] = await Promise.all([
        api.get<any>('/emergencies/dashboard').catch(() => ({ data: null })),
        api.get<any>('/emergencies?page_size=50').catch(() => ({ data: [] })),
        api.get<any[]>('/medications').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (incRes?.data) {
        const list = Array.isArray(incRes.data) ? incRes.data : incRes.data.items || [];
        setIncidents(list);
        if (list.length > 0 && !selectedIncident) {
          setSelectedIncident(list[0]);
        }
      }
      if (medsRes?.data) {
        setMedications(medsRes.data);
        if (medsRes.data.length > 0 && !resourceMedId) {
          setResourceMedId(medsRes.data[0].id);
        }
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load emergency coordination data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmergencyData();
  }, []);

  // Declare Emergency Incident
  const handleDeclareEmergency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!declareTitle.trim()) return;
    setIsSubmitting(true);
    try {
      await api.post('/emergencies', {
        emergency_type: declareCategory || 'DISEASE_CLUSTER',
        title: declareTitle,
        description: declareDescription || declareTitle,
        affected_area: declareArea || 'District Jurisdiction',
        source: 'District Emergency Operations Center (EOC)',
        affected_facility_ids: [],
      });
      setActionSuccess('Emergency incident declared & broadcasted to district control');
      setIsDeclareModalOpen(false);
      setDeclareTitle('');
      setDeclareDescription('');
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to declare emergency');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Set Priority
  const handleSetPriority = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;
    setIsSubmitting(true);
    try {
      await api.post(`/emergencies/${selectedIncident.id}/priority`, {
        priority: priorityLevel,
        reason: priorityReason || 'Human adjudication by District Emergency Coordinator',
      });
      setActionSuccess(`Incident priority set to ${priorityLevel}`);
      setIsPriorityModalOpen(false);
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to set priority');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Update Status
  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;
    setIsSubmitting(true);
    try {
      await api.post(`/emergencies/${selectedIncident.id}/status`, {
        status: incidentStatus,
        note: statusNotes || 'Status updated by Coordinator',
      });
      setActionSuccess(`Incident status updated to ${incidentStatus}`);
      setIsStatusModalOpen(false);
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to update status');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create Task
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;
    setIsSubmitting(true);
    try {
      await api.post(`/emergencies/${selectedIncident.id}/tasks`, {
        assigned_role: taskTitle || 'EMERGENCY_RESPONSE_OFFICER',
        description: taskDescription || 'Rapid response task for deployed emergency team',
        assigned_user_id: taskAssignedTo || undefined,
        facility_id: selectedIncident.affected_facilities?.[0]?.facility_id || undefined,
      });
      setActionSuccess('Rapid response task dispatched');
      setIsTaskModalOpen(false);
      setTaskTitle('');
      setTaskDescription('');
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to dispatch task');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Emergency Resource Request to DSCO
  const handleRequestResources = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;
    const targetFacilityId = selectedIncident.affected_facilities?.[0]?.facility_id || user?.facility_id;
    if (!targetFacilityId) {
      alert('Cannot issue emergency requisition without an assigned facility ID.');
      return;
    }
    setIsSubmitting(true);
    try {
      await api.post(`/emergencies/${selectedIncident.id}/resource-requests`, {
        facility_id: targetFacilityId,
        medication_id: resourceMedId,
        quantity: Number(resourceQty),
        reason: resourceReason || `Urgent mobilization for emergency incident: ${selectedIncident.title}`,
        priority: 'EMERGENCY',
      });
      setActionSuccess('Emergency requirement dispatched to District Supply Officer (DSCO)');
      setIsResourceModalOpen(false);
      setResourceReason('');
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to transmit resource request');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Resolve Emergency
  const handleResolveEmergency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;
    setIsSubmitting(true);
    try {
      await api.post(`/emergencies/${selectedIncident.id}/resolve`, {
        resolution_summary: resolutionSummary || 'All response tasks executed and community risk neutralized.',
        confirmation_reference: `EOC-RESOLVE-${Date.now()}`,
      });
      setActionSuccess('Incident formally marked as RESOLVED & debrief archived');
      setIsResolveModalOpen(false);
      setResolutionSummary('');
      fetchEmergencyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to resolve incident');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading District Emergency Command Centre..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchEmergencyData} />;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-red-900 via-rose-900 to-amber-950 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-rose-200 text-sm font-semibold tracking-wide uppercase">
              <ShieldAlert className="w-4 h-4" />
              <span>Role 08: District Emergency Coordinator (DEC)</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">District Emergency Operations & Incident Command</h1>
            <p className="text-rose-100 text-sm mt-1">
              Rapid epidemic response, natural disaster triage mobilization, and emergency supply channel orchestration.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsDeclareModalOpen(true)}
              className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg transition animate-pulse"
            >
              <Flame className="w-4 h-4" />
              Declare Emergency Incident
            </button>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-rose-200 hover:text-white text-xs font-bold uppercase">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-4 rounded-lg shadow-sm overflow-x-auto">
        <button
          onClick={() => handleTabChange('dashboard')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'dashboard'
              ? 'border-red-600 text-red-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Activity className="w-4 h-4" />
          Command Cockpit
        </button>
        <button
          onClick={() => handleTabChange('incidents')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'incidents'
              ? 'border-red-600 text-red-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertOctagon className="w-4 h-4" />
          Active Incident Command
          {incidents.filter(i => i.status !== 'RESOLVED').length > 0 && (
            <span className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {incidents.filter(i => i.status !== 'RESOLVED').length}
            </span>
          )}
        </button>
        <button
          onClick={() => handleTabChange('tasks')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'tasks'
              ? 'border-red-600 text-red-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Users className="w-4 h-4" />
          Field Tasks & Deployment
        </button>
        <button
          onClick={() => handleTabChange('resources')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'resources'
              ? 'border-red-600 text-red-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Truck className="w-4 h-4" />
          Emergency Supplies & Logistics
        </button>
      </div>

      {/* TAB 1: COMMAND COCKPIT */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Key KPI Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Emergencies</p>
                <h3 className="text-2xl font-black text-red-600 mt-1">{dashboardData?.active_count ?? incidents.length}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Under live coordination</span>
              </div>
              <div className="p-3 bg-red-50 text-red-600 rounded-lg">
                <AlertOctagon className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Affected Facilities</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.affected_facilities_count ?? 3}</h3>
                <span className="text-xs text-amber-600 font-medium mt-1 inline-block">Under emergency protocols</span>
              </div>
              <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                <MapPin className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Rapid Response Tasks</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.open_tasks_count ?? 8}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Field assignments dispatched</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Emergency Supply Indents</p>
                <h3 className="text-2xl font-bold text-purple-700 mt-1">{dashboardData?.emergency_requests_count ?? 2}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Transmitted to DSCO</span>
              </div>
              <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                <Truck className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Incidents Table */}
          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-gray-900">Active Incident Stream</h3>
            <DataTable
              data={incidents}
              keyField="id"
              emptyMessage="No emergency incidents currently active in this district."
              columns={[
                {
                  header: 'Incident Title',
                  accessor: (inc) => (
                    <div>
                      <div className="font-semibold text-gray-900">{inc.title}</div>
                      <div className="text-xs text-gray-500 font-mono">Category: {inc.category}</div>
                    </div>
                  ),
                },
                {
                  header: 'Priority',
                  accessor: (inc) => (
                    <Badge 
                      label={inc.priority || 'UNASSIGNED'} 
                      status={inc.priority === 'CRITICAL' ? 'danger' : inc.priority === 'HIGH' ? 'warning' : 'info'} 
                    />
                  ),
                },
                {
                  header: 'Status',
                  accessor: (inc) => (
                    <Badge 
                      label={inc.status} 
                      status={inc.status === 'RESOLVED' ? 'success' : inc.status === 'CONTAINED' ? 'info' : 'danger'} 
                    />
                  ),
                },
                {
                  header: 'Declared At',
                  accessor: (inc) => new Date(inc.created_at).toLocaleString(),
                },
                {
                  header: 'Command Actions',
                  accessor: (inc) => (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => {
                          setSelectedIncident(inc);
                          setIsPriorityModalOpen(true);
                        }}
                        className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded text-xs font-semibold"
                      >
                        Set Priority
                      </button>
                      <button
                        onClick={() => {
                          setSelectedIncident(inc);
                          setIsStatusModalOpen(true);
                        }}
                        className="px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-300 rounded text-xs font-semibold"
                      >
                        Status
                      </button>
                      {inc.status !== 'RESOLVED' && (
                        <button
                          onClick={() => {
                            setSelectedIncident(inc);
                            setIsResolveModalOpen(true);
                          }}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  ),
                },
              ]}
            />
          </div>
        </div>
      )}

      {/* TAB 2: ACTIVE INCIDENT COMMAND */}
      {activeTab === 'incidents' && (
        <div className="space-y-6">
          {selectedIncident ? (
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge 
                      label={selectedIncident.priority || 'UNASSIGNED'} 
                      status={selectedIncident.priority === 'CRITICAL' ? 'danger' : 'warning'} 
                    />
                    <Badge 
                      label={selectedIncident.status} 
                      status={selectedIncident.status === 'RESOLVED' ? 'success' : 'danger'} 
                    />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mt-2">{selectedIncident.title}</h3>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">Declared: {new Date(selectedIncident.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsTaskModalOpen(true)}
                    className="px-3.5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Dispatch Task
                  </button>
                  <button
                    onClick={() => setIsResourceModalOpen(true)}
                    className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
                  >
                    <Truck className="w-3.5 h-3.5" />
                    Mobilize Supplies
                  </button>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-gray-700 uppercase mb-1">Incident Situation Brief</h4>
                <p className="text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">
                  {selectedIncident.description}
                </p>
              </div>

              {/* Tasks within this incident */}
              <div>
                <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <Users className="w-4 h-4 text-red-600" />
                  Deployed Incident Response Tasks
                </h4>
                {selectedIncident.tasks?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedIncident.tasks.map((task: any) => (
                      <div key={task.id} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between text-xs">
                        <div>
                          <div className="font-semibold text-gray-900">{task.title}</div>
                          <div className="text-gray-500">{task.description}</div>
                        </div>
                        <Badge label={task.status || 'IN_PROGRESS'} status={task.status === 'COMPLETED' ? 'success' : 'warning'} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">No tasks currently assigned to this incident.</p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Select an incident from the Command Cockpit to manage operations.</p>
          )}
        </div>
      )}

      {/* TAB 3: FIELD TASKS & DEPLOYMENT */}
      {activeTab === 'tasks' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Rapid Response Tasks Register</h3>
              <p className="text-xs text-gray-500">Track field deployment of medical officers, paramedics, and mobile relief vans.</p>
            </div>
          </div>
          <p className="text-xs text-gray-600">Select any active incident from the Command Cockpit to assign new field duties.</p>
        </div>
      )}

      {/* TAB 4: EMERGENCY SUPPLIES */}
      {activeTab === 'resources' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Emergency Medicine Requisitions & Logistics</h3>
            <p className="text-xs text-gray-500">Requirements routed on high-priority emergency channel to District Supply Officer (DSCO).</p>
          </div>
          <p className="text-xs text-gray-600">
            Requisitions can be triggered directly from the active incident view and automatically bypass standard monthly quota reviews.
          </p>
        </div>
      )}

      {/* MODAL: Declare Emergency Incident */}
      <Modal
        isOpen={isDeclareModalOpen}
        onClose={() => setIsDeclareModalOpen(false)}
        title="Declare District Emergency Incident"
      >
        <form onSubmit={handleDeclareEmergency} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Incident Title</label>
            <input
              type="text"
              value={declareTitle}
              onChange={(e) => setDeclareTitle(e.target.value)}
              placeholder="e.g. Cyclone Michaung Coastal Inundation & Cholera Outbreak"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Emergency Type</label>
              <select
                value={declareCategory}
                onChange={(e) => setDeclareCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="DISEASE_CLUSTER">Disease Cluster / Epidemic</option>
                <option value="FLOOD">Flood Inundation</option>
                <option value="CYCLONE">Cyclone Storm Impact</option>
                <option value="HEATWAVE">Severe Heatwave</option>
                <option value="MASS_CASUALTY">Mass Casualty Incident</option>
                <option value="FIRE">Fire Outbreak</option>
                <option value="INFRASTRUCTURE_FAILURE">Infrastructure / Power Failure</option>
                <option value="OTHER">Other Critical Emergency</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Affected Area</label>
              <input
                type="text"
                value={declareArea}
                onChange={(e) => setDeclareArea(e.target.value)}
                placeholder="e.g. Chengalpattu Coastal Sub-division"
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Detailed Situation Report</label>
            <textarea
              value={declareDescription}
              onChange={(e) => setDeclareDescription(e.target.value)}
              placeholder="Describe geographical extent, impacted PHCs, estimated population vulnerable, and immediate needs"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-28"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsDeclareModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Declaring...' : 'Broadcast Emergency'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Set Priority */}
      <Modal
        isOpen={isPriorityModalOpen}
        onClose={() => setIsPriorityModalOpen(false)}
        title="Human Adjudication of Priority"
      >
        <form onSubmit={handleSetPriority} className="space-y-4">
          <p className="text-xs text-gray-600">
            Per system rules, AI never sets priority. An authorized human coordinator must evaluate and record justification.
          </p>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Priority Classification</label>
            <select
              value={priorityLevel}
              onChange={(e) => setPriorityLevel(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="ROUTINE">ROUTINE</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Recorded Reason / Rationale</label>
            <textarea
              value={priorityReason}
              onChange={(e) => setPriorityReason(e.target.value)}
              placeholder="Provide clinical or disaster management justification"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsPriorityModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Saving...' : 'Set Priority'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Update Incident Status */}
      <Modal
        isOpen={isStatusModalOpen}
        onClose={() => setIsStatusModalOpen(false)}
        title="Update Emergency Incident Status"
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Operational Status</label>
            <select
              value={incidentStatus}
              onChange={(e) => setIncidentStatus(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="ACTIVE">ACTIVE (Full response operational)</option>
              <option value="CONTAINED">CONTAINED (Spread or damage halted)</option>
              <option value="RESOLVED">RESOLVED (De-escalated)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Status Notes</label>
            <textarea
              value={statusNotes}
              onChange={(e) => setStatusNotes(e.target.value)}
              placeholder="Detail reasons for status transition"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsStatusModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Updating...' : 'Update Status'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Dispatch Task */}
      <Modal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        title="Dispatch Rapid-Response Task"
      >
        <form onSubmit={handleCreateTask} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Task Title</label>
            <input
              type="text"
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              placeholder="e.g. Deploy 2 Mobile Medical Units to Melmaruvathur"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Task Instructions</label>
            <textarea
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
              placeholder="Specify duties, required medical kits, and target location"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsTaskModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Dispatching...' : 'Dispatch Task'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Mobilize Emergency Supplies */}
      <Modal
        isOpen={isResourceModalOpen}
        onClose={() => setIsResourceModalOpen(false)}
        title="Emergency Requisition to District Supply Officer"
      >
        <form onSubmit={handleRequestResources} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Medicine / Supply</label>
            <select
              value={resourceMedId}
              onChange={(e) => setResourceMedId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            >
              {medications.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.strength})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Emergency Quantity</label>
            <input
              type="number"
              value={resourceQty}
              onChange={(e) => setResourceQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Urgency Justification</label>
            <textarea
              value={resourceReason}
              onChange={(e) => setResourceReason(e.target.value)}
              placeholder="State emergency justification for DSCO priority dispatch"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsResourceModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Transmitting...' : 'Dispatch Requisition'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Resolve Emergency */}
      <Modal
        isOpen={isResolveModalOpen}
        onClose={() => setIsResolveModalOpen(false)}
        title="Mark Emergency Incident as Resolved"
      >
        <form onSubmit={handleResolveEmergency} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">After-Action Summary & Resolution Debrief</label>
            <textarea
              value={resolutionSummary}
              onChange={(e) => setResolutionSummary(e.target.value)}
              placeholder="Summarize total patients treated, containment measures verified, and remaining follow-up instructions"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-28"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsResolveModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Archiving...' : 'Confirm Resolution'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
