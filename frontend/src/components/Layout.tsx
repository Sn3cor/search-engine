const Layout = ({
    children,
    wide = false,
}: {
    children: React.ReactNode;
    wide?: boolean;
}) => {
    return (
        <div className="min-h-screen bg-slate-50 flex flex-col justify-start items-center p-4 md:p-8">
            <div
                className={`w-full flex flex-col items-center gap-6 ${wide ? "max-w-6xl" : "max-w-2xl"}`}
            >
                <h1 className="text-4xl text-slate-900 font-extrabold tracking-tight">
                    search-engine
                </h1>
                {children}
            </div>
        </div>
    );
};

export default Layout;