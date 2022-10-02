import { createContext, useState } from "react"


const DesktopLayoutProvider = () => {
    const [desktop, setDesktop] = useState(true);
    
    const Context = createContext({
        isDesktop: desktop
    });
    
}