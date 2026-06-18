import { useState, useEffect } from 'react';
import axios from 'axios';
import { useQuery,useMutation,useQueryClient } from '@tanstack/react-query';
import CrewManifest from './CrewManifest';

function App() {
  const queryClient=useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');  
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [date, setDate] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [activeTelemetryId, setActiveTelemetryId] = useState(null);
  const [telemetryLogs, setTelemetryLogs] = useState([]);

  //Read Engine -- use chache vault
  const { data: missions=[], isLoading, isError }=useQuery({
    queryKey: ['missions',searchTerm],
    queryFn: async ()=>{
      const url = searchTerm 
        ? `http://127.0.0.1:8000/missions?search=${searchTerm}`
        : 'http://127.0.0.1:8000/missions';
      const response = await axios.get(url);
      return response.data.missions;
    }
  });
  //Write Engine - DB
  const addMissionMutation= useMutation({
    mutationFn: (newMission)=> axios.post('http://127.0.0.1:8000/missions',newMission),
    onSuccess: ()=>{
      queryClient.invalidateQueries({queryKey:['missions']});
      setName('');setTarget('');setDate('');
    }
  });
  //update
  const updateMissionMutation=useMutation({
    mutationFn: ({id,updateData})=> axios.put(`http://127.0.0.1:8000/missions/${id}`,updateData),
    onSuccess:()=>{
      queryClient.invalidateQueries({queryKey:['missions']});
      setEditingId(null)
    }
  });
  //Delete
  const deleteMissionMutation=useMutation({
    mutationFn: (id)=> axios.delete(`http://127.0.0.1:8000/missions/${id}`),
    onSuccess:()=>{
      queryClient.invalidateQueries({queryKey:['missions']})
    }
  });
  //Event Handlers
  const handleSubmit = (e) => {
    e.preventDefault(); 
    addMissionMutation.mutate({name,target_destination:target,launch_date:date||null});
  };

  const saveUpdate = (mission) => {
    updateMissionMutation.mutate({
      id: mission.id,
      updateData: {name:editName,target_destination:mission.target_destination,launch_date:mission.launch_date}
    });
  };

  const loadTelemetry = async (id) => {
    try {
      if (activeTelemetryId === id) {
        setActiveTelemetryId(null);
        return;
      }
      const response = await axios.get(`http://127.0.0.1:8000/missions/${id}/telemetry`);
      const dataArray = response.data.telemetry || [];
      setTelemetryLogs(dataArray);
      setActiveTelemetryId(id);
    } catch (err) {
      console.error("Error loading telemetry", err);
    }
  };

  const triggerPing = async (id) => {
    try {
      await axios.post(`http://127.0.0.1:8000/missions/${id}/telemetry/simulate`);
      const response = await axios.get(`http://127.0.0.1:8000/missions/${id}/telemetry`);
      const dataArray = response.data.telemetry || [];
      setTelemetryLogs(dataArray);
    } catch (err) {
      console.error("Error simulating telemetry", err);
    }
  };

  // Status Color Picker
  const getStatusColorClass = (status) => {
    if (status === 'Critical') return 'text-red-500'; 
    if (status === 'Warning') return 'text-orange-400'; 
    return 'text-emerald-400'; 
  };

  return (
    <div className="relative min-h-screen font-sans text-slate-200">

      <div className="fixed inset-0 z-[-1] bg-[#020617] overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vh] bg-cyan-600/20 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[60vw] h-[60vh] bg-blue-900/40 rounded-full blur-[150px]"></div>
        <div className="absolute top-[30%] left-[50%] w-[50vw] h-[50vh] bg-indigo-800/20 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="max-w-4xl mx-auto p-8 relative z-10">
        
        <h1 className="text-5xl font-extrabold text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 mb-10 tracking-widest uppercase drop-shadow-[0_0_15px_rgba(34,211,238,0.2)]">
          Space Command
        </h1>
    
      <form onSubmit={handleSubmit} className="relative bg-slate-800/40 backdrop-blur-xl p-8 rounded-2xl shadow-[0_0_30px_rgba(0,0,0,0.5)] mb-10 border border-slate-600/50">
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <h3 className="text-2xl font-semibold text-cyan-300 mb-6 mt-0 tracking-wide flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          Initialize New Mission
        </h3>
        
        <div className="grid gap-5 md:grid-cols-4 relative z-10">
          <input type="text" placeholder="Mission Designation" value={name} onChange={(e) => setName(e.target.value)} required className="p-3 rounded-lg bg-slate-900/80 border border-slate-600/50 text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all" />
          <input type="text" placeholder="Orbital Target" value={target} onChange={(e) => setTarget(e.target.value)} required className="p-3 rounded-lg bg-slate-900/80 border border-slate-600/50 text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all" />
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="p-3 rounded-lg bg-slate-900/80 border border-slate-600/50 text-cyan-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all [color-scheme:dark]" />
          <button 
            type="submit" 
            disabled={addMissionMutation.isPending}
            className="bg-cyan-600 hover:bg-cyan-400 text-slate-900 font-extrabold py-3 px-4 rounded-lg transition-all duration-300 shadow-[0_0_15px_rgba(8,145,178,0.5)] hover:shadow-[0_0_25px_rgba(34,211,238,0.8)] uppercase tracking-wider"
          >
            {addMissionMutation.isPending ? 'Launching...':'Launch Sequence'}
          </button>
        </div>
      </form>

      {/* Search Bar */}
      <div className='mb-8'>
        <input type="text" placeholder='🔍 Search missions by name...' value={searchTerm} onChange={(e)=> setSearchTerm(e.target.value)} 
        className='w-full p-4 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200 shadow-inner'/>
      </div>

      {isLoading && <div className="text-cyan-400 font-bold text-center text-xl mb-4 animate-pulse">Establishing secure link to satellite network...</div>}
      {isError && <div className="text-red-400 font-bold mb-4 p-4 bg-red-900/20 border border-red-500/50 rounded-lg backdrop-blur-sm">⚠️ Critical Error: Uplink connection severed.</div>}
      
      <div className="grid gap-6">
        {missions.length === 0 && !isError && !isLoading ? (
          <p className="text-slate-400 italic text-center text-lg">Awaiting telemetry data...</p>
        ) : (
          missions.map((mission) => (
            <div key={mission.id} className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
              
              {editingId === mission.id ? (
                <div className="flex gap-3 mb-4">
                  <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)} className="p-2 rounded bg-slate-900 border border-slate-600 text-white focus:outline-none focus:border-blue-500 flex-grow" />
                  <button onClick={() => saveUpdate(mission)} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded transition duration-200">Save</button>
                  <button onClick={() => setEditingId(null)} className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white font-bold rounded transition duration-200">Cancel</button>
                </div>
              ) : (
                <h2 className="text-2xl font-bold text-blue-300 mb-2">{mission.name}</h2>
              )}

              <p className="text-slate-300 font-medium mb-1">Target: <span className="text-white">{mission.target_destination}</span></p>
              <p className="text-slate-300 font-medium mb-4">Status: <span className="text-yellow-400">{mission.status || "Planning"}</span></p>
              
              <div className="flex flex-wrap gap-3 mt-4">
                <button onClick={() => { setEditingId(mission.id); setEditName(mission.name); }} className="px-4 py-2 bg-orange-500 hover:bg-orange-400 text-white font-bold rounded transition duration-200">Edit</button>
                <button onClick={() => deleteMissionMutation.mutate(mission.id)} className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded transition duration-200">Delete</button>
                <button onClick={() => loadTelemetry(mission.id)} className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white font-bold rounded transition duration-200">
                  {activeTelemetryId === mission.id ? 'Close Telemetry' : 'View Telemetry'}
                </button>
              </div>

              {/* Telemetry Panel */}
              {activeTelemetryId === mission.id && (
                <div className="mt-6 p-5 bg-slate-900 rounded-lg border border-slate-700 text-slate-300 shadow-inner">
                  <div className="flex justify-between items-center border-b border-slate-700 pb-3 mb-3">
                    <h3 className="text-lg font-bold m-0 text-cyan-400">🛰️ Live Sensor Feed</h3>
                    <button onClick={() => triggerPing(mission.id)} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded transition duration-200">
                       Ping Ship
                    </button>
                  </div>
                  
                  {(!telemetryLogs || telemetryLogs.length === 0) ? (
                    <p className="italic text-slate-500">No signal established yet. Ping the ship.</p>
                  ) : (
                    <ul className="list-none p-0 m-0">
                      {telemetryLogs.map(log => (
                        <li key={log.id} className="py-3 border-b border-slate-700 flex justify-between items-center last:border-0">
                          <span className="font-mono text-sm text-slate-400">[{new Date(log.timestamp).toLocaleTimeString()}] {log.parameter_name}</span>
                          <span>
                            <strong className="mr-4 text-white">{log.parameter_value}</strong> 
                            <span className={`font-bold text-sm ${getStatusColorClass(log.status_level)}`}>
                              {log.status_level ? log.status_level.toUpperCase() : 'UNKNOWN'}
                            </span>
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {/* Crew Manifest Component */}
              <CrewManifest missionId={mission.id} />
              
            </div>
          ))
        )}
      </div>
    </div>
  </div>
  );
}

export default App;