export interface Config {
    apiBaseUrl: string;
    oidcAuthority: string;
    hCaptchaSiteKey: string;
    sshUrl: string;
    sftpUrl: string;
}
// TODO: change defaults to netsoc.co
export const config: Config = {
    apiBaseUrl: (process.env.REACT_APP_NETSOC_API_URL ?? "https://api.beta.netsoc.cloud").replace(
        new RegExp('[/]+$'),
        ''
    ),
    oidcAuthority: process.env.REACT_APP_OIDC_AUTHORITY ?? "https://keycloak.netsoc.co/auth/realms/freeipa",
    hCaptchaSiteKey: "82ab2e7f-4765-4cff-ab41-648eb653ac11",
    sshUrl: process.env.REACT_APP_SSH_URL ?? '',
    sftpUrl: process.env.REACT_APP_SFTP_URL ?? ''
}

export default config
