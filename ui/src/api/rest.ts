
export interface Detail {
  msg: string;
  loc: string[];
}

export interface Error {
  detail: Detail;
}

export interface Info {
  detail: Detail;
}

// fetchRest function performs a request to the given fetch arguments
// if it does not get a statusCode in param expectedStatus it will throw an exception
// If the response of the rest support the Error interface it will return the error as the exception message
// otherwise the statusCode and statusText
// If the fetch fails completely (i.e connection refused), a message is returned witvh the fetch exception message
export async function fetchRest (input: RequestInfo, init?: RequestInit | undefined, expectedStatus: number[] = [200, 201]): Promise<Response> {
  try {
    const res = await fetch(input, init)

    if (!expectedStatus.includes(res.status)) {
      let msg = `${res.status}: ${res.statusText}`

      // Test if the error returned has a rest error payload
      try {
        const err: Error = await res.json()

        if (err?.detail?.msg) {
          msg = err.detail.msg
        } else {
          msg = `${res.status}: ${res.statusText}`
        }
      } catch { }

      // Throw message
      throw new Error(msg)
    }

    return res
  } catch (e) {
    throw new Error(`Could not perform request: ${e}. If issues persist contact the SysAdmins on the UCC Netsoc Discord`)
  }
}
