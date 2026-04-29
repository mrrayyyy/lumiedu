type Props = {
  role: "learner" | "tutor";
  text: string;
  latencyMs?: number;
};

export default function ChatBubble({ role, text, latencyMs }: Props) {
  const isLearner = role === "learner";

  return (
    <div className={`flex ${isLearner ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isLearner
            ? "bg-indigo-600 text-white"
            : "border border-gray-200 bg-white text-gray-900"
        }`}
      >
        {!isLearner && (
          <div className="mb-1 flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600">LumiEdu</span>
            {latencyMs !== undefined && (
              <span className="text-xs text-gray-400">{latencyMs}ms</span>
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
      </div>
    </div>
  );
}
