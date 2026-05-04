"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROLE_LABELS, useAuth } from "@/lib/auth-context";
import {
  BookIcon,
  ChartIcon,
  HomeIcon,
  LogoutIcon,
} from "@/components/icons";
import type { Role } from "@/lib/types";
import type { ReactNode } from "react";

type NavItem = {
  href: string;
  label: string;
  icon: ReactNode;
  roles: Role[];
};

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Trang chu",
    icon: <HomeIcon />,
    roles: ["admin", "teacher", "student", "parent"],
  },
  {
    href: "/admin/users",
    label: "Nguoi dung",
    icon: <HomeIcon />,
    roles: ["admin"],
  },
  {
    href: "/admin/classes",
    label: "Tat ca lop hoc",
    icon: <BookIcon className="h-5 w-5" strokeWidth={2} />,
    roles: ["admin"],
  },
  {
    href: "/teacher/classes",
    label: "Lop cua toi",
    icon: <BookIcon className="h-5 w-5" strokeWidth={2} />,
    roles: ["teacher"],
  },
  {
    href: "/teacher/students",
    label: "Hoc sinh",
    icon: <HomeIcon />,
    roles: ["teacher"],
  },
  {
    href: "/student/assignments",
    label: "Bai duoc giao",
    icon: <BookIcon className="h-5 w-5" strokeWidth={2} />,
    roles: ["student"],
  },
  {
    href: "/parent/children",
    label: "Cac con",
    icon: <HomeIcon />,
    roles: ["parent"],
  },
  {
    href: "/progress",
    label: "Tien do",
    icon: <ChartIcon />,
    roles: ["admin", "teacher", "student", "parent"],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { email, role, fullName, logout } = useAuth();
  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex items-center gap-3 border-b border-gray-200 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-sm font-bold text-white">
          L
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900">LumiEdu</h1>
          <p className="text-xs text-gray-500">{ROLE_LABELS[role]}</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {visibleItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-gray-200 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-xs font-medium text-gray-700">
            {(fullName || email).charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-gray-900">
              {fullName || email}
            </p>
            <p className="truncate text-xs text-gray-500">{email}</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            title="Dang xuat"
          >
            <LogoutIcon />
          </button>
        </div>
      </div>
    </aside>
  );
}
