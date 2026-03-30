const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, ...rest } = options;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...rest.headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  if (!res.ok) {
    const message = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${message}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get<T>(path: string, init?: RequestInit) {
    return request<T>(path, { ...init, method: "GET" });
  },
  post<T>(path: string, body?: unknown, init?: RequestInit) {
    return request<T>(path, { ...init, method: "POST", body });
  },
  put<T>(path: string, body?: unknown, init?: RequestInit) {
    return request<T>(path, { ...init, method: "PUT", body });
  },
  delete<T>(path: string, init?: RequestInit) {
    return request<T>(path, { ...init, method: "DELETE" });
  },
};
