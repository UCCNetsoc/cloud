import { SpotlightAction, SpotlightProvider } from "@mantine/spotlight";
import { IconServer2, IconHome, IconInfoCircle, IconPackage, IconUser, IconVocabulary, IconBrandDocker } from "@tabler/icons";
import { useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { InstanceContext } from "../App";

const SpotlightComponent = (props: { children: React.ReactNode }) => {
    const { instances } = useContext(InstanceContext)
    const [spotlight, setSpotlight] = useState<SpotlightAction[]>([])

    const navigate = useNavigate()
    const actions: SpotlightAction[] = [
        {
            title: 'Instances',
            onTrigger: () => {
                // redirect
                navigate('/instances');
            },
            icon: <IconServer2 size={18} />,
            description: "Learn more about this project",
        },
        {
            title: 'Home',
            onTrigger: () => {
                // redirect
                navigate('/');
            },
            icon: <IconHome size={18} />,
            description: "Home",
        },
        {
            title: 'About',
            onTrigger: () => {
                // redirect
                navigate('/about');
            },
            icon: <IconInfoCircle size={18} />,
            description: "Learn more about this project",
        },
        {
            title: 'Kubernetes',
            onTrigger: () => {
                // redirect
                navigate('/about');
            },
            icon: <IconPackage size={18} />,
            description: "Managed Kubernetes cluster"
        },
        {
            title: 'Account',
            onTrigger: () => {
                // redirect
                navigate('/account');
            },
            icon: <IconUser size={18} />,
            description: "Your account settings"
        },
        {
            title: 'Wiki',
            onTrigger: () => {
                window.open("https://wiki.netsoc.co")
            },
            icon: <IconVocabulary size={18} />,
            description: "Wiki for help with getting started"
        },
    ]

    useEffect(() => {
        if (instances) {
            const tmp = actions
            tmp.push(...instances.map((instance) => {
                return {
                    title: instance.hostname,
                    onTrigger: () => {
                        // window.location.href = `/instances?q=${instance.id}`
                        if (window.location.href.startsWith("/instances")) {

                            window.history.replaceState(null, instance.hostname, `?q=${instance.id}`)
                        }
                        navigate(`/instances?q=${instance.id}`)

                    },
                    icon: <IconBrandDocker size={18} />,
                    description: `${instance.type.toUpperCase()} - ${instance.specs.cores} vCPUs ${instance.specs.memory / 1024}GB RAM`,
                }
            }))
            setSpotlight(tmp)
        }
    }, [instances])
    return (

        <SpotlightProvider shortcut={['mod + K']} actions={spotlight}>
            {props.children}
        </SpotlightProvider>
    )
}

export default SpotlightComponent;
