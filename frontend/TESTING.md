# Frontend testing

Run commands from the `frontend` directory.

- `npm ci` installs the exact dependency versions recorded in `package-lock.json`.
- `npm run lint` checks JavaScript and JSX with ESLint.
- `npm run test:unit` runs Vitest unit tests under `src/` only.
- `npm run test:e2e` runs Playwright browser tests under `e2e/`.
- `npm run build` creates the production frontend bundle.

The end-to-end tests exercise API-backed workflows. Start the backend and its configured dependencies, and ensure the test accounts and fixtures expected by the existing E2E tests are provisioned. Playwright starts Vite automatically; Vite proxies API and WebSocket requests to the backend on port 8000. A successful frontend-only startup does not establish that the backend workflows are healthy.
