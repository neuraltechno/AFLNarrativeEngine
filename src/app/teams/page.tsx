import fs from 'fs';
import path from 'path';
import Link from 'next/link';

export interface PlayerFormImpact {
  playerId: string;
  playerName: string;
  baselineScore: number;
  windowScore: number;
  delta: number;
  role: 'Engine Room' | 'Missing Link' | 'One-Man Band';
  narrativeBlurb: string;
  statType: string;
}

export interface TeamTrend {
  team: string;
  trend: 'Rising' | 'Stable' | 'Falling';
  narrative_tags?: string[];
  key_players?: PlayerFormImpact[];
  current_ladder_position?: number;
  expected_ladder_position?: number;
  supporting_metrics: {
    recent_win_rate: number;
    recent_avg_margin: number;
    recent_avg_score: number;
    win_rate_trend: number;
    margin_trend: number;
    weighted_margin_trend?: number;
    strength_of_schedule?: number;
    next_3_sos?: number;
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

function FormMatrix({ trends }: { trends: TeamTrend[] }) {
  const matrixTeams = trends.filter(
    (t) => t.current_ladder_position && t.expected_ladder_position
  );

  if (matrixTeams.length === 0) return null;

  const ticks = Array.from({ length: 18 }, (_, i) => i + 1);
  const reversedTicks = [...ticks].reverse();

  return (
    <div className="mb-12">
      <div className="flex gap-4 mb-4 text-sm font-medium">
        <div className="flex items-center gap-2"><div className="w-4 h-4 bg-[#86efac] rounded-sm"></div> <span className="text-zinc-900 dark:text-zinc-100">Rising</span></div>
        <div className="flex items-center gap-2"><div className="w-4 h-4 bg-[#60a5fa] rounded-sm"></div> <span className="text-zinc-900 dark:text-zinc-100">Falling</span></div>
        <div className="flex items-center gap-2"><div className="w-4 h-4 bg-[#fbbf24] rounded-sm"></div> <span className="text-zinc-900 dark:text-zinc-100">Stable</span></div>
      </div>

      <div className="relative w-full aspect-square md:aspect-[2/1] bg-[#1e293b] rounded-xl font-sans overflow-hidden">
        {/* Y Axis Label */}
        <div className="absolute top-4 left-6 text-zinc-300 text-sm">
          Expected Ladder Position &uarr;
        </div>

        {/* Y Axis Ticks */}
        <div className="absolute top-16 bottom-16 left-0 w-12 md:w-16 text-[10px] md:text-xs font-semibold text-zinc-400 pointer-events-none">
          {ticks.map(tick => {
            const topPercent = ((tick - 1) / 17) * 100;
            return (
              <div key={tick} className="absolute w-full text-center -translate-y-1/2" style={{ top: `${topPercent}%` }}>
                {tick}
              </div>
            );
          })}
        </div>

        {/* Chart Area */}
        <div className="absolute top-16 bottom-16 left-12 md:left-16 right-6 md:right-8 border-l border-b border-zinc-600/50">
          
          {/* Quadrants */}
          <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 z-0 pointer-events-none">
            <div className="border-r border-b border-dashed border-zinc-500/50 flex items-start justify-start p-2 md:p-4 text-zinc-500/70 font-bold uppercase tracking-widest text-[10px] md:text-sm">Sleeping Giants</div>
            <div className="border-b border-dashed border-zinc-500/50 flex items-start justify-end p-2 md:p-4 text-zinc-500/70 font-bold uppercase tracking-widest text-[10px] md:text-sm">True Contenders</div>
            <div className="border-r border-dashed border-zinc-500/50 flex items-end justify-start p-2 md:p-4 text-zinc-500/70 font-bold uppercase tracking-widest text-[10px] md:text-sm">Rebuilders</div>
            <div className="flex items-end justify-end p-2 md:p-4 text-zinc-500/70 font-bold uppercase tracking-widest text-[10px] md:text-sm">Paper Tigers</div>
          </div>

          {/* X Axis Ticks */}
          <div className="absolute -bottom-10 left-0 right-0 h-10 text-[10px] md:text-xs font-semibold text-zinc-400 pointer-events-none">
            {reversedTicks.map(tick => {
              const leftPercent = ((18 - tick) / 17) * 100;
              return (
                <div key={tick} className="absolute text-center -translate-x-1/2" style={{ left: `${leftPercent}%`, top: '8px' }}>
                  {tick}
                </div>
              );
            })}
          </div>
          
          {/* X Axis Label */}
          <div className="absolute -bottom-16 left-0 right-0 text-center text-zinc-300 text-sm">
            Actual Ladder Position &rarr;
          </div>

          {/* Dots */}
          <div className="absolute inset-0 z-10">
            {matrixTeams.map((team) => {
              const xPercent = ((18 - team.current_ladder_position!) / 17) * 100;
              const yPercent = ((team.expected_ladder_position! - 1) / 17) * 100;

              let dotColor = "bg-[#fbbf24]";
              if (team.trend === "Rising") dotColor = "bg-[#86efac]";
              if (team.trend === "Falling") dotColor = "bg-[#60a5fa]";

              return (
                <div
                  key={team.team}
                  className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1 hover:z-20 transition-transform hover:scale-125 cursor-default group"
                  style={{
                    left: `${xPercent}%`,
                    top: `${yPercent}%`,
                  }}
                  title={`${team.team}\nActual: ${team.current_ladder_position}\nExpected: ${team.expected_ladder_position}`}
                >
                  <span className="text-[10px] md:text-xs font-bold text-white drop-shadow-md">{team.team.substring(0, 3).toUpperCase()}</span>
                  <div className={`w-4 h-4 md:w-5 md:h-5 rounded-full border border-black shadow-sm ${dotColor}`}></div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

import { TeamList } from './TeamList';

export default async function TeamsPage() {
  const trends = await getTeamTrends();

  // Sort by expected_ladder_position as default
  const sortedTrends = [...trends].sort((a, b) => {
    const posA = a.expected_ladder_position ?? 99;
    const posB = b.expected_ladder_position ?? 99;
    return posA - posB;
  });

  // Determine max round from fixture data (completed matches)
  const getRound = () => {
    const fixturePath = path.join(process.cwd(), 'data', 'raw', 'fixture_2026.json');
    if (!fs.existsSync(fixturePath)) return 0;
    const fixtures = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
    const completed = fixtures.filter((f: any) => f.complete === 100);
    return completed.length > 0 ? Math.max(...completed.map((f: any) => f.round)) : 0;
  };
  
  const currentRound = getRound();

  return (
    <div className="p-8 font-sans max-w-4xl mx-auto">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold mb-2">Team Trends</h1>
          <p className="text-zinc-600 dark:text-zinc-400">2026 Season Analysis • Round {currentRound}</p>
        </div>
      </header>

      <FormMatrix trends={trends} />

      <TeamList trends={sortedTrends} />

      <section className="mt-8 mb-8 p-5 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm text-zinc-700 dark:text-zinc-300">
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
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">The Next 3 Weeks</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">Projects form against the upcoming fixture. If a rising team faces a brutal draw, it triggers a <strong>Reality Check Window</strong>. If a falling team gets an easy draw, it&apos;s a <strong>Soft Landing</strong>.</p>
          </div>
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Finishing Power (Q4)</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">The net 4th-quarter score margin over the last 5 games. A positive trend indicates strong late-game structure, while a drop indicates late-game fatigue.</p>
          </div>
          <div>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">3-Week Efficiency</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">Rolling percentage (Points For / Points Against) over the last 3 matches. Shows structural form independent of single-game blowouts.</p>
          </div>
          <div className="md:col-span-2">
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Player Trends</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-2">Highlights individual player form driving team momentum:</p>
            <ul className="text-xs text-zinc-600 dark:text-zinc-400 grid gap-x-4 gap-y-2 md:grid-cols-3">
              <li><strong className="text-green-600 dark:text-green-400">🚂 The Engine Room:</strong> A player whose massive spike in contested possessions is fueling a rising team.</li>
              <li><strong className="text-red-600 dark:text-red-400">👻 The Missing Link:</strong> A key midfielder whose plummeting clearances are driving a falling team&apos;s slump.</li>
              <li><strong className="text-amber-600 dark:text-amber-400">🎸 The One-Man Band:</strong> A player carrying an unsustainably high percentage (over 35%) of the team&apos;s total clearances.</li>
            </ul>
          </div>
          <div className="md:col-span-2">
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1 text-xs uppercase tracking-wider">Narrative Tags</strong>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-2">Automated qualitative insights generated when specific underlying metrics breach historical thresholds:</p>
            <ul className="text-xs text-zinc-600 dark:text-zinc-400 grid gap-x-4 gap-y-2 md:grid-cols-2">
              <li><strong className="text-zinc-900 dark:text-zinc-100">Flat-Track Bullies:</strong> Crushing the minnows, but haven&apos;t beaten anyone good.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">The Cardiac Kids:</strong> Every game goes down to the wire. Better check your blood pressure.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Sinking Ship:</strong> Falling trend combined with high late-game fatigue or mounting losses.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">The Ultimate Tease:</strong> The stats say they should be top 4. The ladder says otherwise due to late fade-outs.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Downhill Skiers:</strong> Look like superstars when the game is on their terms, but go missing when the heat is on.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Premiership Quarter Specialists:</strong> Always come out breathing fire in the 3rd quarter.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Honourable Losses:</strong> The ultimate backhanded compliment. They try hard, but just aren&apos;t quite good enough.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Handbrake On:</strong> Boring, slow, chip-it-around football. The fans are falling asleep.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">The One-Man Band:</strong> One player accounts for the vast majority of Clearances or Inside 50s.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Traffic Cones:</strong> Opposition teams are just waltzing through. No defensive pressure whatsoever.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">September Teasers:</strong> Flying early, crying late. Peaked way too early in the season.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Battle-Tested Rise:</strong> Form improvement against tough opponents.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Soft Draw Rise:</strong> Form improvement against weaker opponents.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Reality Check Window:</strong> Rising trend but facing a brutal upcoming draw.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Soft Landing:</strong> Falling trend but a much easier upcoming draw offers hope.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Paper Tigers:</strong> Ladder position higher than expected.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Sleeping Giants:</strong> Ladder position lower than expected.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Market Corrected:</strong> Ladder position matches expected performance.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Glass Ceiling:</strong> Expected top 4 finish but form is dropping.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">Wildcard Contender:</strong> Sitting in 7th-10th, battling for a Wildcard Finals spot.</li>
              <li><strong className="text-zinc-900 dark:text-zinc-100">The Great Escape:</strong> Outside the top 10 but surging towards finals contention.</li>
            </ul>
          </div>
        </div>

        <p className="mt-5 text-xs text-zinc-500 dark:text-zinc-500 italic">
          * For teams with 5-9 games, trend is based on overall win rate (&ge;60% Rising, &le;40% Falling). At least 5 games required.
        </p>
      </section>

      {trends.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded text-amber-800">
          No trend data found. Please run the trend calculation script.
        </div>
      )}

      <nav className="mt-12">
        <Link href="/" className="text-blue-600 hover:underline">Back to Home</Link>
      </nav>
    </div>
  );
}
