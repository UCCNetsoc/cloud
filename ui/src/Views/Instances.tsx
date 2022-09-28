import { useEffect, useState } from "react";
import { IsLoggedIn } from "../api/account";
import InstanceTable from "../Components/InstanceTable";
import { LoginModal } from "../Components/LoginModal";

const Instances = () => {
  const [loggedIn, setLoggedIn] = useState(true);
  useEffect(() => {
    (async () => {
      try {
        await IsLoggedIn()
      } catch {
        setLoggedIn(false)
      }
    })()
  }, [])

  if (loggedIn) {
    return (
      <>
        <InstanceTable />
      </>
    )
  } else {
    return (
      <>
        <LoginModal />
      </>
    )
  }
}

export default Instances;
