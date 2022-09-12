import { useEffect } from "react";
import { userManager } from "../userManager";

const SilentLogin = () => {
    useEffect(() => {
        userManager.signinSilentCallback(window.location.toString());
        window.location.href = "/";
    })
    return (<></>)
}

export default SilentLogin;
