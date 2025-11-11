import { z } from "zod";

const passwordSchema = z
  .string()
  .min(8, "Password should be at least 8 characters.") // Minimum length validation
  .refine((password) => /[A-Z]/.test(password), {
    message: "Password should contain at least one uppercase letter.",
  }) // At least one uppercase letter
  .refine((password) => /[!@#$%^&*(),.?":{}|<>]/.test(password), {
    message: "Password should contain at least one special character.",
  });

export const passwordResetConfirmSchema = z
  .object({
    password: passwordSchema,
    passwordConfirm: z.string(),
    token: z.string({ required_error: "Token is required" }),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords must match.",
    path: ["passwordConfirm"],
  });

export const registerSchema = z.object({
  password: passwordSchema,
  email: z.string().email({ message: "Invalid email address" }),
});

export const loginSchema = z.object({
  password: z.string().min(1, { message: "Password is required" }),
  email: z.string().email({ message: "Invalid email address" }),
});

export const itemSchema = z.object({
  title: z.string().min(1, { message: "Title is required" }),
  description: z.string().min(1, { message: "Description is required" }),
});

export const notebookSchema = z.object({
  title: z.string().min(1, { message: "Title is required" }),
  description: z.string().optional(),
});

// Source-related schemas
export const sourceCreateSchema = z.object({
  title: z.string().min(1, { message: "Title is required" }),
  description: z.string().optional(),
  source_type: z.enum(["document", "url", "video", "image", "text"]),
  source_metadata: z.record(z.any()).optional(),
});

export const urlInputSchema = z.object({
  url: z.string().url({ message: "Please enter a valid URL" }),
  title: z.string().optional(),
  description: z.string().optional(),
});

export const notebookSourceCreateSchema = z.object({
  source_id: z.string().uuid({ message: "Invalid source ID" }),
  position: z.number().int().min(0).optional(),
});
