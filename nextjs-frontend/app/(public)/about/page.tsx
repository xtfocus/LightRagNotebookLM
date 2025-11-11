'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex justify-between items-center p-6 bg-white dark:bg-gray-800 shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto p-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
            About OpenStorm
          </h1>
          
          <div className="prose dark:prose-invert max-w-none">
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
              OpenStorm is a powerful research platform designed to help you discover, analyze, and explore information in ways never before possible.
            </p>
            
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Our Mission
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              We believe that research should be accessible, efficient, and insightful. OpenStorm combines cutting-edge AI technology with intuitive design to make research a seamless experience.
            </p>
            
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Key Features
            </h2>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 mb-6 space-y-2">
              <li>Advanced AI-powered research assistance</li>
              <li>Intelligent data analysis and insights</li>
              <li>Collaborative research tools</li>
              <li>Seamless integration with existing workflows</li>
              <li>Real-time collaboration and sharing</li>
            </ul>
            
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Get Started
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Ready to revolutionize your research process? Join OpenStorm today and experience the future of research.
            </p>
            
            <div className="flex gap-4">
              <Link href="/register">
                <Button className="px-6 py-3">
                  Get Started
                </Button>
              </Link>
              <Link href="/using-openstorm">
                <Button variant="outline" className="px-6 py-3">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 