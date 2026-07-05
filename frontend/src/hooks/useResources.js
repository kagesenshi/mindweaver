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
            setProjects(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createProject = useCallback(async (data) => {
        const response = await apiClient.post('/projects', data);
        await fetchProjects();
        return response.data;
    }, [fetchProjects]);

    const updateProject = useCallback(async (id, data) => {
        const response = await apiClient.put(`/projects/${id}`, data);
        await fetchProjects();
        return response.data;
    }, [fetchProjects]);

    const deleteProject = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/projects/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchProjects();
    }, [fetchProjects]);

    const getProjectState = useCallback(async (id) => {
        const response = await apiClient.get(`/projects/${id}/_state`);
        return response.data;
    }, []);

    const refreshProjectState = useCallback(async (id) => {
        const response = await apiClient.post(`/projects/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/projects/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/projects/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    const getProjectCertManager = useCallback(async (id) => {
        const response = await apiClient.get(`/projects/${id}/_cert_manager`);
        return response.data;
    }, []);

    const getProjectIssuerCert = useCallback(async (id, name, kind, namespace) => {
        const response = await apiClient.get(`/projects/${id}/_issuer_cert`, {
            params: { name, kind, namespace }
        });
        return response.data;
    }, []);

    const deployProjectIssuer = useCallback(async (id) => {
        const response = await apiClient.post(`/projects/${id}/_deploy_issuer`);
        return response.data;
    }, []);

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    return { projects, loading, error, fetchProjects, createProject, updateProject, deleteProject, getProjectState, refreshProjectState, fetchActions, executeAction, getProjectCertManager, getProjectIssuerCert, deployProjectIssuer };
};


const createGenericSourceHook = (endpoint) => {
    return () => {
        const [items, setItems] = useState([]);
        const [loading, setLoading] = useState(false);
        const [error, setError] = useState(null);

        const fetchItems = useCallback(async () => {
            setLoading(true);
            try {
                const response = await apiClient.get(endpoint);
                setItems(response.data.data || []);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        }, []);

        const createItem = useCallback(async (data) => {
            const response = await apiClient.post(endpoint, data);
            await fetchItems();
            return response.data;
        }, [fetchItems]);

        const updateItem = useCallback(async (id, data) => {
            const response = await apiClient.put(`${endpoint}/${id}`, data);
            await fetchItems();
            return response.data;
        }, [fetchItems]);

        const deleteItem = useCallback(async (id, confirmName) => {
            await apiClient.delete(`${endpoint}/${id}`, {
                headers: { 'X-RESOURCE-NAME': confirmName }
            });
            await new Promise(resolve => setTimeout(resolve, 500));
            await fetchItems();
        }, [fetchItems]);

        const testConnection = useCallback(async (id) => {
            const response = await apiClient.post(`${endpoint}/${id}/_test-connection`);
            return response.data;
        }, []);

        useEffect(() => {
            fetchItems();
        }, [fetchItems]);

        return { items, loading, error, fetchItems, createItem, updateItem, deleteItem, testConnection };
    };
};

export const useDatabaseSources = createGenericSourceHook('/database-sources');

export const usePgSql = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/pgsql');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/pgsql', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/pgsql/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/pgsql/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/pgsql/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/pgsql/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/pgsql/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/pgsql/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useK8sClusters = () => {
    const [clusters, setClusters] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchClusters = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/k8s_clusters');
            setClusters(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createCluster = useCallback(async (data) => {
        const response = await apiClient.post('/k8s_clusters', data);
        await fetchClusters();
        return response.data;
    }, [fetchClusters]);

    const updateCluster = useCallback(async (id, data) => {
        const response = await apiClient.put(`/k8s_clusters/${id}`, data);
        await fetchClusters();
        return response.data;
    }, [fetchClusters]);

    const deleteCluster = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/k8s_clusters/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchClusters();
    }, [fetchClusters]);

    const getClusterState = useCallback(async (id) => {
        const response = await apiClient.get(`/k8s_clusters/${id}/_state`);
        return response.data;
    }, []);

    const refreshClusterState = useCallback(async (id) => {
        const response = await apiClient.post(`/k8s_clusters/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/k8s_clusters/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/k8s_clusters/${id}/_actions`, { action, parameters });
        await fetchClusters();
        return response.data;
    }, [fetchClusters]);

    useEffect(() => {
        fetchClusters();
    }, [fetchClusters]);

    return {
        clusters, loading, error,
        fetchClusters, createCluster, updateCluster, deleteCluster,
        getClusterState, refreshClusterState, fetchActions, executeAction
    };
};

export const useS3Storages = () => {
    const [storages, setStorages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchStorages = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/s3_storages');
            setStorages(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createStorage = useCallback(async (data) => {
        const response = await apiClient.post('/s3_storages', data);
        await fetchStorages();
        return response.data;
    }, [fetchStorages]);

    const updateStorage = useCallback(async (id, data) => {
        const response = await apiClient.put(`/s3_storages/${id}`, data);
        await fetchStorages();
        return response.data;
    }, [fetchStorages]);

    const deleteStorage = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/s3_storages/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchStorages();
    }, [fetchStorages]);

    const testConnection = useCallback(async (data) => {
        const response = await apiClient.post('/s3_storages/_test-connection', data);
        return response.data;
    }, []);

    const browseStorage = useCallback(async (id, params = {}) => {
        const response = await apiClient.get(`/s3_storages/${id}/_fs`, { params });
        return response.data;
    }, []);

    const uploadFile = useCallback(async (id, bucket, prefix, file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await apiClient.post(`/s3_storages/${id}/_fs`, formData, {
            params: { bucket, prefix, action: 'put' },
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    }, []);

    const downloadFile = useCallback(async (id, bucket, key) => {
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
    }, []);

    const deleteFile = useCallback(async (id, bucket, key) => {
        const response = await apiClient.post(`/s3_storages/${id}/_fs`, null, {
            params: { bucket, key, action: 'rm' }
        });
        return response.data;
    }, []);

    useEffect(() => {
        fetchStorages();
    }, [fetchStorages]);

    return { storages, loading, error, fetchStorages, createStorage, updateStorage, deleteStorage, testConnection, browseStorage, uploadFile, downloadFile, deleteFile };
};

export const useLdapConfigs = () => {
    const [configs, setConfigs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchConfigs = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/ldap_configs');
            setConfigs(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createConfig = useCallback(async (data) => {
        const response = await apiClient.post('/ldap_configs', data);
        await fetchConfigs();
        return response.data;
    }, [fetchConfigs]);

    const updateConfig = useCallback(async (id, data) => {
        const response = await apiClient.put(`/ldap_configs/${id}`, data);
        await fetchConfigs();
        return response.data;
    }, [fetchConfigs]);

    const deleteConfig = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/ldap_configs/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchConfigs();
    }, [fetchConfigs]);

    const testConnection = useCallback(async (data) => {
        const response = await apiClient.post('/ldap_configs/_test-connection', data);
        return response.data;
    }, []);

    useEffect(() => {
        fetchConfigs();
    }, [fetchConfigs]);

    return { configs, loading, error, fetchConfigs, createConfig, updateConfig, deleteConfig, testConnection };
};

export const useHiveMetastore = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/hive-metastore');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/hive-metastore', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/hive-metastore/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/hive-metastore/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/hive-metastore/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/hive-metastore/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/hive-metastore/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/hive-metastore/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useTrino = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/trino');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/trino', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/trino/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/trino/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/trino/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/trino/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/trino/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/trino/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useAirflow = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/airflow');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/airflow', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/airflow/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/airflow/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/airflow/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/airflow/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/airflow/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/airflow/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useSuperset = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/superset');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/superset', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/superset/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/superset/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/superset/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/superset/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/superset/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/superset/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};
export const useProjectLocalUsers = createGenericSourceHook('/project-local-users');


export const useKafka = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/kafka');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/kafka', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/kafka/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/kafka/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/kafka/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/kafka/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/kafka/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/kafka/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useNifi = () => {
    const [platforms, setPlatforms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPlatforms = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/platform/nifi');
            setPlatforms(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPlatform = useCallback(async (data) => {
        const response = await apiClient.post('/platform/nifi', data);
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const updatePlatformState = useCallback(async (id, state, headers = {}) => {
        const response = await apiClient.post(`/platform/nifi/${id}/_state`, state, { headers });
        await fetchPlatforms();
        return response.data;
    }, [fetchPlatforms]);

    const deletePlatform = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/platform/nifi/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchPlatforms();
    }, [fetchPlatforms]);

    const getPlatformState = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/nifi/${id}/_state`);
        return response.data;
    }, []);

    const refreshPlatformState = useCallback(async (id) => {
        const response = await apiClient.post(`/platform/nifi/${id}/_refresh`);
        return response.data;
    }, []);

    const fetchActions = useCallback(async (id) => {
        const response = await apiClient.get(`/platform/nifi/${id}/_actions`);
        return response.data.actions || [];
    }, []);

    const executeAction = useCallback(async (id, action, parameters = {}) => {
        const response = await apiClient.post(`/platform/nifi/${id}/_actions`, { action, parameters });
        return response.data;
    }, []);

    useEffect(() => {
        fetchPlatforms();
    }, [fetchPlatforms]);

    return {
        platforms,
        loading,
        error,
        fetchPlatforms,
        createPlatform,
        updatePlatformState,
        deletePlatform,
        getPlatformState,
        refreshPlatformState,
        fetchActions,
        executeAction
    };
};

export const useSSHKeys = () => {
    const [keys, setKeys] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchKeys = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/ssh_keys');
            setKeys(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createKey = useCallback(async (data) => {
        const response = await apiClient.post('/ssh_keys', data);
        await fetchKeys();
        return response.data;
    }, [fetchKeys]);

    const updateKey = useCallback(async (id, data) => {
        const response = await apiClient.put(`/ssh_keys/${id}`, data);
        await fetchKeys();
        return response.data;
    }, [fetchKeys]);

    const deleteKey = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/ssh_keys/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchKeys();
    }, [fetchKeys]);

    useEffect(() => {
        fetchKeys();
    }, [fetchKeys]);

    return { keys, loading, error, fetchKeys, createKey, updateKey, deleteKey };
};

export const useGitRepos = () => {
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchRepos = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/git_repos');
            setRepos(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createRepo = useCallback(async (data) => {
        const response = await apiClient.post('/git_repos', data);
        await fetchRepos();
        return response.data;
    }, [fetchRepos]);

    const updateRepo = useCallback(async (id, data) => {
        const response = await apiClient.put(`/git_repos/${id}`, data);
        await fetchRepos();
        return response.data;
    }, [fetchRepos]);

    const deleteRepo = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/git_repos/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchRepos();
    }, [fetchRepos]);

    const testConnection = useCallback(async (data) => {
        const response = await apiClient.post('/git_repos/_test-connection', data);
        return response.data;
    }, []);

    useEffect(() => {
        fetchRepos();
    }, [fetchRepos]);

    return { repos, loading, error, fetchRepos, createRepo, updateRepo, deleteRepo, testConnection };
};

export const useContainerRegistries = () => {
    const [registries, setRegistries] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchRegistries = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/container_registries');
            setRegistries(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createRegistry = useCallback(async (data) => {
        const response = await apiClient.post('/container_registries', data);
        await fetchRegistries();
        return response.data;
    }, [fetchRegistries]);

    const updateRegistry = useCallback(async (id, data) => {
        const response = await apiClient.put(`/container_registries/${id}`, data);
        await fetchRegistries();
        return response.data;
    }, [fetchRegistries]);

    const deleteRegistry = useCallback(async (id, confirmName) => {
        await apiClient.delete(`/container_registries/${id}`, {
            headers: { 'X-RESOURCE-NAME': confirmName }
        });
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchRegistries();
    }, [fetchRegistries]);

    const testConnection = useCallback(async (data) => {
        const response = await apiClient.post('/container_registries/_test-connection', data);
        return response.data;
    }, []);

    useEffect(() => {
        fetchRegistries();
    }, [fetchRegistries]);

    return { registries, loading, error, fetchRegistries, createRegistry, updateRegistry, deleteRegistry, testConnection };
};

export const useStacks = () => {
    const [stacks, setStacks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchStacks = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/stacks');
            setStacks(response.data.data || []);
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStacks();
    }, [fetchStacks]);

    return { stacks, loading, error, fetchStacks };
};

export const useUsers = createGenericSourceHook('/users');



