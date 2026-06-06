# AFL Narrative Engine - Calculations & Metrics Reference

This document catalogs and explains all data calculations, formulas, proxies, and narrative trigger logic used for generating the teams and players analytics, trends, and stories in the AFL Narrative Engine.

---

## Team Calculations & Trends

Team metrics are computed in `scripts/calculate_team_trends.py` by analyzing historical match data and future fixtures.

### 1. Basic Team Metrics
*   **Team Match Filtering:** Matches are dynamically classified as completed or future based on the `complete` status in raw fixture files or existence of scores in match data.
*   **Current Season Points ($PTS_{curr}$):** 
    $$PTS_{curr} = (Wins \times 4) + (Draws \times 2)$$
    Calculated exclusively for the 2026 season matches.
*   **Current Season Percentage ($PCT_{curr}$):**
    $$PCT_{curr} = \left( \frac{\text{Total Points For}}{\text{Total Points Against}} \right) \times 100$$

### 2. Form & Trend Calculations
*   **Recent Window vs. Previous Window:**
    *   **Recent Window (Last 5 Games):** Average win rate ($WR_{rec}$), average margin ($M_{rec}$), average score ($S_{rec}$).
    *   **Previous Window (Games -10 to -5):** Average win rate ($WR_{prev}$), average margin ($M_{prev}$).
*   **Strength of Schedule (SoS):**
    *   Each opponent's strength is calculated as their overall season win rate.
    *   **Recent SoS ($SoS_{rec}$):** Average win rate of the opponents in the last 5 games.
    *   **Recent SoS Multiplier ($SoS_{mult}$):**
        $$SoS_{mult} = \frac{SoS_{rec}}{0.5} \quad \text{if } SoS_{rec} > 0 \text{ else } 1.0$$
*   **Weighted Margin Difference ($\Delta M_{weighted}$):**
    Adjusts the margin movement based on the difficulty of the opponents faced in each window.
    $$\Delta M_{weighted} = (M_{rec} \times SoS_{mult, rec}) - (M_{prev} \times SoS_{mult, prev})$$
*   **Trend Direction determination:**
    *   **Rising:** $\Delta WR \ge 0.20$ OR $\Delta M_{weighted} \ge 15$.
    *   **Falling:** $\Delta WR \le -0.20$ OR $\Delta M_{weighted} \le -15$.
    *   **Stable:** Anything in between.
    *(Fallback for teams with 5–9 games: Rising if $WR_{rec} \ge 0.6$, Falling if $WR_{rec} \le 0.4$, else Stable).*

### 3. Predictive & Advanced Team Metrics
*   **Quarter Powers:** Computes performance across quarters in the recent window (last 5 games). Quarter score detail arrays represent `[goals, behinds]` per team.
    *   $Q1\_Margin = \text{Team Q1 Score} - \text{Opponent Q1 Score}$
    *   $Q2\_Margin = \text{Team Q2 Change} - \text{Opponent Q2 Change}$
    *   $Q3\_Margin = \text{Team Q3 Change} - \text{Opponent Q3 Change}$
    *   $Q4\_Margin = \text{Team Q4 Change} - \text{Opponent Q4 Change}$ (Finishing Power)
*   **Rolling Efficiency:** Point ratio over the last 3 matches:
    $$Rolling\_Efficiency = \left( \frac{\sum_{\text{last 3}} Score_{\text{team}}}{\sum_{\text{last 3}} Score_{\text{opponent}}} \right) \times 100$$
*   **Form Modifier ($FM$):** Combine rolling efficiency, recent win rate, and strength of schedule difficulty:
    $$FM = \left(\frac{Rolling\_Efficiency}{100.0} \times 0.5\right) + \left(\frac{WR_{rec}}{0.5} \times 0.3\right) + (SoS_{mult} \times 0.2)$$
*   **Expected Points ($xPts$) & Expected Percentage ($xPct$):**
    $$xPts = PTS_{curr} \times FM$$
    $$xPct = PCT_{curr} \times FM$$
*   **Ladder Standings:**
    *   **Current Ladder Position (CLP):** Ranked by $PTS_{curr}$ descending, then $PCT_{curr}$ descending.
    *   **Expected Ladder Position (ELP):** Ranked by $xPts$ descending, then $xPct$ descending.
*   **Next 3 Weeks SoS ($SoS_{next3}$):** Average win rate of upcoming 3 opponents in the fixture.

### 4. Team Narrative Tag Triggers
*   **"Flat-Track Bullies":** $WR_{rec} > 0.6$ AND $SoS_{rec} < 0.4$.
*   **"The Cardiac Kids":** $Q4\_Margin > 10$ AND $|M_{rec}| < 12$.
*   **"Premiership Quarter Specialists":** $Q3\_Margin > 15$ AND $Q3\_Margin > (Q1\_Margin + 10)$ AND $Q3\_Margin > (Q4\_Margin + 10)$.
*   **"Honourable Losses":** $WR_{rec} < 0.3$ AND $-15 < M_{rec} < 0$.
*   **"September Teasers":** Games analyzed $\ge 15$ AND $WR_{rec} \le 0.2$ AND consecutive losses $\ge 3$ (proxied/associated with season win rate dropping).
*   **"Battle-Tested Rise":** Trend is **Rising** AND $SoS_{rec} > 0.55$.
*   **"Soft Draw Rise":** Trend is **Rising** AND $SoS_{rec} < 0.45$.
*   **"Reality Check Window":** Trend is **Rising** AND $SoS_{next3} > 0.55$.
*   **"Soft Landing":** Trend is **Falling** AND $SoS_{next3} < 0.45$.
*   **"Sinking Ship":** Trend is **Falling** AND Consecutive Losses $\ge 3$.
*   **"The Ultimate Tease":** $CLP > ELP$ AND $(CLP - ELP) \ge 3$ AND $Q4\_Margin < -10$.
*   **"Paper Tigers":** $CLP \le 4$ AND $ELP \ge CLP + 4$.
*   **"Sleeping Giants":** $CLP \ge 8$ AND $ELP \le CLP - 4$.
*   **"Market Corrected":** $|CLP - ELP| \le 1$.
*   **"Glass Ceiling":** $ELP \le 4$ AND Trend is **Falling**.
*   **"The Great Escape":** $CLP \ge 11$ AND $ELP \le 10$ AND Trend is **Rising**.
*   **"Wildcard Contender":** $7 \le CLP \le 10$.

---

## Player Calculations & Player Impact Rating (PIR)

Player metrics are computed in `scripts/calculate_player_trends.py` based on 2026 player match logs.

### 1. Stat Definitions & Proxies
*   **Metres Gained (Proxy):**
    $$Metres\_Gained = Kicks \times 25 + Handballs \times 5$$

### 2. Player Role Assignment
To prevent generalist scaling bias, players with $\ge 3$ games are classified into 1 of 7 roles based on their season averages:
1.  **Ruck:** Hit Outs (HO) $\ge 10.0$ per game.
2.  **Rebounding Defender:** Rebound 50s (RB) $\ge 3.0$ per game.
3.  **Key Forward:** Marks Inside 50 (MI) $\ge 1.5$ OR (Goals (GL) $\ge 1.5$ AND Marks (MK) $\ge 4.0$).
4.  **Inside Midfielder:** Clearances (CL) $\ge 3.5$ OR Contested Possessions (CP) $\ge 9.0$.
5.  **Key Defender:** One Percenters (1% - Spoils) $\ge 4.5$ AND Marks (MK) $\ge 3.0$.
6.  **Small/General Forward:** Goals (GL) $\ge 0.8$ per game.
7.  **Outside/Winger (Default):** Falls into none of the above.

### 3. Player Impact Rating (PIR) Formula
Each role has a unique scoring matrix, which is normalized to a 10–100 scale. Below are the formulas for raw score calculation before normalization:

*   **Inside Midfielder:**
    $Score = (CP \times 3.0) + (CL \times 4.0) + (TK \times 2.0) + (GA \times 4.0) + (I50 \times 1.5) - (CG \times 2.0) - (FA \times 1.5)$
    $PIR = \max\left(10, \frac{Score}{110} \times 100\right)$
*   **Outside/Winger:**
    $Score = (Metres\_Gained \times 0.1) + (I50 \times 3.0) + (UP \times 1.5) + (MK \times 2.0) + (GA \times 4.0) - (CG \times 2.0)$
    $PIR = \max\left(10, \frac{Score}{115} \times 100\right)$
*   **Key Forward:**
    $Score = (MI \times 8.0) + (GL \times 12.0) + (BH \times 4.0) + (CM \times 6.0) + (CP \times 1.5) - (CG \times 2.0)$
    $PIR = \max\left(10, \frac{Score}{105} \times 100\right)$
*   **Small/General Forward:**
    $Score = (GL \times 15.0) + (BH \times 5.0) + (GA \times 6.0) + (TK \times 3.0) + (I50 \times 2.0) + (CP \times 1.5) - (CG \times 1.5)$
    $PIR = \max\left(10, \frac{Score}{90} \times 100\right)$
*   **Key Defender:**
    $Score = (Spoils \times 5.0) + (MK \times 3.0) + (CM \times 6.0) + (CP \times 2.0) - (CG \times 2.0)$
    $PIR = \max\left(10, \frac{Score}{85} \times 100\right)$
*   **Rebounding Defender:**
    $Score = (RB \times 6.0) + (Metres\_Gained \times 0.12) + (UP \times 1.5) + (MK \times 2.5) - (CG \times 2.5)$
    $PIR = \max\left(10, \frac{Score}{170} \times 100\right)$
*   **Ruck:**
    $Score = (HO \times 1.2) + (CL \times 3.0) + (CP \times 2.5) + (TK \times 2.0) + (CM \times 5.0) - (CG \times 2.0)$
    $PIR = \max\left(10, \frac{Score}{120} \times 100\right)$
*   **Fallback Default:**
    $Score = (CP \times 2.0) + (UP \times 1.0) + (TK \times 1.5) + (GL \times 5.0) - (CG \times 1.5)$
    $PIR = \max\left(10, \frac{Score}{75} \times 100\right)$

### 4. Player Trend Calculations
*   **Recent Window:** Average PIR of the last 3 games ($PIR_{rec\_avg}$).
*   **Previous Window:** Average PIR of games -6 to -3 ($PIR_{prev\_avg}$).
*   **PIR Delta ($\Delta PIR$):**
    $$\Delta PIR = \frac{PIR_{rec\_avg} - PIR_{prev\_avg}}{PIR_{prev\_avg}}$$
*   **Trend Assignment:**
    *   **Rising:** $\Delta PIR \ge 0.20$
    *   **Falling:** $\Delta PIR \le -0.20$
    *   **Stable:** Anything in between.

### 5. Player Narrative Tag Triggers
*   **"The Leather Poisoner":** Disposals (DI) $\ge 26.0$ AND $Metres\_Gained < 300.0$ AND Goal Assists (GA) $< 0.5$.
*   **"Pure Grit":** $\left(\frac{CP}{DI}\right) \ge 0.55$ AND Clearances (CL) $\ge 4.5$ AND Tackles (TK) $\ge 5.0$.
*   **"The Kick-To-Self Merchant":** $\left(\frac{UP}{DI}\right) \ge 0.75$ AND $CP < 4.0$.
*   **"The Almost Man":** $(GL + BH) \ge 2.5$ AND $\left(\frac{GL}{GL + BH}\right) < 0.40$.
*   **"The Decoy":** Assigned role is **Key Forward** AND Goals (GL) $\le 0.8$ AND Goal Assists (GA) $\ge 0.8$.
*   **"The Heatwave":** Assigned role is **Small/General Forward** AND Tackles (TK) $\ge 4.0$.
*   **"The Double Agent":** Clangers (CG) $\ge 4.5$ OR Free Kicks Against (FA) $\ge 2.0$.
*   **"The Traffic Warden":** Assigned role is **Key Defender** AND Marks (MK) $\ge 5.0$ AND One Percenters (1%) $\ge 6.0$.
*   **"The Unsung Hero":** Disposals (DI) $< 16.0$ AND Contested Possessions (CP) $\ge 8.0$ AND Tackles (TK) $\ge 4.0$.
*   **"The Breakout Watch":** Trend is **Rising** AND Total Career Games (2023-2026 proxy) $\le 40$.
*   **"The Cliff-Edge":** Trend is **Falling** AND Total Career Games (2023-2026 proxy) $\ge 50$.

---

## Team & Player Correlations

Team and player correlations are calculated in `scripts/calculate_team_trends.py` to identify player dependencies.

*   **The Engine Room:** When a team is **Rising**, the script extracts candidates who have high Contested Possessions (CP) in the last 5 weeks and checks their growth against the previous 5 weeks. If a player shows a significant positive delta ($\ge 5\%$), they are designated as the team's engine room.
*   **The Missing Link:** When a team is **Falling**, the script reviews top clearance (CL) players in the previous 5 weeks and checks if their clearance numbers plummet in the recent 5 weeks. If a player has a negative clearance delta ($\le -5\%$), they are tagged as the missing link.
*   **The One-Man Band:** If a single player is responsible for $> 35\%$ of a team's total clearances over the last 5 weeks, they are designated as carrying a "One-Man Band" burden.
