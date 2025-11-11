"use server";

import { cookies } from "next/headers";
import { loginLoginAccessToken } from "@/app/clientService";
import { loginSchema } from "@/lib/definitions";
import { getErrorMessage } from "@/lib/utils";

export async function login(prevState: unknown, formData: FormData) {
  const validatedFields = loginSchema.safeParse({
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  const { email, password } = validatedFields.data;

  const input = {
    body: {
      username: email, // Map email to username for OAuth2 compatibility
      password,
    },
  };

  try {
    const { data, error } = await loginLoginAccessToken(input);
    if (error) {
      return { server_validation_error: getErrorMessage(error) };
    }
    
    // Set the access token in cookies with proper security settings
    const cookieStore = await cookies();
    cookieStore.set("accessToken", data.access_token, {
      httpOnly: false, // Allow client-side access for AuthContext
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 86400, // 24 hours
      path: "/",
    });
    
    // Return success state instead of redirecting
    return { success: true };
  } catch (err) {
    console.error("Login error:", err);
    return {
      server_error: "An unexpected error occurred. Please try again later.",
    };
  }
}
