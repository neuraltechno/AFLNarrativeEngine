import fs from 'fs';
import path from 'path';

interface Match {
  Date: string;
  Round: number | string;
  'Home team': string;
  'Away Team': string;
  'Home team score': number;
  'Away team score': number;
  'Winning team': string;
  Margin: number;
}

async function getMatches(): Promise<Match[]> {
  const filePath = path.join(process.cwd(), 'data', 'raw', 'matches_2025.json');
  if (!fs.existsSync(filePath)) {
    return [];
  }
  const fileContents = fs.readFileSync(filePath, 'utf8');
  try {
    return JSON.parse(fileContents);
  } catch (e) {
    return [];
  }
}

export default async function RoundsPage() {
  const allMatches = await getMatches();
  
  // Group by round
  const rounds = allMatches.reduce((acc, match) => {
    const roundName = `Round ${match.Round}`;
    if (!acc[roundName]) {
      acc[roundName] = [];
    }
    acc[roundName].push(match);
    return acc;
  }, {} as Record<string, Match[]>);

  const roundNames = Object.keys(rounds).sort((a, b) => {
    const numA = parseInt(a.replace('Round ', '')) || 0;
    const numB = parseInt(b.replace('Round ', '')) || 0;
    return numB - numA; // Latest first
  });

  return (
    <div className="p-8 font-sans max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Match History</h1>
        <p className="text-zinc-600">Explore results from the 2025 AFL Season.</p>
      </header>

      <div className="space-y-12">
        {roundNames.map((roundName) => (
          <section key={roundName}>
            <h2 className="text-2xl font-bold mb-4 border-b pb-2">{roundName}</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {rounds[roundName].map((match, idx) => (
                <div key={idx} className="border rounded-lg p-4 bg-white shadow-sm">
                  <div className="flex justify-between items-center mb-3 text-xs text-zinc-400">
                    <span>{new Date(match.Date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <div className={`font-semibold ${match['Winning team'] === match['Home team'] ? 'text-zinc-900' : 'text-zinc-500'}`}>
                      {match['Home team']}
                    </div>
                    <div className="text-xl font-bold">{match['Home team score']}</div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className={`font-semibold ${match['Winning team'] === match['Away Team'] ? 'text-zinc-900' : 'text-zinc-500'}`}>
                      {match['Away Team']}
                    </div>
                    <div className="text-xl font-bold">{match['Away team score']}</div>
                  </div>
                  <div className="mt-3 pt-3 border-t text-sm text-center text-zinc-600">
                    {match['Winning team'] ? (
                      <span className="font-medium text-blue-600">
                        {match['Winning team']} by {match.Margin}
                      </span>
                    ) : (
                      'Draw'
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {roundNames.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded text-amber-800">
          No match data found for 2025.
        </div>
      )}

      <nav className="mt-12">
        <a href="/" className="text-blue-600 hover:underline">Back to Home</a>
      </nav>
    </div>
  );
}
