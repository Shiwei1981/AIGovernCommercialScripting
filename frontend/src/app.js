import { ensureSignedIn, signIn, signOut } from './auth/authClient.js';
import { renderGeneratePage } from './pages/generate.js';
import { renderHistoryPage } from './pages/history.js';
import { renderAuditTracePage } from './pages/audit-trace.js';

function createShell() {
  const root = document.getElementById('app');
  root.innerHTML = `
    <header>
      <h1>CommercialScripting</h1>
      <nav>
        <button id="signin-btn">Sign in</button>
        <button id="signout-btn">Sign out</button>
      </nav>
    </header>
    <main id="page"></main>
  `;

  document.getElementById('signin-btn').addEventListener('click', signIn);
  document.getElementById('signout-btn').addEventListener('click', signOut);
}

function route() {
  const page = document.getElementById('page');
  const hash = window.location.hash || '#/generate';

  if (hash.startsWith('#/history')) {
    renderHistoryPage(page);
    return;
  }
  if (hash.startsWith('#/audit')) {
    renderAuditTracePage(page);
    return;
  }
  renderGeneratePage(page);
}

async function bootstrap() {
  createShell();
  await ensureSignedIn();
  window.addEventListener('hashchange', route);
  route();
}

bootstrap();
