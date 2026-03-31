import { searchGenerations } from '../services/apiClient.js';

export function renderHistoryPage(container) {
  container.innerHTML = `
    <section>
      <h2>History Search</h2>
      <form id="history-form">
        <label>User ID <input id="user-id" /></label>
        <label>Session ID <input id="session-id" /></label>
        <label>Generation ID <input id="generation-id" /></label>
        <button type="submit">Search</button>
      </form>
      <pre id="history-output"></pre>
    </section>
  `;

  container.querySelector('#history-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const params = {};
    const userId = container.querySelector('#user-id').value.trim();
    const sessionId = container.querySelector('#session-id').value.trim();
    const generationId = container.querySelector('#generation-id').value.trim();
    if (userId) params.userId = userId;
    if (sessionId) params.sessionId = sessionId;
    if (generationId) params.generationId = generationId;

    try {
      const result = await searchGenerations(params);
      container.querySelector('#history-output').textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      container.querySelector('#history-output').textContent = String(error);
    }
  });
}
