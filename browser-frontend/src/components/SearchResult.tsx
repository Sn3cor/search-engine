import { type Result } from "../types/search";

const SearchResult = ({ id, result }: {
    id: number,
    result: Result
}) => {
    return (
        <div>
            <h2>{id}. {result.name} ({result.similarity})</h2>
        </div>
    )
};

export default SearchResult