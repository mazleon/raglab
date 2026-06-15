/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      // Proxy backend API endpoints (must match FastAPI routes)
      { source: '/api/query', destination: 'http://localhost:8000/query' },
      { source: '/api/health', destination: 'http://localhost:8000/health' },
      { source: '/api/experiments', destination: 'http://localhost:8000/experiments' },
      { source: '/api/architectures', destination: 'http://localhost:8000/architectures' },
      { source: '/api/benchmark', destination: 'http://localhost:8000/benchmark' },
      { source: '/api/dashboard', destination: 'http://localhost:8000/dashboard' },
      { source: '/api/memory/:path*', destination: 'http://localhost:8000/memory/:path*' },
    ]
  },
}

export default nextConfig
