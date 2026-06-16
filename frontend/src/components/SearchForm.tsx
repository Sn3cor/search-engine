import { useNavigate } from "react-router-dom";

const SearchForm = ({ defaultValue }: {
    defaultValue?: string
}) => {
    const navigate = useNavigate();

    const handleSearch = (e: React.SyntheticEvent) => {
        e.preventDefault();
        const target = e.target as typeof e.target & {
            query: { value: string };
        };
        const query = target.query.value.trim();
        if (query) {
            const params = new URLSearchParams({ q: query });
            navigate(`/search?${params.toString()}`);
        }
    }

    return (
        <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-lg">
            <input
                type="text"
                defaultValue={defaultValue}
                name="query"
                placeholder="..."
                className="w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />

            <input
                type="submit"
                value="Search"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-xl shadow-lg shadow-blue-200 cursor-pointer transition-colors"
            />
        </form>
    );
};

export default SearchForm;