import { describe, it, expect } from 'vitest'
import { createTemplateField } from '@/__tests__/factories'
import {
  toDetailsData,
  toEditableField,
  type ApplicationTemplateForm,
} from '@/domain/applicationTemplates'

function createForm(overrides: Partial<ApplicationTemplateForm> = {}): ApplicationTemplateForm {
  return {
    name: 'Wniosek o urlop',
    instructions: 'Sporządź wniosek.',
    description: 'Wniosek o urlop dziekański.',
    organizationId: 'pwr',
    suborganizationId: 'w4',
    fields: [],
    ...overrides,
  }
}

describe('toDetailsData', () => {
  it('keeps filled values', () => {
    const field = createTemplateField({ defaultValue: '123456', pattern: String.raw`\d{6}` })

    expect(toDetailsData(createForm({ fields: [field] }))).toEqual({
      name: 'Wniosek o urlop',
      instructions: 'Sporządź wniosek.',
      description: 'Wniosek o urlop dziekański.',
      organizationId: 'pwr',
      suborganizationId: 'w4',
      fields: [field],
    })
  })

  it('trims texts', () => {
    const details = toDetailsData(
      createForm({ name: '  Wniosek ', instructions: ' Instrukcje\n', description: ' Opis ' }),
    )

    expect(details).toMatchObject({
      name: 'Wniosek',
      instructions: 'Instrukcje',
      description: 'Opis',
    })
  })

  it('sends empty optional values as null', () => {
    const details = toDetailsData(
      createForm({
        instructions: '  ',
        description: '',
        organizationId: '',
        suborganizationId: '',
        fields: [createTemplateField({ defaultValue: '', pattern: '' })],
      }),
    )

    expect(details).toMatchObject({
      instructions: null,
      description: null,
      organizationId: null,
      suborganizationId: null,
      fields: [{ defaultValue: null, pattern: null }],
    })
  })
})

describe('toEditableField', () => {
  it('copies options so that editing does not change the loaded template', () => {
    const field = createTemplateField({ fieldType: 'SELECT', options: ['zimowy', 'letni'] })

    const editableField = toEditableField(field)
    editableField.options.push('oba')

    expect(editableField).toMatchObject({ name: field.name, fieldType: 'SELECT' })
    expect(field.options).toEqual(['zimowy', 'letni'])
  })
})
