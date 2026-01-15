import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const checkAuth = async () => {
        const token = localStorage.getItem('mindweaver-token');
        if (!token) {
            setLoading(false);
            setUser(null);
            return;
        }

        try {
            const response = await apiClient.get('/auth/me');
            setUser(response.data);
        } catch (err) {
            console.error('Auth check failed:', err);
            localStorage.removeItem('mindweaver-token');
            setUser(null);
            setError(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = (redirectUrl = window.location.origin + '/callback') => {
        const baseUrl = apiClient.defaults.baseURL;
        window.location.href = `${baseUrl}/auth/login?redirect_url=${encodeURIComponent(redirectUrl)}`;
    };

    const handleCallback = async (code, redirectUrl) => {
        setLoading(true);
        try {
            const response = await apiClient.post(`/auth/callback?code=${code}&redirect_url=${encodeURIComponent(redirectUrl)}`);
            const { access_token } = response.data;
            localStorage.setItem('mindweaver-token', access_token);
            await checkAuth();
            return true;
        } catch (err) {
            console.error('Callback failed:', err);
            setError(err);
            setLoading(false);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('mindweaver-token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, error, login, logout, handleCallback, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
};
