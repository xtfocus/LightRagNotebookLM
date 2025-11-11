'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Calendar, User, Tag } from 'lucide-react';

export default function BlogPage() {
  const blogPosts = [
    {
      id: 1,
      title: "Introducing OpenStorm: The Future of Research",
      excerpt: "Discover how OpenStorm is revolutionizing the way researchers work with AI-powered tools and collaborative features.",
      author: "OpenStorm Team",
      date: "2024-01-15",
      tags: ["Product", "AI", "Research"],
      readTime: "5 min read"
    },
    {
      id: 2,
      title: "5 Ways AI is Transforming Research Workflows",
      excerpt: "Explore the key ways artificial intelligence is changing how researchers discover, analyze, and share information.",
      author: "Dr. Sarah Chen",
      date: "2024-01-10",
      tags: ["AI", "Workflow", "Technology"],
      readTime: "8 min read"
    },
    {
      id: 3,
      title: "Best Practices for Collaborative Research",
      excerpt: "Learn how to effectively collaborate with your team using OpenStorm's powerful collaboration tools.",
      author: "Research Team",
      date: "2024-01-05",
      tags: ["Collaboration", "Best Practices", "Teamwork"],
      readTime: "6 min read"
    }
  ];

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
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            OpenStorm Blog
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Latest insights, updates, and stories from the OpenStorm team and community.
          </p>
        </div>
        
        <div className="space-y-8">
          {blogPosts.map((post) => (
            <article key={post.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {post.title}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {post.excerpt}
                </p>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>{post.author}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-4 w-4" />
                    <span>{new Date(post.date).toLocaleDateString()}</span>
                  </div>
                  <span>{post.readTime}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {post.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400"
                    >
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </span>
                  ))}
                </div>
                
                <Button variant="outline" size="sm">
                  Read More
                </Button>
              </div>
            </article>
          ))}
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Stay updated with the latest from OpenStorm
          </p>
          <Link href="/register">
            <Button className="px-6 py-3">
              Subscribe to Updates
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
} 