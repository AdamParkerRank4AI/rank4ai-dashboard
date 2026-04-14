import { useState, useEffect, useRef } from 'react';
import { supabase, STAGES } from '../lib/supabase';

const STAGE_COLORS = {
  partial: { bg: 'bg-gray-800', border: 'border-gray-700', text: 'text-gray-400', pill: 'bg-gray-700 text-gray-300' },
  new: { bg: 'bg-blue-900/20', border: 'border-blue-800/40', text: 'text-blue-400', pill: 'bg-blue-900 text-blue-300' },
  contacted: { bg: 'bg-cyan-900/20', border: 'border-cyan-800/40', text: 'text-cyan-400', pill: 'bg-cyan-900 text-cyan-300' },
  qualified: { bg: 'bg-yellow-900/20', border: 'border-yellow-800/40', text: 'text-yellow-400', pill: 'bg-yellow-900 text-yellow-300' },
  proposal: { bg: 'bg-orange-900/20', border: 'border-orange-800/40', text: 'text-orange-400', pill: 'bg-orange-900 text-orange-300' },
  negotiation: { bg: 'bg-purple-900/20', border: 'border-purple-800/40', text: 'text-purple-400', pill: 'bg-purple-900 text-purple-300' },
  won: { bg: 'bg-green-900/20', border: 'border-green-800/40', text: 'text-green-400', pill: 'bg-green-900 text-green-300' },
  lost: { bg: 'bg-red-900/20', border: 'border-red-800/40', text: 'text-red-400', pill: 'bg-red-900 text-red-300' },
};

const SOURCE_COLORS = {
  website: 'bg-blue-800 text-blue-200',
  paid: 'bg-orange-800 text-orange-200',
  manual: 'bg-gray-700 text-gray-300',
  referral: 'bg-green-800 text-green-200',
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return mins + 'm ago';
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  const days = Math.floor(hrs / 24);
  if (days < 30) return days + 'd ago';
  return Math.floor(days / 30) + 'mo ago';
}

function LeadCard({ lead, onClick, onDragStart }) {
  const colors = STAGE_COLORS[lead.current_stage] || STAGE_COLORS.new;
  const sourceColor = SOURCE_COLORS[lead.source] || SOURCE_COLORS.manual;

  return (
    <div
      draggable
      onDragStart={(e) => { e.dataTransfer.setData('text/plain', lead.id); onDragStart(lead.id); }}
      onClick={() => onClick(lead)}
      className={`${colors.bg} border ${colors.border} rounded-lg p-3 cursor-pointer hover:brightness-110 transition mb-2`}
    >
      <div className="flex items-start justify-between mb-1">
        <span className="text-sm font-medium text-white truncate max-w-[160px]">
          {lead.company_name || lead.contact_name || lead.email || 'Unknown'}
        </span>
        <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${sourceColor}`}>{lead.source}</span>
      </div>
      {lead.contact_name && lead.company_name && (
        <div className="text-xs text-gray-400 mb-2">{lead.contact_name}</div>
      )}
      <div className="flex gap-2 text-[10px] text-gray-500 mb-2">
        {lead.website_url && <span title={lead.website_url}>site</span>}
        {lead.email && <span title={lead.email}>email</span>}
        {lead.phone && <span title={lead.phone}>phone</span>}
      </div>
      <div className="flex items-center justify-between text-[10px]">
        <div className="flex gap-2 text-gray-500">
          <span>Assigned: <span className="text-gray-400">{lead.assigned_to || '--'}</span></span>
          {lead.audit_score && (
            <span>Audit: <span className={lead.audit_score >= 70 ? 'text-green-400' : lead.audit_score >= 40 ? 'text-yellow-400' : 'text-red-400'}>{lead.audit_score}/100</span></span>
          )}
        </div>
        <span className="text-gray-600">{timeAgo(lead.last_activity_at)}</span>
      </div>
      {lead.notes && (
        <div className="text-[10px] text-gray-600 mt-1 truncate">{lead.notes}</div>
      )}
    </div>
  );
}

function LostModal({ onConfirm, onCancel }) {
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onCancel}>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-96" onClick={e => e.stopPropagation()}>
        <h3 className="text-white font-semibold mb-4">Why was this lead lost?</h3>
        <div className="space-y-2 mb-4">
          {['Price', 'Competitor', 'No Budget', 'Ghosted', 'Not Ready', 'Other'].map(r => (
            <label key={r} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input type="radio" name="reason" value={r} checked={reason === r} onChange={() => setReason(r)} className="accent-red-500" />
              {r}
            </label>
          ))}
        </div>
        <textarea
          placeholder="Notes (optional)"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-sm text-gray-300 mb-4"
          rows={3}
        />
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="px-3 py-1.5 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={() => reason && onConfirm(reason, notes)} disabled={!reason} className="px-3 py-1.5 text-sm bg-red-600 text-white rounded disabled:opacity-50">Mark Lost</button>
        </div>
      </div>
    </div>
  );
}

function WonModal({ onConfirm, onCancel }) {
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onCancel}>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-96" onClick={e => e.stopPropagation()}>
        <h3 className="text-white font-semibold mb-4">Won! What's the deal value?</h3>
        <input
          type="text"
          placeholder="e.g. 2000/mo or 5000 one-off"
          value={value}
          onChange={e => setValue(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-sm text-gray-300 mb-3"
        />
        <textarea
          placeholder="Notes (optional)"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-sm text-gray-300 mb-4"
          rows={3}
        />
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="px-3 py-1.5 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={() => onConfirm(value, notes)} className="px-3 py-1.5 text-sm bg-green-600 text-white rounded">Mark Won</button>
        </div>
      </div>
    </div>
  );
}

function NewLeadModal({ onSave, onCancel }) {
  const [form, setForm] = useState({
    company_name: '', contact_name: '', email: '', phone: '', website_url: '',
    company_size: '', source: 'manual', assigned_to: 'Jimmy', notes: '',
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onCancel}>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-[480px] max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h3 className="text-white font-semibold mb-4">Add New Lead</h3>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[
            ['company_name', 'Company Name'],
            ['contact_name', 'Contact Name'],
            ['email', 'Email'],
            ['phone', 'Phone'],
            ['website_url', 'Website'],
            ['company_size', 'Company Size'],
          ].map(([k, label]) => (
            <div key={k}>
              <label className="text-[10px] text-gray-500 block mb-1">{label}</label>
              <input value={form[k]} onChange={e => set(k, e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300" />
            </div>
          ))}
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">Source</label>
            <select value={form.source} onChange={e => set('source', e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300">
              <option value="manual">Manual</option>
              <option value="website">Website</option>
              <option value="paid">Paid</option>
              <option value="referral">Referral</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-gray-500 block mb-1">Assigned To</label>
            <select value={form.assigned_to} onChange={e => set('assigned_to', e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300">
              <option value="Jimmy">Jimmy</option>
              <option value="Adam">Adam</option>
              <option value="Oliver">Oliver</option>
            </select>
          </div>
        </div>
        <div className="mb-4">
          <label className="text-[10px] text-gray-500 block mb-1">Notes</label>
          <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={3} className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-300" />
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="px-3 py-1.5 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button onClick={() => onSave(form)} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded">Add Lead</button>
        </div>
      </div>
    </div>
  );
}

function DetailModal({ lead, activities, tasks, onClose, onUpdate, onAddActivity, onAddTask, onToggleTask }) {
  const [editing, setEditing] = useState({});
  const [newNote, setNewNote] = useState('');
  const [newTask, setNewTask] = useState('');
  const colors = STAGE_COLORS[lead.current_stage] || STAGE_COLORS.new;

  const saveField = async (field, value) => {
    await onUpdate(lead.id, { [field]: value });
    setEditing(e => ({ ...e, [field]: false }));
  };

  const EditableField = ({ field, label, value, type = 'text' }) => {
    const [val, setVal] = useState(value || '');
    if (editing[field]) {
      return (
        <div className="mb-2">
          <label className="text-[10px] text-gray-500">{label}</label>
          {type === 'textarea' ? (
            <textarea value={val} onChange={e => setVal(e.target.value)} onBlur={() => saveField(field, val)} autoFocus rows={3} className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300" />
          ) : (
            <input value={val} onChange={e => setVal(e.target.value)} onBlur={() => saveField(field, val)} onKeyDown={e => e.key === 'Enter' && saveField(field, val)} autoFocus className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300" />
          )}
        </div>
      );
    }
    return (
      <div className="mb-2 cursor-pointer hover:bg-gray-800/50 rounded px-1 -mx-1" onClick={() => setEditing(e => ({ ...e, [field]: true }))}>
        <label className="text-[10px] text-gray-500">{label}</label>
        <div className="text-sm text-gray-300">{value || '--'}</div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-[700px] max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className={`p-4 border-b ${colors.border} flex items-center justify-between`}>
          <div>
            <h2 className="text-lg font-semibold text-white">{lead.company_name || lead.contact_name || 'Unknown'}</h2>
            <div className="flex gap-2 mt-1">
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${colors.pill}`}>{lead.current_stage}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${SOURCE_COLORS[lead.source] || SOURCE_COLORS.manual}`}>{lead.source}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl">&times;</button>
        </div>

        <div className="grid grid-cols-2 gap-6 p-4">
          <div>
            <h3 className="text-xs font-semibold text-gray-400 mb-3 uppercase">Details</h3>
            <EditableField field="company_name" label="Company" value={lead.company_name} />
            <EditableField field="contact_name" label="Contact" value={lead.contact_name} />
            <EditableField field="email" label="Email" value={lead.email} />
            <EditableField field="phone" label="Phone" value={lead.phone} />
            <EditableField field="website_url" label="Website" value={lead.website_url} />
            <EditableField field="company_size" label="Size" value={lead.company_size} />
            <EditableField field="assigned_to" label="Assigned To" value={lead.assigned_to} />
            <EditableField field="marketing_type" label="Marketing Type" value={lead.marketing_type} />
            <EditableField field="agency_experience" label="Agency Experience" value={lead.agency_experience} />
            <EditableField field="goals" label="Goals" value={lead.goals} type="textarea" />
            <EditableField field="notes" label="Notes" value={lead.notes} type="textarea" />

            {lead.audit_score != null && (
              <div className="mb-2">
                <label className="text-[10px] text-gray-500">Audit Score</label>
                <div className={`text-sm font-medium ${lead.audit_score >= 70 ? 'text-green-400' : lead.audit_score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>{lead.audit_score}/100 ({lead.audit_status})</div>
              </div>
            )}

            {lead.current_stage === 'won' && (
              <div className="mb-2">
                <label className="text-[10px] text-gray-500">Deal Value</label>
                <div className="text-sm text-green-400">{lead.won_value || '--'}</div>
              </div>
            )}
            {lead.current_stage === 'lost' && (
              <div className="mb-2">
                <label className="text-[10px] text-gray-500">Lost Reason</label>
                <div className="text-sm text-red-400">{lead.lost_reason || '--'}</div>
                {lead.lost_notes && <div className="text-xs text-gray-500">{lead.lost_notes}</div>}
              </div>
            )}

            <div className="mt-4">
              <h3 className="text-xs font-semibold text-gray-400 mb-2 uppercase">Move Stage</h3>
              <div className="flex flex-wrap gap-1">
                {STAGES.filter(s => s.id !== lead.current_stage).map(s => (
                  <button key={s.id} onClick={() => onUpdate(lead.id, { current_stage: s.id }, s.id)} className={`text-[10px] px-2 py-1 rounded ${STAGE_COLORS[s.id].pill} hover:brightness-125`}>{s.label}</button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-gray-400 mb-3 uppercase">Tasks</h3>
            <div className="space-y-1 mb-3">
              {tasks.map(t => (
                <div key={t.id} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={t.status === 'done'} onChange={() => onToggleTask(t.id, t.status === 'done' ? 'pending' : 'done')} className="accent-green-500" />
                  <span className={t.status === 'done' ? 'text-gray-600 line-through' : 'text-gray-300'}>{t.title}</span>
                  {t.due_date && <span className="text-[10px] text-gray-600">{new Date(t.due_date).toLocaleDateString('en-GB')}</span>}
                </div>
              ))}
            </div>
            <div className="flex gap-1 mb-6">
              <input value={newTask} onChange={e => setNewTask(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && newTask.trim()) { onAddTask(lead.id, newTask.trim()); setNewTask(''); } }} placeholder="Add task..." className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300" />
              <button onClick={() => { if (newTask.trim()) { onAddTask(lead.id, newTask.trim()); setNewTask(''); } }} className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-sm">+</button>
            </div>

            <h3 className="text-xs font-semibold text-gray-400 mb-3 uppercase">Activity</h3>
            <div className="flex gap-1 mb-3">
              <input value={newNote} onChange={e => setNewNote(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && newNote.trim()) { onAddActivity(lead.id, newNote.trim()); setNewNote(''); } }} placeholder="Add note..." className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300" />
              <button onClick={() => { if (newNote.trim()) { onAddActivity(lead.id, newNote.trim()); setNewNote(''); } }} className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-sm">+</button>
            </div>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {activities.map(a => (
                <div key={a.id} className="border-l-2 border-gray-800 pl-3 py-1">
                  <div className="text-xs text-gray-300">
                    {a.action === 'stage_change' ? (
                      <span><span className="text-gray-500">{a.from_stage}</span> &rarr; <span className={STAGE_COLORS[a.to_stage]?.text || 'text-white'}>{a.to_stage}</span></span>
                    ) : a.action === 'note' ? (
                      <span>{a.details}</span>
                    ) : (
                      <span>{a.action}: {a.details}</span>
                    )}
                  </div>
                  <div className="text-[10px] text-gray-600">{a.created_by && `${a.created_by} · `}{timeAgo(a.created_at)}</div>
                </div>
              ))}
              {activities.length === 0 && <div className="text-xs text-gray-600">No activity yet</div>}
            </div>
          </div>
        </div>

        <div className="p-3 border-t border-gray-800 text-[10px] text-gray-600 flex justify-between">
          <span>Created: {new Date(lead.created_at).toLocaleDateString('en-GB')}</span>
          <span>Last activity: {timeAgo(lead.last_activity_at)}</span>
        </div>
      </div>
    </div>
  );
}

export default function CrmKanban() {
  const [leads, setLeads] = useState([]);
  const [activities, setActivities] = useState({});
  const [tasks, setTasks] = useState({});
  const [selectedLead, setSelectedLead] = useState(null);
  const [showNewLead, setShowNewLead] = useState(false);
  const [lostModal, setLostModal] = useState(null);
  const [wonModal, setWonModal] = useState(null);
  const [dragId, setDragId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const fetchLeads = async () => {
    const { data } = await supabase.from('conversations').select('*').order('last_activity_at', { ascending: false });
    setLeads(data || []);
    setLoading(false);
  };

  const fetchActivities = async (convId) => {
    const { data } = await supabase.from('activity_log').select('*').eq('conversation_id', convId).order('created_at', { ascending: false });
    setActivities(a => ({ ...a, [convId]: data || [] }));
  };

  const fetchTasks = async (convId) => {
    const { data } = await supabase.from('crm_tasks').select('*').eq('conversation_id', convId).order('created_at', { ascending: true });
    setTasks(t => ({ ...t, [convId]: data || [] }));
  };

  useEffect(() => { fetchLeads(); }, []);

  const openDetail = async (lead) => {
    setSelectedLead(lead);
    await Promise.all([fetchActivities(lead.id), fetchTasks(lead.id)]);
  };

  const updateLead = async (id, updates, targetStage) => {
    if (targetStage === 'lost') {
      setLostModal(id);
      return;
    }
    if (targetStage === 'won') {
      setWonModal(id);
      return;
    }
    await supabase.from('conversations').update(updates).eq('id', id);
    await fetchLeads();
    if (selectedLead?.id === id) {
      const { data } = await supabase.from('conversations').select('*').eq('id', id).single();
      setSelectedLead(data);
      fetchActivities(id);
    }
  };

  const handleLost = async (reason, notes) => {
    const id = lostModal;
    await supabase.from('conversations').update({ current_stage: 'lost', lost_reason: reason, lost_notes: notes }).eq('id', id);
    setLostModal(null);
    await fetchLeads();
    if (selectedLead?.id === id) {
      const { data } = await supabase.from('conversations').select('*').eq('id', id).single();
      setSelectedLead(data);
      fetchActivities(id);
    }
  };

  const handleWon = async (value, notes) => {
    const id = wonModal;
    await supabase.from('conversations').update({ current_stage: 'won', won_value: value, won_notes: notes }).eq('id', id);
    setWonModal(null);
    await fetchLeads();
    if (selectedLead?.id === id) {
      const { data } = await supabase.from('conversations').select('*').eq('id', id).single();
      setSelectedLead(data);
      fetchActivities(id);
    }
  };

  const addActivity = async (convId, note) => {
    await supabase.from('activity_log').insert({ conversation_id: convId, action: 'note', details: note, created_by: 'Adam' });
    fetchActivities(convId);
  };

  const addTask = async (convId, title) => {
    await supabase.from('crm_tasks').insert({ conversation_id: convId, title, assigned_to: 'Jimmy' });
    fetchTasks(convId);
  };

  const toggleTask = async (taskId, newStatus) => {
    await supabase.from('crm_tasks').update({ status: newStatus }).eq('id', taskId);
    if (selectedLead) fetchTasks(selectedLead.id);
  };

  const createLead = async (form) => {
    await supabase.from('conversations').insert({ ...form, current_stage: 'new' });
    setShowNewLead(false);
    fetchLeads();
  };

  const handleDrop = async (stageId, e) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('text/plain');
    if (!id) return;
    const lead = leads.find(l => l.id === id);
    if (!lead || lead.current_stage === stageId) return;

    if (stageId === 'lost') { setLostModal(id); return; }
    if (stageId === 'won') { setWonModal(id); return; }

    await supabase.from('conversations').update({ current_stage: stageId }).eq('id', id);
    fetchLeads();
    setDragId(null);
  };

  const stageCounts = {};
  STAGES.forEach(s => { stageCounts[s.id] = leads.filter(l => l.current_stage === s.id).length; });
  const totalActive = leads.filter(l => !['won', 'lost'].includes(l.current_stage)).length;

  const filteredStages = filter === 'active'
    ? STAGES.filter(s => !['won', 'lost'].includes(s.id))
    : filter === 'closed'
    ? STAGES.filter(s => ['won', 'lost'].includes(s.id))
    : STAGES;

  if (loading) return <div className="text-gray-500 text-center py-20">Loading CRM...</div>;

  return (
    <div>
      {/* Stats bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-4">
          <div className="text-sm text-gray-400">
            <span className="text-white font-medium">{leads.length}</span> total leads
            <span className="mx-2 text-gray-700">|</span>
            <span className="text-white font-medium">{totalActive}</span> active
            <span className="mx-2 text-gray-700">|</span>
            <span className="text-green-400 font-medium">{stageCounts.won || 0}</span> won
            <span className="mx-2 text-gray-700">|</span>
            <span className="text-red-400 font-medium">{stageCounts.lost || 0}</span> lost
          </div>
        </div>
        <div className="flex gap-2">
          <select value={filter} onChange={e => setFilter(e.target.value)} className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300">
            <option value="all">All Stages</option>
            <option value="active">Active Only</option>
            <option value="closed">Won/Lost</option>
          </select>
          <button onClick={() => setShowNewLead(true)} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-500">+ New Lead</button>
        </div>
      </div>

      {/* Kanban */}
      <div className="flex gap-3 overflow-x-auto pb-4" style={{ minHeight: '60vh' }}>
        {filteredStages.map(stage => {
          const stageLeads = leads.filter(l => l.current_stage === stage.id);
          const colors = STAGE_COLORS[stage.id];
          return (
            <div
              key={stage.id}
              className="flex-shrink-0 w-[240px]"
              onDragOver={e => e.preventDefault()}
              onDrop={e => handleDrop(stage.id, e)}
            >
              <div className={`flex items-center justify-between mb-2 px-2`}>
                <span className={`text-xs font-semibold uppercase ${colors.text}`}>{stage.label}</span>
                <span className="text-[10px] text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">{stageLeads.length}</span>
              </div>
              <div className={`rounded-lg border border-dashed ${colors.border} p-2 min-h-[200px] ${dragId ? 'bg-gray-800/30' : ''}`}>
                {stageLeads.map(lead => (
                  <LeadCard key={lead.id} lead={lead} onClick={openDetail} onDragStart={setDragId} />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modals */}
      {selectedLead && (
        <DetailModal
          lead={selectedLead}
          activities={activities[selectedLead.id] || []}
          tasks={tasks[selectedLead.id] || []}
          onClose={() => setSelectedLead(null)}
          onUpdate={updateLead}
          onAddActivity={addActivity}
          onAddTask={addTask}
          onToggleTask={toggleTask}
        />
      )}
      {showNewLead && <NewLeadModal onSave={createLead} onCancel={() => setShowNewLead(false)} />}
      {lostModal && <LostModal onConfirm={handleLost} onCancel={() => setLostModal(null)} />}
      {wonModal && <WonModal onConfirm={handleWon} onCancel={() => setWonModal(null)} />}
    </div>
  );
}
