import fs from 'fs';
import path from 'path';
import Link from 'next/link';

export interface PlayerTrend {
  name: string;
  team: string;
  role: string;
  games_played: number;
  pir: number;
  recent_pir: number;
  pir_trend: number;
  trend: 'Rising' | 'Stable' | 'Falling';
  narrative_tags: string[];
  stats: {
    disposals: number;
    kicks: number;
    handballs: number;
    marks: number;
    goals: number;
    behinds: number;
    tackles: number;
    clearances: number;
    contested_possessions: number;
    uncontested_possessions: number;
    clangers: number;
    goal_assists: number;
    spoils: number;
    hitouts: number;
  };
  highlight: string;
}

async function getPlayerTrends(): Promise<PlayerTrend[]> {
  const filePath = path.join(process.cwd(), 'data', 'metrics', 'player_trends.json');
  if (!fs.existsSync(filePath)) {
    return [];
  }
  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents);
}

export default async function PlayersPage() {
  const allPlayers = await getPlayerTrends();
  
  // Show top 50 players by default to keep load times/rendering fast and clean
  const players = allPlayers.slice(0, 60);

  // Determine round from fixtures (max round completed)
  const getRound = () => {
    const fixturePath = path.join(process.cwd(), 'data', 'raw', 'fixture_2026.json');
    if (!fs.existsSync(fixturePath)) return 0;
    const fixtures = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
    const completed = fixtures.filter((f: any) => f.complete === 100);
    return completed.length > 0 ? Math.max(...completed.map((f: any) => f.round)) : 0;
  };
  
  const currentRound = getRound();

  return (
    <div className="p-8 font-sans max-w-5xl mx-auto">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold mb-2">Player Ratings & Trends</h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            2026 Season Analysis • Round {currentRound}
          </p>
        </div>
      </header>


      {/* Overview stats cards */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <div className="p-4 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl">
          <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Total Players Analyzed</span>
          <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">{allPlayers.length}</p>
        </div>
        <div className="p-4 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl">
          <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Rising Players</span>
          <p className="text-2xl font-bold text-green-600">{allPlayers.filter(p => p.trend === 'Rising').length}</p>
        </div>
        <div className="p-4 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl">
          <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Under-the-Radar Heroes</span>
          <p className="text-2xl font-bold text-purple-600">
            {allPlayers.filter(p => p.narrative_tags.includes('The Unsung Hero')).length}
          </p>
        </div>
      </div>

      {/* Players grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {players.map((player) => {
          let trendColor = "text-zinc-500";
          let trendBadge = "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300";
          if (player.trend === 'Rising') {
            trendColor = "text-green-600";
            trendBadge = "bg-green-100 dark:bg-green-950/50 text-green-700 dark:text-green-400";
          } else if (player.trend === 'Falling') {
            trendColor = "text-blue-600";
            trendBadge = "bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400";
          }

          return (
            <div key={`${player.name}-${player.team}`} className="p-6 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">{player.name}</h3>
                    <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
                      {player.team} &bull; {player.role}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-black text-blue-600 dark:text-blue-400" title="Player Impact Rating (Season Average)">
                      {player.pir}
                    </span>
                    <div className="text-[10px] text-zinc-400 font-semibold">PIR</div>
                  </div>
                </div>

                {/* PIR Breakdown tooltip/info */}
                <div className="text-[10px] text-zinc-400 font-semibold mb-3">
                  <span className="cursor-help" title={`Based on ${player.role} performance metrics`}>PIR Breakdown (Active)</span>
                </div>

                {/* Highlight text */}
                <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-50 dark:bg-zinc-900/50 p-2.5 rounded-lg border border-zinc-100 dark:border-zinc-800/50 mb-3">
                  🔥 {player.highlight}
                </p>

                {/* Narrative Tags list */}
                {player.narrative_tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {player.narrative_tags.map(tag => (
                      <span key={tag} className="px-2 py-1 text-xs font-bold rounded bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-400 border border-amber-100 dark:border-amber-900/40">
                        🏷️ {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Stats overview footer inside card */}
              <div className="pt-4 border-t border-zinc-100 dark:border-zinc-900">
                <div className="text-xs text-zinc-500 mb-2 font-semibold">Primary Drivers for {player.role} PIR</div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {player.role === 'Inside Midfielder' && (
                    <>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.contested_possessions}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CP</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.clearances}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CL</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.tackles}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">TK</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.goal_assists}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">GA</div></div>
                    </>
                  )}
                  {player.role === 'Key Forward' && (
                    <>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.marks}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">MK</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.goals}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">GL</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.behinds}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">BH</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.contested_possessions}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CP</div></div>
                    </>
                  )}
                  {player.role === 'Key Defender' && (
                    <>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.spoils}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">1%</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.marks}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">MK</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.contested_possessions}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CP</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.clangers}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CG</div></div>
                    </>
                  )}
                  {player.role === 'Rebounding Defender' && (
                    <>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.disposals}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">DIS</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.marks}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">MK</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.uncontested_possessions}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">UP</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.clangers}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CG</div></div>
                    </>
                  )}
                  {!['Inside Midfielder', 'Key Forward', 'Key Defender', 'Rebounding Defender'].includes(player.role) && (
                    <>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.disposals}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">DIS</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.goals}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">GL</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.tackles}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">TK</div></div>
                      <div><div className="font-semibold text-zinc-900 dark:text-zinc-100">{player.stats.clangers}</div><div className="text-[10px] text-zinc-400 font-bold uppercase">CG</div></div>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Informational guide */}
      <section className="mt-12 p-6 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm text-zinc-700 dark:text-zinc-300">
        <h2 className="font-bold text-zinc-900 dark:text-zinc-100 mb-4 text-base">Player Insights Guide</h2>
        <p className="mb-4 text-zinc-600 dark:text-zinc-400">
          Our <strong>Player Impact Rating (PIR)</strong> weights actions based on role, providing a season-long average metric of influence. We also analyze a rolling 3-game window to identify rising stars and falling veterans, with shifts marked as <em>Rising</em> or <em>Falling</em> when performance swings &ge;20% compared to the prior 3-week period.
        </p>

        <p className="mb-4">
          Rather than valuing high-volume cheap touches (like standard Fantasy stats), PIR weights actions based on role:
        </p>

        <ul className="space-y-4 text-xs">
          <li>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1">Inside Midfielders</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Heavily weighted on Contested Possessions, Clearances, Tackles, and Goal Assists. penalized for clangers.</span>
          </li>
          <li>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1">Key Forwards</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Heavily weighted on Marks Inside 50, Goals, Behinds, and Contested Marks.</span>
          </li>
          <li>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1">Key Defenders</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Heavily weighted on Spoils (One-Percenters), Intercept Marks, and Contested Marks.</span>
          </li>
          <li>
            <strong className="text-zinc-900 dark:text-zinc-100 block mb-1">Rebounding Defenders</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Heavily weighted on Rebound 50s, Metres Gained, and Uncontested Marks.</span>
          </li>
        </ul>

        <h3 className="font-bold text-zinc-900 dark:text-zinc-100 mt-6 mb-3 text-sm">Narrative Tag Rules</h3>
        <ul className="grid gap-4 md:grid-cols-2 text-xs">
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Leather Poisoner</strong>
            <span className="text-zinc-600 dark:text-zinc-400">High-volume accumulator who gets heaps of the ball but doesn&apos;t damage the opposition (averages &ge;26 disposals, &lt;300m metres gained, &lt;0.5 goal assists).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ Pure Grit</strong>
            <span className="text-zinc-600 dark:text-zinc-400">A blue-collar player doing the hard, dirty work in the trenches (&ge;55% contested possession rate, &ge;4.5 clearances, &ge;5.0 tackles).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Kick-To-Self Merchant</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Pumps up stats with uncontested, low-impact play (&ge;75% uncontested possession rate and &lt;4.0 contested possessions).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Almost Man</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Highly dangerous forward generating scoring shots but missing targets (&ge;2.5 shots per game with &lt;40% conversion rate).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Decoy</strong>
            <span className="text-zinc-600 dark:text-zinc-400">A key forward pulling defenders away and setting up goals for teammates (&le;0.8 goals per game and &ge;0.8 goal assists).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Heatwave</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Pressure forward trapping the ball inside 50 with intense defensive efforts (averages &ge;4.0 tackles as a small/general forward).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Double Agent</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Highly active but turns the ball over or concedes critical penalties constantly (&ge;4.5 clangers per game).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Traffic Warden</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Key defender completely commanding the air and spoiling everything (&ge;5.0 marks and &ge;6.0 spoils per game).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Unsung Hero</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Low disposal count but massive physical impact on the contest (&lt;16.0 disposals, &ge;8.0 contested possessions, and &ge;4.0 tackles).</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Breakout Watch</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Younger/fewer-game players whose PIR ratings spike significantly (&ge;20% increase) in a 3-week window.</span>
          </li>
          <li className="p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <strong className="text-amber-800 dark:text-amber-400 block mb-1">🏷️ The Cliff-Edge</strong>
            <span className="text-zinc-600 dark:text-zinc-400">Veteran players whose physical output/PIR drops off sharply (&le;-20% decrease) over a 4-week window.</span>
          </li>
        </ul>
      </section>

      <nav className="mt-12">
        <Link href="/" className="text-blue-600 hover:underline">Back to Home</Link>
      </nav>
    </div>
  );
}
