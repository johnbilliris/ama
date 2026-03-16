declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

declare module "react" {
  export type PropsWithChildren<T = unknown> = T & { children?: any };
  export function useDeferredValue<T>(value: T): T;
  export function useState<T>(initialState: T | (() => T)): [T, (value: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: any[]): void;
  export function startTransition(scope: () => void): void;
}

declare module "react/jsx-runtime" {
  export const Fragment: unique symbol;
  export function jsx(type: any, props: any, key?: any): any;
  export function jsxs(type: any, props: any, key?: any): any;
}

declare module "next/navigation" {
  export function useParams<T extends Record<string, string> = Record<string, string>>(): T;
}

declare const process: {
  env: Record<string, string | undefined>;
};
