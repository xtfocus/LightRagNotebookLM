"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { register } from "@/components/actions/register-action";
import { FieldError } from "@/components/ui/FormError";
import { EnhancedFormError } from "@/components/ui/EnhancedFormError";
import { FormLoadingOverlay } from "@/components/ui/FormLoadingOverlay";
import { useNotifications } from "@/components/ui/NotificationContext";
import { getNotificationConfig } from "@/lib/notifications";
import { PasswordRequirements } from "@/components/ui/PasswordRequirements";
import { getRedirectPath } from "@/lib/redirects";
import { useAuth } from "@/contexts/AuthContext";

export default function Page() {
  const [state, dispatch] = useActionState(register, undefined);
  const { addNotification } = useNotifications();
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, loading, router]);

  // Handle success state
  useEffect(() => {
    if (state?.success) {
      const notification = getNotificationConfig("REGISTRATION_SUCCESS");
      addNotification({
        ...notification,
        autoClose: true, // Enable auto-close
        autoCloseDelay: 5000, // Auto-close after 5 seconds
      });
    }
  }, [state?.success, addNotification]);

  // Show loading or redirect if user is already authenticated
  if (loading || isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If registration was successful, show success state
  if (state?.success) {
    return (
      <div className="flex h-screen">
        {/* Left Side - OpenStorm Branding (Black Background) */}
        <div className="hidden lg:flex lg:w-1/2 bg-black text-white flex-col justify-center items-center p-12">
          <div className="max-w-md text-center">
            <h1 className="text-5xl font-bold mb-6">
              OpenStorm
            </h1>
            <h2 className="text-2xl font-semibold mb-4">
              Research anything
            </h2>
            <p className="text-lg text-gray-300 mb-8">
              Discover, analyze, and explore with our powerful research platform
            </p>
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-3">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-gray-300">AI-powered research assistance</span>
              </div>
              <div className="flex items-center justify-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-gray-300">Intelligent data analysis</span>
              </div>
              <div className="flex items-center justify-center space-x-3">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-gray-300">Collaborative research tools</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Success Message (White Background) */}
        <div className="flex-1 lg:w-1/2 bg-white flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            {/* Mobile Header - Only visible on mobile */}
            <div className="lg:hidden text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                OpenStorm
              </h1>
              <p className="text-gray-600">
                Research anything
              </p>
            </div>

            <Card className="w-full border-0 shadow-none">
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-gray-900">
                  🎉 Registration Successful!
                </CardTitle>
                <CardDescription className="text-base text-gray-600 mt-2">
                  Your account has been created successfully.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="text-center space-y-4">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-blue-800 text-sm">
                      Your account is pending admin approval. You will be able to sign in once an administrator approves your account.
                    </p>
                  </div>
                  <p className="text-sm text-gray-600">
                    We'll notify you when your account is approved and ready to use.
                  </p>
                </div>
                <div className="space-y-3">
                  <Button 
                    onClick={() => router.push(getRedirectPath("LOGIN"))}
                    className="w-full h-12 text-base font-semibold"
                  >
                    Go to Login
                  </Button>
                  <Button 
                    onClick={() => {
                      router.push("/");
                    }}
                    variant="outline"
                    className="w-full h-12 text-base font-semibold"
                  >
                    Back to Home
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Left Side - OpenStorm Branding (Black Background) */}
      <div className="hidden lg:flex lg:w-1/2 bg-black text-white flex-col justify-center items-center p-12">
        <div className="max-w-md text-center">
          <h1 className="text-5xl font-bold mb-6">
            OpenStorm
          </h1>
          <h2 className="text-2xl font-semibold mb-4">
            Research anything
          </h2>
          <p className="text-lg text-gray-300 mb-8">
            Discover, analyze, and explore with our powerful research platform
          </p>
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-3">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-300">AI-powered research assistance</span>
            </div>
            <div className="flex items-center justify-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">Intelligent data analysis</span>
            </div>
            <div className="flex items-center justify-center space-x-3">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-gray-300">Collaborative research tools</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Registration Form (White Background) */}
      <div className="flex-1 lg:w-1/2 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Header - Only visible on mobile */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              OpenStorm
            </h1>
            <p className="text-gray-600">
              Research anything
            </p>
          </div>

          <FormLoadingOverlay>
            <form action={dispatch}>
              <Card className="w-full border-0 shadow-none">
                <CardHeader className="text-center pb-6">
                  <CardTitle className="text-3xl font-bold text-gray-900">
                    Create Account
                  </CardTitle>
                  <CardDescription className="text-base text-gray-600 mt-2">
                    Join OpenStorm to start your research journey
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label
                      htmlFor="full_name"
                      className="text-sm font-medium text-gray-700"
                    >
                      Full Name
                    </Label>
                    <Input
                      id="full_name"
                      name="full_name"
                      type="text"
                      placeholder="Enter your full name"
                      required
                      className="h-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                    <FieldError state={state} field="full_name" />
                  </div>
                  <div className="space-y-2">
                    <Label
                      htmlFor="email"
                      className="text-sm font-medium text-gray-700"
                    >
                      Email
                    </Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      placeholder="Enter your email"
                      required
                      className="h-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                    <FieldError state={state} field="email" />
                  </div>
                  <div className="space-y-2">
                    <Label
                      htmlFor="password"
                      className="text-sm font-medium text-gray-700"
                    >
                      Password
                    </Label>
                    <Input
                      id="password"
                      name="password"
                      type="password"
                      placeholder="Create a password"
                      required
                      className="h-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                    <FieldError state={state} field="password" />
                    <PasswordRequirements />
                  </div>
                  <Button
                    type="submit"
                    className="w-full h-12 bg-black text-white hover:bg-gray-800"
                  >
                    Create Account
                  </Button>
                  <EnhancedFormError state={state} />
                  <div className="text-center text-sm text-gray-600">
                    Already have an account?{" "}
                    <Link
                      href="/login"
                      className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Sign in
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </form>
          </FormLoadingOverlay>
        </div>
      </div>
    </div>
  );
}
