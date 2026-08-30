/**
 * Converts snake_case keys to camelCase.
 * Used at the API boundary so components receive camelCase props.
 */
type SnakeToCamel<S extends string> = S extends `${infer Head}_${infer Tail}`
  ? `${Head}${Capitalize<SnakeToCamel<Tail>>}`
  : S

type CamelizeKeys<T> = T extends Array<infer U>
  ? Array<CamelizeKeys<U>>
  : T extends object
  ? {
      [K in keyof T as SnakeToCamel<K & string>]: CamelizeKeys<T[K]>
    }
  : T

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

export function camelizeKeys<T>(obj: T): CamelizeKeys<T> {
  if (Array.isArray(obj)) {
    return obj.map(camelizeKeys) as CamelizeKeys<T>
  }
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date)) {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([key, value]) => [
        snakeToCamel(key),
        camelizeKeys(value),
      ])
    ) as CamelizeKeys<T>
  }
  return obj as CamelizeKeys<T>
}
