import { type ModelResult } from "../types/search";

const SearchResult = ({ id, result }: {
    id: number,
    result: ModelResult
}) => {
    return (
        <div>

            <a href={result.url} target="_blank">
                <h2>{id}. {result.title} ({result.score})</h2>
            </a>
        </div>
    )
};

export default SearchResult