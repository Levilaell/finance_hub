"use client";

import * as React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./table";

interface Column<T> {
  key: string;
  header: string | (() => React.ReactNode);
  cell: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor?: (item: T) => string;
  className?: string;
  selectable?: boolean;
  selectedRows?: string[];
  onSelectionChange?: (selected: string[]) => void;
}

export function DataTable<T extends { id: string }>({
  columns,
  data,
  keyExtractor = (item) => item.id,
  className = "",
  selectable = false,
  selectedRows = [],
  onSelectionChange,
}: DataTableProps<T>) {
  return (
    <div className={`w-full ${className}`}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column.key} className={column.className}>
                {typeof column.header === 'function' ? column.header() : column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length > 0 ? (
            data.map((item) => {
              const key = keyExtractor(item);
              return (
                <TableRow
                  key={key}
                  className={selectedRows?.includes(key) ? "bg-gray-50" : ""}
                >
                  {columns.map((column) => (
                    <TableCell key={`${key}-${column.key}`} className={column.className}>
                      {column.cell(item)}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })
          ) : (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="h-24 text-center text-gray-500"
              >
                No results found
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}