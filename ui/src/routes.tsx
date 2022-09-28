import { IconServer2, IconBox, IconUser, IconVocabulary, IconInfoCircle } from "@tabler/icons";

export default [
    {
        name: "Instances",
        icon: <IconServer2 size={48} />,
        path: "/instances",
    },
    {
        name: "Kubernetes",
        icon: <IconBox size={48} />,
        disabled: true,
        small: "Coming Soon!",
        path: "/kubernetes",
    },
    {
        name: "Account",
        icon: <IconUser size={48} />,
        path: "/account",
    },
    {
        name: "Wiki",
        icon: <IconVocabulary size={48} />,
        path: "/wiki",
    },
    {
        name: "About",
        icon: <IconInfoCircle size={48} />,
        path: "/about",
    }
]
