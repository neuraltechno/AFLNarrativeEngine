# AFL Narrative Engine

A system for generating narrative-driven AFL match reports and seasonal insights using AI.

## Project Structure

- **`/src/app`**: Next.js App Router pages and layouts.
- **`/components`**: Reusable UI components.
- **`/lib`**: Shared utilities, API clients, and business logic.
- **`/data`**: Local data storage.
  - **`/data/narratives`**: Generated narrative content.
  - **`/data/metrics`**: Processed AFL statistical data.
- **`/scripts`**: Maintenance and data processing scripts.

## Foundation

This project is built with:
- **Next.js 15+** (App Router)
- **TypeScript**
- **Tailwind CSS**

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.
