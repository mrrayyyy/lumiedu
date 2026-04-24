You are generating TypeScript API client code for a Next.js app project. Follow the project's established patterns exactly.

**IMPORTANT: This rule only applies when cURL command examples are provided. If no cURL example is available, inform the user that at least one valid cURL command is required and do not create any API functions.**

### Goals

- Define API functions under `src/services/` using the existing service style.
- Define all request/response interfaces under `src/interfaces/` per the interface guidelines.
- Reuse existing types if available; otherwise create new ones with clear names.

### Service Implementation Rules (MUST FOLLOW)

1. Import the shared API instance from the local index re-export:
   - `import { api } from "@/services";`
   - Do NOT create new clients; always use the shared `api` from `src/services`.
2. Function signature and naming:
   - Export individual functions (preferred, matches current codebase) or group related endpoints into a named export object (e.g., `userService`, `authService`).
   - Use clear verb-first method names: `getX`, `listX`, `createX`, `updateX`, `deleteX`.
   - Use arrow functions without async keyword: `export const getUsers = () => api.get<User[]>("/users")`.
3. HTTP methods and typing:
   - Use the HTTP method, path, headers, and parameters as shown in the provided cURL command sample.
   - Use `api.get<T>(path, { params })` for GET with query params.
   - Use `api.post<T>(path, data, config?)`, `api.put<T>`, `api.patch<T>`, `api.delete<T>` for others.
   - Always provide the response generic `T` using interfaces defined in the service file or from `src/interfaces`.
   - Type request payloads via their interfaces at the call site (the `data` variable is typed).
   - Note: The API client uses Axios and returns `response.data` directly via interceptors, so the generic `T` represents the actual response data.
4. Paths and params:
   - **Always use leading slashes in paths**: `` `/users/${id}` `` (not `` `users/${id}` ``).
   - Interpolate path params with template strings: `` `/users/${id}` ``.
   - Pass query params via `{ params }` on GET (as inferred from the cURL command URL).
5. Headers and special cases:
   - If the cURL sample specifies custom headers, include them in the third `config` argument.
   - For file uploads, use `FormData` and set `Content-Type: multipart/form-data` in headers (as shown in the cURL command).
6. Return value:
   - Return the `api` call directly. Do not wrap in extra try/catch unless a header/timeout is required or clear error handling is present in the cURL usage.
7. File placement:
   - Group related endpoints into a single `*.service.ts` file (e.g., `user.service.ts`, `auth.service.ts`).
   - Add `export * from "./<feature>.service";` to `src/services/index.ts` if new service files are created.

Example patterns (mirror the existing code style):

\`\`\`ts
// Option 1: Individual exports (preferred, matches current codebase)
import { api } from "@/services";
import type { User, CreateUserRequest } from "@/interfaces";

// GET all resources
export const getUsers = () => api.get<User[]>("/users");

// GET single resource with path parameter
export const getUser = (id: number) => api.get<User>(\`/users/\${id}\`);

// GET with query parameters
export const searchUsers = (params: { q: string; page?: number }) =>
api.get<User[]>("/users/search", { params });

// POST with typed body
export const createUser = (data: CreateUserRequest) =>
api.post<User>("/users", data);

// PUT with path parameter and partial data
export const updateUser = (id: number, data: Partial<User>) =>
api.put<User>(\`/users/\${id}\`, data);

// DELETE with path parameter
export const deleteUser = (id: number) => api.delete(\`/users/\${id}\`);

// Option 2: Grouped exports (also acceptable)
export const userService = {
getUsers: () => api.get<User[]>("/users"),
getUser: (id: number) => api.get<User>(\`/users/\${id}\`),
createUser: (data: CreateUserRequest) => api.post<User>("/users", data),
updateUser: (id: number, data: Partial<User>) =>
api.put<User>(\`/users/\${id}\`, data),
deleteUser: (id: number) => api.delete(\`/users/\${id}\`),
};
\`\`\`

### Interface Definition Rules (MUST FOLLOW)

- Location: Define all interfaces inside `src/interfaces/`.
- Reuse First: If a suitable file already exists (e.g., `token.ts`, `trade.ts`, `profile.ts`, etc.), add new interfaces there. Otherwise create a new file with a descriptive name.
- Naming: Use PascalCase for interface/type names (e.g., `CreateItemRequest`, `ItemResponse`, `ItemsResponse`).
- Exports: Ensure new interfaces are exported from their file and re-exported through `src/interfaces/index.ts`.
- Typing:
  - Use explicit primitive types (`string`, `number`, `boolean`).
  - Mark optional fields with `?` when not guaranteed by the API.
  - Prefer literal unions for documented enums (e.g., `status: "active" | "disabled"`).
  - Use `string` for ISO dates unless otherwise guaranteed.
  - For paginated lists, reuse `IPaginationParams` if appropriate and define a corresponding `...Response` shape that matches fields shown in the cURL command result.
- Do NOT declare interfaces inline inside service files.

Example interface structure:

\`\`\`ts
// src/interfaces/item.ts
export interface CreateItemRequest {
name: string;
description?: string;
}

export interface Item {
id: string;
name: string;
description?: string;
createdAt: string;
}

export interface CreateItemResponse {
item: Item;
}

export interface ListItemsResponse {
items: Item[];
total: number;
}
\`\`\`

And remember to update the barrel:

\`\`\`ts
// src/interfaces/index.ts
export \* from "./item";
\`\`\`

### Conventions to Respect from Existing Code

- Import style: `import { api } from '@/services';` in service files.
- Use generics for response typing on `api` calls.
- **Always use leading slashes in API paths**: `/users`, `/tokens/${address}`, etc.
- Follow the folder structure and reuse types like `IPaginationParams`, `IResponse<T>`, etc., when applicable.
- Keep function names concise and descriptive; one function per endpoint.
- The API client uses Axios with interceptors that return `response.data` directly, so type the generic `T` as the actual response data structure.

### Deliverables

For each endpoint in the provided cURL command(s):

1. A typed function in the appropriate `src/services/*.service.ts` file.
2. Request/response/DTO interfaces in `src/interfaces/` with proper exports (and re-export in `src/interfaces/index.ts`).

### Environment

- Do not change the API client. Base URL is provided by `NEXT_PUBLIC_API_BASE_URL`.
- The API client is configured in `src/lib/ApiClient.ts` and exported from `src/services/index.ts`.
- Authentication tokens are automatically added via request interceptors from `localStorage.getItem("accessToken")`.

### Prerequisites Check

**BEFORE PROCEEDING:** Verify that at least one clear and valid cURL command is provided. If no example is available:

1. Inform the user: "A sample cURL command is required to generate API functions."
2. Request the user to provide a cURL example representing the desired API endpoint.
3. Do NOT create any API endpoints or functions without a provided cURL command.

### Final step

After generating all functions and interfaces, double-check imports/exports and that function signatures reference the correct types from `src/interfaces`.

**Note:** API functions will only be defined based on provided cURL command examples. No endpoints will be created without clear cURL samples describing path, method, headers, and payload.
