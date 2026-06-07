"use client";

import { useState } from 'react';
import type { TeamTrend } from './page';

export function TeamList({ trends }: { trends: TeamTrend[] }) {
  const [expandedTeam, setExpandedTeam] = useState<string | null>(null);

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {trends.map((team) => (
        <TeamCard 
          key={team.team} 
          team={team} 
          isExpanded={expandedTeam === team.team}
          onToggle={() => setExpandedTeam(expandedTeam === team.team ? null : team.team)}
        />
      ))}
    </div>
  );
}

function TeamCard({ team, isExpanded, onToggle }: { team: TeamTrend, isExpanded: boolean, onToggle: () => void }) {
  return (
    <div 
      className={`border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-sm hover:shadow-md transition-all bg-white dark:bg-zinc-900 overflow-hidden ${isExpanded ? 'md:col-span-2 lg:col-span-3 ring-2 ring-blue-500/50' : 'cursor-pointer'}`}
      onClick={!isExpanded ? onToggle : undefined}
    >
      {/* QUICK VIEW (Default) */}
      {!isExpanded && (
        <div className="p-4 h-full flex flex-col">
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

          {(team.current_ladder_position || team.expected_ladder_position) && (
            <div className="flex justify-between items-center mb-3 text-sm">
              <span className="text-zinc-500">Ladder Position: <strong className="text-zinc-900 dark:text-zinc-100">{team.current_ladder_position}</strong></span>
              
              {team.expected_ladder_position && (
                <span className="text-zinc-500 flex items-center gap-1">
                  Expected: <strong className="text-zinc-900 dark:text-zinc-100">{team.expected_ladder_position}</strong>
                  {team.current_ladder_position! > team.expected_ladder_position ? (
                    <span className="text-green-500 text-xs" title="Underperforming, expected to rise">▲</span>
                  ) : team.current_ladder_position! < team.expected_ladder_position ? (
                    <span className="text-red-500 text-xs" title="Overperforming, expected to fall">▼</span>
                  ) : (
                    <span className="text-zinc-400 text-xs">—</span>
                  )}
                </span>
              )}
            </div>
          )}

          {/* Narrative Tags */}
          <div className="flex-1">
            {team.narrative_tags && team.narrative_tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {team.narrative_tags.map(tag => (
                  <span key={tag} className="px-2 py-0.5 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded text-[10px] font-medium tracking-wide">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* BROADER VIEW (Expanded details - Dashboard Layout) */}
      {isExpanded && (
        <div className="p-4 bg-zinc-950 text-zinc-200 cursor-default">
          <div className="flex justify-between items-center mb-4">
             <div className="flex items-center gap-4">
                <h2 className="text-2xl font-bold">{team.team}</h2>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  team.trend === 'Rising' ? 'bg-green-900/50 text-green-400 border border-green-800' :
                  team.trend === 'Falling' ? 'bg-red-900/50 text-red-400 border border-red-800' :
                  'bg-zinc-800 text-zinc-300 border border-zinc-700'
                }`}>
                  {team.trend}
                </span>
             </div>
             <button 
               className="text-zinc-500 hover:text-zinc-300 p-1 rounded-full hover:bg-zinc-800 transition-colors"
               onClick={(e) => { e.stopPropagation(); onToggle(); }}
             >
               <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
             </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            
            {/* COLUMN 1: Ladder & Narratives */}
            <div className="flex flex-col gap-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2 font-semibold">Ladder Position</div>
                <div className="flex justify-between items-center bg-zinc-950 p-3 rounded border border-zinc-800/50">
                  <div className="flex flex-col">
                    <span className="text-xs text-zinc-500 font-medium">Current</span>
                    <span className="text-3xl font-bold text-zinc-100">{team.current_ladder_position}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-xs text-zinc-500 font-medium">Expected</span>
                    <div className="flex items-center gap-2">
                      <span className="text-3xl font-bold text-zinc-100">{team.expected_ladder_position}</span>
                      {team.current_ladder_position && team.expected_ladder_position && team.current_ladder_position > team.expected_ladder_position ? (
                        <span className="text-green-500 text-sm">▲</span>
                      ) : team.current_ladder_position && team.expected_ladder_position && team.current_ladder_position < team.expected_ladder_position ? (
                        <span className="text-red-500 text-sm">▼</span>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>

              {team.narrative_tags && team.narrative_tags.length > 0 && (
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex-1">
                  <div className="text-xs text-zinc-500 uppercase tracking-wider mb-3 font-semibold">Narrative Hub</div>
                  <div className="flex flex-wrap gap-2">
                    {team.narrative_tags.map(tag => (
                      <span key={tag} className="px-2.5 py-1 bg-blue-900/20 text-blue-400 rounded border border-blue-800/30 text-xs font-medium tracking-wide">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* COLUMN 2: Metrics */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col">
              <div className="text-xs text-zinc-500 uppercase tracking-wider mb-4 font-semibold">Performance Analysis</div>
              
                <div className="grid grid-cols-2 gap-3 mb-5">
                  <div className="bg-zinc-950 p-3 rounded border border-zinc-800/50 flex flex-col items-center justify-center">
                    <span className="text-xs text-zinc-500 mb-1 font-medium">Win Rate (Last 5)</span>
                    <span className="text-xl font-bold text-zinc-100">{(team.supporting_metrics.recent_win_rate * 100)?.toFixed(0) || '-'}%</span>
                  </div>
                  <div className="bg-zinc-950 p-3 rounded border border-zinc-800/50 flex flex-col items-center justify-center">
                    <span className="text-xs text-zinc-500 mb-1 font-medium">Efficiency (3-Wk)</span>
                    <span className="text-xl font-bold text-zinc-100">{(team.supporting_metrics.rolling_efficiency ?? 0).toFixed(1)}%</span>
                  </div>
                  <div className="bg-zinc-950 p-3 rounded border border-zinc-800/50 flex flex-col items-center justify-center">
                    <span className="text-xs text-zinc-500 mb-1 font-medium">Avg Margin</span>
                    <span className={`text-xl font-bold ${team.supporting_metrics.recent_avg_margin > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {team.supporting_metrics.recent_avg_margin > 0 ? '+' : ''}{team.supporting_metrics.recent_avg_margin?.toFixed(1) || '-'}
                    </span>
                  </div>
                  <div className="bg-zinc-950 p-3 rounded border border-zinc-800/50 flex flex-col items-center justify-center">
                    <span className="text-xs text-zinc-500 mb-1 font-medium">Avg Score</span>
                    <span className="text-xl font-bold text-zinc-100">{team.supporting_metrics.recent_avg_score?.toFixed(1) || '-'}</span>
                  </div>
                </div>
                
                <div className="space-y-3 text-sm mt-auto">
                   {team.supporting_metrics.strength_of_schedule !== undefined && (
                      <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                        <span className="text-zinc-400">Opponent SoS</span>
                        <span className="font-mono bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800/50">{(team.supporting_metrics.strength_of_schedule * 100)?.toFixed(0) || '-'}%</span>
                      </div>
                    )}
                    {team.supporting_metrics.weighted_margin_trend !== undefined && (
                      <div className="flex justify-between items-center border-b border-zinc-800 pb-2">
                        <span className="text-zinc-400">SoS-Weighted Margin Trend</span>
                        <span className={`font-mono px-2 py-0.5 rounded border border-zinc-800/50 ${team.supporting_metrics.weighted_margin_trend > 0 ? 'text-green-400 bg-green-950/20' : 'text-red-400 bg-red-950/20'}`}>
                          {team.supporting_metrics.weighted_margin_trend > 0 ? '+' : ''}{team.supporting_metrics.weighted_margin_trend?.toFixed(1) || '-'}
                        </span>
                      </div>
                    )}
                    {team.supporting_metrics.finishing_power !== undefined && (
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-400">Finishing Power (Q4)</span>
                        <span className={`font-mono px-2 py-0.5 rounded border border-zinc-800/50 ${team.supporting_metrics.finishing_power > 0 ? 'text-green-400 bg-green-950/20' : 'text-red-400 bg-red-950/20'}`}>
                          {team.supporting_metrics.finishing_power > 0 ? '+' : ''}{team.supporting_metrics.finishing_power?.toFixed(1) || '-'}
                        </span>
                      </div>
                    )}
                </div>

            </div>

            {/* COLUMN 3: Future & Story */}
            <div className="flex flex-col gap-4">
              {team.supporting_metrics.next_3_sos !== undefined && (
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                   <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2 font-semibold">The Next 3 Weeks</div>
                   <div className="bg-zinc-950 p-3 rounded border border-zinc-800/50">
                     <div className="flex justify-between items-center mb-2">
                       <span className="text-sm text-zinc-400">Upcoming SoS</span>
                       <span className={`font-bold px-2 py-0.5 rounded border ${team.supporting_metrics.next_3_sos > 0.55 ? 'text-red-400 border-red-900 bg-red-950/30' : team.supporting_metrics.next_3_sos < 0.45 ? 'text-green-400 border-green-900 bg-green-950/30' : 'text-zinc-300 border-zinc-700 bg-zinc-800'}`}>
                         {(team.supporting_metrics.next_3_sos * 100).toFixed(0)}%
                       </span>
                     </div>
                     {team.narrative_tags?.includes("Reality Check Window") && (
                        <div className="mt-3 text-xs font-bold text-red-400 flex items-center gap-1.5 bg-red-950/30 border border-red-900/50 p-2 rounded">
                          <span className="text-base">⚠️</span> Reality Check Window
                        </div>
                      )}
                      {team.narrative_tags?.includes("Soft Landing") && (
                        <div className="mt-3 text-xs font-bold text-green-400 flex items-center gap-1.5 bg-green-950/30 border border-green-900/50 p-2 rounded">
                          <span className="text-base">🪂</span> Soft Landing
                        </div>
                      )}
                   </div>
                </div>
              )}

              {team.key_players && team.key_players.length > 0 && (
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex-1 flex flex-col">
                  <div className="text-xs text-zinc-500 uppercase tracking-wider mb-3 font-semibold">Player Stories</div>
                  <div className="space-y-2 flex-1">
                    {team.key_players.map((kp, idx) => (
                      <div key={idx} className="bg-zinc-950 p-3 rounded border border-zinc-800/50 text-xs">
                        <div className="font-bold mb-1.5 flex items-center gap-1.5 text-[11px] uppercase tracking-wide">
                          {kp.role === 'Engine Room' && <><span className="text-base">🚂</span> <span className="text-green-400">The Engine Room</span></>}
                          {kp.role === 'Missing Link' && <><span className="text-base">👻</span> <span className="text-red-400">The Missing Link</span></>}
                          {kp.role === 'One-Man Band' && <><span className="text-base">🎸</span> <span className="text-amber-400">The One-Man Band</span></>}
                        </div>
                        <p className="text-zinc-400 leading-relaxed">
                          <strong className="text-zinc-200">{kp.playerName}</strong> {kp.narrativeBlurb}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
