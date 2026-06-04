export type PlayerFormImpact = {
  playerId: string;
  playerName: string;
  baselineScore: number;
  windowScore: number;
  delta: number;
  role: 'Engine Room' | 'Missing Link' | 'One-Man Band' | 'None';
  narrativeBlurb: string;
  statType: 'Clearances' | 'Contested Possessions' | 'Inside 50s' | 'Score Involvements' | 'General';
};

export type TeamStatsContext = {
  // General Win/Loss
  winRate: number; // 0.0 to 1.0
  winRateLast5: number; // 0.0 to 1.0
  consecutiveLosses: number;
  averageMargin: number; // Absolute average margin
  averageLosingMargin: number; // Average margin in losses
  strengthOfSchedule: number; // 0.0 to 1.0
  expectedLadderPositionDiff: number; // e.g., Actual Ladder - Expected Ladder (negative means underperforming)
  recentTrend: 'rising' | 'falling' | 'stable';
  roundNumber: number;

  // Player Impact (Player-Team Trend Correlation)
  topPlayerDelta?: number; // E.g., > 0.20 for 20% spike
  worstPlayerDelta?: number; // E.g., < -0.20 for 20% drop
  maxPlayerStatShare?: number; // E.g. 0.36 for 36% of team's clearances
  keyPlayers?: PlayerFormImpact[];

  // Scoring & Quarters
  averageScore: number;
  q1Differential: number;
  q2Differential: number;
  q3Differential: number;
  q4Differential: number;

  // Gameplay & Pressure
  uncontestedPossessionDiff: number; // Positive means they get more uncontested possession
  contestedPossessionDropoff: number; // Drop off in contested ball during losses compared to wins
  uncontestedMarks: number;
  inside50s: number;
  tacklesInside50: number;

  // Opposition
  oppInside50s: number;
  oppScoringEfficiency: number; // Percentage of Inside 50s resulting in a score (0.0 to 1.0)
};

export type NarrativeTag = {
  id: string;
  label: string;
  description: string;
  type: 'positive' | 'negative' | 'neutral';
  condition: (stats: TeamStatsContext) => boolean;
};

export const TEAM_NARRATIVE_TAGS: NarrativeTag[] = [
  {
    id: 'flat-track-bullies',
    label: 'Flat-Track Bullies',
    description: "Crushing the minnows, but haven't beaten anyone good.",
    type: 'negative',
    condition: (stats) => stats.winRate > 0.6 && stats.strengthOfSchedule < 0.4,
  },
  {
    id: 'cardiac-kids',
    label: 'The Cardiac Kids',
    description: 'Every game goes down to the wire. Better check your blood pressure.',
    type: 'neutral',
    condition: (stats) => stats.q4Differential > 10 && stats.averageMargin < 12,
  },
  {
    id: 'sinking-ship',
    label: 'Sinking Ship',
    description: 'Falling trend combined with high late-game fatigue and mounting losses.',
    type: 'negative',
    condition: (stats) => stats.recentTrend === 'falling' && stats.consecutiveLosses >= 3,
  },
  {
    id: 'ultimate-tease',
    label: 'The Ultimate Tease',
    description: 'The stats say they should be top 4. The ladder says otherwise due to late fade-outs.',
    type: 'negative',
    condition: (stats) => stats.expectedLadderPositionDiff <= -3 && stats.q4Differential < -10,
  },
  {
    id: 'downhill-skiers',
    label: 'Downhill Skiers',
    description: 'Look like superstars when the game is on their terms, but go missing when the heat is on.',
    type: 'negative',
    condition: (stats) => stats.uncontestedPossessionDiff > 20 && stats.contestedPossessionDropoff > 15,
  },
  {
    id: 'premiership-quarter-specialists',
    label: 'Premiership Quarter Specialists',
    description: 'Always come out breathing fire in the 3rd quarter.',
    type: 'positive',
    condition: (stats) => 
      stats.q3Differential > 15 && 
      stats.q3Differential > stats.q1Differential + 10 &&
      stats.q3Differential > stats.q4Differential + 10,
  },
  {
    id: 'honourable-losses',
    label: 'Honourable Losses',
    description: 'The ultimate backhanded compliment. They try hard, but just aren\'t quite good enough.',
    type: 'neutral',
    condition: (stats) => stats.winRateLast5 < 0.3 && stats.averageLosingMargin > 0 && stats.averageLosingMargin < 15,
  },
  {
    id: 'handbrake-on',
    label: 'Handbrake On',
    description: 'Boring, slow, chip-it-around football. The fans are falling asleep.',
    type: 'negative',
    condition: (stats) => stats.uncontestedMarks > 100 && stats.inside50s < 45 && stats.averageScore < 75,
  },
  {
    id: 'traffic-cones',
    label: 'Traffic Cones',
    description: 'Opposition teams are just waltzing through. No defensive pressure whatsoever.',
    type: 'negative',
    condition: (stats) => stats.tacklesInside50 < 8 && stats.oppInside50s > 55 && stats.oppScoringEfficiency > 0.5,
  },
  {
    id: 'september-teasers',
    label: 'September Teasers',
    description: 'Flying early, crying late. Peaked way too early in the season.',
    type: 'negative',
    condition: (stats) => stats.roundNumber >= 15 && stats.winRate > 0.5 && stats.consecutiveLosses >= 3,
  },
  {
    id: 'one-man-band',
    label: 'The One-Man Band',
    description: 'A single player is carrying the entire load for clearances or inside 50s.',
    type: 'neutral',
    condition: (stats) => (stats.maxPlayerStatShare ?? 0) > 0.35,
  },
  {
    id: 'engine-room',
    label: 'The Engine Room',
    description: 'Team is surging, driven by a massive individual form spike.',
    type: 'positive',
    condition: (stats) => stats.recentTrend === 'rising' && (stats.topPlayerDelta ?? 0) > 0.20,
  },
  {
    id: 'missing-link',
    label: 'The Missing Link',
    description: 'Team form is plummeting, perfectly correlating with a key player dropping off a cliff.',
    type: 'negative',
    condition: (stats) => stats.recentTrend === 'falling' && (stats.worstPlayerDelta ?? 0) < -0.20,
  }
];

/**
 * Evaluates a team's statistical context against all narrative tag rules 
 * and returns the tags that match.
 */
export function getTagsForTeam(stats: TeamStatsContext): NarrativeTag[] {
  return TEAM_NARRATIVE_TAGS.filter((tag) => tag.condition(stats));
}
