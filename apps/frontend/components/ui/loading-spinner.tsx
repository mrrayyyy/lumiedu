import { SpinnerIcon } from "@/components/icons";

type Props = {
  message?: string;
};

export default function LoadingSpinner({ message = "Dang tai..." }: Props) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="flex items-center gap-3 text-gray-500">
        <SpinnerIcon />
        {message}
      </div>
    </div>
  );
}
