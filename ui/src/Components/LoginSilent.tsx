import { userManager } from "../userManager"

const LoginSilent = () => {
    // userManager.signinRedirectCallback().then
    userManager.signinSilent().then(function () {
      }).catch((err) => {
        console.log(err);
      });
    return (<></>)
}

export default LoginSilent
