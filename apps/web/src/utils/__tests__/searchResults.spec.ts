import { describe, it, expect } from 'vitest'
import {
  buildTableOfContents,
  groupResultsByHeader,
  type RegulationSearchResult,
} from '@/utils/searchResults'

function section(
  id: string,
  header: string | null,
  summaryLabel: string | null = null,
): RegulationSearchResult {
  return {
    id,
    header,
    text: `Tekst ${id}`,
    elements: [],
    summary_label: summaryLabel,
    summary: summaryLabel && `Opis ${id}`,
  }
}

describe('groupResultsByHeader', () => {
  it('gives each group of consecutive results an identifier', () => {
    const groups = groupResultsByHeader([
      section('1', 'Art. 1'),
      section('2', 'Art. 1'),
      section('3', 'Art. 2'),
    ])

    expect(groups.map(({ id, items }) => [id, items.length])).toEqual([
      ['result-group-0', 2],
      ['result-group-1', 1],
    ])
  })
})

describe('buildTableOfContents', () => {
  it('nests sections under the chapters of their breadcrumbs', () => {
    const groups = groupResultsByHeader([
      section('1', 'Dział I > Rozdział 1 > Art. 1'),
      section('2', 'Dział I > Rozdział 1 > Art. 2'),
      section('3', 'Dział I > Rozdział 2 > Art. 3'),
      section('4', 'Dział II > Art. 4'),
    ])

    expect(buildTableOfContents(groups)).toEqual([
      {
        title: 'Dział I',
        firstGroupId: 'result-group-0',
        children: [
          {
            title: 'Rozdział 1',
            firstGroupId: 'result-group-0',
            children: [
              {
                title: 'Art. 1',
                groupId: 'result-group-0',
                firstGroupId: 'result-group-0',
                children: [],
              },
              {
                title: 'Art. 2',
                groupId: 'result-group-1',
                firstGroupId: 'result-group-1',
                children: [],
              },
            ],
          },
          {
            title: 'Rozdział 2',
            firstGroupId: 'result-group-2',
            children: [
              {
                title: 'Art. 3',
                groupId: 'result-group-2',
                firstGroupId: 'result-group-2',
                children: [],
              },
            ],
          },
        ],
      },
      {
        title: 'Dział II',
        firstGroupId: 'result-group-3',
        children: [
          {
            title: 'Art. 4',
            groupId: 'result-group-3',
            firstGroupId: 'result-group-3',
            children: [],
          },
        ],
      },
    ])
  })

  it('links a chapter that has its own section to that section', () => {
    const groups = groupResultsByHeader([
      section('1', 'Rozdział 1'),
      section('2', 'Rozdział 1 > Art. 1'),
    ])

    expect(buildTableOfContents(groups)).toEqual([
      {
        title: 'Rozdział 1',
        groupId: 'result-group-0',
        firstGroupId: 'result-group-0',
        children: [
          {
            title: 'Art. 1',
            groupId: 'result-group-1',
            firstGroupId: 'result-group-1',
            children: [],
          },
        ],
      },
    ])
  })

  it('describes an entry with the summary of its first section', () => {
    const groups = groupResultsByHeader([
      section('1', 'Art. 1', 'Zakres ustawy'),
      section('2', 'Art. 1', 'Inny zakres'),
      section('3', 'Art. 2'),
    ])

    expect(
      buildTableOfContents(groups).map(({ title, summaryLabel, summary }) => ({
        title,
        summaryLabel,
        summary,
      })),
    ).toEqual([
      { title: 'Art. 1', summaryLabel: 'Zakres ustawy', summary: 'Opis 1' },
      { title: 'Art. 2', summaryLabel: undefined, summary: undefined },
    ])
  })

  it('starts a new entry when a chapter appears again after another one', () => {
    const groups = groupResultsByHeader([
      section('1', 'Rozdział 1 > Art. 1'),
      section('2', 'Rozdział 2 > Art. 5'),
      section('3', 'Rozdział 1 > Art. 2'),
    ])

    expect(buildTableOfContents(groups).map((node) => node.title)).toEqual([
      'Rozdział 1',
      'Rozdział 2',
      'Rozdział 1',
    ])
  })

  it('leaves out sections without a header', () => {
    const groups = groupResultsByHeader([section('1', null), section('2', 'Art. 1')])

    expect(buildTableOfContents(groups).map((node) => node.title)).toEqual(['Art. 1'])
  })
})
