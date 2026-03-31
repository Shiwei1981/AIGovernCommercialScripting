import { createGeneration } from '../services/apiClient.js';

export function renderGeneratePage(container) {
  container.innerHTML = `
    <section>
      <h2>Generate Script</h2>
      <form id="generate-form">
        <label>Session ID <input id="session-id" required /></label>
        <label>Prompt <textarea id="prompt" required></textarea></label>
        <label><input type="checkbox" id="use-recent-news" checked /> Use recent allowlisted news</label>
        <button type="submit">Generate</button>
      </form>
      <pre id="generate-output"></pre>
      <ul id="citation-list"></ul>
    </section>
  `;

  container.querySelector('#generate-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      sessionId: container.querySelector('#session-id').value,
      prompt: container.querySelector('#prompt').value,
      useRecentNews: container.querySelector('#use-recent-news').checked,
    };

    try {
      const result = await createGeneration(payload);
      container.querySelector('#generate-output').textContent = result.responseText || result.failureReason;
      container.querySelector('#citation-list').innerHTML = (result.sourceReferences || [])
        .map((item) => `<li><a href="${item.canonicalUrl}" target="_blank" rel="noreferrer">${item.sourceTitle}</a></li>`)
        .join('');
    } catch (error) {
      container.querySelector('#generate-output').textContent = String(error);
    }
  });
}
