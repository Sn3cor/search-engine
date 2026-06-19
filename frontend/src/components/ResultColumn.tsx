import { type ModelResult } from "../types/search";
import SearchResult from "./SearchResult";

const accentStyles = {
    bow: "text-blue-700",
    lsa: "text-violet-700",
    bm25: "text-emerald-700",
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
                className={`rounded-t-xl px-4 py-3 text-left font-semibold tracking-wide uppercase text-xs ${accentStyles[variant]}`}
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
