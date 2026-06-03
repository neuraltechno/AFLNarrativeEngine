import fs from 'fs';
import path from 'path';

interface TeamTrend {
  team: string;
  trend: 'Rising' | 'Stable' | 'Falling';
  narrative_tags?: string[];
  supporting_metrics: {
    recent_win_rate: number;
    recent_avg_margin: number;
    recent_avg_score: number;
    win_rate_trend: number;
    margin_trend: number;
    weighted_margin_trend?: number;
    strength_of_schedule?: number;
    finishing_power?: number;
    rolling_efficiency?: number;
    games_analyzed: number;
  };
}

async function getTeamTrends(): Promise<TeamTrend[]> {
  const filePath = path.join(process.cwd(), 'data', 'metrics', 'team_trends.json');
  if (!fs.existsSync(filePath)) {
    return [];
  }
  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents);
}

export default async function TeamsPage() {
  const trends = await getTeamTrends();

  return (
    <div className="p-8 font-sans max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Team Trends</h1>
        <p className="text-zinc-600 dark:text-zinc-400">Analysis of team momentum based on recent performance.</p>
      </header>

      <section className="mb-8 p-5 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm text-zinc-700 dark:text-zinc-300">
        <h2 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-3 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
          How Trends are Calculated
        </h2>
        <p className="mb-4">
          Trends compare a team&apos;s performance over their **last 5 games** against the **previous 5 games**. We also track deeper structural metrics to form narratives:
        </p>
        
        <ul className="grid gap-3 md:grid-cols-3 mb-5">
          <li className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
              <strong className="text-zinc-900 dark:text-zinc-100">Rising</strong>
            </div>
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Win rate up &ge;20% or SoS-weighted avg margin up &ge;15 pts.</span>
          </li>
          <li className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
              <strong className="text-zinc-900 dark:text-zinc-100">Falling</strong>
            </div>
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Win rate down &ge;20% or SoS-weighted avg margin down &ge;15 pts.</span>
          </li>
          <li className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-zinc-400 shrink-0" />
              <strong className="text-zinc-900 dark:text-zinc-100">Stable</strong>
            </div>
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Performance remains within thresholds.</span>
          </li>
        </ul>

        <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800 grid gap-4 md:grid-cols-2">
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Strength of Schedule (SoS)</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">Average win rate of recent opponents. We weight margin trends based on SoS so that beating top teams counts more than beating bottom teams.</p>
          </div>
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Finishing Power (Q4)</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">The net 4th-quarter score margin over the last 5 games. A positive trend indicates strong late-game structure, while a drop indicates late-game fatigue.</p>
          </div>
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">3-Week Efficiency</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">Rolling percentage (Points For / Points Against) over the last 3 matches. Shows structural form independent of single-game blowouts.</p>
          </div>
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Narrative Tags</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">Automated qualitative insights (e.g., <span className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 px-1 py-0.5 rounded mx-0.5 font-medium">Battle-Tested Rise</span>) generated when specific underlying metrics breach historical thresholds.</p>
          </div>
        </div>

        <p className="mt-5 text-xs text-zinc-500 dark:text-zinc-500 italic">
          * For teams with 5-9 games, trend is based on overall win rate (&ge;60% Rising, &le;40% Falling). At least 5 games required.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {trends.map((team) => (
          <div 
            key={team.team} 
            className="border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-zinc-900"
          >
            <div className="flex justify-between items-start mb-2">
              <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">{team.team}</h2>
              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                team.trend === 'Rising' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                team.trend === 'Falling' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300'
              }`}>
                {team.trend}
              </span>
            </div>

            {team.narrative_tags && team.narrative_tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {team.narrative_tags.map(tag => (
                  <span key={tag} className="px-2 py-0.5 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded text-[10px] font-medium tracking-wide">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            <div className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
              <div className="flex justify-between">
                <span>Recent Win Rate:</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{(team.supporting_metrics.recent_win_rate * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Margin:</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{team.supporting_metrics.recent_avg_margin.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Score:</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{team.supporting_metrics.recent_avg_score.toFixed(1)}</span>
              </div>
              {team.supporting_metrics.strength_of_schedule !== undefined && (
                <div className="flex justify-between">
                  <span>Opponent SoS:</span>
                  <span className={`font-semibold ${team.supporting_metrics.strength_of_schedule > 0.55 ? 'text-red-600 dark:text-red-400' : team.supporting_metrics.strength_of_schedule < 0.45 ? 'text-green-600 dark:text-green-400' : 'text-zinc-900 dark:text-zinc-100'}`}>
                    {(team.supporting_metrics.strength_of_schedule * 100).toFixed(0)}%
                  </span>
                </div>
              )}
              {team.supporting_metrics.weighted_margin_trend !== undefined && (
                <div className="flex justify-between">
                  <span>SoS-Weighted Margin Trend:</span>
                  <span className={`font-semibold ${team.supporting_metrics.weighted_margin_trend > 0 ? 'text-green-600 dark:text-green-400' : team.supporting_metrics.weighted_margin_trend < 0 ? 'text-red-600 dark:text-red-400' : 'text-zinc-900 dark:text-zinc-100'}`}>
                    {team.supporting_metrics.weighted_margin_trend > 0 ? '+' : ''}{team.supporting_metrics.weighted_margin_trend.toFixed(1)}
                  </span>
                </div>
              )}
              {team.supporting_metrics.finishing_power !== undefined && (
                <div className="flex justify-between">
                  <span>Finishing Power (Q4):</span>
                  <span className={`font-semibold ${team.supporting_metrics.finishing_power > 0 ? 'text-green-600 dark:text-green-400' : team.supporting_metrics.finishing_power < 0 ? 'text-red-600 dark:text-red-400' : 'text-zinc-900 dark:text-zinc-100'}`}>
                    {team.supporting_metrics.finishing_power > 0 ? '+' : ''}{team.supporting_metrics.finishing_power.toFixed(1)}
                  </span>
                </div>
              )}
              {team.supporting_metrics.rolling_efficiency !== undefined && (
                <div className="flex justify-between">
                  <span>3-Wk Efficiency:</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {team.supporting_metrics.rolling_efficiency.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {trends.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded text-amber-800">
          No trend data found. Please run the trend calculation script.
        </div>
      )}

      <nav className="mt-12">
        <a href="/" className="text-blue-600 hover:underline">Back to Home</a>
      </nav>
    </div>
  );
}
