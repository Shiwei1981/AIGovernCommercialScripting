export const msalConfig = {
  auth: {
    clientId: window.__env?.ENTRA_CLIENT_ID || '',
    authority: window.__env?.ENTRA_AUTHORITY || '',
    redirectUri: window.__env?.ENTRA_REDIRECT_URI || `${window.location.origin}/auth/callback`,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: ['api://commercialscripting/access_as_user'],
};
