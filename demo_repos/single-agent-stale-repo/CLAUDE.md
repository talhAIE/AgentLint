# CLAUDE.md

This file instructs Claude on how to work in this repository.

## Package Manager

Use npm to install dependencies:

```bash
npm install
npm run build
npm test
```

## Test Command

Run the test suite with:

```bash
npm test
```

## Project Structure

- `src/` — application source code
- `src/services/` — service layer modules
- `tests/` — test files
- `dist/` — build output (generated)

## Code Style

- Use ESLint for linting: `npm run lint`
- Use Prettier for formatting: `npm run format`

## Notes

- Node.js 16 is required
- Build artifacts go in `dist/`
