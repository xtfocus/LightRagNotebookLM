"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/components/actions/login-action";
import { FieldError } from "@/components/ui/FormError";
import { EnhancedFormError } from "@/components/ui/EnhancedFormError";
import { FormLoadingOverlay } from "@/components/ui/FormLoadingOverlay";
import { useAuth } from "@/contexts/AuthContext";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { OpenStormBranding } from "@/components/ui/OpenStormBranding";
import { MobileHeader } from "@/components/ui/MobileHeader";
import { useAuthRedirect } from "@/hooks/useAuthRedirect";

export default function Page() {
  const [state, dispatch] = useActionState(login, undefined);
  const router = useRouter();
  const { refreshAuth } = useAuth();
  const { loading, isAuthenticated } = useAuthRedirect({ requireAuth: false });

  // Handle successful login
  useEffect(() => {
    if (state?.success) {
      refreshAuth().then(() => {
        router.push("/dashboard");
      });
    }
  }, [state?.success, router, refreshAuth]);

  // Show loading or redirect if user is already authenticated
  if (loading || isAuthenticated) {
    return <LoadingSpinner />;
  }

  return (
    <div className="flex h-screen">
      <OpenStormBranding />
      
      {/* Right Side - Login Form (White Background) */}
      <div className="flex-1 lg:w-1/2 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <MobileHeader />

          <FormLoadingOverlay>
            <form action={dispatch}>
              <Card className="w-full border-0 shadow-none">
                <CardHeader className="text-center pb-6">
                  <CardTitle className="text-3xl font-bold text-gray-900">
                    Welcome back
                  </CardTitle>
                  <CardDescription className="text-base text-gray-600 mt-2">
                    Sign in to your account to continue
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
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
                      placeholder="Enter your password"
                      required
                      className="h-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                    <FieldError state={state} field="password" />
                  </div>
                  <div className="flex items-center justify-between">
                    <Link
                      href="/password-recovery"
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <Button
                    type="submit"
                    className="w-full h-12 bg-black text-white hover:bg-gray-800"
                  >
                    Sign In
                  </Button>
                  <EnhancedFormError state={state} />
                  <div className="text-center text-sm text-gray-600">
                    Don't have an account?{" "}
                    <Link
                      href="/register"
                      className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Sign up
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
