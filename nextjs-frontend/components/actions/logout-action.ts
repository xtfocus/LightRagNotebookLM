"use server";

import { cookies } from "next/headers";

export async function logout() {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return { message: "No access token found" };
  }

  // Clear the access token cookie
  cookieStore.delete("accessToken");
  
  // Return success state instead of redirecting
  return { success: true };
}
