# Frontend

## Environment Variables

The frontend uses Vite environment variables. Configure the WebSocket API endpoint with `VITE_API_WS_URL` in a `.env` file:

```env
VITE_API_WS_URL=ws://localhost:8000
```

This value is used to establish the chat WebSocket connection.

## Troubleshooting

If the dev server fails to start due to stale optimized dependencies:

1. Stop the dev server.
2. Delete `node_modules/.vite` (or run `npm run dev -- --force` to rebuild optimized deps).
3. Restart with `npm run dev`.

