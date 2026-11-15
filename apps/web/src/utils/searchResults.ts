import type { SearchResult, SectionRepresentation } from '@/api/generated/model'

const BREADCRUMB_SEPARATOR = ' > '

export type RegulationSearchResult = SectionRepresentation &
  Partial<Pick<SearchResult, 'score' | 'highlight'>>

export type ResultGroup = {
  id: string
  header: string | null
  items: Array<RegulationSearchResult>
}

export type TocNode = {
  title: string
  summaryLabel?: string
  summary?: string
  groupId?: string
  firstGroupId: string
  children: Array<TocNode>
}

export function groupResultsByHeader(results: Array<RegulationSearchResult>): Array<ResultGroup> {
  const groups: Array<ResultGroup> = []

  for (const result of results) {
    const lastGroup = groups[groups.length - 1]

    if (lastGroup && lastGroup.header === result.header) {
      lastGroup.items.push(result)
    } else {
      groups.push({
        id: `result-group-${String(groups.length)}`,
        header: result.header,
        items: [result],
      })
    }
  }

  return groups
}

export function buildTableOfContents(groups: Array<ResultGroup>): Array<TocNode> {
  const root: Array<TocNode> = []

  for (const group of groups) {
    if (!group.header) continue

    const node = group.header
      .split(BREADCRUMB_SEPARATOR)
      .reduce<TocNode | undefined>(
        (parent, title) => findOrAddChild(parent ? parent.children : root, title, group.id),
        undefined,
      )

    if (node && node.groupId === undefined) {
      const [firstItem] = group.items
      node.groupId = group.id
      node.summaryLabel = firstItem?.summary_label ?? undefined
      node.summary = firstItem?.summary ?? undefined
    }
  }

  return root
}

function findOrAddChild(siblings: Array<TocNode>, title: string, groupId: string): TocNode {
  const lastSibling = siblings[siblings.length - 1]
  if (lastSibling?.title === title) return lastSibling

  const node: TocNode = { title, firstGroupId: groupId, children: [] }
  siblings.push(node)
  return node
}
