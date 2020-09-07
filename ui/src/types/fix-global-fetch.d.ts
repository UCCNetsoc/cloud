// typescript-fetch relies on GlobalFetch to work correctly
// GlobalFetch was removed in TypeScript 3.6.2 and typescript-fetch has not been updated for this yet
declare type GlobalFetch = WindowOrWorkerGlobalScope
