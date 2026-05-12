import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { type Result } from "../types/search";
import SearchForm from "../components/SearchForm";
import Layout from "../components/Layout";
import SearchResult from "../components/SearchResult";

const SearchPage = () => {
    const [seachParams] = useSearchParams();
    const query = seachParams.get('q');
    if (query === "") {
        const navigate = useNavigate();
        navigate("/")
    }
    const [results, setResults] = useState<Result[]>([]);

    useEffect(() => {
        const fetchResults = () => {
            const data: Result[] = [
                {
                    name: "test",
                    similarity: 0.9
                },
                {
                    name: "test",
                    similarity: 0.2
                },
                {
                    name: "test",
                    similarity: 0.5
                }
            ]

            setResults(data);
        }

        fetchResults();
    }, []);

    return (
        <Layout>
            <SearchForm defaultValue={query ?? undefined} />
            <h2 className="text-2xl">
                Results for: <span className="text-blue-500">{query}</span>
            </h2>
            <div>
                {results.map((result, i) => (
                    < SearchResult
                        key={i}
                        id={i + 1}
                        result={result}
                    />
                ))}
            </div>
        </Layout>
    )
}

export default SearchPage;