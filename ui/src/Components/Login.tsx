import { userManager } from "../userManager"

const Login = () => {
    // userManager.signinRedirectCallback().then
    userManager.signinRedirect({redirectMethod: "replace"}).then(function () {
        console.log('signinRedirect done');
      }).catch(function (err) {
        console.log(err);
      });
    return (<></>)
}

export default Login