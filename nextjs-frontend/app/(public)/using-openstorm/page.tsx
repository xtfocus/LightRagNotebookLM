'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft, BookOpen, Search, Users, Zap } from 'lucide-react';

export default function UsingOpenStormPage() {
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
            Using OpenStorm
          </h1>
          
          <div className="prose dark:prose-invert max-w-none">
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              Learn how to make the most of OpenStorm's powerful research capabilities and features.
            </p>
            
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                    <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Research & Discovery</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Use our AI-powered search to find relevant information quickly and efficiently.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Organize & Document</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Create notebooks and organize your research findings systematically.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                    <Users className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Collaborate</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Work together with your team on research projects and share insights.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-orange-100 dark:bg-orange-900/20 rounded-lg flex items-center justify-center">
                    <Zap className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">AI Insights</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Get intelligent insights and analysis powered by advanced AI technology.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Getting Started
            </h2>
            <ol className="list-decimal list-inside text-gray-600 dark:text-gray-400 mb-6 space-y-2">
              <li>Create your account and complete the onboarding process</li>
              <li>Set up your first research project or notebook</li>
              <li>Start exploring with our AI-powered search</li>
              <li>Organize your findings and collaborate with your team</li>
              <li>Generate insights and reports using our analysis tools</li>
            </ol>
            
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Need Help?
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Our comprehensive documentation and support team are here to help you succeed with OpenStorm.
            </p>
            
            <div className="flex gap-4">
              <Link href="/register">
                <Button className="px-6 py-3">
                  Start Your Journey
                </Button>
              </Link>
              <Link href="/blog">
                <Button variant="outline" className="px-6 py-3">
                  Read Our Blog
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 