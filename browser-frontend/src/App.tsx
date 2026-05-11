import { BrowserRouter, Routes, Route, useSearchParams, useNavigate } from "react-router-dom"

const SearchForm = ({ defaultValue }: {
  defaultValue?: string
}) => {
  const navigate = useNavigate();

  const handleSearch = (e: React.SyntheticEvent) => {
    e.preventDefault();
    const target = e.target as typeof e.target & {
      query: { value: string };
    };
    const query = target.query.value;
    if (query) navigate(`/search?q=${encodeURIComponent(query)}`);
  }

  return (
    <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-lg">
      <input
        type="text"
        defaultValue={defaultValue}
        name="query"
        placeholder="Czego szukasz?..."
        className="w-full px-4 py-3 rounded-xl border border-slate-300 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
      />

      <input
        type="submit"
        value="Search"
        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-xl shadow-lg shadow-blue-200 cursor-pointer transition-colors"
      />
    </form>
  )
}

const Home = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-2xl flex flex-col md:flex-row justify-center gap-3">
        <SearchForm />
      </div>
    </div>
  )
}

const Search = () => {
  const [seachParams] = useSearchParams();
  const query = seachParams.get('q');

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold">Wyniki dla: <span className="text-blue-500">{query}</span></h2>
    </div>
  )
}

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App