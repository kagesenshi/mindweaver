import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to attach the token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('mindweaver-token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        const project = localStorage.getItem('mindweaver-project');
        if (project) {
            try {
                const projectData = JSON.parse(project);
                if (projectData && projectData.id) {
                    config.headers['x-project-id'] = projectData.id;
                }
            } catch (e) {
                console.error("Failed to parse project from local storage", e);
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle errors (e.g., 401 Unauthorized)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Clear token and redirect to login if unauthorized
            localStorage.removeItem('mindweaver-token');
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;
