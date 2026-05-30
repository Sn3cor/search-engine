const Home = ({ children }: {
    children: React.ReactNode
}) => {
    return (
        <div className="min-h-screen bg-slate-50 flex flex-col justify-start items-center p-4">
            <div className="w-full max-w-2xl flex flex-col justify-between items-center gap-5">
                <h1 className="text-4xl text-black font-extrabold">simple-browser</h1>
                {children}
            </div>

        </div >
    );
};

export default Home;