

## 1. Team Metrics & Trend Enhancements

### Guarding Against Small Sample Sizes (Early Season)

* **The Problem:** In Rounds 1 to 5, your "Previous Window (Games -10 to -5)" doesn't exist, and your 5-game fallback kicks in. However, even at Round 2 or 3, a single massive win or loss will wildly distort $Rolling\_Efficiency$ and $FM$ (Form Modifier).
* **The Fix:** Implement an **anchor weight** for the first 5 rounds. Blend the current season's early data with the previous season's final ladder/points status, decaying the historical weight by 20% each week until Round 6, where the current season completely takes over.

### Fix the Form Modifier ($FM$) Scale Mismatch

* **The Problem:** Look at your formula:

$$FM = \left(\frac{Rolling\_Efficiency}{100.0} \times 0.5\right) + \left(\frac{WR_{rec}}{0.5} \times 0.3\right) + (SoS_{mult} \times 0.2)$$



If a team has a 100% win rate ($WR_{rec} = 1.0$), that middle term becomes $\frac{1.0}{0.5} \times 0.3 = 0.6$. If their rolling efficiency is 150% (scoring 300 points, conceding 200), the first term is $1.5 \times 0.5 = 0.75$. Your $FM$ will regularly exceed $1.5$, compounding exponentially when multiplied by current points to get $xPts$. A team on 40 points could suddenly have an $xPts$ of 65 midway through the year.
* **The Fix:** Center $FM$ strictly around a baseline of `1.0`. Normalise the components so a perfectly average team equals 1.0, and elite teams cap out around 1.25.

$$FM = 1.0 + \left( \left(\frac{Rolling\_Efficiency - 100}{100}\right) \times 0.4 \right) + ((WR_{rec} - 0.5) \times 0.4) + ((SoS_{rec} - 0.5) \times 0.2)$$



### Dynamic Narrative Triggers

* **"The Cardiac Kids":** Your current trigger requires $|M_{rec}| < 12$ (average margin under 2 goals) AND a final quarter margin $> 10$. If a team gets blown out for three quarters and kicks 5 late goals to lose by 10, they aren't "Cardiac Kids"—they just junk-timed a loss. Change this trigger to: `Wins in last 5 matches >= 3` AND `Count(Matches won where Q3_Margin < 0 and Q4_Margin > 0) >= 2`.
* **"Flat-Track Bullies":** Add an explicit check against elite teams to make this robust: `WR vs Top 8 Teams <= 0.20` AND `WR vs Bottom 10 Teams >= 0.80`.

---

## 2. Player Metrics & PIR Enhancements

### The "Metres Gained" Proxy Flaw

* **The Problem:** Your proxy formula is:

$$Metres\_Gained = Kicks \times 25 + Handballs \times 5$$



While clean, this heavily penalizes high-yardage outside runners (who average 35+ metres per kick) and over-rewards players who execute short, sideways chips across half-back.
* **The Fix:** Incorporate **Rebound 50s (RB)** and **Inside 50s (I50)** as functional multipliers for territory depth. They act as concrete proof that a disposal actually moved the ball into a new zone:

$$Metres\_Gained\_Proxy = (Kicks \times 22) + (Handballs \times 4) + (I50 \times 30) + (RB \times 35)$$



### Strict Hierarchy for Role Assignment

* **The Problem:** Players will easily bleed across multiple roles, causing volatile weekly swings. For example, a modern dynamic midfielder like Marcus Bontempelli could simultaneously trigger **Inside Midfielder** (Clearances $\ge 3.5$) and **Key Forward** (Goals $\ge 1.5$, Marks $\ge 4.0$).
* **The Fix:** Execute role allocation using a strict **if-else exclusive hierarchy queue**. Run the highly specific roles first, and default down to the general ones:
1. **Ruck** (First check)
2. **Key Defender**
3. **Key Forward**
4. **Inside Midfielder**
5. **Rebounding Defender**
6. **Small/General Forward**
7. **Outside/Winger** (Fallback)



### Volume Protection for PIR Normalization

* **The Problem:** Your PIR raw denominators (e.g., dividing Inside Midfielder raw score by 110) assume a high-volume performance. If a player subbed on late in the game gets 3 clearances, 4 tackles, and 4 contested possessions, their raw score will be mathematically decent, but their low total volume shouldn't equate to a 75 PIR match.
* **The Fix:** Scale the raw score by a **Time on Ground (TOG%)** factor, or if the Fryzigg feed doesn't reliably extract TOG%, apply a progressive penalization multiplier if total Disposals are below a baseline floor for that specific role (e.g., if $DI < 12$ for a Midfielder, multiply PIR by $\frac{DI}{12}$).

### Veteran Status & "The Cliff-Edge" Validation

* **The Problem:** The "Cliff-Edge" narrative tag is intended for veteran players whose output is declining sharply as they approach retirement. However, the existing logic only looks at a falling trend in the current season, causing it to trigger for young players (e.g., 1st or 2nd year players) who might just be experiencing a "sophomore slump" or standard form fluctuation.
* **The Fix:** Introduce a **Career Games Proxy**. By aggregating games played ($GM$) from the 2023, 2024, and 2025 historical data files and adding current 2026 games, we establish a total games count. 
    * **"The Cliff-Edge":** Only trigger if `Total Career Games >= 50`.
    * **"The Breakout Watch":** Conversely, shift this tag to use the same proxy, triggering only if `Total Career Games <= 40`.

---

## 3. Team & Player Correlations (The Narrative Logic)

Your correlation concepts ("Engine Room", "Missing Link") are great storytelling hooks. To ensure your scripts don't output blanks or throw errors, tighten the logic parameters:

### "The One-Man Band" Safety Valve

* **The Enhancement:** If a team has a single player clearing $> 35\%$ of the ball, but the team's total clearance differential is dead last in the league, he isn't a "One-Man Band" driving a system—he's just surviving in a broken midfield.
* **The Change:** Change the trigger to require that the team's overall clearance differential is neutral or positive: `Player_Clearances / Team_Clearances > 0.35` AND `Team_Total_Clearances >= Opponent_Total_Clearances (5-week average)`.

### "The Missing Link" Identity Guard

* **The Problem:** If a team is **Falling** and a player's clearances drop by $5\%$, they trigger the tag. But a drop from 8 clearances down to 7.6 is a $5\%$ drop, which is standard statistical noise.
* **The Fix:** Require a hard volume drop alongside the percentage swing:
`Clearance_Delta <= -0.15` (a 15% drop) AND `Raw_Clearance_Loss >= 1.5 clearances per game`.

---


