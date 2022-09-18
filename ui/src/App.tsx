import { ColorScheme, ColorSchemeProvider, MantineProvider } from '@mantine/core';
import { NotificationsProvider } from '@mantine/notifications';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Callback from './Components/Callback';
import Layout from './Components/Layout';
import Login from './Components/Login';
import SilentLogin from './Components/CallbackSilent';
import About from './Views/About';
import Home from './Views/Home';
import Instances from './Views/Instances';
import CallbackSilent from './Components/CallbackSilent';
import { useHotkeys, useLocalStorage } from '@mantine/hooks';
import Account from './Views/Account';
import { createContext, useEffect, useState } from 'react';
import { Cloud } from './types';
import { GetAllInstances } from './api';
import { userManager } from './userManager';
import { User } from 'oidc-client-ts';
import SpotlightComponent from './Components/SpotlightComponent';

export const DesktopContext = createContext(true)
// export const InstanceContext = createContext([] as Cloud.Instance[] | null)
export const InstanceContext = createContext({
  instances: [] as Cloud.Instance[] | null,
  setInstances: (_instances: Cloud.Instance[] | null) => { }
});

export const UserContext = createContext({
  user: null as User | null,
  setUser: (_user: User | null) => { }
});

export const InstanceTemplateContext = createContext({
  instanceTemplates: [] as Cloud.Template[] | null,
  setInstanceTemplates: (_instanceTemplates: Cloud.Template[] | null) => { }
});

export default function App() {
  const [loading, setLoading] = useState(false);
  const [desktop, setDesktop] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [instanceRetries, setInstanceRetries] = useState(2)
  const [instances, setInstances] = useState<Cloud.Instance[] | null>(null)
  const [instanceTemplates, setInstanceTemplates] = useState<Cloud.Template[] | null>(null)

  useEffect(() => {
    checkWidth()
    if (loading) return;
    (async () => {
      await setLoading(true);
      if (instanceRetries > 0 && instances == null) {
        try {
          setInstances(await GetAllInstances());
          setUser(await userManager.getUser())
        } finally {
          setInstanceRetries(instanceRetries - 1)
        }
        window.addEventListener("resize", checkWidth);
      }
    })();
  }, [loading])

  const checkWidth = () => {
    if (window.innerWidth < 980) {
      setDesktop(false)
    } else {
      setDesktop(true)
    }
  }

  const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
    key: 'mantine-color-scheme',
    defaultValue: 'dark',
    getInitialValueInEffect: true,
  });

  const toggleColorScheme = (value?: ColorScheme) =>
    setColorScheme(value || (colorScheme === 'dark' ? 'light' : 'dark'));

  useHotkeys([['mod+J', () => toggleColorScheme()]]);

  return (
    <>
      <ColorSchemeProvider colorScheme={colorScheme} toggleColorScheme={toggleColorScheme}>
        <MantineProvider
          theme={{
            colorScheme,
            colors: {
              'netsoc-blue': ['#007bde']
            }
          }}
          withGlobalStyles withNormalizeCSS
        >
          <NotificationsProvider>
            <DesktopContext.Provider value={desktop}>
              <UserContext.Provider value={{ user, setUser }}>
                <InstanceContext.Provider value={{ instances, setInstances }}>
                  <InstanceTemplateContext.Provider value={{ instanceTemplates, setInstanceTemplates }}>
                    <BrowserRouter>
                      <SpotlightComponent>
                        <Layout>
                          <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/login/silent" element={<SilentLogin />} />
                            <Route path="/callback" element={<Callback />} />
                            <Route path="/callback/silent" element={<CallbackSilent />} />
                            <Route path="/" element={<Home />} />
                            <Route path="/instances" element={<Instances />} />
                            <Route path="/about" element={<About />} />
                            <Route path="/account" element={<Account />} />
                          </Routes>
                        </Layout>
                      </SpotlightComponent>
                    </BrowserRouter>
                  </InstanceTemplateContext.Provider>
                </InstanceContext.Provider>
              </UserContext.Provider>
            </DesktopContext.Provider>
          </NotificationsProvider>
        </MantineProvider>
      </ColorSchemeProvider>
    </>
  );
}
