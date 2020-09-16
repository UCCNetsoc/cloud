
import { config } from '@/config'

export interface Property {
  title? : string;
  description? : string;
  pattern? : string;
  minLength? : number;
  maxLength? : number;
  type: string;
  // multipleOf
  // maximum
  // exclusiveMaximum
  // minimum
  // exclusiveMinimum
  // maxItems
  // minItems
  // uniqueItems
  // maxProperties
  // minProperties
  // required
  // enum
}

let spec: any

export async function openApiLoadSpec () {
  const req = await fetch(`${config.apiBaseUrl}/openapi.json`)
  spec = await req.json()
}

export function openApiGetSchemaProperty (schema: string, property: string): Property {
  if (spec === undefined) {
    throw new Error("spec wasn't loaded")
  }

  const requirements = spec?.components?.schemas?.[schema]?.properties?.[property]

  if (requirements) {
    return requirements
  }

  throw new Error(`could not find ${schema} with property ${property}`)
}

const reMemo: { [id: string]: RegExp } = {}

// Returns true if the given input matches the properties rules
export function openApiPropertyValidateData (property: Property, input: number|string): boolean {
  if (!property?.type) return false
  if (property.type !== typeof input) return false

  if (property.type === 'string') {
    // // console.log(property)
    if (property?.maxLength && (input as string).length > property.maxLength) return false
    if (property?.minLength && (input as string).length < property.minLength) return false

    if (property?.pattern) {
      const pattern: string = property.pattern

      if (!(pattern in reMemo)) {
        reMemo[pattern] = new RegExp(property.pattern)
      }

      if (!reMemo[pattern].test((input as string))) return false
    }
  }

  return true
}

// Returns a function that can validate input against the supplied property
// The validator returns true when the data is valid, or a string explaining why not if invalid
export function openApiPropertyValidator (property: Property): ((value: number | string) => string | boolean) {
  return (value: number|string): string|boolean => {
    if (!openApiPropertyValidateData(property, value)) {
      return property.description || 'Invalid'
    }

    return true
  }
}
