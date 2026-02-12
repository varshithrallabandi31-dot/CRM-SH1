"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bot, Mail, Globe, User, CheckCircle, AlertCircle, Loader2, Send, FileEdit, Clock, Hand } from 'lucide-react';
import { API_BASE_URL } from '@/config';

interface Draft {
  company_name: string;
  website_url: string;
  primary_email: string;
  recommended_services?: string;
  outreach: { subject: string; body: string };
  inbound: { subject: string; body: string };
}

interface Activity {
  id: number;
  company_name: string;
  email: string;
  sent_at: string;
  status: string;
  recommended_services?: string;
}

export default function EmailAgentPage() {
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState<Draft | null>(null);
  const [draftType, setDraftType] = useState<'outreach' | 'inbound'>('outreach');
  const [activities, setActivities] = useState<Activity[]>([]);

  const [formData, setFormData] = useState({
    company_name: '',
    website_url: '',
    primary_email: ''
  });

  // Fetch activities on mount
  useEffect(() => {
    fetchActivities();
  }, []);

  const fetchActivities = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/activities`);
      setActivities(res.data.activities || []);
    } catch (err) {
      console.error("Failed to fetch activities", err);
    }
  };

  const handleDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    setDraft(null);

    try {
      const data = new FormData();
      data.append('company_name', formData.company_name);
      data.append('website_url', formData.website_url);
      data.append('primary_email', formData.primary_email);

      // Call generate endpoint
      const res = await axios.post(`${API_BASE_URL}/generate`, {
        urls: [formData.website_url]
      });

      const result = res.data[0];
      if (result && !result.error) {
        const emailData = result.emails[0];
        setDraft({
          company_name: result.analysis.company_name,
          website_url: result.url,
          primary_email: formData.primary_email,
          recommended_services: '', // Handle if needed
          outreach: emailData.outreach,
          inbound: emailData.inbound
        });
        setDraftType('outreach');
      } else {
        setError(result?.error || "Failed to generate draft.");
      }

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to process lead. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (isManual = false) => {
    if (!draft) return;
    setSending(true);
    setError(null);

    try {
      // Send both drafts (handled by backend)
      const res = await axios.post(`${API_BASE_URL}/send-lead`, {
        ...draft,
        manual: isManual
      });

      if (res.data.success) {
        setSuccess(isManual ? 
          `Lead recorded! ${res.data.outbound_sent ? 'Outbound' : ''} ${res.data.inbound_sent ? 'Inbound' : ''}` : 
          `Emails sent successfully to ${draft.company_name}!`
        );
        setDraft(null);
        setFormData({ company_name: '', website_url: '', primary_email: '' });
        fetchActivities(); // Refresh table
      }

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to process lead. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Email Agent</h1>
        <p className="text-slate-500 mt-2 text-lg">AI-powered outreach automation and lead generation.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sticky top-24">
            <h2 className="font-bold text-xl mb-6 flex items-center gap-2 text-slate-800">
              <Bot className="w-6 h-6 text-blue-600" />
              New Outreach
            </h2>

            <form onSubmit={handleDraft} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Company Name</label>
                <div className="relative group">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    type="text"
                    required
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-500 outline-none transition-all text-slate-900 placeholder:text-slate-400 shadow-sm"
                    placeholder="Acme Corp"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Website URL</label>
                <div className="relative group">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    type="text"
                    required
                    value={formData.website_url}
                    onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-500 outline-none transition-all text-slate-900 placeholder:text-slate-400 shadow-sm"
                    placeholder="https://example.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Primary Email</label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    type="email"
                    required
                    value={formData.primary_email}
                    onChange={(e) => setFormData({ ...formData, primary_email: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-500 outline-none transition-all text-slate-900 placeholder:text-slate-400 shadow-sm"
                    placeholder="contact@example.com"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || sending}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileEdit className="w-5 h-5" />}
                {loading ? 'Analyzing...' : 'Generate Draft'}
              </button>
            </form>

            {success && (
              <div className="mt-6 p-4 bg-green-50 border border-green-100 text-green-800 text-sm rounded-lg flex items-start gap-3 shadow-sm">
                <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-green-600" />
                <span className="font-medium">{success}</span>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-100 text-red-800 text-sm rounded-lg flex items-start gap-3 shadow-sm">
                <AlertCircle className="w-5 h-5 mt-0.5 shrink-0 text-red-600" />
                <span className="font-medium">{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Draft Preview OR Activities List */}
        <div className="lg:col-span-8 space-y-8">

          {/* Draft Preview Section */}
          {draft && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 animate-in fade-in slide-in-from-bottom-4 ring-1 ring-slate-100">
              <div className="flex justify-between items-center mb-6">
                <h2 className="font-bold text-xl flex items-center gap-2 text-slate-800">
                  <FileEdit className="w-6 h-6 text-purple-600" />
                  Draft Preview
                </h2>
                <div className="flex bg-slate-100 p-1 rounded-lg">
                  <button
                    onClick={() => setDraftType('outreach')}
                    className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${draftType === 'outreach' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                  >
                    Outbound Outreach
                  </button>
                  <button
                    onClick={() => setDraftType('inbound')}
                    className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${draftType === 'inbound' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                  >
                    Inbound Request
                  </button>
                </div>
                <button
                  onClick={() => setDraft(null)}
                  className="text-sm text-slate-500 hover:text-slate-800 font-medium px-3 py-1 rounded hover:bg-slate-100 transition-colors"
                >
                  Discard
                </button>
              </div>

              <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">To</span>
                    <p className="text-slate-900 font-medium">{draft.primary_email}</p>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Type</span>
                    <p className="text-slate-900 font-medium capitalize">{draftType}</p>
                  </div>
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Subject</span>
                  <p className="font-semibold text-slate-900 bg-white p-3 rounded border border-slate-200">{draft[draftType].subject}</p>
                </div>
                <div className="pt-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Body</span>
                  <div
                    className="mt-2 prose prose-slate prose-sm max-w-none text-slate-800 bg-white p-6 rounded-lg border border-slate-200 shadow-sm min-h-[200px]"
                    dangerouslySetInnerHTML={{ __html: draft[draftType].body }}
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-end gap-4">
                <button
                  onClick={() => setDraft(null)}
                  className="px-5 py-2.5 text-slate-700 hover:bg-slate-100 rounded-lg font-semibold transition-colors border border-transparent hover:border-slate-200"
                >
                  Edit Inputs
                </button>
                <button
                  onClick={() => handleSend(true)}
                  disabled={sending}
                  className="bg-blue-600 text-white px-7 py-2.5 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5"
                >
                  <Hand className="w-5 h-5" /> Sent Manually
                </button>
                <button
                  onClick={() => handleSend(false)}
                  disabled={sending}
                  className="bg-green-600 text-white px-7 py-2.5 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 text-white"
                >
                  {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  Send Email
                </button>
              </div>
            </div>
          )}

          {/* Activities Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white">
              <h2 className="font-bold text-lg text-slate-800">Recent Outreach Activities</h2>
              <Link href="/clients" className="text-sm text-blue-600 font-semibold hover:text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition-colors">
                View All
              </Link>
            </div>

            {activities.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-12 bg-white">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                  <Bot className="w-8 h-8 text-slate-300" />
                </div>
                <h3 className="text-slate-900 font-semibold text-lg">No recent activities</h3>
                <p className="text-slate-500 mt-2 max-w-xs mx-auto">Start a new outreach to see results appearing here.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-xs text-slate-500 uppercase tracking-wider font-bold border-b border-slate-200">
                      <th className="px-6 py-4">Company</th>
                      <th className="px-6 py-4">Services</th>
                      <th className="px-6 py-4">Email</th>
                      <th className="px-6 py-4">Sent At</th>
                      <th className="px-6 py-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {activities.map((activity) => (
                      <tr key={activity.id} className="hover:bg-slate-50/80 transition-colors group bg-white">
                        <td className="px-6 py-4 font-semibold text-slate-900">{activity.company_name}</td>
                        <td className="px-6 py-4 text-slate-600 max-w-xs truncate" title={activity.recommended_services}>
                          {activity.recommended_services ? (
                            <span className="inline-block px-2 py-1 rounded bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200">
                              {activity.recommended_services.split(',')[0]} {activity.recommended_services.split(',').length > 1 && `+${activity.recommended_services.split(',').length - 1}`}
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-slate-600">{activity.email}</td>
                        <td className="px-6 py-4 text-slate-500">
                          <div className="flex items-center gap-2">
                            {formatDate(activity.sent_at)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 border border-green-200 shadow-sm">
                            <CheckCircle className="w-3.5 h-3.5 mr-1" />
                            {activity.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
