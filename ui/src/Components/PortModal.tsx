import { ScrollArea, Divider, Code, TextInput, Switch, Button, Loader, NumberInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from "@mantine/notifications";
import { IconWorld, IconServer } from "@tabler/icons";
import { useContext, useEffect, useState } from "react";
import { AddInstancePort, GetFreePort } from "../api";
import { Cloud } from "../types";

import Dialog from './Dialog';
import ModalTop from "./ModalTop";

const PortModal = (props: { instance: Cloud.Instance }) => {
  const [loading, setLoading] = useState(false)
  const [ready, setReady] = useState(false)
  const [freePort, setFreePort] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!loading) {
      setLoading(true);
      (async () => {
        setFreePort(await GetFreePort(props.instance.type, props.instance.hostname));
        console.log(freePort)
        setReady(true);
      })();
    }
  }, [loading])

  const banned_ports = [
    21, 23, 25, 53, 143
  ]

  const form = useForm<{ external_port: number | undefined, internal_port: number | undefined }>({
    initialValues: {
      external_port: freePort,
      internal_port: undefined,
    },
    validate: (values) => ({
      external_port: values.external_port && values.external_port > 0 && values.external_port < 65536 && !banned_ports.includes(values.external_port) ? null : "Invalid port",
      internal_port: values.internal_port && values.internal_port > 0 && values.internal_port < 65536 ? null : "Invalid port",
    })
  })

  return (
    ready ? (
      <>
        <Dialog>
          <ScrollArea style={{ height: "700px", margin: "auto" }}>
            <h1 style={{ textAlign: "center" }}>Add a TCP Port</h1>
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
            </div>
            <Divider style={{
              width: "60%",
              margin: "0.4em auto"
            }} />
            <form
              onSubmit={form.onSubmit((values) => {
                showNotification({
                  title: "Adding Port...",
                  message: `Adding Port ${values.internal_port} to instance ${props.instance.hostname}`,
                  autoClose: true,
                  color: "cyan",
                  icon: <Loader />,
                })
                try {
                  if (values.external_port && values.internal_port) {
                    // invert the https value as 'true' interprets it so that the internal service is using https already
                    AddInstancePort(props.instance.type, props.instance.hostname, values.external_port, values.internal_port).then((status_code) => {
                      showNotification({
                        title:
                          <span style={{ display: "flex", alignItems: "center", }}>
                            <Loader sx={{ margin: "0 1em" }} /> <span>Added Port{props.instance.hostname}</span>
                          </span>,
                        message: `Port ${values.internal_port} added to instance ${props.instance.hostname}`,
                        autoClose: true,
                        color: "teal",
                        icon: <IconServer />,
                      })
                    })
                  }
                } catch (e: any) {
                  showNotification({
                    title: "Error adding Port",
                    message: e.message ? e.message : "Unkown error",
                    autoClose: true,
                    color: "red",
                    icon: <IconServer />,
                  })
                }
              })}
              style={{
                width: "80%",
                maxWidth: "500px",
                margin: "auto",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "space-evenly",
                height: "260px"
              }}>

              <NumberInput
                label="External Port"
                placeholder="External Port"
                value={form.values.external_port}
                onChange={(value) => form.setFieldValue("external_port", value)}
                required
                style={{ width: "100%" }}
              />

              <NumberInput
                label="Internal Port"
                placeholder="Internal Port"
                value={form.values.internal_port}
                onChange={(value) => form.setFieldValue("internal_port", value)}
                required
                style={{ width: "100%" }}
              />

              <Divider style={{
                width: "60%",
                margin: "0.4em auto"
              }} />

              <div style={{ paddingBottom: "1em" }}>
                <Button style={{ margin: "0 1em" }} type="submit">
                  Add Port
                </Button>
              </div>
            </form>
          </ScrollArea>
        </Dialog>
      </>)
      :
      <>
        <ModalTop />
        <div style={{
          width: "100%",
          height: "700px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <Loader />
        </div>
      </>
  )
}

export default PortModal;