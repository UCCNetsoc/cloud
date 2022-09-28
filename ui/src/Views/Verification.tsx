import { Button, Modal, PasswordInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from "@mantine/notifications";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { VerifyAccountSignup } from "../api";
import { DesktopContext } from "../App";
import ModalTop from "../Components/ModalTop";

const Verification = () => {

  const desktop = useContext(DesktopContext)
  const navigate = useNavigate()

  const { username, token } = useParams()

  const form = useForm<{ password: string, confirm_password: string }>({
    initialValues: {
      password: "",
      confirm_password: "",
    },
    validate: (values) => ({
      password: (values.password.length < 8 || values.password.length > 128) ? "Must be between 8 and 128 characters" : null,
      confirm_password: (values.password === values.confirm_password) ? null : "Passwords do not match"
    })
  })


  return (
    <>
      <Modal size="lg" fullScreen={!desktop} opened={true} onClose={() => { navigate("/") }}>
        <ModalTop />
        <div style={{ paddingTop: "12px" }}>
          <h1>Email Verification for {username}</h1>
          <form style={{ display: "flex", flexDirection: "column", justifyContent: "space-evenly", height: "240px"}}
            onSubmit={form.onSubmit((values) => {
              VerifyAccountSignup(username as string, token as string, values.password).then((resp) => {
                showNotification({
                  title: "Verified account",
                  message: resp.detail.msg
                })
                navigate("/")
              }).catch(() => {
                showNotification({
                  title: "Failed to verify account",
                  message: "If issues persist, leave a message in netsoc-cloud channel on the Discord."
                })
              })
            })}>
            <PasswordInput label="Password" withAsterisk {...form.getInputProps("password")} />
            <PasswordInput label="Confirm Password" withAsterisk {...form.getInputProps("confirm_password")} />
            <Button type="submit">Sign Up</Button>
            {!desktop ? (
              <Button onClick={() => { navigate("/") }}>Cancel</Button>
            ) : <></>}
          </form>
        </div>
      </Modal>
    </>
  )
}

export default Verification;
