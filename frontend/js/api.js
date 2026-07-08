// ============================================================
// api.js - Backend REST API client layer
// ============================================================

const BASE_URL = 'http://localhost:8080/api';

const API = {
    async request(endpoint, options = {}) {
        const token = Auth.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers
        };

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, config);
            if (response.status === 413 || response.status === 401) {
                // Token invalid or expired
                Auth.logout();
                throw new Error("Session expired. Please log in again.");
            }
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `HTTP error! Status: ${response.status}`);
            }

            // If API returns PDF or byte array
            if (config.responseType === 'blob') {
                return await response.blob();
            }

            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${endpoint}:`, error);
            throw error;
        }
    },

    // Auth actions
    login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },

    register(username, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },

    // Analysis actions
    analyze(brand) {
        return this.request('/analysis/analyze', {
            method: 'POST',
            body: JSON.stringify({ brand })
        });
    },

    // Report history actions
    getHistory() {
        return this.request('/reports/history', {
            method: 'GET'
        });
    },

    async downloadPdf(reportId, brandName) {
        const blob = await this.request(`/reports/${reportId}/pdf`, {
            method: 'GET',
            responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${brandName}_Brand_Report.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    }
};
