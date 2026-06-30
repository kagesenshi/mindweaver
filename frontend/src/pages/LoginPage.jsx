// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';
import { Layers, Rocket, LogIn, Loader2, WifiOff, RefreshCw } from 'lucide-react';
import apiClient from '../services/api';

const LoginPage = () => {
    const { login, loginLocal, brandName, brandLogo, brandBgColor, fetchBrand } = useAuth();
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [oidcEnabled, setOidcEnabled] = useState(null);
    const [connectionError, setConnectionError] = useState(false);

    const fetchFeatureFlags = async () => {
        setConnectionError(false);
        try {
            const baseUrl = apiClient.defaults.baseURL;
            const rootUrl = baseUrl.replace(/\/api\/v1\/?$/, '');
            const response = await fetch(`${rootUrl}/feature-flags`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setOidcEnabled(data.oidc_enabled ?? false);
            // Immediately load/refresh the brand config on successful connection
            fetchBrand();
        } catch (err) {
            console.error('Failed to fetch feature flags:', err);
            setOidcEnabled(false);
            setConnectionError(true);
        }
    };

    useEffect(() => {
        /**
         * Fetch feature flags and brand settings from the backend when the login page mounts.
         */
        fetchFeatureFlags();
        fetchBrand();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);



    const handleLocalLogin = async (e) => {
        /**
         * Handle local username/password login submission.
         */
        e.preventDefault();
        setError(null);
        setSubmitting(true);
        try {
            const success = await loginLocal(username, password);
            if (success) {
                navigate('/');
            } else {
                setError('Invalid username or password.');
            }
        } catch (err) {
            console.error(err);
            setError('Login failed. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#08090b] flex flex-col items-center justify-center p-8 overflow-hidden relative">
            {/* Background decoration */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                {!connectionError && (
                    <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div 
                            className="w-32 h-32 bg-blue-600 rounded-[32px] flex items-center justify-center shadow-2xl shadow-blue-600/40 mx-auto mb-6 overflow-hidden"
                            style={brandBgColor ? { backgroundColor: brandBgColor, boxShadow: `0 25px 50px -12px ${brandBgColor}66` } : {}}
                        >
                            {brandLogo ? (
                                <div 
                                    className="w-24 h-24 text-white flex items-center justify-center svg-container [&>svg]:w-full [&>svg]:h-full [&>svg]:stroke-current" 
                                    dangerouslySetInnerHTML={{ __html: brandLogo }} 
                                />
                            ) : (
                                <Layers className="text-white" size={64} />
                            )}
                        </div>

                        <h1 className="text-5xl font-bold tracking-tight text-white mb-3">{brandName}</h1>
                        <p className="text-slate-500 text-base">Deployment and metadata layer for data platforms.</p>
                    </div>
                )}


                <div className="bg-slate-900/40 border border-slate-800/60 p-10 rounded-[40px] shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-150">
                    {connectionError ? (
                        <div className="flex flex-col items-center justify-center text-center py-6">
                            <div className="w-16 h-16 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center justify-center text-red-500 mb-6 animate-pulse">
                                <WifiOff size={32} />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-3">Unable to Connect</h2>
                            <p className="text-slate-400 text-sm max-w-sm mb-8 leading-relaxed">
                                Could not establish a connection to the backend API. Please check if the server is running and try again.
                            </p>
                            <button
                                id="retry-connection-button"
                                onClick={fetchFeatureFlags}
                                className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.98] group"
                            >
                                <RefreshCw size={18} className="group-hover:rotate-180 transition-transform duration-500" />
                                RETRY CONNECTION
                            </button>
                        </div>
                    ) : (
                        <>
                            <h2 className="text-3xl font-bold text-white mb-2 text-center">Welcome back</h2>
                            <p className="text-slate-500 text-base text-center mb-8 uppercase tracking-widest font-medium">Sign In</p>

                            {/* Local login form */}
                            <form onSubmit={handleLocalLogin} className="space-y-4 mb-6" id="local-login-form">
                                <div>
                                    <input
                                        id="login-username"
                                        type="text"
                                        placeholder="Username"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="w-full bg-slate-800/60 border border-slate-700/60 text-white placeholder-slate-500 px-4 py-3.5 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                                        required
                                        disabled={submitting}
                                    />
                                </div>
                                <div>
                                    <input
                                        id="login-password"
                                        type="password"
                                        placeholder="Password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-slate-800/60 border border-slate-700/60 text-white placeholder-slate-500 px-4 py-3.5 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                                        required
                                        disabled={submitting}
                                    />
                                </div>

                                {error && (
                                    <p id="login-error" className="text-red-400 text-sm text-center">{error}</p>
                                )}

                                <button
                                    id="login-submit"
                                    type="submit"
                                    disabled={submitting}
                                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.98] shadow-lg shadow-blue-600/20 group disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {submitting ? (
                                        <Loader2 size={18} className="animate-spin" />
                                    ) : (
                                        <LogIn size={18} className="group-hover:translate-x-1 transition-transform" />
                                    )}
                                    {submitting ? 'SIGNING IN...' : 'SIGN IN'}
                                </button>
                            </form>

                            {/* OIDC login - only shown when oidc_enabled is true */}
                            {oidcEnabled && (
                                <>
                                    <div className="flex items-center justify-center gap-4 mb-6">
                                        <div className="h-px flex-1 bg-slate-800" />
                                        <span className="text-sm text-slate-600 font-bold uppercase tracking-widest">Or</span>
                                        <div className="h-px flex-1 bg-slate-800" />
                                    </div>

                                    <button
                                        id="oidc-login-button"
                                        onClick={() => login()}
                                        className="w-full bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/60 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.98] group"
                                    >
                                        <Rocket size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                                        CONTINUE WITH SSO
                                    </button>
                                </>
                            )}

                            <div className="mt-8 flex items-center justify-center gap-4">
                                <div className="h-px flex-1 bg-slate-800" />
                                <span className="text-sm text-slate-600 font-bold uppercase tracking-widest">Secure session</span>
                                <div className="h-px flex-1 bg-slate-800" />
                            </div>

                            <p className="mt-8 text-sm text-slate-500 text-center leading-relaxed">
                                By continuing, you agree to our Terms of Service<br />and Privacy Policy.
                            </p>
                        </>
                    )}
                </div>

            </div>
        </div>
    );
};

export default LoginPage;
