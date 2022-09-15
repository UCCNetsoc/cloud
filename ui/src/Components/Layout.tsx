import { Anchor, AppShell, Avatar, Burger, Group, Header, MantineProvider, MediaQuery, Menu, Navbar, Text, UnstyledButton } from "@mantine/core"
import { IconBox, IconInfoCircle, IconServer2, IconUser, IconVocabulary } from "@tabler/icons";
import React, { useState } from "react";

const Layout = ({ children }: { children: React.ReactNode }) => {
  const [opened, setOpened] = useState(false);

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
      navbarOffsetBreakpoint="sm"
      navbar={
        <Navbar hiddenBreakpoint="sm" hidden={true} width={{ base: 200 }} p="xs">
          <Group py="md">
            {routes.map((route) => (
              <Anchor
                key={route.name}
                aria-disabled={route.disabled}
                href={route.disabled ? '#' : route.path}
                style={{ width: "100%" }}
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
              </Anchor>
            ))}
          </Group>
        </Navbar >
      }
      header={
        < MantineProvider theme={{ colorScheme: "dark" }}>
          <Header height={60} p="xs" style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <MediaQuery largerThan="sm" styles={{ display: "none" }}>
                <Burger
                  opened={opened}
                  onClick={() => setOpened((o) => !o)}
                  size="sm"
                  // color={theme.colors.gray[6]}
                  mr="lg"
                />
              </MediaQuery>
              <Anchor href="/" style={{
                height: "100%",
                paddingLeft: "6px",
              }}>
                <img alt="Netsoc Cloud" height="32px" src="https://netsoc.cloud/img/cloud-logo.caa8765e.svg"></img>
              </Anchor>
            </div>
            <div style={{ margin: "0 1em" }}>
              <Menu>
                <Menu.Target>
                  <Avatar variant="gradient" size="sm" radius="xl">TG</Avatar>
                </Menu.Target>
                <Menu.Dropdown>
                  <Menu.Item>Account</Menu.Item>
                  <Menu.Item>Logout</Menu.Item>
                </Menu.Dropdown>
              </Menu>
            </div>
          </Header>
        </MantineProvider >
      }
    >
      {children}
    </AppShell >
  )
}

export default Layout
