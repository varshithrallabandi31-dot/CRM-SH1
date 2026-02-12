"use client";

import { useState, useEffect } from "react";
import { 
  Users, 
  MessageSquare, 
  Send, 
  FileText, 
  ShoppingCart, 
  Ticket, 
  Activity, 
  CheckCircle2, 
  Clock, 
  PauseCircle,
  TrendingUp,
  Globe,
  Briefcase,
  Target,
  Search,
  Zap,
  MoreVertical
} from "lucide-react";
import { API_BASE_URL } from '@/config';
import { useRole } from "@/context/RoleContext";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const { role, email, user } = useRole();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch(`${API_BASE_URL}/dashboard-stats?role=${role}&email=${email}`);
        const data = await res.json();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    }
    if (role) fetchStats();
  }, [role, email]);

  const CircularProgress = ({ percent, label, sublabel }: any) => (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-gray-200"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={251.2}
            strokeDashoffset={251.2 - (251.2 * percent) / 100}
            className="text-blue-600 transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center font-bold text-lg">
          {percent}%
        </div>
      </div>
      <div className="mt-3 text-center">
        <p className="text-sm font-bold text-gray-900">{label}</p>
        <p className="text-[10px] text-gray-400 font-bold uppercase">{sublabel}</p>
      </div>
    </div>
  );

  const MetricCard = ({ title, value, subValue, icon: Icon, color }: any) => (
    <div className="bg-white p-6 rounded-[2rem] border shadow-sm flex flex-col justify-between">
      <div className="flex justify-between items-start mb-4">
        <div className={cn("p-3 rounded-2xl", color)}>
          <Icon className="w-5 h-5" />
        </div>
        <button className="text-gray-300 hover:text-gray-600"><MoreVertical className="w-5 h-5" /></button>
      </div>
      <div>
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">{title}</p>
        <h3 className="text-2xl font-black mt-1 text-gray-900">{value}</h3>
      </div>
      <p className="text-xs text-blue-600 font-bold mt-2">{subValue}</p>
    </div>
  );

  if (loading) return <div className="p-8 flex items-center gap-3 font-bold"><Clock className="animate-spin" /> Preparing Dashboard...</div>;

  const isAdmin = role === 'Admin' || role === 'Employee';

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Dynamic Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">
            {isAdmin ? 'Project Dashboard' : 'Your Growth Strategy'}
          </h1>
          <p className="text-gray-500 font-medium">
            Welcome back, <span className="text-blue-600 font-bold">{user?.name || 'User'}</span>. Here is your current snapshot.
          </p>
        </div>
        <div className="flex gap-3">
           <button className="px-6 py-3 bg-white border rounded-2xl font-bold text-sm hover:shadow-md transition-all">Take a Tour</button>
           <button className="px-6 py-3 bg-gray-900 text-white rounded-2xl font-bold text-sm hover:bg-black shadow-lg shadow-gray-900/20 transition-all">View Files</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Stats Rail */}
        <div className="lg:col-span-3 bg-white rounded-[2.5rem] border shadow-sm p-8 flex flex-col gap-10">
          <CircularProgress percent={stats?.metrics?.successRate?.replace('%','') || (isAdmin? 75 : 85)} label="Success Rate" sublabel="Live Projects" />
          <CircularProgress percent={48} label="Conversion" sublabel="Draft to Sent" />
          <CircularProgress percent={92} label="Health Score" sublabel="SEO Performance" />
          
          <div className="mt-4 pt-8 border-t border-gray-100 flex flex-col gap-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500 font-medium">Total Failed</span>
              <span className="font-bold text-red-500">{stats?.metrics?.failed || 0}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500 font-medium">Successful</span>
              <span className="font-bold text-green-500">{stats?.metrics?.successful || 0}</span>
            </div>
          </div>
        </div>

        {/* Main Dashboard Content */}
        <div className="lg:col-span-9 space-y-8">
          {/* Top Summary Widgets */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
             {isAdmin ? (
               <>
                <MetricCard title="Total Prospects" value={stats?.total || 0} subValue="+12.5% vs LW" icon={Users} color="bg-blue-50 text-blue-600" />
                <MetricCard title="Active Campaigns" value={stats?.active || 0} subValue="Running Now" icon={Zap} color="bg-orange-50 text-orange-600" />
                <MetricCard title="Drafts Ready" value={stats?.pending || 0} subValue="Awaiting Review" icon={Clock} color="bg-indigo-50 text-indigo-600" />
                <MetricCard title="Total Sent" value={stats?.completedActivities || 523} subValue="+5% Growth" icon={Send} color="bg-green-50 text-green-600" />
               </>
             ) : (
               <>
                <MetricCard title="Services Offered" value={stats?.recommended_services?.split(',').length || 0} subValue="Personalized for you" icon={Briefcase} color="bg-blue-50 text-blue-600" />
                <MetricCard title="Target Keywords" value={stats?.targetKeywords?.length || 0} subValue="Top SEO Focus" icon={Target} color="bg-indigo-50 text-indigo-600" />
                <MetricCard title="Next Milestone" value={stats?.nextMilestone ? "Active" : "Locked"} subValue={stats?.nextMilestoneDate || "Awaiting Setup"} icon={Clock} color="bg-purple-50 text-purple-600" />
                <MetricCard title="Strategy Level" value="Advanced" subValue="AI Optimized" icon={Zap} color="bg-orange-50 text-orange-600" />
               </>
             )}
          </div>

          {/* Center Graphic & Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-[2.5rem] border shadow-sm p-8 space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-lg">Project Highlights</h3>
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              
              {isAdmin ? (
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-2xl flex justify-between items-center">
                    <div className="flex gap-3 items-center">
                       <Search className="w-4 h-4 text-gray-400" />
                       <span className="text-sm font-bold">Top Search: "SEO Agency Mumbai"</span>
                    </div>
                    <span className="text-xs bg-blue-100 text-blue-700 font-bold px-2 py-1 rounded">TRENDING</span>
                  </div>
                  <div className="h-40 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl flex items-end p-4 gap-2">
                    {[40, 70, 45, 90, 65, 80, 55].map((h, i) => (
                      <div key={i} className="bg-blue-600 w-full rounded-t-lg transition-all hover:bg-blue-700" style={{height: `${h}%`}}></div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                   <div className="space-y-2">
                      <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest italic">Current SEO Strategy</label>
                      <p className="text-gray-700 italic font-medium leading-relaxed bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                        "{stats?.seoStrategy || 'Your personalized strategy is being compiled by our AI...'}"
                      </p>
                   </div>
                   <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 border rounded-2xl">
                         <Globe className="w-4 h-4 text-blue-600 mb-2" />
                         <span className="text-xs font-bold text-gray-400 uppercase">Website</span>
                         <p className="text-sm font-bold text-gray-900 truncate">{stats?.website || 'N/A'}</p>
                      </div>
                      <div className="p-4 border rounded-2xl">
                         <Target className="w-4 h-4 text-indigo-600 mb-2" />
                         <span className="text-xs font-bold text-gray-400 uppercase">Status</span>
                         <p className="text-sm font-bold text-gray-900">{stats?.status || 'Active'}</p>
                      </div>
                   </div>
                </div>
              )}
            </div>

            <div className="bg-gray-900 rounded-[2.5rem] shadow-2xl p-8 text-white relative overflow-hidden group">
               <div className="absolute top-[-20%] right-[-20%] w-[60%] h-[60%] bg-blue-600/20 blur-[100px] rounded-full group-hover:bg-blue-600/30 transition-all duration-1000"></div>
               <div className="relative z-10 flex flex-col h-full justify-between">
                  <div className="space-y-1">
                    <h3 className="text-xl font-bold">In-Depth Analysis</h3>
                    <p className="text-gray-400 text-sm">Real-time performance monitoring</p>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between text-xs font-bold text-gray-400 mb-1">
                      <span>PROJECT GOAL</span>
                      <span>85% ACHIEVED</span>
                    </div>
                    <div className="w-full bg-white/10 h-3 rounded-full overflow-hidden">
                      <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full w-[85%] rounded-full shadow-[0_0_20px_rgba(59,130,246,0.5)]"></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-8 pt-4">
                    <div>
                      <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest">Amount Pledged</p>
                      <p className="text-xl font-black text-blue-400">{stats?.metrics?.pledged || '$41,264,435'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest">Goal Variance</p>
                      <p className="text-xl font-black text-indigo-400">$171,873,988</p>
                    </div>
                  </div>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Secondary Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8">
         <div className="bg-white p-6 rounded-3xl border shadow-sm flex items-center gap-4">
            <div className="p-4 bg-purple-50 text-purple-600 rounded-2xl"><ShoppingCart className="w-6 h-6" /></div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase">Market Share</p>
              <p className="text-lg font-black">+24.8% <span className="text-green-500 text-xs font-bold">UP</span></p>
            </div>
         </div>
         <div className="bg-white p-6 rounded-3xl border shadow-sm flex items-center gap-4">
            <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl"><Activity className="w-6 h-6" /></div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase">Bot Activity</p>
              <p className="text-lg font-black">99.9% <span className="text-blue-500 text-xs font-bold">STABLE</span></p>
            </div>
         </div>
         <div className="bg-white p-6 rounded-3xl border shadow-sm flex items-center gap-4">
            <div className="p-4 bg-orange-50 text-orange-600 rounded-2xl"><Zap className="w-6 h-6" /></div>
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase">AI Utilization</p>
              <p className="text-lg font-black">100% <span className="text-orange-500 text-xs font-bold">ACTIVE</span></p>
            </div>
         </div>
      </div>
    </div>
  );
}
