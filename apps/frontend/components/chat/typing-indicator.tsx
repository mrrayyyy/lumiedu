export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-indigo-600">LumiEdu</span>
          <span className="text-xs text-gray-400">dang suy nghi...</span>
        </div>
        <div className="mt-2 flex gap-1">
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "0ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "150ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-300" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}
