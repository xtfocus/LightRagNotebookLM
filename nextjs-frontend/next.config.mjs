import ForkTsCheckerWebpackPlugin from 'fork-ts-checker-webpack-plugin';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable Next.js telemetry
  telemetry: false,
  
  // Memory optimization settings
  experimental: {
    // Reduce memory usage in development
    optimizePackageImports: ['@radix-ui/react-icons', 'lucide-react', 'react-icons'],
    // Reduce memory usage for webpack
    webpackBuildWorker: false,
  },
  
  // Optimize webpack configuration
  webpack: (config, { isServer, dev }) => {
    if (!isServer) {
      config.plugins.push(
        new ForkTsCheckerWebpackPlugin({
          async: true,
          typescript: {
            configOverwrite: {
              compilerOptions: {
                skipLibCheck: true,
              },
            },
            memoryLimit: 512, // Reduce TypeScript memory usage
          },
        })
      );
    }
    
    // Reduce memory usage in development
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: ['**/node_modules', '**/.git'],
      };
      
      // Simplify optimization to avoid module format issues
      config.optimization = {
        ...config.optimization,
        // Disable problematic chunk splitting in development
        splitChunks: false,
        // Ensure proper module handling
        moduleIds: 'named',
        chunkIds: 'named',
      };
    }
    
    return config;
  },
  
  // Disable image optimization to save memory
  images: {
    unoptimized: true,
  },
};

export default nextConfig;