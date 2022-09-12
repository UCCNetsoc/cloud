import { useEffect } from "react"
import { userManager } from "../userManager"

const Callback = () => {
    useEffect(() => {
        console.log(window.location.toString())
        userManager.signinRedirectCallback(window.location.toString()).then((something) => {
            console.log(something)
        })
        // window.location.href = "/"

    }, [])
    return (
        <></>
    )
}

export default Callback