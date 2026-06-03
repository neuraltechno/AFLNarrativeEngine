'use server';

import { exec } from 'child_process';
import { promisify } from 'util';
import { revalidatePath } from 'next/cache';

const execPromise = promisify(exec);

export async function runScript(scriptName: string) {
  try {
    // Determine command based on script name
    let command = '';
    if (scriptName === 'fetch') {
      command = 'python scripts/fetch_data.py';
    } else if (scriptName === 'trends') {
      command = 'python scripts/calculate_team_trends.py';
    } else {
      throw new Error('Unknown script');
    }

    const { stdout, stderr } = await execPromise(command);
    
    if (stderr && !stdout) {
      return { success: false, error: stderr };
    }

    // Refresh the data on the pages
    revalidatePath('/');
    revalidatePath('/teams');
    revalidatePath('/rounds');

    return { success: true, output: stdout };
  } catch (error: any) {
    console.error(`Error running script ${scriptName}:`, error);
    return { success: false, error: error.message };
  }
}
