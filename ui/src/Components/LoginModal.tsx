import { Modal, Text, Button, Anchor } from "@mantine/core"
import { Link } from "react-router-dom"
import { userManager } from "../userManager"
import ModalTop from "./ModalTop"

export const LoginModal = () => {
  return (
    <Modal centered opened={true} title="Login or Sign Up" onClose={function (): void {
      throw new Error("Function not implemented.")
    }}>
      <ModalTop />
      <section style={{ maxWidth: "90%", margin: "auto" }}>
        <h1 style={{ textAlign: "center" }}>Login or Sign up</h1>
        <Text>
          Netsoc Cloud is free a service provided for UCC students by <Anchor href="https://netsoc.co/rk">UCC Netsoc</Anchor> to host their own containers and virtual machines.
        </Text>
        <br />
        <Text>
          As such, to gain access, you must be a UCC student and have a valid student number and email.
        </Text>
      </section>

      <nav style={{ margin: "2em auto 2em auto", display: "flex", flexDirection: "column", justifyContent: "center", width: "80%" }}>
        <Button fullWidth color="cyan.8" style={{ marginBottom: "1em" }} onClick={() => {
          userManager.signinRedirect({ redirectMethod: "replace" }).then(function () {
            console.log('signinRedirect done');
          }).catch((err) => {
            console.log(err);
          });
        }}>Login</Button>
        <Button fullWidth component={Link} to="/signup">Sign Up</Button>
      </nav>
    </Modal >
  )
}
