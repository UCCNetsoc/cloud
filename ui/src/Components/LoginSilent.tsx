import { userManager } from "../userManager"

const LoginSilent = () => {
    // userManager.signinRedirectCallback().then
    userManager.signinSilent().then(function () {
      }).catch(function (err) {
        console.log(err);
      });
    return (<></>)
}

export default LoginSilent