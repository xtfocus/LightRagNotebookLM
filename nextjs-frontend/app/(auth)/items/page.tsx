import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableHeader,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { fetchItems } from "@/components/actions/items-action";
import { DeleteButton } from "@/app/(auth)/dashboard/deleteButton";
import { ItemsReadItemsResponse } from "@/app/openapi-client";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default async function ItemsPage() {
  const items = (await fetchItems()) as ItemsReadItemsResponse;

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Manage Items</h2>
      <p className="text-lg mb-6">
        Here, you can see the overview of your items and manage them.
      </p>
      <div className="mb-6">
        <Link href="/items/add-item">
          <Button variant="outline" className="text-lg px-4 py-2">
            Add New Item
          </Button>
        </Link>
      </div>
      <section className="p-6 bg-white rounded-lg shadow-lg mt-8">
        <h2 className="text-xl font-semibold mb-4">Items</h2>
        <Table className="min-w-full text-sm">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px]">Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-center">Quantity</TableHead>
              <TableHead className="text-center">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!items.data?.length ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center">
                  No results.
                </TableCell>
              </TableRow>
            ) : (
              items.data?.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>{item.title}</TableCell>
                  <TableCell>{item.description}</TableCell>
                  <TableCell className="text-center">-</TableCell>
                  <TableCell className="text-center">
                    <DropdownMenu>
                      <DropdownMenuTrigger className="cursor-pointer p-1 text-gray-600 hover:text-gray-800">
                        <span className="text-lg font-semibold">...</span>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="p-2">
                        <DropdownMenuItem disabled={true}>
                          Edit
                        </DropdownMenuItem>
                        <DeleteButton itemId={item.id} />
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </section>
    </div>
  );
} 