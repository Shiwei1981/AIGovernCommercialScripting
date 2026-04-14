---
agent: speckit.checklist
---

# CommercialScripting Quality Checklist

- [ ] Requirements preserve Entra sign-in, Azure OpenAI, Azure AI Search, Azure SQL, history search, and auditability.
- [ ] Generation identity and audit contracts align with the portfolio shared-contract definitions.
- [ ] Database design avoids modification of existing tables.
- [ ] Docker -> ACR -> Azure Web App deployment assumptions are explicit.
- [ ] Frontend and backend single Docker image/container packaging requirement is explicit.
- [ ] Environment-variable and secret-handling rules are fully defined.
- [ ] Azure Web App App Settings are defined as the runtime configuration injection path.
- [ ] Delivered code paths contain no placeholder or mock-only implementations for core integrations.
- [ ] Test cases cover sign-in, generation, search, auditability, and failure handling.
- [ ] A developer-machine direct testing method is documented and can run core workflows without Docker packaging, ACR, or Azure Web App deployment.
- [ ] Documentation-validation items are assigned for direct Azure OpenAI SDK/REST, AI Search, Entra, and Azure SQL.
- [ ] Any uncertainty is defaulted and marked as "待 clarify 确认" with owner and due date.
- [ ] Constraints do not cite deleted implementation history as mandatory basis.
- [ ] Spec, plan, and tasks are consistent and contain no conflicting deployment/runtime instructions.
- [ ] Requirements-to-tasks traceability is explicit for high-risk integrations and governance controls.
