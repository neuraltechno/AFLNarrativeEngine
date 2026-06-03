import fs from 'fs';
import path from 'path';

async function getStats() {
  const trendsPath = path.join(process.cwd(), 'data', 'metrics', 'team_trends.json');
  let risingCount = 0;
  let fallingCount = 0;
  let totalTeams = 0;

  if (fs.existsSync(trendsPath)) {
    const trends = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
    totalTeams = trends.length;
    risingCount = trends.filter((t: any) => t.trend === 'Rising').length;
    fallingCount = trends.filter((t: any) => t.trend === 'Falling').length;
  }

  return { risingCount, fallingCount, totalTeams };
}

export default async function Home() {
  const stats = await getStats();

  return (
    <div className="p-8 font-sans max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-4">AFL Narrative Engine</h1>
      <p className="text-xl text-zinc-600 mb-8">
        Translating AFL statistics into stories, insights, and trends.
      </p>
      
      <div className="grid gap-6 md:grid-cols-2 mb-12">
        <div className="bg-zinc-50 border rounded-xl p-6">
          <h2 className="text-xl font-bold mb-2">Team Trends</h2>
          <p className="text-zinc-600 mb-4">
            Currently tracking {stats.totalTeams} teams. 
            {stats.risingCount} are rising, {stats.fallingCount} are falling.
          </p>
          <a href="/teams" className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
            View All Trends
          </a>
        </div>
        
        <div className="bg-zinc-50 border rounded-xl p-6">
          <h2 className="text-xl font-bold mb-2">Round Narratives</h2>
          <p className="text-zinc-600 mb-4">
            Analysis of the latest matches and key stories.
          </p>
          <a href="/rounds" className="inline-block bg-zinc-800 text-white px-4 py-2 rounded-lg font-medium hover:bg-zinc-900 transition-colors">
            Explore Rounds
          </a>
        </div>
      </div>

      <div className="flex gap-4 mb-12">
        <a href="/admin" className="text-sm text-zinc-500 hover:text-blue-600 flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          Admin Panel
        </a>
      </div>

      <div className="border-t pt-8">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">Project Status</h3>
        <ul className="space-y-2 text-zinc-600">
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Phase 1: Foundation (Complete)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Phase 2: Data Pipeline (Complete)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            Phase 3: Team Trend Engine (In Progress)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-zinc-300"></span>
            Phase 4: AI Narrative Generation (Pending)
          </li>
        </ul>
      </div>
    </div>
  );
}
