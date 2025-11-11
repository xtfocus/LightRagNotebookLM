import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { UsersRegisterUserError, LoginLoginAccessTokenError } from "@/app/clientService";
import { getErrorMessage as getUserFriendlyErrorMessage } from "./errorMessages";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getErrorMessage(
  error: UsersRegisterUserError | LoginLoginAccessTokenError,
): string {
  return getUserFriendlyErrorMessage(error);
}
