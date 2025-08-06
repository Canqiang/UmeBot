# Frontend

## Troubleshooting

If the dev server fails to start due to stale optimized dependencies:

1. Stop the dev server.
2. Delete `node_modules/.vite` (or run `npm run dev -- --force` to rebuild optimized deps).
3. Restart with `npm run dev`.

