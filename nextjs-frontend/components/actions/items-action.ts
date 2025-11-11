"use server";

import { cookies } from "next/headers";
import { itemsReadItems, itemsDeleteItem, itemsCreateItem } from "@/app/clientService";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { itemSchema } from "@/lib/definitions";
import { getRedirectPath } from "@/lib/redirects";

export async function fetchItems() {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return { message: "No access token found" };
  }

  const { data, error } = await itemsReadItems({
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (error) {
    return { message: error };
  }

  return data;
}

export async function removeItem(id: string) {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return { message: "No access token found" };
  }

  const { error } = await itemsDeleteItem({
    headers: {
      Authorization: `Bearer ${token}`,
    },
    path: {
      id: id,
    },
  });

  if (error) {
    return { message: error };
  }
  revalidatePath("/dashboard");
}

export async function addItem(prevState: {}, formData: FormData) {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    return { message: "No access token found" };
  }

  const validatedFields = itemSchema.safeParse({
    title: formData.get("title"),
    description: formData.get("description"),
  });

  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors };
  }

  const { title, description } = validatedFields.data;

  const input = {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: {
      title,
      description,
    },
  };
  const { error } = await itemsCreateItem(input);
  if (error) {
    return { message: `${error.detail}` };
  }
  redirect(getRedirectPath("DASHBOARD"));
}
