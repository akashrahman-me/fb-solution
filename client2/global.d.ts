// global.d.ts
export {};

declare global {
    interface Window {
        electron: {
            platform: string;
            windowMinimize: () => void;
            windowMaximize: () => void;
            windowClose: () => void;
            send: (channel: string, data?: unknown) => void;
            receive: (channel: string, func: (...args: unknown[]) => void) => void;
            invoke: (channel: string, data?: unknown) => Promise<unknown>;
            getVersion: () => string;
        };
        path: {
            join: (...args: string[]) => string;
            basename: (path: string) => string;
            dirname: (path: string) => string;
        };
    }
}
