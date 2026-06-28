import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../services/api';

const AuthContext = createContext(null);

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [brandName, setBrandName] = useState('Mindweaver');
    const [brandLogo, setBrandLogo] = useState('');
    const [brandBgColor, setBrandBgColor] = useState(null);

    const fetchBrand = async () => {
        try {
            const response = await apiClient.get('/_brand');
            if (response.data.name) {
                setBrandName(response.data.name);
            }
            if (response.data.logo) {
                setBrandLogo(response.data.logo);
            }
            if (response.data.bgcolor) {
                setBrandBgColor(response.data.bgcolor);
            }
        } catch (err) {
            console.error('Failed to fetch brand configuration:', err);
        }
    };

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
        fetchBrand();
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

    const loginLocal = async (username, password) => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.post('/auth/login', {
                username,
                password,
            });
            const { access_token } = response.data;
            localStorage.setItem('mindweaver-token', access_token);
            await checkAuth();
            return true;
        } catch (err) {
            console.error('Local login failed:', err);
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
        <AuthContext.Provider value={{ user, loading, error, login, loginLocal, logout, handleCallback, checkAuth, brandName, brandLogo, brandBgColor, fetchBrand }}>
            {children}
        </AuthContext.Provider>
    );
};


