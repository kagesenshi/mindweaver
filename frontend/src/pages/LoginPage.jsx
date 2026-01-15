import React from 'react';
import { useAuth } from '../providers/AuthProvider';
import { Layers, Rocket } from 'lucide-react';

const LoginPage = () => {
    const { login } = useAuth();

    return (
        <div className="min-h-screen bg-[#08090b] flex flex-col items-center justify-center p-8 overflow-hidden relative">
            {/* Background decoration */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-600/40 mx-auto mb-6">
                        <Layers className="text-white" size={32} />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-white mb-3">Mindweaver</h1>
                    <p className="text-slate-500 text-sm">Deployment and metadata layer for data platforms.</p>
                </div>

                <div className="bg-slate-900/40 border border-slate-800/60 p-10 rounded-[40px] shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-150">
                    <h2 className="text-xl font-bold text-white mb-2 text-center">Welcome back</h2>
                    <p className="text-slate-500 text-xs text-center mb-8 uppercase tracking-widest font-medium">Enterprise SSO Login</p>

                    <button
                        onClick={() => login()}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.98] shadow-lg shadow-blue-600/20 group"
                    >
                        <Rocket size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                        CONTINUE WITH SSO
                    </button>

                    <div className="mt-8 flex items-center justify-center gap-4">
                        <div className="h-px flex-1 bg-slate-800" />
                        <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">Secure session</span>
                        <div className="h-px flex-1 bg-slate-800" />
                    </div>

                    <p className="mt-8 text-[10px] text-slate-500 text-center leading-relaxed">
                        By continuing, you agree to our Terms of Service<br />and Privacy Policy.
                    </p>
                </div>

                <div className="mt-12 flex justify-center gap-6 animate-in fade-in duration-1000 delay-500">
                    <span className="text-[10px] text-slate-600 font-mono uppercase">Nodes: Stable</span>
                    <span className="text-[10px] text-slate-600 font-mono uppercase">API: Operational</span>
                    <span className="text-[10px] text-slate-600 font-mono uppercase">v1.2.0-core</span>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
