import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../providers/AuthProvider';

const CallbackPage = () => {
    const [searchParams] = useSearchParams();
    const { handleCallback } = useAuth();
    const navigate = useNavigate();
    const processed = useRef(false);

    useEffect(() => {
        if (processed.current) return;

        const code = searchParams.get('code');
        const redirectUrl = window.location.origin + '/callback';

        if (code) {
            processed.current = true;
            handleCallback(code, redirectUrl).then((success) => {
                if (success) {
                    navigate('/');
                } else {
                    navigate('/login?error=callback_failed');
                }
            });
        } else {
            navigate('/login');
        }
    }, [searchParams, handleCallback, navigate]);

    return (
        <div className="min-h-screen bg-[#08090b] flex flex-col items-center justify-center">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-slate-500 font-medium animate-pulse">Processing login...</p>
        </div>
    );
};

export default CallbackPage;
