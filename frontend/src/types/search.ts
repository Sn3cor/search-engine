export interface ModelResult {
    rank: number,
    page_id: number,
    title: string,
    url: string,
    score: number
};

export interface Result {
    bow: ModelResult[],
    lsa: ModelResult[],
    bm25: ModelResult[]
};