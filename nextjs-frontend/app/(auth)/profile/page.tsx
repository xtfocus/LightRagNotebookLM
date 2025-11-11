"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Mail, Calendar, User as UserIcon } from "lucide-react";

interface User {
  id: string;
  email: string;
  is_superuser: boolean;
  full_name?: string | null;
}

export default function ProfilePage() {
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

  // Get first letter of user email for avatar
  const getUserInitial = () => {
    if (!user?.email) return "U";
    return user.email.charAt(0).toUpperCase();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Profile</h2>
        <p className="text-muted-foreground">
          Manage your account information and preferences.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* User Avatar and Basic Info */}
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="bg-gray-300 text-gray-700 font-semibold text-lg">
                {getUserInitial()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h3 className="text-lg font-semibold">
                {user?.full_name || 'John Doe'}
              </h3>
              <p className="text-sm text-muted-foreground">
                {user?.is_superuser ? 'Administrator' : 'User'}
              </p>
            </div>
          </div>

          {/* User Details */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="h-4 w-4" />
                <span>Email Address</span>
              </div>
              <p className="text-sm font-medium">{user?.email}</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <UserIcon className="h-4 w-4" />
                <span>Preferred Name</span>
              </div>
              <p className="text-sm font-medium">John Doe</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Joined Date</span>
              </div>
              <p className="text-sm font-medium">August 6, 2025</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span>Account Status</span>
              </div>
              <p className="text-sm font-medium">
                {user?.is_superuser ? 'Administrator' : 'Active User'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Additional Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">About</h4>
              <p className="text-sm text-muted-foreground">
                This is a demo profile page showing user information. In a real application, 
                users would be able to update their profile information, change passwords, 
                and manage their account settings.
              </p>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Account Features</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Email notifications</li>
                <li>• Two-factor authentication (coming soon)</li>
                <li>• Profile picture upload</li>
                <li>• Account preferences</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 