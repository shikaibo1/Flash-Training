import { readFile, writeFile, mkdir, mkdtemp, rm, realpath } from 'node:fs/promises';
import { dirname, join, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import ts from 'typescript';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const cache = join(root, 'node_modules', '.cache');
await mkdir(cache, { recursive: true });
const output = await mkdtemp(join(cache, 'flash-review-'));
try {
  for (const [source, filename] of [
    ['src/components/FeedbackPanel.tsx', 'FeedbackPanel.mjs'],
    ['src/lib/feedback.ts', 'feedback.mjs'],
    ['src/lib/stats.ts', 'stats.mjs'],
    ['src/lib/sessionCache.ts', 'sessionCache.mjs'],
  ]) {
    const text = await readFile(join(root, source), 'utf8');
    const result = ts.transpileModule(text, { compilerOptions: {
      module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
    }, fileName: source });
    await writeFile(join(output, filename), result.outputText);
  }
  const result = spawnSync(process.execPath, ['--test', 'tests/review.test.mjs'], {
    cwd: root, stdio: 'inherit', env: { ...process.env, FLASH_TEST_DIR: output, TZ: 'America/New_York' },
  });
  process.exitCode = result.status ?? 1;
} finally {
  const destination = await realpath(output);
  const within = relative(await realpath(cache), destination);
  if (!within || within.startsWith('..') || isAbsolute(within)) throw new Error('Unsafe test cleanup target');
  await rm(destination, { recursive: true, force: true });
}
