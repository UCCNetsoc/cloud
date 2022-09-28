import HCaptcha from "@hcaptcha/react-hcaptcha";
import { Button, Checkbox, Modal, TextInput, Text } from "@mantine/core"
import { useForm } from "@mantine/form"
import { showNotification } from "@mantine/notifications";

import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom"
import { SendVerificationEmail, SignupUccStudent } from "../api";
import { DesktopContext } from "../App";
import ModalTop from "../Components/ModalTop";
import config from "../config";

const Signup = () => {
  const [captchaToken, setCaptchaToken] = useState("")
  const [tosOpen, setTosOpen] = useState(false);

  const desktop = useContext(DesktopContext)

  const navigate = useNavigate();
  const form = useForm({
    initialValues: {
      email: "",
      username: "",
      tos: false,
      member: false,
    },
    validate: {
      email: (value) => (/^\d+$/.test(value) ? null : "Must be a UCC Student ID"),
      username: (value) => (/^[a-zA-Z0-9-]*$/.test(value) ? null : "Username must be alphanumeric, and can contain dashes"),
      tos: (value: boolean) => ((value === true) ? null : "Must accept the TOS"),
      member: (value: boolean) => ((value === true) ? null : "Must be a member of UCC Netsoc"),
    }
  });

  return (
    <Modal fullScreen={!desktop} centered size="lg" opened={true} onClose={() => { navigate("/") }}>
      <ModalTop />
      <form style={{
        padding: "12px 0",
        maxWidth: "600px",
        minWidth: " 200px",
        width: "80%",
        margin: "auto",
        minHeight: "500px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-evenly"
      }} onSubmit={form.onSubmit((values) => {
        if (values.tos && values.member) {
          SignupUccStudent(values.username, values.email + "@umail.ucc.ie").then((resp) => {
            showNotification({
              title: "Signup created",
              message: resp.detail.msg
            })

            SendVerificationEmail(values.email + "@umail.ucc.ie", captchaToken).then((response) => {
              showNotification({
                title: "Email verification sent",
                message: response.detail.msg
              })

              navigate("/")
            }).catch(() => {
              showNotification({
                title: "Email verification failed to send",
                message: "If issues persist, contact the SysAdmins in the netsoc-cloud channel on the Discord"
              })
            })
          }).catch(() => {
            showNotification({
              title: "Failed to signup",
              message: "If issues persist, please ask in the netsoc-cloud channel on our discord."
            })
          })
        } else {
          showNotification({
            title: "You must be a UCC Netsoc member, and accept the ToS to create an account",
            message: undefined
          })
        }
      })}>
        <h1>Signup for Netsoc Cloud</h1>
        <TextInput rightSectionWidth={"200px"} rightSection={<span>@umail.ucc.ie</span>} {...form.getInputProps("email")} withAsterisk placeholder="studentnumber" label="Student Email" />
        <TextInput {...form.getInputProps("username")} withAsterisk placeholder="username-here" label="Username" />
        <nav>
          <ul style={{ listStyleType: "none" }}>
            <li style={{ margin: "0 0 0.4em 0" }}>
              <Checkbox {...form.getInputProps("member", { type: "checkbox" })} label={<span>I am a member of <Text sx={{ display: "inline", cursor: "pointer" }} color="blue" onClick={() => { window.open("https://netsoc.co/rk") }}>UCC Netsoc</Text></span>} />
            </li>
            <li>
              <Checkbox {...form.getInputProps("tos", { type: "checkbox" })} label={<span>I have read the <Text sx={{ display: "inline", cursor: "pointer" }} color="blue" onClick={() => { setTosOpen(true) }}>Terms of Service</Text></span>} />
            </li>
          </ul>
        </nav>
        <HCaptcha
          sitekey={config.hCaptchaSiteKey}
          onVerify={(token, ekey) => {
            setCaptchaToken(token)
          }}
        />
        <nav style={{ padding: "2em 0", display: "flex", flexDirection: "row-reverse" }}>
          <Button disabled={!form.values.tos || !form.values.member} type="submit">Sign up</Button>
        </nav>
      </form>
      <Modal opened={tosOpen} onClose={() => { setTosOpen(false) }} size="md" >
        <h1>Terms of Service</h1>
      </Modal>
    </Modal>
  )
}

export default Signup
