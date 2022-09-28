import { ScrollArea, Divider, Code, TextInput, Switch, Button, Loader, NumberInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from "@mantine/notifications";
import { IconWorld, IconServer } from "@tabler/icons";
import { useContext, useEffect, useState } from "react";
import { AddVhost, GetVhostRequirements } from "../api";
import { UserContext } from "../App";
import { Cloud } from "../types";

import Dialog from './Dialog';

const VhostModal = (props: { instance: Cloud.Instance }) => {
  const [vhostRequirements, setVhostRequirements] = useState<Cloud.VHostRequirements | null>(null);

  useEffect(() => {
    (async () => {
      setVhostRequirements(await GetVhostRequirements());
    })();
  }, [])

  const { user } = useContext(UserContext);

  const form = useForm<{ domain: string, port: number, https: boolean }>({
    initialValues: {
      domain: "",
      port: 80,
      https: true,
    },
    validate: (values) => ({
      domain: /^(?!:\/\/)(?=.{1,255}$)((.{1,63}\.){1,127}(?![0-9]*$)[a-z0-9-]+\.?)$/.test(values.domain) ? null : "Invalid hostname",
      port: values.port > 0 && values.port < 65536 ? null : "Invalid port",
      https: null
    })
  })

  return (
    <>
      <Dialog>
        <ScrollArea style={{ height: "700px", margin: "auto" }}>
          <h1 style={{ textAlign: "center" }}>Add a VHost</h1>
          <p style={{ width: "90%", maxWidth: "500px", margin: "auto", textAlign: "center" }}>A VHost forwards HTTP(s) traffic into your instance using a unique domain name.</p>
          <Divider style={{
            width: "60%",
            margin: "1em auto"
          }} />
          <div style={{ width: "80%", maxWidth: "400px", margin: "auto" }}>
            <section>
              <h4 style={{ margin: 0 }}>Using your <em>free</em> Netsoc Cloud domain</h4>
              <p>
                You can use any domain in the form of <Code sx={{ fontSize: "0.9em", whiteSpace: "nowrap" }}>*.netsoc.cloud</Code>
              </p>
            </section>
            <section>
              <h4 style={{ margin: 0 }}>Using your <em>own</em> domain</h4>
              <p>
                You can use any domain in the form of <Code sx={{ fontSize: "0.9em", whiteSpace: "nowrap" }}>*.netsoc.cloud</Code>
              </p>
              <ol>
                <li>Go to your domain registrar and add the following records:
                  <ul>
                    <li>
                      <Code>TXT</Code> record of key <Code>_netsoc</Code> and value <Code>{user?.profile.preferred_username}</Code>
                    </li>
                    <li>
                      <Code>A</Code> record of value <Code>{vhostRequirements?.user_domain.allowed_a_aaaa}</Code>
                    </li>
                  </ul>
                </li>
                <li>
                  Wait for the DNS records to propagate (this can take up to 24 hours)
                </li>
              </ol>
            </section>
          </div>
          <Divider style={{
            width: "60%",
            margin: "0.4em auto"
          }} />
          <form
            onSubmit={form.onSubmit((values) => {
              showNotification({
                title:
                  <span style={{ display: "flex", alignItems: "center", }}>
                    <Loader sx={{ margin: "0 1em" }} /> <span>Adding VHost{props.instance.hostname}</span>
                  </span>,
                message: `Adding VHost ${values.domain} to instance ${props.instance.hostname}`,
                autoClose: true,
                color: "cyan",
                icon: <Loader />,
              })
              try {
                // invert the https value as 'true' interprets it so that the internal service is using https already
                AddVhost(props.instance.type, props.instance.hostname, values.domain, values.port, !values.https).then((_status_code) => {
                  showNotification({
                    title: "Added VHost",
                    message: `VHost ${values.domain} added to instance ${props.instance.hostname}`,
                    autoClose: true,
                    color: "teal",
                    icon: <IconServer />,
                  })
                })
              } catch (e: any) {
                showNotification({
                  title: "Error adding VHost",
                  message: e.message ? e.message : "Unkown error",
                  autoClose: true,
                  color: "red",
                  icon: <IconServer />,
                })
              }
            })}
            style={{
              width: "100%",
              maxWidth: "800px",
              margin: "auto",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "space-evenly",
              height: "260px"
            }}>
            <TextInput style={{ width: "65%" }} label="Domain" placeholder={`${user?.profile.preferred_username}.netsoc.cloud`} type="text" {...form.getInputProps("domain")} icon={<IconWorld />} />
            <NumberInput style={{ width: "40%" }} label="Internal Port" defaultValue={80} type="number" {...form.getInputProps("port")} icon={<IconServer />} />
            <div>
              <Switch defaultChecked label="Managed SSL" {...form.getInputProps("https")} />
            </div>

            <Divider style={{
              width: "60%",
              margin: "0.4em auto"
            }} />

            <div style={{ paddingBottom: "1em" }}>
              <Button style={{ margin: "0 1em" }} type="submit">
                Add VHost
              </Button>
            </div>
          </form>
        </ScrollArea>
      </Dialog>
    </>
  )
}

export default VhostModal;
