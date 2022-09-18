import { Anchor, AspectRatio, Code, MantineProvider, Text } from "@mantine/core";
import LandingBtn from "../Components/LandingBtn";
import routes from '../routes';
import { DesktopContext } from '../App';
import { useContext } from "react";
import { IconChevronDown, IconServer2, IconTools, IconWorld } from "@tabler/icons";
import styles from './Home.module.css';

const Home = () => {
  const desktop = useContext(DesktopContext);

  return (
    <MantineProvider theme={{ colorScheme: "dark" }}>
      <div style={{
        width: "100%",
        minHeight: "95%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        overflow: "hidden",
      }}>
        <video muted loop autoPlay={true}
          style={{
            zIndex: -1,
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        >
          <source src="https://netsoc.cloud/media/bgvideo-orig.92e68a06.mp4" type="video/mp4" />
        </video>
        <div style={{
          width: "100%",
          height: "95%",
          position: "absolute",
          transform: "translate(-50%, -50%)",
          top: "50%",
          left: "50%",
          right: "0",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}>
          <AspectRatio ratio={628 / 255}
            style={{
              width: "30%",
              marginTop: "30px",
              background: 'url("https://netsoc.cloud/img/cloud-logo.caa8765e.svg") no-repeat',
            }}
          >
          </AspectRatio>
          <section
            style={{
              fontSize: "1.5em",
              userSelect: "none",
              marginTop: "1.5em",
              width: "80%",
              maxWidth: "800px",
              textAlign: "center",
            }}
          >
            <Text color="white" style={{ fontSize: "1em", lineHeight: "1.4em", userSelect: "none" }}>
              New to Netsoc or Linux? Try out our <Anchor href="/wiki">Wiki</Anchor> to get started.
            </Text>
            <Text color="white" style={{ fontSize: "1em", lineHeight: "1.4em", userSelect: "none" }}>
              Need help? Check out the <Code sx={{ fontSize: "0.9em", whiteSpace: "nowrap" }} >#netsoc-cloud</Code> channel on our <Anchor href="https://discord.gg">Discord</Anchor>.
            </Text>
          </section>
          <ul style={{
            marginTop: desktop ? "6em" : "2em",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            flexDirection: desktop ? "row" : "column",
          }}>
            {routes.map((route, index) => (
              <LandingBtn key={index} url={route.path} icon={route.icon} name={route.name} small={route.small} disabled={route.disabled} />
            ))}
          </ul>
          <IconChevronDown className={styles.downArrow} size={64} onClick={() => {
            window.scrollBy({
              top: window.innerHeight,
              behavior: "smooth",
            });
          }} />
        </div>
      </div>
      <article className={styles.offers}>
        <h1>What we offer</h1>

        <section>
          <h2><IconWorld />Web Services</h2>
          <Text>
            Easily deploy a web service with a few clicks. Pre-configured templates include WordPress, Ghost CMS, static hosting and more
          </Text>
        </section>

        <section>
          <h2><IconTools /> Development Tools</h2>
          <Text>
            Boot a container with support for any programming language you can think of, and access the terminal using your browser.
          </Text>
        </section>

        <section>
          <h2 style={{ display: "flex", alignItems: "center" }}><IconServer2 /> Virtual Private Servers</h2>
          <Text>
            Launch a Linux host like Debian / Ubuntu / Arch / CentOS and run tools like Docker, LXD and more
          </Text>
        </section>
      </article>
    </MantineProvider>
  )
}

export default Home;
