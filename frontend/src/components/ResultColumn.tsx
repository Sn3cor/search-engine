import { type ModelResult } from "../types/search";
import SearchResult from "./SearchResult";

const accentStyles = {
    bow: "border-t-blue-500 text-blue-700 bg-blue-50",
    lsa: "border-t-violet-500 text-violet-700 bg-violet-50",
    bm25: "border-t-emerald-500 text-emerald-700 bg-emerald-50",
};

const ResultColumn = ({
    label,
    variant,
    results,
}: {
    label: string;
    variant: "bow" | "lsa" | "bm25";
    results?: ModelResult[];
}) => {
    return (
        <section className="flex min-w-0 flex-1 flex-col rounded-xl border border-slate-200 bg-slate-50/50">
            <div
                className={`rounded-t-xl border-t-4 px-4 py-3 text-left font-semibold tracking-wide uppercase text-xs ${accentStyles[variant]}`}
            >
                {label}
            </div>
            <div className="flex flex-col gap-2 p-3">
                {results === undefined ? (
                    <p className="py-8 text-center text-sm text-slate-400">Loading…</p>
                ) : results.length === 0 ? (
                    <p className="py-8 text-center text-sm text-slate-400">No results</p>
                ) : (
                    results.map((result) => (
                        <SearchResult key={result.page_id} result={result} />
                    ))
                )}
            </div>
        </section>
    );
};

export default ResultColumn;
