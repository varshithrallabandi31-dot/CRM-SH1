"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, ExternalLink, Clock, CheckCircle2, PauseCircle, ChevronRight, Plus } from 'lucide-react';
import Link from 'next/link';
import { API_BASE_URL } from '@/config';

interface Client {
  id: number;
  projectName: string;
  category: string;
  email: string;
  status: string;
  keywords: string[];
  website: string;
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const router = useRouter();
  const [formData, setFormData] = useState({
    companyName: '',
    websiteUrl: '',
    email: '',
    projectName: '',
    gmbName: '',
    seoStrategy: '',
    tagline: '',
    targetKeywords: ''
  });

  useEffect(() => {
    fetchClients();
  }, [filter]);

  const fetchClients = async () => {
    setLoading(true);
    try {
      const url = filter === 'All' 
        ? `${API_BASE_URL}/clients`
        : `${API_BASE_URL}/clients?status=${filter}`;
      
      const res = await fetch(url);
      const data = await res.json();
      setClients(data.clients || []);
    } catch (error) {
      console.error("Error fetching clients:", error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddClient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/clients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          targetKeywords: formData.targetKeywords.split(',').map(k => k.trim())
        })
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchClients();
        setFormData({
          companyName: '',
          websiteUrl: '',
          email: '',
          projectName: '',
          gmbName: '',
          seoStrategy: '',
          tagline: '',
          targetKeywords: ''
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filteredClients = clients.filter(c => 
    c.projectName?.toLowerCase().includes(search.toLowerCase()) ||
    c.email?.toLowerCase().includes(search.toLowerCase())
  );

  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'Active': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'Pending': return <Clock className="w-4 h-4 text-blue-500" />;
      case 'Hold': return <PauseCircle className="w-4 h-4 text-orange-500" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Add Client
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center sticky top-0 bg-white">
              <h2 className="text-xl font-bold">Add New Client</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">×</button>
            </div>
            <form onSubmit={handleAddClient} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Company Name</label>
                  <input required className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.companyName} onChange={e => setFormData({...formData, companyName: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Website URL</label>
                  <input required className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.websiteUrl} onChange={e => setFormData({...formData, websiteUrl: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Email</label>
                  <input required type="email" className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Project Name</label>
                  <input className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.projectName} onChange={e => setFormData({...formData, projectName: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">GMB Name</label>
                  <input className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.gmbName} onChange={e => setFormData({...formData, gmbName: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">SEO Strategy</label>
                  <input className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.seoStrategy} onChange={e => setFormData({...formData, seoStrategy: e.target.value})} />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Tagline</label>
                <input className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.tagline} onChange={e => setFormData({...formData, tagline: e.target.value})} />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Target Keywords (comma separated)</label>
                <textarea className="w-full px-4 py-2 bg-gray-50 border rounded-lg outline-none focus:ring-1 focus:ring-blue-500" value={formData.targetKeywords} onChange={e => setFormData({...formData, targetKeywords: e.target.value})} />
              </div>
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 border rounded-lg font-bold text-gray-500 hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700">Add Client</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <p className="text-sm text-gray-500">Total Clients</p>
          <p className="text-2xl font-bold">{clients.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm border-l-4 border-l-green-500">
          <p className="text-sm text-gray-500">Active</p>
          <p className="text-2xl font-bold">{clients.filter(c => c.status === 'Active').length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm border-l-4 border-l-orange-500">
          <p className="text-sm text-gray-500">On Hold</p>
          <p className="text-2xl font-bold">{clients.filter(c => c.status === 'Hold').length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm border-l-4 border-l-blue-500">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold">{clients.filter(c => c.status === 'Pending').length}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="p-4 border-b flex flex-col md:flex-row gap-4 justify-between items-center">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search clients..." 
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
            {['All', 'Active', 'Hold', 'Pending'].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filter === s ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-6 py-4 font-semibold">Project</th>
                <th className="px-6 py-4 font-semibold">Category</th>
                <th className="px-6 py-4 font-semibold">Email</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold">Keywords</th>
                <th className="px-6 py-4 font-semibold"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-500">Loading clients...</td></tr>
              ) : filteredClients.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-500">No clients found</td></tr>
              ) : filteredClients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-6 py-4">
                    <span className="font-bold text-gray-900">{client.projectName}</span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">
                    {client.category}
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">
                    {client.email}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <StatusIcon status={client.status} />
                      <span className="text-sm font-medium">{client.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {client.keywords?.slice(0, 2).map((k, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-[10px] rounded-full">
                          {k}
                        </span>
                      ))}
                      {client.keywords?.length > 2 && (
                        <span className="text-[10px] text-gray-400">+{client.keywords.length - 2}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link 
                      href={`/clients/${client.id}`}
                      className="p-2 hover:bg-blue-50 text-gray-400 hover:text-blue-600 rounded-lg inline-flex"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
