'use client';

import { Button } from "@/components/ui/button";
import { BurgerMenu } from "@/components/ui/BurgerMenu";
import { AuthButton } from "@/components/ui/AuthButton";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { ArrowRight, Search, BookOpen, Users, Zap } from "lucide-react";

export default function Home() {
  const { isAuthenticated, loading } = useAuth();

  const features = [
    {
      icon: Search,
      title: "Research",
      description: "Discover insights with AI"
    },
    {
      icon: BookOpen,
      title: "Organize",
      description: "Structure your findings"
    },
    {
      icon: Users,
      title: "Collaborate",
      description: "Work together seamlessly"
    },
    {
      icon: Zap,
      title: "Analyze",
      description: "Get intelligent insights"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-gray-100">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-black">
            OpenStorm
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <BurgerMenu />
          <AuthButton />
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold text-black mb-6 leading-tight">
            Research
            <span className="text-green-600"> anything</span>
          </h1>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Discover, analyze, and explore with our powerful research platform
          </p>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            {!loading && (
              <>
                {!isAuthenticated ? (
                  <Link href="/register">
                    <Button className="px-8 py-4 text-lg font-semibold bg-black text-white hover:bg-gray-800 rounded-lg flex items-center gap-2">
                      Get Started
                      <ArrowRight className="h-5 w-5" />
                    </Button>
                  </Link>
                ) : (
                  <Link href="/dashboard">
                    <Button className="px-8 py-4 text-lg font-semibold bg-black text-white hover:bg-gray-800 rounded-lg flex items-center gap-2">
                      Go to Dashboard
                      <ArrowRight className="h-5 w-5" />
                    </Button>
                  </Link>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <div key={index} className="text-center group">
                  <div className="w-16 h-16 bg-white rounded-lg flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:shadow-md transition-shadow">
                    <IconComponent className="h-8 w-8 text-green-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-black mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-black mb-4">
            Ready to start researching?
          </h2>
          <p className="text-gray-600 mb-8">
            Join thousands of researchers who trust OpenStorm
          </p>
          {!loading && !isAuthenticated && (
            <Link href="/register">
              <Button className="px-8 py-4 text-lg font-semibold bg-green-600 text-white hover:bg-green-700 rounded-lg">
                Start Your Research
              </Button>
            </Link>
          )}
          {!loading && isAuthenticated && (
            <Link href="/dashboard">
              <Button className="px-8 py-4 text-lg font-semibold bg-green-600 text-white hover:bg-green-700 rounded-lg">
                Go to Dashboard
              </Button>
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 border-t border-gray-100">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-gray-500">
            © 2024 OpenStorm. Research anything.
          </p>
        </div>
      </footer>
    </div>
  );
}
