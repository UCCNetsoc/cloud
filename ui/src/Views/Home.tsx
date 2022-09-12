import { Anchor, AspectRatio, Code, MantineProvider, Text } from "@mantine/core";

const Home = () => {
    return (
        <MantineProvider theme={{ colorScheme: "dark" }}>
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
                height: "100%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                transition: 'padding-bottom .2s cubic-bezier(.25,.8,.5,1)'
            }}>
                <AspectRatio ratio={628 / 255}
                    style={{
                        width: "45%",
                        background: 'url("https://netsoc.cloud/img/cloud-logo.caa8765e.svg") no-repeat',
                    }}
                >
                </AspectRatio>
                <section
                    style={{
                        fontSize: "1.8em",
                        userSelect: "none",
                        marginTop: "1.5em",
                        maxWidth: "800px",
                        textAlign: "center",
                    }}
                >

                    <Text color="white" style={{ fontSize: "1em", lineHeight: "1.4em", userSelect: "none" }}>
                        New to Netsoc or Linux? Try out our <Anchor href="/wiki">Wiki</Anchor> to get started.
                    </Text>
                    <Text color="white" style={{ fontSize: "1em", lineHeight: "1.4em", userSelect: "none" }}>
                        {/* Need help? Check out the <code style={{ padding: "4px 6px", background: "#111f", fontWeight: "bold", whiteSpace: "nowrap" }}>#netsoc-cloud</code> channel on our <Anchor href="https://discord.gg">Discord</Anchor>. */}
                        Need help? Check out the <Code sx={{ fontSize: "0.9em", whiteSpace: "nowrap" }} >#netsoc-cloud</Code> channel on our <Anchor href="https://discord.gg">Discord</Anchor>.
                    </Text>
                </section>
                <ul>
                    
                </ul>
            </div>
        </MantineProvider>
    )
}

export default Home;
