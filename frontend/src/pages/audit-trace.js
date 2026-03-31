import { getAuditTrace } from '../services/apiClient.js';

export function renderAuditTracePage(container) {
  container.innerHTML = `
    <section>
      <h2>Audit Trace</h2>
      <form id="audit-form">
        <label>Generation ID <input id="generation-id" required /></label>
        <button type="submit">Load Trace</button>
      </form>
      <pre id="audit-output"></pre>
    </section>
  `;

  container.querySelector('#audit-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const generationId = container.querySelector('#generation-id').value.trim();
      const result = await getAuditTrace(generationId);
      container.querySelector('#audit-output').textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      container.querySelector('#audit-output').textContent = String(error);
    }
  });
}
