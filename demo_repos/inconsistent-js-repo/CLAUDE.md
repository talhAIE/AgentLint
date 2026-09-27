# CLAUDE.md

This file instructs Claude on how to work in this repository.

## Package Manager

Use pnpm to install dependencies:

```bash
pnpm install
pnpm run build
pnpm run test
```

## Test Command

Run the test suite with Vitest:

```bash
pnpm run test
```

## Project Structure

- `src/` — application source code
- `tests/` — test files
- `dist/` — build output (generated, do not edit)

## Code Style

- Use ESLint for linting: `pnpm run lint`
- Use Prettier for formatting: `pnpm run format`

## Definition of Done

Always run pnpm lint and pnpm test before completing a task.

## Notes

- Node.js 18 is required
- Build artifacts go in `dist/`
