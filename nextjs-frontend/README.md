# Next.js Frontend – AGUI & CopilotKit Protocol Integration Guide

## Overview
This frontend is built with Next.js 15.1.0 and supports integration with multiple AI agent protocols, including AGUI and CopilotKit. The architecture is designed for flexibility, maintainability, and easy extension—allowing you to add new agent-backed chat or co-pilot features to any page with minimal duplication.

## Key Features
- **Route Progress**: Automatic navigation progress indicators using nprogress
- **Agent Integration**: Support for AGUI and CopilotKit protocols
- **Modern UI**: Built with Radix UI components and Tailwind CSS
- **Type Safety**: Full TypeScript support with strict type checking
- **Testing**: Jest and React Testing Library setup
- **Code Quality**: ESLint, Prettier, and TypeScript configuration
- **OpenAPI Integration**: Auto-generated type-safe API client from backend schema

---

## Agent Protocols Supported
- **AGUI**: Connects to an AGUI backend agent via HTTP.
- **CopilotKit**: Connects to a CopilotKit backend agent (e.g., OpenAI, custom LLM, etc.).

Agents are configured and referenced using a central config file to avoid hardcoding names and URLs throughout the codebase.

---

## Key Files & Structure
- `app/agentConfig.ts` – Central place for agent names and runtime URLs.
- `app/ClientCopilotKitWrapper.tsx` – Conditional CopilotKit provider wrapper.
- `app/(auth)/aguichat/page.tsx` – Example of AGUI agent integration with sidebar.
- `app/api/copilotkit-agui/route.ts` – Backend API route for AGUI agent.
- `app/api/copilotkit/route.ts` – Backend API route for CopilotKit agent.
- `components/ui/RouteProgress.tsx` – Navigation progress indicator component.
- `components/ui/progress.tsx` – Agent progress visualization component.
- `lib/config.ts` – Application configuration and feature flags.
- `openapi-ts.config.ts` – OpenAPI client generation configuration.

---

## Dependencies & Technologies
- **Next.js**: 15.1.0 with App Router
- **React**: 19.0.0
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **Radix UI**: Accessible component primitives
- **CopilotKit**: 1.9.0 for AI agent integration
- **AG-UI Client**: 0.0.28 for AGUI protocol
- **NProgress**: 0.2.0 for route progress indicators
- **React Hook Form**: 7.54.0 for form handling
- **Zod**: 3.23.8 for schema validation
- **@hey-api/openapi-ts**: Auto-generated type-safe API client

---

## Route Progress Feature
The application includes automatic route progress indicators using nprogress:

- **Automatic Detection**: Progress starts on navigation and link clicks
- **Smart Completion**: Progress completes when page content loads
- **Same-page Handling**: Brief progress animation for same-page clicks
- **Logging**: Comprehensive logging for debugging (development only)

The RouteProgress component is automatically included in the root layout and can be configured via `lib/config.ts`.

---

## API Configuration & Backend-Frontend Synchronization

This frontend uses a centralized API configuration system and auto-generated TypeScript clients from the backend's OpenAPI schema to ensure type safety and API consistency.

### API Configuration System

The frontend uses `lib/apiConfig.ts` for centralized API configuration:

```typescript
export const API_CONFIG = {
  // Backend API prefix - configurable via environment
  BACKEND_API_PREFIX: process.env.NEXT_PUBLIC_BACKEND_API_PREFIX || "/api/v1",
  
  // Agent API prefix - configurable via environment  
  AGENT_API_PREFIX: process.env.NEXT_PUBLIC_AGENT_API_PREFIX || "/api/v1",
  
  // Base URLs for different services
  BACKEND_BASE_URL: process.env.NEXT_PUBLIC_API_URL || "http://backend:8000",
  AGENT_BASE_URL: process.env.AGENT_URL || "http://agent:8000",
};
```

### Helper Functions

Use these helper functions to build API URLs dynamically:

```typescript
import { buildBackendUrl, buildAgentUrl } from "@/lib/apiConfig";

// Build backend API URLs
const userUrl = buildBackendUrl("users/me");
const itemsUrl = buildBackendUrl("items");

// Build agent API URLs  
const agentChatUrl = buildAgentUrl("chat");
```

### OpenAPI Client Generation

**Important:** This project uses a containerized development environment. Always run client generation from within the frontend container:

```bash
# Start the backend first to get fresh schema
docker compose up backend -d

# Generate the API client from within the frontend container
docker compose exec frontend pnpm generate-client
```

**Why use the container?**
- Environment variables are properly set in containers
- Volume mounts ensure access to shared OpenAPI schema
- Consistent with the development workflow

### Backend-Frontend Synchronization Process

**Automated Process (Recommended):**

When backend API changes occur, use the automated Makefile targets:

```bash
# For normal API changes
make sync-api-client

# For major backend changes (restarts backend)
make sync-api-client-force

# Generate client and clean up containers afterward
make sync-api-client-clean
```

**Manual Process (if needed):**

1. **Update Backend Configuration:**
   ```bash
   # Ensure backend is running with latest changes
   docker compose up backend -d
   ```

2. **Regenerate OpenAPI Schema:**
   ```bash
   # The schema is automatically updated when backend starts
   # Verify it's current by checking the health endpoint
   curl http://localhost:8000/api/v1/utils/health-check/
   ```

3. **Regenerate Frontend Client:**
   ```bash
   # Generate client from within the frontend container
   docker compose exec frontend pnpm generate-client
   ```

4. **Update Frontend Code:**
   - Use `buildBackendUrl()` helper for new API calls
   - Update any hardcoded `/api/v1` paths to use configuration
   - Test the integration

### Environment Variables

Configure API prefixes via environment variables:

```bash
# In .env or docker-compose.yml
BACKEND_API_PREFIX="/api/v1"
NEXT_PUBLIC_BACKEND_API_PREFIX="/api/v1"
NEXT_PUBLIC_AGENT_API_PREFIX="/api/v1"
```

### Common Synchronization Issues

**Problem:** OpenAPI client generation fails locally
**Solution:** Always use `docker compose exec frontend pnpm generate-client`

**Problem:** 404 errors after backend changes
**Solution:** 
1. Regenerate the OpenAPI client
2. Check function names (they may change)
3. Update data structures if API responses changed

**Problem:** Environment variables not working
**Solution:** Ensure variables are set in docker-compose.yml and restart containers

### Development Workflow Best Practices

1. **Always work in containers** for API-related tasks
2. **Use helper functions** instead of hardcoded paths
3. **Regenerate client** after any backend API changes
4. **Test incrementally** after each synchronization step
5. **Check environment variables** in docker-compose.yml first

### Important Notes
- **Always regenerate the client** when the backend API changes
- **Check function names** - they may change between regenerations
- **Verify data structures** - API responses and request bodies may be updated
- **Update tests** - test files need to be updated when client functions change

---

## How to Add a New Agent Protocol to a Page

### 1. **Define Agent Name and Runtime URL**
Edit `app/agentConfig.ts` to add your new agent:

```ts
export const MY_AGENT_NAME = "myagent";
export const MY_AGENT_RUNTIME_URL = "/api/copilotkit-myagent";
```

### 2. **Create or Update the API Route**
Add a new API route under `app/api/` for your agent, e.g. `app/api/copilotkit-myagent/route.ts`.
- Register your agent using the name from `agentConfig.ts`.
- **⚠️ CRITICAL**: The agent name in `CopilotRuntime` MUST exactly match the agent name registered in the backend.
- Example for AGUI:

```ts
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { MY_AGENT_NAME } from "../../agentConfig";

export const POST = async (req: NextRequest) => {
  const myAgent = new HttpAgent({ url: process.env.AGENT_MYAGENT_URL });
  const runtime = new CopilotRuntime({
    agents: { [MY_AGENT_NAME]: myAgent },
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: MY_AGENT_RUNTIME_URL,
  });
  return handleRequest(req);
};
```

### ⚠️ Agent Name Consistency Checklist

Before testing your agent, verify these names match exactly:

1. **Backend agent registration** (in `fastapi_agent/app/main.py`):
   ```python
   register_agent(my_agent)  # agent.name = "myagent"
   ```

2. **Frontend agent config** (in `app/agentConfig.ts`):
   ```typescript
   export const MY_AGENT_NAME = "myagent";  // ✅ Must match backend
   ```

3. **Frontend CopilotRuntime** (in your route.ts):
   ```typescript
   const runtime = new CopilotRuntime({
     agents: {
       [MY_AGENT_NAME]: myAgent,  // ✅ Uses the config constant
     },
   });
   ```

**Common Mistake**: Using different names like `"myagent"` in backend but `"my-agent"` in frontend.
```

### 3. **Update ClientCopilotKitWrapper (if needed)**
If you want the agent available on specific routes, update `app/ClientCopilotKitWrapper.tsx`:

```tsx
import { MY_AGENT_NAME, MY_AGENT_RUNTIME_URL } from "./agentConfig";

export default function ClientCopilotKitWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/myagent")) {
    return (
      <CopilotKit key={pathname} runtimeUrl={MY_AGENT_RUNTIME_URL} agent={MY_AGENT_NAME}>
        {children}
      </CopilotKit>
    );
  }
  // For all other routes, just render children without CopilotKit context
  return <>{children}</>;
}
```

### 4. **Integrate the Agent in Your Page/Component**
Create your page or component with the agent integration:

```tsx
import "@copilotkit/react-ui/styles.css";
import { useCoAgentStateRender } from "@copilotkit/react-core";
import dynamic from "next/dynamic";
import { MY_AGENT_NAME } from "../agentConfig";

const CopilotSidebar = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => mod.CopilotSidebar),
  { ssr: false }
);

export default function MyAgentPage() {
  // Render agent progress logs if present
  const maybeProgress = useCoAgentStateRender<any>({
    name: MY_AGENT_NAME,
    render: ({ state }) => {
      if (state?.logs?.length > 0) {
        return <Progress logs={state.logs} />;
      }
      return null;
    },
  });

  return (
    <div className="flex flex-col items-center justify-center h-full w-full max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">My Agent Chat</h1>
      {maybeProgress ?? null}
      <CopilotSidebar
        labels={{
          title: "My Agent Assistant",
          initial: "Hi! How can I assist you today?",
        }}
        defaultOpen={true}
      />
    </div>
  );
}
```

---

## Troubleshooting

### Agent Name Issues
If you get "Failed to find any agents" errors:

1. **Check agent name consistency** using the checklist above
2. **Verify environment variables** are set correctly
3. **Restart services** after making name changes
4. **Check browser console** for detailed error messages
5. **Verify API endpoints** are accessible

### Common Configuration Mistakes
- **Agent name mismatch**: Backend `"agent"` vs Frontend `"agent-chat"`
- **Wrong environment variables**: Using `AGENT_URL` instead of `AGENT_AGUI_URL`
- **Missing agent registration**: Forgetting to register agent in `main.py`
- **Case sensitivity**: `"MyAgent"` vs `"myagent"` are different

## Development Setup

### Prerequisites
- Node.js 20+
- pnpm (recommended) or npm
- Docker (for containerized development)

### Installation
```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Run tests
pnpm test

# Type checking
pnpm tsc

# Generate API client
pnpm generate-client
```

### Docker Development
```bash
# Build and start all services
docker compose up --build

# Start only frontend
docker compose up frontend
```

---

## Configuration

### Environment Variables
- `AGENT_URL`: Backend agent service URL
- `AGENT_API_PREFIX`: API prefix for agent endpoints
- `NEXT_PUBLIC_LOG_LEVEL`: Logging level (debug, info, warn, error, none)
- `NEXT_PUBLIC_ENABLE_SERVER_LOGS`: Enable server-side logging

### Feature Flags (`lib/config.ts`)
- `routeProgress`: Enable/disable navigation progress indicators
- `prefetching`: Enable/disable automatic prefetching

---

## Best Practices
- **Always use constants from `agentConfig.ts`** for agent names and URLs—never hardcode.
- **Wrap only the components/pages that need agent context** with `<CopilotKit>`. The `ClientCopilotKitWrapper` handles this automatically for specific routes.
- **Keep API route agent registration in sync** with frontend agent names.
- **Document new agents** in `agentConfig.ts` and this README.
- **Use the Progress component** to show agent execution progress.
- **Follow the established patterns** for agent integration and UI components.
- **Regenerate the OpenAPI client** whenever the backend API changes.
- **Update tests** when client function names or data structures change.

---

## Troubleshooting

### Agent Integration Issues
- **Agent Not Found:**
  - Ensure the agent is registered in the backend API route with the exact name used in the frontend.
  - Check that the runtime URL matches between frontend and backend.
  - See [CopilotKit troubleshooting guide](https://docs.copilotkit.ai/coagents/troubleshooting/common-issues#i-am-getting-agent-not-found-error).
- **Environment Variables:**
  - Make sure any required backend URLs (e.g., `AGENT_URL`) are set in your environment.
- **Context Errors:**
  - If you see errors about missing CopilotKit context, ensure your component is wrapped in `<CopilotKit ...>` or the route is handled by `ClientCopilotKitWrapper`.

### Route Progress Issues
- Check that `routeProgress` is enabled in `lib/config.ts`
- Verify nprogress is properly imported in `RouteProgress.tsx`

### API Client Issues
- **404 Errors**: Regenerate the OpenAPI client with `pnpm generate-client`
- **Function Name Changes**: Update all references when client functions are renamed
- **Data Structure Changes**: Update components and tests when API responses change
- **Type Errors**: Run `pnpm tsc` to check for type mismatches after client regeneration

### Common Client Regeneration Issues
When regenerating the OpenAPI client, you may need to update:

1. **Function Names**: 
   - `registerRegister` → `usersRegisterUser`
   - `authJwtLogin` → `loginLoginAccessToken`
   - `readItem` → `itemsReadItems`

2. **Data Structures**:
   - Item fields: `name` → `title`, `quantity` removed
   - Password reset: `password` → `new_password`
   - API responses: Updated response structures

3. **Parameter Structures**:
   - Path vs body parameters may change
   - Request/response object structures may be updated

4. **Test Files**: Update all test references to match new client functions

---

## Example: Adding a New AGUI Agent
1. Add to `agentConfig.ts`:
   ```ts
   export const SALES_AGENT_NAME = "sales";
   export const SALES_AGENT_RUNTIME_URL = "/api/copilotkit-sales";
   ```
2. Create `app/api/copilotkit-sales/route.ts` and register the agent as above.
3. Update `ClientCopilotKitWrapper.tsx` to include the new route pattern.
4. Create your page component with CopilotSidebar integration.

---

## Contribution Guidelines
- **Add new agent constants** to `agentConfig.ts`.
- **Document your agent** in this README.
- **Follow code style and DRY principles**—reuse config, avoid duplication.
- **Test your integration** on both frontend and backend before submitting PRs.
- **Use TypeScript** for all new code.
- **Follow the established component patterns** in `components/ui/`.
- **Regenerate and test the API client** when backend changes are made.

---

## Support
For questions or issues, contact the project maintainer or open an issue in the repository. 