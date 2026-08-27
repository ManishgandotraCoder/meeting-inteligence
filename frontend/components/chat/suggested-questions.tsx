export function SuggestedQuestions({
  suggestions,
  onSelect,
}: {
  suggestions: string[];
  onSelect: (question: string) => void;
}) {
  return (
    <div className="mt-5 flex flex-wrap justify-center gap-2">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          onClick={() => onSelect(suggestion)}
          className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-gray-600 transition hover:border-brand/20 hover:bg-brand-soft/60 hover:text-brand"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}
