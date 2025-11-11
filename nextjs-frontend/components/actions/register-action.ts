"use server";

import { usersRegisterUser } from "@/app/clientService";

import { registerSchema } from "@/lib/definitions";
import { getErrorMessage } from "@/lib/utils";

export async function register(prevState: unknown, formData: FormData) {
  const validatedFields = registerSchema.safeParse({
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
      email,
      password,
    },
  };
  try {
    const { error } = await usersRegisterUser(input);
    if (error) {
      return { server_validation_error: getErrorMessage(error) };
    }
  } catch (err) {
    console.error("Registration error:", err);
    return {
      server_error: "An unexpected error occurred. Please try again later.",
    };
  }
  
  // Return success state instead of redirecting
  return {
    success: true,
    message: "Account created successfully! You've been added to our waitlist.",
  };
}
