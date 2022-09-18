import { ThemeContext } from "@emotion/react";
import { ActionIcon, Anchor, AppShell, Avatar, Burger, Group, Header, MantineProvider, MediaQuery, Menu, Navbar, Text, UnstyledButton } from "@mantine/core"
import { useColorScheme } from "@mantine/hooks";
import { IconBox, IconDoorExit, IconInfoCircle, IconServer2, IconUser, IconVocabulary } from "@tabler/icons";
import React, { useContext, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { DesktopContext, UserContext } from "../App";
import { userManager } from "../userManager";
const Layout = ({ children }: { children: React.ReactNode }) => {
  const [opened, setOpened] = useState(false);
  const { user } = useContext(UserContext);

  const desktop = useContext(DesktopContext);

  //   useEffect(() => {
  //     if (desktop) {
  //       setOpened(true);
  //     }
  //   }, [desktop]);
  // }, [])

  const routes = [
    {
      name: "Instances",
      icon: <IconServer2 size={18} />,
      path: "/instances",
    },
    {
      name: "Kubernetes",
      icon: <IconBox size={18} />,
      disabled: true,
      small: "Coming Soon!",
      path: "/kubernetes",
    },
    {
      name: "Account",
      icon: <IconUser size={18} />,
      path: "/account",
    },
    {
      name: "Wiki",
      icon: <IconVocabulary size={18} />,
      path: "/wiki",
    },
    {
      name: "About",
      icon: <IconInfoCircle size={18} />,
      path: "/about",
    }
  ]

  return (
    <AppShell
      padding="md"
      navbarOffsetBreakpoint="md"
      navbar={
        useLocation()?.pathname === "/" ? <></> : (
          <Navbar

            hidden={!opened || desktop} width={{ base: 200 }} p="xs">
            <Group py="md">
              {routes.map((route) => (
                <Link
                  key={route.name}
                  to={route.path}
                  style={{ width: "100%", textDecoration: "none" }}
                >
                  <UnstyledButton
                    style={{
                      width: "100%",
                      paddingLeft: "6px",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    <i style={{ margin: "0 10px", display: "inline" }}>{route.icon}</i>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <Text style={{ color: `${route.disabled ? "dimmed" : "unset"}` }}>{route.name}</Text>
                      <Text size="xs" color="dimmed">{route.small ? route.small : null}</Text>
                    </div>
                  </UnstyledButton>
                </Link>
              ))}
            </Group>
          </Navbar >
        )
      }
      header={
        < MantineProvider theme={{ colorScheme: "dark" }}>
          <Header height={60} p="xs" style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              {!desktop ? (
                < Burger
                  opened={opened}
                  onClick={() => setOpened((o) => !o)}
                  // size="sm"
                  // color={theme.colors.gray[6]}
                  mr="lg"
                />
              ) : <> </>}
              <Link to="/" style={{
                height: "100%",
                paddingLeft: "6px",
              }}>
                <img alt="Netsoc Cloud" height="32px" src="https://netsoc.cloud/img/cloud-logo.caa8765e.svg"></img>
              </Link>
            </div>
            <div style={{ margin: "0 1em", display: "flex", alignItems: "center" }}>
              <Link style={{ color: useColorScheme() == "dark" ? "white" : "black", textDecoration: "none", marginRight: "1.4em" }} to="/account">
                {user?.profile.preferred_username}
              </Link>
              <ActionIcon onClick={() => { userManager.signoutPopup().then(() => { window.location.href = "/" }) }}>
                <IconDoorExit />
              </ActionIcon>
            </div>
          </Header>
        </MantineProvider >
      }
    >
      <div style={{ display: "block" }}>
        {children}
      </div>
    </AppShell>
  );
}

export default Layout
