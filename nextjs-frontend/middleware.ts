import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { usersReadUserMe } from "@/app/clientService";

// Get login redirect path from environment or use default
const LOGIN_REDIRECT_PATH = process.env.NEXT_PUBLIC_REDIRECT_LOGIN || "/login";

// Define public routes that don't require authentication
const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/register", 
  "/password-recovery",
  "/about",
  "/using-openstorm",
  "/blog"
];

// Define protected routes that require authentication
const PROTECTED_ROUTES = [
  "/dashboard",
  "/items",
  "/aguichat",
  "/admin",
  "/notebooks",
  "/sources",
  "/profile"
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the current path is a protected route
  const isProtectedRoute = PROTECTED_ROUTES.some(route => 
    pathname.startsWith(route)
  );

  // If it's not a protected route, allow access
  if (!isProtectedRoute) {
    return NextResponse.next();
  }

  // For protected routes, check authentication
  const token = request.cookies.get("accessToken");

  if (!token) {
    return NextResponse.redirect(new URL(LOGIN_REDIRECT_PATH, request.url));
  }

  try {
  const options = {
    headers: {
      Authorization: `Bearer ${token.value}`,
    },
  };

  const { error } = await usersReadUserMe(options);

  if (error) {
    return NextResponse.redirect(new URL(LOGIN_REDIRECT_PATH, request.url));
  }
  } catch (error) {
    console.error("Middleware auth check error:", error);
    return NextResponse.redirect(new URL(LOGIN_REDIRECT_PATH, request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/items/:path*",
    "/aguichat/:path*",
    "/admin/:path*",
    "/notebooks/:path*",
    "/sources/:path*",
    "/profile/:path*"
  ],
};
