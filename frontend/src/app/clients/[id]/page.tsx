"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Globe, 
  User, 
  MapPin, 
  ShieldCheck, 
  Hash, 
  MessageSquare, 
  Activity, 
  Plus, 
  Send,
  Loader2,
  Trash2,
  CheckCircle,
  Clock,
  Briefcase,
  Users
} from 'lucide-react';
import { API_BASE_URL } from '@/config';
import { useRole } from '@/context/RoleContext';
import { cn } from '@/lib/utils';

export default function ClientDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [client, setClient] = useState<any>(null);
  const [remarks, setRemarks] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isKeywordModalOpen, setIsKeywordModalOpen] = useState(false);
  const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const { role } = useRole();
  const [isMilestoneModalOpen, setIsMilestoneModalOpen] = useState(false);
  const [milestoneData, setMilestoneData] = useState({
    nextMilestone: '',
    nextMilestoneDate: ''
  });

  useEffect(() => {
    if (id) {
      Promise.all([
        fetchClientData(),
        fetchRemarks(),
        fetchActivities(),
        fetchEmployees()
      ]).finally(() => setLoading(false));
    }
  }, [id]);

  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/employees`);
      const data = await res.json();
      setEmployees(data.employees || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchClientData = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}`);
      if (res.ok) {
        const data = await res.json();
        setClient(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRemarks = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/remarks`);
      if (res.ok) {
        const data = await res.json();
        setRemarks(data.remarks || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchActivities = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/activities`);
      if (res.ok) {
        const data = await res.json();
        setActivities(data.activities || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignEmployee = async (employeeId: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/assign-employee`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: employeeId })
      });
      if (res.ok) {
        setIsAssignModalOpen(false);
        fetchClientData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddKeyword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyword.trim()) return;
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: newKeyword })
      });
      if (res.ok) {
        setNewKeyword('');
        fetchClientData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRemoveKeyword = async (keyword: string) => {
    if (!confirm(`Remove keyword "${keyword}"?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/keywords`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword })
      });
      if (res.ok) {
        fetchClientData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddRemark = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const content = (form.elements.namedItem('content') as HTMLTextAreaElement).value;
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/remarks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, createdBy: 'Admin' })
      });
      if (res.ok) {
        fetchRemarks();
        form.reset();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}/activities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          method: formData.get('method'),
          content: formData.get('content')
        })
      });
      if (res.ok) {
        fetchActivities();
        setIsActivityModalOpen(false);
        form.reset();
      }
    } catch (err) {
      console.error(err);
    }
  };


  const updateProfile = async (updates: any) => {
    try {
      const res = await fetch(`${API_BASE_URL}/clients/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (res.ok) {
        fetchClientData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProfile(milestoneData);
    setIsMilestoneModalOpen(false);
  };


  if (loading) return <div className="p-8"><Loader2 className="animate-spin" /> Loading Client Details...</div>;
  if (!client) return <div className="p-8 text-red-500">Client not found.</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      {/* Header Section */}
      <div className="bg-white rounded-xl shadow-sm border p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Briefcase className="w-8 h-8 text-blue-600" />
            {client.companyName}
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <Globe className="w-4 h-4" /> {client.website}
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setIsAssignModalOpen(true)}
            className="px-4 py-2 border rounded-lg font-bold hover:bg-gray-50 flex items-center gap-2"
          >
            <Users className="w-4 h-4" /> {client.assignedEmployee ? `Assigned: ${client.assignedEmployee.name}` : 'Assign Employee'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content (Left) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tabs */}
          <div className="flex border-b">
            {['overview', 'remarks', 'activities'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 font-bold border-b-2 transition-colors capitalize ${activeTab === tab ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500'}`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="bg-white rounded-xl border shadow-sm p-6">
            {activeTab === 'overview' && (
              <div className="space-y-8">
                <section>
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><MapPin className="w-5 h-5" /> Project Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50 p-6 rounded-xl">
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">Project Name</label>
                      <p className="font-medium">{client.projectName || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">GMB Name</label>
                      <p className="font-medium">{client.gmbName || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">Email</label>
                      <p className="font-medium">{client.email}</p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">Phone</label>
                      <p className="font-medium">{client.phone}</p>
                    </div>
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><ShieldCheck className="w-5 h-5" /> SEO Strategy</h3>
                  <div className="p-4 border rounded-xl bg-blue-50/50 italic text-gray-700">
                    "{client.seoStrategy || 'No strategy defined yet.'}"
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><Briefcase className="w-5 h-5" /> Recommended Services</h3>
                  <div className="flex flex-wrap gap-2">
                    {client.recommended_services ? (
                      client.recommended_services.split(',').map((service: string) => (
                        <span key={service} className="px-3 py-1 bg-blue-100 text-blue-800 border border-blue-200 rounded-full text-sm font-medium">
                          {service.trim()}
                        </span>
                      ))
                    ) : (
                      <p className="text-gray-400 italic">No services recommended yet.</p>
                    )}
                  </div>
                </section>

                <section>
                   <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-bold flex items-center gap-2"><Hash className="w-5 h-5" /> Target Keywords</h3>
                      <button 
                        onClick={() => setIsKeywordModalOpen(true)}
                        className="text-blue-600 hover:text-blue-800 flex items-center gap-1 text-sm font-bold"
                      >
                        <Plus className="w-4 h-4" /> Add Keyword
                      </button>
                   </div>
                   <div className="flex flex-wrap gap-2">
                     {client.targetKeywords?.map((kw: string) => (
                       <span key={kw} className="px-3 py-1 bg-gray-100 border rounded-full text-sm flex items-center gap-2 group">
                         {kw}
                         <button onClick={() => handleRemoveKeyword(kw)} className="text-gray-400 hover:text-red-500 transition-colors">
                           <Trash2 className="w-3 h-3" />
                         </button>
                       </span>
                     ))}
                   </div>
                </section>
              </div>
            )}

            {activeTab === 'remarks' && (
              <div className="space-y-6">
                <form onSubmit={handleAddRemark} className="space-y-4">
                  <textarea 
                    name="content"
                    placeholder="Add a new internal remark..."
                    className="w-full p-4 border rounded-xl focus:ring-2 focus:ring-blue-500 min-h-[100px]"
                    required
                  />
                  <button className="px-6 py-2 bg-gray-900 text-white rounded-lg font-bold hover:bg-black transition-colors self-end">
                    Post Remark
                  </button>
                </form>

                <div className="space-y-4">
                  {remarks.map(r => (
                    <div key={r.id} className="p-4 bg-gray-50 rounded-xl border">
                      <div className="flex justify-between text-xs font-bold text-gray-500 mb-2">
                        <span>{r.createdBy}</span>
                        <span>{new Date(r.createdAt).toLocaleString()}</span>
                      </div>
                      <p className="text-gray-800">{r.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'activities' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold flex items-center gap-2"><Activity className="w-5 h-5" /> Recent Activities</h3>
                  <button onClick={() => setIsActivityModalOpen(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 flex items-center gap-2 text-sm">
                    <Plus className="w-4 h-4" /> Log Activity
                  </button>
                </div>
                
                <div className="space-y-4">
                  {activities.map(a => (
                    <div key={a.id} className="flex gap-4 p-4 border-l-4 border-blue-500 bg-white shadow-sm rounded-r-xl">
                      <div className="bg-blue-100 p-2 rounded-lg h-fit">
                        {a.method === 'Email' ? <Send className="w-4 h-4 text-blue-600" /> : <Activity className="w-4 h-4 text-blue-600" />}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{a.action} ({a.method})</div>
                        <p className="text-gray-600 text-sm whitespace-pre-wrap mt-1">{a.content}</p>
                        <div className="text-[10px] text-gray-400 mt-2 font-bold uppercase tracking-wider">{new Date(a.createdAt).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Widgets (Right) */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" /> Current Status
            </h3>
            <div className="flex items-center gap-3">
              <div className={cn("w-3 h-3 rounded-full animate-pulse", 
                client.status === 'Active' ? 'bg-green-500' : 
                client.status === 'Hold' ? 'bg-orange-500' : 'bg-blue-500'
              )}></div>
              {role === 'Admin' ? (
                <select 
                  value={client.status} 
                  onChange={(e) => updateProfile({ status: e.target.value })}
                  className="font-bold text-gray-900 bg-transparent border-none focus:ring-0 cursor-pointer"
                >
                  <option value="Active">Active</option>
                  <option value="Hold">On Hold</option>
                  <option value="Pending">Pending</option>
                </select>
              ) : (
                <span className="font-bold text-gray-900">Client is {client.status}</span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {client.status === 'Active' ? 'All strategy and monitoring services are running.' : 
               client.status === 'Hold' ? 'Services are temporarily paused.' : 'Account is awaiting final setup.'}
            </p>
          </div>

          <div className="bg-white rounded-xl border shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" /> Next Milestone
              </h3>
              {role === 'Admin' && (
                <button 
                  onClick={() => {
                    setMilestoneData({
                      nextMilestone: client.nextMilestone || '',
                      nextMilestoneDate: client.nextMilestoneDate || ''
                    });
                    setIsMilestoneModalOpen(true);
                  }}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-4 h-4" />
                </button>
              )}
            </div>
            {client.nextMilestone ? (
              <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
                <div className="text-sm font-bold text-blue-800">{client.nextMilestone}</div>
                <div className="text-xs text-blue-600">{client.nextMilestoneDate}</div>
              </div>
            ) : (
              <div className="text-sm text-gray-400 italic">No milestone set</div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {isAssignModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
           <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
             <h3 className="text-xl font-bold mb-6">Assign Employee</h3>
             <div className="space-y-3">
               {employees.map(emp => (
                 <button 
                  key={emp.id}
                  onClick={() => handleAssignEmployee(emp.id)}
                  className="w-full p-4 border rounded-xl hover:bg-blue-50 flex items-center justify-between group transition-colors"
                >
                   <div className="text-left">
                     <div className="font-bold">{emp.name}</div>
                     <div className="text-xs text-gray-500">{emp.role}</div>
                   </div>
                   <Plus className="w-5 h-5 text-gray-300 group-hover:text-blue-600" />
                 </button>
               ))}
             </div>
             <button onClick={() => setIsAssignModalOpen(false)} className="w-full mt-6 text-gray-500 text-sm hover:underline">Cancel</button>
           </div>
        </div>
      )}

      {isKeywordModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
           <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
             <h3 className="text-xl font-bold mb-6">Add Target Keyword</h3>
             <form onSubmit={handleAddKeyword} className="space-y-4">
               <input 
                  autoFocus
                  className="w-full p-4 border rounded-xl"
                  placeholder="e.g. SEO Services Mumbai"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  required
               />
               <button className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700">Add Keyword</button>
             </form>
             <button onClick={() => setIsKeywordModalOpen(false)} className="w-full mt-6 text-gray-500 text-sm hover:underline">Cancel</button>
           </div>
        </div>
      )}
      
      {isActivityModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
           <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <h3 className="text-xl font-bold mb-6">Log New Activity</h3>
              <form onSubmit={handleAddActivity} className="space-y-4">
                <div>
                   <label className="text-xs font-bold text-gray-500 uppercase">Activity Type</label>
                   <select name="method" className="w-full p-4 border rounded-xl mt-1">
                      <option>Call</option>
                      <option>Meeting</option>
                      <option>Email</option>
                      <option>Analysis</option>
                      <option>Update</option>
                   </select>
                </div>
                <div>
                   <label className="text-xs font-bold text-gray-500 uppercase">Description</label>
                   <textarea name="content" className="w-full p-4 border rounded-xl mt-1 min-h-[100px]" required></textarea>
                </div>
                <button className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700">Save Activity</button>
              </form>
              <button onClick={() => setIsActivityModalOpen(false)} className="w-full mt-6 text-gray-500 text-sm hover:underline">Cancel</button>
           </div>
        </div>
      )}
      {isMilestoneModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
           <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <h3 className="text-xl font-bold mb-6">Set Next Milestone</h3>
              <form onSubmit={handleUpdateMilestone} className="space-y-4">
                <div>
                   <label className="text-xs font-bold text-gray-500 uppercase">Milestone Title</label>
                   <input 
                      className="w-full p-4 border rounded-xl mt-1"
                      placeholder="e.g. Monthly SEO Review"
                      value={milestoneData.nextMilestone}
                      onChange={(e) => setMilestoneData({...milestoneData, nextMilestone: e.target.value})}
                      required
                   />
                </div>
                <div>
                   <label className="text-xs font-bold text-gray-500 uppercase">Date/Time Description</label>
                   <input 
                      className="w-full p-4 border rounded-xl mt-1"
                      placeholder="e.g. Next Monday at 2 PM"
                      value={milestoneData.nextMilestoneDate}
                      onChange={(e) => setMilestoneData({...milestoneData, nextMilestoneDate: e.target.value})}
                      required
                   />
                </div>
                <button className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700">Save Milestone</button>
              </form>
              <button onClick={() => setIsMilestoneModalOpen(false)} className="w-full mt-6 text-gray-500 text-sm hover:underline">Cancel</button>
           </div>
        </div>
      )}
    </div>
  );
}
