// ============================================================
// auth.js - Auth Helpers & Session State management
// ============================================================

const TOKEN_KEY = 'brand_analyzer_jwt_token';

const Auth = {
    saveToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
    },

    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    },

    logout() {
        localStorage.removeItem(TOKEN_KEY);
        window.location.href = 'login.html';
    },

    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        
        try {
            // Check if JWT token is expired
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp * 1000;
            return Date.now() < exp;
        } catch (e) {
            return false;
        }
    },

    requireAuth() {
        if (!this.isAuthenticated()) {
            this.logout();
        }
    },

    redirectIfAuthenticated() {
        if (this.isAuthenticated()) {
            window.location.href = 'dashboard.html';
        }
    }
};
