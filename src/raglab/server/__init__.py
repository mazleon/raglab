"""HTTP server layer: session/engine wiring, auth deps, and SSE streaming.

Keeps the FastAPI routers thin — they translate requests into calls on these
helpers, which own the composition + persistence concerns.
"""
