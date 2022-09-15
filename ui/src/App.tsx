import { ColorScheme, ColorSchemeProvider, MantineProvider } from '@mantine/core';
import { SpotlightAction, SpotlightProvider } from '@mantine/spotlight';
import { NotificationsProvider } from '@mantine/notifications';
import { IconBrandDocker, IconInfoCircle, IconPackage, IconServer, IconServer2, IconUser, IconVocabulary } from '@tabler/icons';
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

export default function App() {

  const actions: SpotlightAction[] = [
    {
      title: 'About',
      onTrigger: () => {
        // redirect
        window.location.href = '/about';
      },
      icon: <IconInfoCircle size={18} />,
      description: "Learn more about this project",
    },
    {
      title: 'Instances',
      onTrigger: () => {
        // redirect
        window.location.href = '/about';
      },
      icon: <IconServer2 size={18} />,
      description: "Learn more about this project",
    },
    {
      title: 'Kubernetes',
      onTrigger: () => {
        // redirect
        window.location.href = '/about';
      },
      icon: <IconPackage size={18} />,
      description: "Managed Kubernetes cluster"
    },
    {
      title: 'Account',
      onTrigger: () => {
        // redirect
        window.location.href = '/about';
      },
      icon: <IconUser size={18} />,
      description: "Your account settings"
    },
    {
      title: 'Wiki',
      onTrigger: () => {
        // redirect
        window.location.href = '/about';
      },
      icon: <IconVocabulary size={18} />,
      description: "Wiki for help with getting started"
    },

    {
      title: "minecraft",
      onTrigger: () => {
        console.log("bruh")
      },
      icon: <IconBrandDocker size={18} />,
      description: "Ubuntu 20.04 LXC",
    },
    {
      title: "web",
      onTrigger: () => {
        console.log("bruh")
      },
      icon: <IconServer size={18} />,
      description: "Arch VM",
    }
  ]

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
          <SpotlightProvider shortcut={['mod + K']} actions={actions}>
            <NotificationsProvider>
              <Layout>
                <BrowserRouter>
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
                </BrowserRouter>
              </Layout>
            </NotificationsProvider>
          </SpotlightProvider>
        </MantineProvider>
      </ColorSchemeProvider>
    </>
  );
}
