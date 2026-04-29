type Props = {
  message: string;
};

export default function ErrorAlert({ message }: Props) {
  return (
    <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
      {message}
    </div>
  );
}
