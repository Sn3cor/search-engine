import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { type Result } from "../types/search";
import SearchForm from "../components/SearchForm";
import Layout from "../components/Layout";
import ResultColumn from "../components/ResultColumn";

const SearchPage = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const query = searchParams.get("q");

    const [results, setResults] = useState<Result | undefined>(undefined);

    useEffect(() => {
        if (!query) {
            navigate("/");
            return;
        }

        setResults(undefined);

        const fetchResults = async () => {
            const response = await fetch(`http://localhost:8000/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query, top_n: 10 }),
            });
            const data = (await response.json()) as Result;
            setResults(data);
        };

        fetchResults();
    }, [query, navigate]);

    return (
        <Layout wide>
            <SearchForm key={query} defaultValue={query ?? undefined} />
            <p className="w-full text-left text-slate-600">
                Results for{" "}
                <span className="font-semibold text-slate-900">&ldquo;{query}&rdquo;</span>
            </p>
            <div className="grid w-full grid-cols-1 gap-4 lg:grid-cols-3">
                <ResultColumn label="BoW" variant="bow" results={results?.bow} />
                <ResultColumn label="LSA" variant="lsa" results={results?.lsa} />
                <ResultColumn label="BM25" variant="bm25" results={results?.bm25} />
            </div>
        </Layout>
    );
};

export default SearchPage;
