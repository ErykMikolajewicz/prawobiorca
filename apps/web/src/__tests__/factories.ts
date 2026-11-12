import { AxiosError, AxiosHeaders } from 'axios'
import type {
  ApplicationRepresentation,
  ApplicationTemplateFieldOutput,
  ApplicationTemplateRepresentation,
  CaseDocument,
  OrganizationData,
  PublishedApplicationTemplate,
  RegulationRepresentation,
  SearchResult,
} from '@/api/generated/model'

export function createHttpError(status: number): AxiosError {
  return new AxiosError('Request failed', undefined, undefined, undefined, {
    status,
    statusText: '',
    data: null,
    headers: {},
    config: { headers: new AxiosHeaders() },
  })
}

export function createFailingRequest() {
  let reject: ((reason: unknown) => void) | undefined
  const request = new Promise<never>((_resolve, rejectRequest) => {
    reject = rejectRequest
  })
  return { request, fail: () => reject?.(createHttpError(500)) }
}

export function createDeferred<T>() {
  let resolve: ((value: T) => void) | undefined
  let reject: ((reason: unknown) => void) | undefined
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return {
    promise,
    resolve: (value: T) => resolve?.(value),
    reject: (reason: unknown) => reject?.(reason),
  }
}

export function createNetworkError(): AxiosError {
  return new AxiosError('Network Error', AxiosError.ERR_NETWORK, undefined, {})
}

export function createRegulation(
  overrides: Partial<RegulationRepresentation> = {},
): RegulationRepresentation {
  return {
    id: 'regulation-1',
    createDate: '2026-09-29T10:00:00',
    presentationName: 'Regulamin studiów',
    description: null,
    regulationType: 'STATUTE',
    preparationStatus: 'PREPARED',
    descriptionStatus: 'NOT_REQUESTED',
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }
}

export function createTemplateField(
  overrides: Partial<ApplicationTemplateFieldOutput> = {},
): ApplicationTemplateFieldOutput {
  return {
    name: 'index_number',
    label: 'Numer indeksu',
    fieldType: 'TEXT',
    required: true,
    passToAi: false,
    defaultValue: null,
    pattern: null,
    options: [],
    ...overrides,
  }
}

export function createApplicationTemplate(
  overrides: Partial<ApplicationTemplateRepresentation> = {},
): ApplicationTemplateRepresentation {
  return {
    id: 'template-1',
    createDate: '2026-10-11T10:00:00',
    name: 'Wniosek o urlop dziekański',
    status: 'DRAFT',
    fields: [],
    instructions: 'Sporządź wniosek do Dziekana.',
    description: null,
    descriptionStatus: 'NOT_REQUESTED',
    organizationId: null,
    suborganizationId: null,
    ...overrides,
  }
}

export function createPublishedTemplate(
  overrides: Partial<PublishedApplicationTemplate> = {},
): PublishedApplicationTemplate {
  return {
    id: 'template-1',
    name: 'Wniosek o urlop dziekański',
    description: null,
    fields: [],
    ...overrides,
  }
}

export function createApplication(
  overrides: Partial<ApplicationRepresentation> = {},
): ApplicationRepresentation {
  return {
    id: 'application-1',
    caseId: 'case-1',
    createDate: '2026-10-11T10:00:00',
    templateName: 'Wniosek o urlop dziekański',
    generationStatus: 'GENERATED',
    name: null,
    ...overrides,
  }
}

export function createCaseDocument(overrides: Partial<CaseDocument> = {}): CaseDocument {
  return {
    id: 'document-1',
    caseId: 'case-1',
    presentationName: 'Regulamin studiów',
    content: '1. Student ma prawo do urlopu.',
    header: '§ 12',
    elements: [{ text: '1. Student ma prawo do urlopu.', subsection: '1' }],
    highlight: null,
    ...overrides,
  }
}

export function createSearchResult(overrides: Partial<SearchResult> = {}): SearchResult {
  return {
    id: 'result-1',
    score: 0.75,
    header: '§ 12',
    text: '1. Student ma prawo do urlopu.',
    elements: [{ text: '1. Student ma prawo do urlopu.', subsection: '1' }],
    highlight: null,
    ...overrides,
  }
}

export function createOrganizations(): Array<OrganizationData> {
  return [
    {
      id: 'pwr',
      name: 'Politechnika Wrocławska',
      shortName: 'PWr',
      suborganizations: [
        { id: 'w4', name: 'Wydział Informatyki' },
        { id: 'w10', name: 'Wydział Mechaniczny' },
      ],
    },
    { id: 'uwr', name: 'Uniwersytet Wrocławski', shortName: 'UWr', suborganizations: [] },
  ]
}
