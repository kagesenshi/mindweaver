import { useState, useCallback, useEffect } from 'react';
import apiClient from '../services/api';

export const useProjects = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchProjects = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/projects');
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

    const deleteProject = async (id, confirmName) => {
        await apiClient.delete(`/projects/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
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

    const deleteDataSource = async (id, confirmName) => {
        await apiClient.delete(`/data_sources/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
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

    const updatePlatformState = async (id, state, headers = {}) => {
        await apiClient.post(`/platform/pgsql/${id}/_state`, state, { headers });
        await fetchPlatforms();
    };

    const deletePlatform = async (id, confirmName) => {
        await apiClient.delete(`/platform/pgsql/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await fetchPlatforms();
    };

    const getPlatformState = async (id) => {
        const response = await apiClient.get(`/platform/pgsql/${id}/_state`);
        return response.data;
    };

    const refreshPlatformState = async (id) => {
        const response = await apiClient.post(`/platform/pgsql/${id}/_refresh`);
        return response.data;
    };

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return { platforms, loading, error, fetchPlatforms, createPlatform, updatePlatformState, deletePlatform, getPlatformState, refreshPlatformState };
};

export const useK8sClusters = () => {
    const [clusters, setClusters] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchClusters = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/k8s_clusters');
            setClusters(response.data.records || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createCluster = async (data) => {
        const response = await apiClient.post('/k8s_clusters', data);
        await fetchClusters();
        return response.data;
    };

    const updateCluster = async (id, data) => {
        const response = await apiClient.put(`/k8s_clusters/${id}`, data);
        await fetchClusters();
        return response.data;
    };

    const deleteCluster = async (id, confirmName) => {
        await apiClient.delete(`/k8s_clusters/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await fetchClusters();
    };

    useEffect(() => {
        fetchClusters();
    }, [fetchClusters]);

    return { clusters, loading, error, fetchClusters, createCluster, updateCluster, deleteCluster };
};

export const useS3Storages = () => {
    const [storages, setStorages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchStorages = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/s3_storages');
            setStorages(response.data.records || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createStorage = async (data) => {
        const response = await apiClient.post('/s3_storages', data);
        await fetchStorages();
        return response.data;
    };

    const updateStorage = async (id, data) => {
        const response = await apiClient.put(`/s3_storages/${id}`, data);
        await fetchStorages();
        return response.data;
    };

    const deleteStorage = async (id, confirmName) => {
        await apiClient.delete(`/s3_storages/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await fetchStorages();
    };

    const testConnection = async (data) => {
        const response = await apiClient.post('/s3_storages/_test-connection', data);
        return response.data;
    };

    const browseStorage = async (id, params = {}) => {
        const response = await apiClient.get(`/s3_storages/${id}/_fs`, { params });
        return response.data;
    };

    const uploadFile = async (id, bucket, prefix, file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await apiClient.post(`/s3_storages/${id}/_fs`, formData, {
            params: { bucket, prefix, action: 'put' },
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    };

    const downloadFile = async (id, bucket, key) => {
        try {
            // Request the presigned URL as JSON
            const response = await apiClient.get(`/s3_storages/${id}/_fs`, {
                params: { bucket, key, action: 'get' },
                headers: {
                    'Accept': 'application/json'
                }
            });

            const { url } = response.data;
            if (url) {
                // Trigger download by opening the URL
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                // Note: We don't set 'download' attribute here because S3/presigned URLs
                // usually handle Content-Disposition themselves, and it might error
                // with some CORS policies if the domains differ.
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        } catch (err) {
            console.error("Failed to download file:", err);
            throw err;
        }
    };

    const deleteFile = async (id, bucket, key) => {
        const response = await apiClient.post(`/s3_storages/${id}/_fs`, null, {
            params: { bucket, key, action: 'rm' }
        });
        return response.data;
    };

    useEffect(() => {
        fetchStorages();
    }, [fetchStorages]);

    return { storages, loading, error, fetchStorages, createStorage, updateStorage, deleteStorage, testConnection, browseStorage, uploadFile, downloadFile, deleteFile };
};
