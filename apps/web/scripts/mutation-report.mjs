import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync } from 'node:fs'

const directory = new URL('../../../.cache/mutation/web/report/', import.meta.url)
const report = JSON.parse(readFileSync(new URL('mutation.json', directory), 'utf8'))
const counts = new Map()
for (const file of Object.values(report.files)) {
  for (const mutant of file.mutants) {
    counts.set(mutant.status, (counts.get(mutant.status) ?? 0) + 1)
  }
}
const revision = execFileSync('git', ['rev-parse', 'HEAD'], {
  cwd: new URL('../../../', import.meta.url),
  encoding: 'utf8',
}).trim()
const summary = [
  '# Frontend mutation tests',
  '',
  `Commit: \`${revision}\``,
  `Generated at: ${new Date().toISOString()}`,
  `Sources: ${Object.keys(report.files).join(', ')}`,
  '',
  '| Status | Count |',
  '| --- | ---: |',
  ...[...counts].toSorted(([left], [right]) => left.localeCompare(right))
    .map(([status, count]) => `| ${status} | ${count} |`),
  `| Total | ${[...counts.values()].reduce((total, count) => total + count, 0)} |`,
  '',
  'Open `mutation.html` to review surviving mutations and their source changes.',
  '`mutation.json` contains all mutants, statuses and test coverage details.',
  'Survivors require review; they are not confirmed bugs. NoCoverage means no selected test covered the mutation.',
  'Timeouts and other abnormal statuses require separate investigation.',
  'Check the workflow outcome and `run.log` for execution failures.',
  '',
]
writeFileSync(new URL('summary.md', directory), summary.join('\n'))
console.log(`Mutation report: ${directory.pathname}`)
