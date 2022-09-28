import { useEffect } from "react";
import { userManager } from "../userManager";

const SilentLogin = () => {
    useEffect(() => {
        userManager.signoutPopupCallback(window.location.toString());
    })
    return (<></>)
}

export default SilentLogin;
