import { useState, useCallback, useEffect } from 'react';
import apiClient from '../services/api';

export const useProjects = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchProjects = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get(`/projects?_cb=${Date.now()}`);
            setProjects(response.data.records || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createProject = async (data) => {
        const response = await apiClient.post('/projects', data);
        await fetchProjects();
        return response.data;
    };

    const updateProject = async (id, data) => {
        const response = await apiClient.put(`/projects/${id}`, data);
        await fetchProjects();
        return response.data;
    };

    const deleteProject = async (id) => {
        await apiClient.delete(`/projects/${id}`);
        await fetchProjects();
    };

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    return { projects, loading, error, fetchProjects, createProject, updateProject, deleteProject };
};

export const useDataSources = () => {
    const [dataSources, setDataSources] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchDataSources = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/data_sources');
            setDataSources(response.data.records || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createDataSource = async (data) => {
        const response = await apiClient.post('/data_sources', data);
        await fetchDataSources();
        return response.data;
    };

    const updateDataSource = async (id, data) => {
        const response = await apiClient.put(`/data_sources/${id}`, data);
        await fetchDataSources();
        return response.data;
    };

    const deleteDataSource = async (id) => {
        await apiClient.delete(`/data_sources/${id}`);
        await fetchDataSources();
    };

    const testConnection = async (id) => {
        const response = await apiClient.post(`/data_sources/${id}/_test-connection`);
        return response.data;
    };

    useEffect(() => {
        fetchDataSources();
    }, [fetchDataSources]);

    return { dataSources, loading, error, fetchDataSources, createDataSource, updateDataSource, deleteDataSource, testConnection };
};

export const usePgSql = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/pgsql');
            setPlatforms(response.data.records || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = async (data) => {
        const response = await apiClient.post('/platform/pgsql', data);
        await fetchPlatforms();
        return response.data;
    };

    const updatePlatformState = async (id, state) => {
        await apiClient.post(`/platform/pgsql/${id}/_state`, state);
        await fetchPlatforms();
    };

    const deletePlatform = async (id) => {
        await apiClient.delete(`/platform/pgsql/${id}`);
        await fetchPlatforms();
    };

    const getPlatformState = async (id) => {
        const response = await apiClient.get(`/platform/pgsql/${id}/_state`);
        return response.data;
    };

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return { platforms, loading, error, fetchPlatforms, createPlatform, updatePlatformState, deletePlatform, getPlatformState };
};
