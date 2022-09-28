import { Avatar, Button, Paper, Table, Text } from "@mantine/core";
import userEvent from "@testing-library/user-event";
import { IdTokenClaims, User } from "oidc-client-ts";
import { useEffect, useState } from "react";
import { userManager } from "../userManager";

function Account() {
  const [user, setAccount] = useState<IdTokenClaims | null>(null)

  useEffect(() => {
    (async () => {
      const oidcUser = await userManager.getUser()
      setAccount(oidcUser?.profile ?? null)
    })()
  }, [])

  return (
    <>
      <Paper p="xl">
        <h1>Account</h1>
        <Table>
          <tbody>
            <tr>
              <td>
                Username
              </td>
              <td>
                {user?.preferred_username}
              </td>
            </tr>
            <tr>
              <td>
                Email
              </td>
              <td>
                {user?.email}
              </td>
            </tr>
          </tbody>
        </Table>
        <Text sx={{ margin: "25px 0 25px 0", maxWidth: 800 }}>
          <p>
            Your account is used for logging into UCC Netsoc web services
          </p>
          <p>
            Please remember to keep the Terms of Use and its Acceptable Use Policy in mind as you share server hardware with our other users.
          </p>
        </Text>

        <nav style={{ maxWidth: 600, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
          <Button color="cyan.8" onClick={() => {
            userManager.signoutPopup().then(() => {
              window.location.href = "/"
            })
          }}>Logout</Button>
          <Button>
            Reset Password
          </Button>
          <Button color="yellow.8">
            Request GDPR Data
          </Button>
          <Button color="red.6">
            Delete Account
          </Button>
        </nav>
      </Paper>
    </>
  )
}

export default Account;
