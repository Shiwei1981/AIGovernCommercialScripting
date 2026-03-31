# Entra App Registration Configuration

## App Model

- Single CommercialScripting SPA app registration for frontend sign-in.
- Backend API exposed with delegated scope `access_as_user`.

## Required Steps

1. Register app `CommercialScripting` in Entra ID.
2. Add SPA redirect URI:
   - `https://<demo-domain>/auth/callback`
3. Enable authorization code flow with PKCE for SPA.
4. Expose API scope:
   - `api://<backend-app-id>/access_as_user`
5. Grant consent for users in the tenant.
6. Configure frontend with `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`, and `ENTRA_REDIRECT_URI`.
7. Configure backend expected audience as the API application ID URI.

## Manual Exception Notes

- Consent prompts and tenant policy exceptions may require admin action.
- Redirect URI updates are manual deployment steps and must be tracked per environment.
