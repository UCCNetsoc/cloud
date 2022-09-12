import { Anchor, Avatar } from "@mantine/core"
import { useEffect, useState } from "react"

const About = () => {
  const [truncateLength, setTruncateLength] = useState(12)

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 500) {
        setTruncateLength(7)
      } else if (window.innerWidth < 768) {
        setTruncateLength(9)
      } else {
        setTruncateLength(12)
      }
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => window.removeEventListener('resize', handleResize)
  })

  interface Contributor {
    login: string
    avatar_url: string
  }

  const [contributors, setContributors] = useState<Array<Contributor>>([])

  useEffect(() => {
    (async () => {
      const request = await fetch("https://api.github.com/repos/UCCNetsoc/cloud/contributors")
      const contributors = await request.json() as Array<Contributor>;
      setContributors(contributors)
    })()
  })

  return (
    <>
      <section style={{
        marginTop: 0,
        maxWidth: "800px",
      }}>
        <h1>Learn about Netsoc Cloud</h1>
        <p>Netsoc Cloud is the REST API and control panel powering UCC Netsoc's services available to members of the society. It provides Container and VPS hosting built atop of Proxmox with routing powered by Traefik
        </p>
        <p>
          It consists of an OpenAPI compliant REST API written in FastAPI, a frontend in React using Mantine and (coming soon) a command line application
        </p>

        <p style={{ marginTop: "2em" }}>
          We would not be able to host this without the help and generosity of Jerry Sweeney (CEO of <Anchor href="https://cix.ie">CloudCIX</Anchor>),
          the <Anchor href="https://societies.ucc.ie/">UCC Societies Executive</Anchor> and <Anchor href="https://github.com/UCCNetsoc/admin">UCC IT Services</Anchor>
        </p>
      </section>

      <h1>Contributors</h1>
      <ul style={{ display: "flex", margin: "auto", padding: "0" }}>
        {contributors.map((contributor) => (
          <Anchor href={`https://github.com/${contributor.login}`} style={{ width: `${truncateLength}ch`, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
            <Avatar src={contributor.avatar_url} radius="xl">{contributor.login}</Avatar>
            <p style={{ textAlign: "center" }}>{contributor.login.length > truncateLength ? contributor.login.slice(0, truncateLength - 3) + '...' : contributor.login}</p>
          </Anchor>
        ))}
      </ul>
    </>
  )
}

export default About;
