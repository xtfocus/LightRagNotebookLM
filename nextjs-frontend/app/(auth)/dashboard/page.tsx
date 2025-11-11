"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Shield } from "lucide-react";

interface User {
  id: string;
  email: string;
  is_superuser: boolean;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      // Get the access token from cookies
      const token = document.cookie
        .split('; ')
        .find(row => row.startsWith('accessToken='))
        ?.split('=')[1];

      const response = await fetch("/api/users/me", {
        headers: {
          "Content-Type": "application/json",
          ...(token && { authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error("Error fetching user:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <>
      <div>
        <h2 className="text-2xl font-semibold mb-6">
          Welcome, {user?.email || 'User'}
        </h2>
        <p className="text-lg mb-6">
          Here, you can see the overview of your dashboard.
        </p>
        
        {user?.is_superuser && (
          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Admin Panel
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              As an administrator, you can manage user approvals and system access.
            </p>
            <Button 
              onClick={() => window.location.href = "/admin"}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Manage User Waitlist
            </Button>
          </div>
        )}
      </div>
    </>
  );
}
