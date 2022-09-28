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
import { useHotkeys, useInterval, useLocalStorage } from '@mantine/hooks';
import Account from './Views/Account';
import { createContext, useEffect, useState } from 'react';
import { Cloud } from './types';
import { GetAllInstances } from './api';
import { userManager } from './userManager';
import { User } from 'oidc-client-ts';
import SpotlightComponent from './Components/SpotlightComponent';
import InstanceApproval from './Views/InstanceApproval';
import Wiki from './Views/Wiki';
import Signup from './Views/Signup';
import Verification from './Views/Verification';

export const DesktopContext = createContext(true)
// export const InstanceContext = createContext([] as Cloud.Instance[] | null)
export const InstanceContext = createContext({
  instances: [] as Cloud.Instance[] | null,
  setInstances: (_instances: Cloud.Instance[] | null) => { },
});

export const UserContext = createContext({
  user: null as User | null,
  setUser: (_user: User | null) => { }
});

export const InstanceTemplateContext = createContext([
  {
    lxcInstanceTemplates: [] as Cloud.Template[] | null,
    setLxcInstanceTemplates: (_instanceTemplates: Cloud.Template[] | null) => { }
  },
  {
    vpsInstanceTemplates: [] as Cloud.Template[] | null,
    setVpsInstanceTemplates: (_instanceTemplates: Cloud.Template[] | null) => { }
  }]
);

export default function App() {
  const [loading, setLoading] = useState(false);
  const [desktop, setDesktop] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [instanceRetries, setInstanceRetries] = useState(2)
  const [instances, setInstances] = useState<Cloud.Instance[] | null>(null)
  const [lxcInstanceTemplates, setLxcInstanceTemplates] = useState<Cloud.Template[] | null>(null)
  const [vpsInstanceTemplates, setVpsInstanceTemplates] = useState<Cloud.Template[] | null>(null)

  const interval = useInterval(() => {
    GetAllInstances().then((instances) => setInstances(instances))
    console.log("Fetched instances")
  }, 15000)

  useEffect(() => {
    interval.start()
    return interval.stop
  }, [])

  useEffect(() => {
    checkWidth()
    if (loading) {
      return
    };
    setLoading(true);
    if (instances == null && instanceRetries > 0) {
      setInstanceRetries(instanceRetries - 1)
      try {
        GetAllInstances().then((instances) => setInstances(instances))
        userManager.getUser().then((user) => setUser(user))
      } finally {
        setInstanceRetries(instanceRetries - 1)
      }
      window.addEventListener("resize", checkWidth);
    }
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
                  <InstanceTemplateContext.Provider value={[{ lxcInstanceTemplates, setLxcInstanceTemplates }, { vpsInstanceTemplates, setVpsInstanceTemplates }]}>
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
                            <Route path="/wiki" element={<Wiki />} />
                            <Route path="/about" element={<About />} />
                            <Route path="/account" element={<Account />} />
                            <Route path="/signup" element={<Signup />} />
                            <Route path="/instance-request/:username/:type-request/:hostname/:token" element={<InstanceApproval />} />
                            <Route path="/account/:username/verification/:token" element={<Verification />} />
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
