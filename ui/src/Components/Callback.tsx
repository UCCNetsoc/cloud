import { useContext, useEffect } from "react"
import { userManager } from "../userManager"
import AuthContext from "./AuthContextProvider";

const Callback = () => {
  useEffect(() => {
    console.log(window.location.toString())
    userManager.signinRedirectCallback(window.location.toString()).then((something) => {
      window.location.href = "/"
    })
    // window.location.href = "/"

  }, [])
  return (
    <></>
  )
}

export default Callback