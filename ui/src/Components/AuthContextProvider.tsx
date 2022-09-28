import { User } from "oidc-client-ts";
import { createContext, useEffect, useState } from "react";
import { userManager } from "../userManager";

// export const AuthContext = createContext({ user: null as User | null, setUser: (user: User | null) => { } });
export const AuthContext = createContext(null as User | null);

export const AuthProvider = (props: { children: JSX.Element }) => {
  // const [user, setUser] = useState<User | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    (async () => {
      setUser(await userManager.getUser())
    })();
  }, [])
  const val = {
    user: userManager.getUser(),
    // setUser: (user: User | null) => {
    //     setUser(user);
    // },
  }

  return (
    <AuthContext.Provider value={user}>
      {props.children}
    </AuthContext.Provider>
  )
}

export default AuthContext;
