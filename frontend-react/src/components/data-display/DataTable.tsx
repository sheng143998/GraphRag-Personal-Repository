import type { ReactNode } from "react";
import "./data-display.css";

interface DataTableProps {
  columns: string[];
  emptyText?: string;
  rows: ReactNode[];
}

export function DataTable({ columns, emptyText = "暂无数据", rows }: DataTableProps) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length > 0 ? rows : (
            <tr>
              <td className="data-table__empty" colSpan={columns.length}>{emptyText}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
