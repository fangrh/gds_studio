# TODOS

## Set up Vitest for frontend component testing
- **What:** Install Vitest + React Testing Library + jsdom. Write initial tests for GdsViewer click handling and ElementDrawer rendering.
- **Why:** Frontend has zero test coverage. Every UI change ships untested. GdsViewer click handling and ElementDrawer state management need tests before the next feature is built on top.
- **Pros:** Catches regressions in click-to-select, drawer toggle, and issue creation flow. Future features (annotation, agent chat) can be tested from day one.
- **Cons:** ~0.5 day to set up. Mocking OpenLayers map interactions is non-trivial.
- **Context:** Backend has pytest with good coverage. Frontend is the gap. The ElementDrawer component introduced in the element-click feature is the natural first test target.
- **Depends on:** Nothing. Independent work.
