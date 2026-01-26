import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import Snackbar from '../components/Snackbar';
import apiClient from '../services/api';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);

    const addNotification = useCallback((message, type = 'error') => {
        const id = Date.now();
        setNotifications(prev => [...prev, { id, message, type }]);
    }, []);

    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    const showError = useCallback((message) => addNotification(message, 'error'), [addNotification]);
    const showSuccess = useCallback((message) => addNotification(message, 'success'), [addNotification]);
    const showInfo = useCallback((message) => addNotification(message, 'info'), [addNotification]);
    const showWarning = useCallback((message) => addNotification(message, 'warning'), [addNotification]);

    useEffect(() => {
        // Register a global error handler for the API client
        const interceptor = apiClient.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 422) {
                    const detail = error.response.data?.detail;
                    let message = "Validation error";

                    if (Array.isArray(detail) && detail.length > 0) {
                        message = detail[0].msg || message;
                    } else if (typeof detail === 'string') {
                        message = detail;
                    } else if (error.response.data?.message) {
                        message = error.response.data.message;
                    }

                    showError(message);
                }
                return Promise.reject(error);
            }
        );

        return () => {
            apiClient.interceptors.response.eject(interceptor);
        };
    }, [showError]);

    return (
        <NotificationContext.Provider value={{ showError, showSuccess, showInfo, showWarning }}>
            {children}
            {notifications.map(n => (
                <Snackbar
                    key={n.id}
                    message={n.message}
                    type={n.type}
                    onClose={() => removeNotification(n.id)}
                />
            ))}
        </NotificationContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useNotification = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotification must be used within a NotificationProvider');
    }
    return context;
};
