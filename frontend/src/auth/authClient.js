import { PublicClientApplication } from '@azure/msal-browser';
import { loginRequest, msalConfig } from './msalConfig.js';

const app = new PublicClientApplication(msalConfig);

export async function ensureSignedIn() {
  await app.initialize();
  const result = await app.handleRedirectPromise();
  if (result?.account) {
    app.setActiveAccount(result.account);
  }
  if (!app.getActiveAccount()) {
    await app.loginRedirect(loginRequest);
  }
}

export async function signIn() {
  await app.loginRedirect(loginRequest);
}

export async function signOut() {
  const account = app.getActiveAccount();
  if (account) {
    await app.logoutRedirect({ account });
  }
}

export async function getAccessToken() {
  const account = app.getActiveAccount();
  if (!account) {
    throw new Error('No signed-in account');
  }
  const token = await app.acquireTokenSilent({ ...loginRequest, account });
  return token.accessToken;
}
