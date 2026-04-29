import type { ReactNode } from "react";

type Props = {
  icon: ReactNode;
  iconBg: string;
  label: string;
  value: string | number;
};

export default function StatCard({ icon, iconBg, label, value }: Props) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${iconBg}`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
