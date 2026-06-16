import { type ModelResult } from "../types/search";

const SearchResult = ({ result }: { result: ModelResult }) => {
    return (
        <a
            href={result.url}
            target="_blank"
            className="group block rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-all hover:border-blue-200 hover:shadow-md"
        >
            <div className="flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600">
                    {result.rank}
                </span>
                <div className="min-w-0 flex-1 text-left">
                    <h3 className="truncate text-sm font-medium text-blue-700 group-hover:underline">
                        {result.title}
                    </h3>
                </div>
                <span className="shrink-0 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-500">
                    {result.score.toFixed(4)}
                </span>
            </div>
        </a>
    );
};

export default SearchResult;
