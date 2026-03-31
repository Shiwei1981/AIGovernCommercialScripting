# VM Manual Binding and Consent Steps

These steps remain manual exceptions for demo deployment.

1. Install TLS certificate and private key on CommercialScriptingVM.
2. Bind certificate to HTTPS listener for app domain.
3. Configure DNS A record to CommercialScriptingVM public IP.
4. Update Entra app redirect URI to deployed callback URL.
5. Grant or confirm tenant consent for API scope.
6. Populate runtime environment variables through secure host configuration.
7. Verify end-to-end sign-in and HTTPS API access.
